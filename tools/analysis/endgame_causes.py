"""Why the opponent out-sells us late in close games: slot, decision or logistics.

For each of our close live games (exact replay of both tapes), every unit the
opponent sold from --from-day on is put in one of three bins by what we were
doing at that step:

  same step  we sold the same good in the same step (queue slot / quantity)
  held       we had the good in the shed and did not sell it (a selling decision)
  not held   we had none in the shed (it was on the plants/animals or being
             carried: logistics)

and valued at what they got minus what we got for the same good over the
same period (our average price). Positive = coins they earned that a better
schedule on our side could have taken.

    python -m tools.analysis.endgame_causes --submissions 56601363 56601249 56609589
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TAPES = ROOT / "rl" / "data" / "our_live_tapes"
ITEMS = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")


def one(job):
    ep, from_day = job[:2]
    factory = job[2] if len(job) > 2 else None
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent
    from tools.data.extract_live_tapes import unpack

    rec = json.loads((TAPES / f"ep{ep}.json").read_text(encoding="utf-8"))
    side = int(rec["our_side"])
    fills: list = []
    cur: dict = {}
    orig_pm, orig_cu = K._process_market, K._commit_unit

    def pm(state, env):
        cur["step"] = int(state[0].observation.step)
        cur["farms"] = list(state[0].observation.farms)
        return orig_pm(state, env)

    def cu(op, item, price, farm, private, market, cap=100):
        ok = orig_cu(op, item, price, farm, private, market, cap)
        if ok and op == "SELL" and item in ITEMS:
            who = [f is farm for f in cur["farms"]].index(True)
            fills.append((cur["step"], who == side, item, price))
        return ok

    K._process_market, K._commit_unit = pm, cu
    try:
        if factory:               # a candidate in our seat instead of our live moves
            import importlib
            mod, fn = factory.split(":")
            us = getattr(importlib.import_module(mod), fn)()
        else:
            us = build_replay_agent(tuple(unpack(rec["our_actions_zlib_b64"])))
        them = build_replay_agent(tuple(unpack(rec["opp_actions_zlib_b64"])))
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": rec["seed"],
                                                   "runTimeout": 36000, "actTimeout": 60}, debug=False)
        env.run([us, them] if side == 0 else [them, us])
    except Exception as error:
        return {"ep": ep, "error": repr(error)}
    finally:
        K._process_market, K._commit_unit = orig_pm, orig_cu
    # our shed at the start of each step (before its unit actions and market)
    shed = {t: dict(env.steps[t][side]["observation"]["private"].get("shed") or {})
            for t in range(len(env.steps))}
    first = from_day * 24
    ours = defaultdict(list)
    for step, mine, item, price in fills:
        if mine and step >= first:
            ours[item].append(price)
    our_avg = {i: sum(v) / len(v) for i, v in ours.items() if v}
    our_steps = {(step, item) for step, mine, item, _ in fills if mine}
    bins = defaultdict(lambda: defaultdict(float))
    units = defaultdict(lambda: defaultdict(int))
    for step, mine, item, price in fills:
        if mine or step < first:
            continue
        if (step, item) in our_steps:
            b = "same step"
        elif int(shed.get(step, {}).get(item, 0)) > 0:
            b = "held"
        else:
            b = "not held"
        ref = our_avg.get(item, price)
        bins[item][b] += price - ref
        units[item][b] += 1
    us_r, them_r = env.state[side].reward or 0.0, env.state[1 - side].reward or 0.0
    return {"ep": ep, "won": us_r > them_r, "margin": us_r - them_r,
            "bins": {i: dict(v) for i, v in bins.items()},
            "units": {i: dict(v) for i, v in units.items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions", type=int, nargs="*", default=[])
    ap.add_argument("--close", type=float, default=3000)
    ap.add_argument("--from-day", type=int, default=24)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=str(ROOT / "rl" / "data" / "l2" / "eval" / "endgame_causes.json"))
    ap.add_argument("--factory", default=None, help="module:function in our seat (default: our live moves)")
    ap.add_argument("--episodes", type=int, nargs="*", default=None, help="only these games")
    args = ap.parse_args()
    eps = []
    for p in sorted(TAPES.glob("ep*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if args.episodes is not None:
            if r["episode_id"] in args.episodes:
                eps.append(r["episode_id"])
        elif (r.get("submission") in args.submissions
                and abs(r["rewards"]["us"] - r["rewards"]["them"]) < args.close):
            eps.append(r["episode_id"])
    print(f"{len(eps)} close games", flush=True)
    with Pool(args.workers) as pool:
        rows = pool.map(one, [(e, args.from_day, args.factory) for e in eps])
    Path(args.out).write_text(json.dumps(rows), encoding="utf-8")
    rows = [r for r in rows if "error" not in r]
    for lab, sel in (("LOST", [r for r in rows if not r["won"]]), ("WON", [r for r in rows if r["won"]])):
        if not sel:
            continue
        n = len(sel)
        print(f"{lab}: {n} games. Opponent's price edge over our average, coins a game "
              f"(units a game), from day {args.from_day}:")
        print(f"   {'item':10s} {'same step':>18s} {'held':>18s} {'not held':>18s}")
        tot = defaultdict(float)
        for it in ITEMS:
            cells = []
            for b in ("same step", "held", "not held"):
                v = sum(r["bins"].get(it, {}).get(b, 0.0) for r in sel) / n
                u = sum(r["units"].get(it, {}).get(b, 0) for r in sel) / n
                tot[b] += v
                cells.append(f"{v:+8.1f} ({u:5.1f})")
            print(f"   {it:10s} " + " ".join(f"{c:>18s}" for c in cells))
        print(f"   {'total':10s} " + " ".join(f"{tot[b]:+18.1f}" for b in ("same step", "held", "not held")))


if __name__ == "__main__":
    main()
