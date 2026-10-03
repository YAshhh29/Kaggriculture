"""Where a candidate differs from the top of the ladder, parameter by parameter.

For each sampled tape this plays the candidate against that team's recorded
play, and separately replays the tape's own game, so every number is measured
on the same world: what the top-200 team did, and what we did facing it.

    python -m tools.eval.failure_grid candidates.candidate_j:agent --tapes 12
"""

from __future__ import annotations

import argparse
import base64
import json
import random
import statistics
import sys
import zlib
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TAPES = ROOT / "kaggle_cache" / "top200_tapes"
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
         "WOOL", "FERTILIZER")


def side_metrics(env, side, sales):
    mix = Counter()
    for st in env.steps:
        act = st[side].get("action") or {}
        for u in [act.get("farmer")] + list(act.get("hands") or []):
            if isinstance(u, list) and u:
                mix["move" if u[0] in MOVES else u[0]] += 1
    total = max(1, sum(mix.values()))
    work = sum(v for k, v in mix.items() if k not in ("move", "PASS"))
    out = {
        "score": float(env.state[side].reward or 0),
        "turns": total,
        "work%": 100.0 * work / total,
        "walk%": 100.0 * mix["move"] / total,
        "idle%": 100.0 * mix["PASS"] / total,
        "water": mix["WATER"], "harvest": mix["HARVEST"],
        "plant": mix["PLANT"], "feed": mix["FEED"], "care": mix["CARE"],
        "manure": mix["COLLECT_FERTILIZER"], "fertilise": mix["FERTILIZE"],
        "units_sold": sum(sales.values()),
    }
    for day in (6, 12, 18, 24):
        i = min(day * 24 + 23, len(env.steps) - 1)
        farm = env.steps[i][0]["observation"]["farms"][side]
        out[f"cash_d{day}"] = float(farm["money"])
        out[f"crops_d{day}"] = sum(
            1 for r in farm["tiles"] for t in r
            if isinstance(t, dict) and t.get("kind") == "PLANT")
        out[f"herd_d{day}"] = sum(
            1 for r in farm["tiles"] for t in r
            if isinstance(t, dict) and "animal" in t)
        out[f"hands_d{day}"] = len(farm.get("hands") or [])
    return out


def play(job):
    spec, path, mode = job
    sys.path.insert(0, str(ROOT))
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent
    from tools.eval.measure_panel import resolve

    record = json.loads(Path(path).read_text(encoding="utf-8"))
    unpack = lambda b: json.loads(zlib.decompress(base64.b64decode(b)).decode())
    theirs = build_replay_agent(tuple(unpack(record["actions_zlib_b64"])))
    seat = 0
    if mode == "tape":
        opponent = build_replay_agent(
            tuple(unpack(record["opponent_actions_zlib_b64"])))
        players = [theirs, opponent]
    else:
        players = [resolve(spec), theirs]

    ctx = {"farms": None}
    sales = Counter()
    om, oc = K._process_market, K._commit_unit

    def market(state, env):
        ctx["farms"] = state[0].observation.farms
        return om(state, env)

    def commit(op, item, price, farm, private, mk, cap=100):
        ok = oc(op, item, price, farm, private, mk, cap)
        if ok and op == "SELL":
            who = next((i for i, f in enumerate(ctx["farms"] or [])
                        if f is farm), None)
            if who == seat:
                sales[item] += 1
        return ok

    K._process_market, K._commit_unit = market, commit
    try:
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": record["seed"],
                                  "runTimeout": 36000, "actTimeout": 60},
                   debug=False)
        env.run(players)
    finally:
        K._process_market, K._commit_unit = om, oc
    return {"mode": mode, "team": record.get("source_team"),
            **side_metrics(env, seat, sales)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--tapes", type=int, default=12)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    paths = sorted(str(p) for p in TAPES.glob("ep*.json"))
    random.Random(11).shuffle(paths)
    paths = paths[: args.tapes]
    jobs = [(args.spec, p, m) for p in paths for m in ("tape", "ours")]
    with Pool(args.workers) as pool:
        rows = pool.map(play, jobs)

    tape = [r for r in rows if r["mode"] == "tape"]
    ours = [r for r in rows if r["mode"] == "ours"]
    keys = ["score", "units_sold", "work%", "walk%", "idle%", "water",
            "harvest", "plant", "feed", "care", "manure", "fertilise",
            "cash_d6", "cash_d12", "cash_d18", "cash_d24",
            "crops_d12", "crops_d18", "crops_d24",
            "herd_d12", "herd_d18", "hands_d12", "hands_d18"]
    print(f"\n{args.spec} vs {len(paths)} top-200 teams (medians)\n")
    print(f"  {'parameter':14s} {'OURS':>10s} {'TOP-200':>10s} {'ratio':>8s}  verdict")
    for k in keys:
        a = statistics.median(r[k] for r in ours)
        b = statistics.median(r[k] for r in tape)
        ratio = (a / b) if b else float("nan")
        flag = ("OK" if 0.9 <= ratio <= 1.15 else
                "LOW" if ratio < 0.9 else "HIGH")
        print(f"  {k:14s} {a:10,.0f} {b:10,.0f} {ratio:8.2f}  {flag}")


if __name__ == "__main__":
    main()
