"""Who sold what, when and at what price, in a real game (exact replay).

Replays both recorded action tapes of one of our live games (seed and seat
from rl/data/our_live_tapes) with the engine's per-unit commit instrumented,
so every filled market unit is logged: step, player, order, item, price.
Summaries compare our sales with the opponent's per item over a day range,
which is where close mirror games are decided.

    python -m tools.analysis.endgame_fills 114140460 114131655 --from-day 22
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TAPES = ROOT / "rl" / "data" / "our_live_tapes"


def fills(episode: int, factory: str | None = None) -> tuple[dict, list]:
    """Fills of the live game, or of `factory` (module:function) replayed in our seat."""
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent
    from tools.data.extract_live_tapes import unpack

    rec = json.loads((TAPES / f"ep{episode}.json").read_text(encoding="utf-8"))
    side = int(rec["our_side"])
    log: list = []
    cur: dict = {}
    orig_pm, orig_cu = K._process_market, K._commit_unit

    def pm(state, env):
        cur["step"] = int(state[0].observation.step)
        cur["farms"] = list(state[0].observation.farms)
        return orig_pm(state, env)

    def cu(op, item, price, farm, private, market, cap=100):
        ok = orig_cu(op, item, price, farm, private, market, cap)
        if ok:
            who = [f is farm for f in cur["farms"]].index(True)
            log.append((cur["step"], "us" if who == side else "them", op, item, price))
        return ok

    K._process_market, K._commit_unit = pm, cu
    try:
        if factory:
            import importlib
            mod, fn = factory.split(":")
            us = getattr(importlib.import_module(mod), fn)()
        else:
            us = build_replay_agent(tuple(unpack(rec["our_actions_zlib_b64"])))
        them = build_replay_agent(tuple(unpack(rec["opp_actions_zlib_b64"])))
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": rec["seed"],
                                                   "runTimeout": 36000, "actTimeout": 60}, debug=False)
        env.run([us, them] if side == 0 else [them, us])
    finally:
        K._process_market, K._commit_unit = orig_pm, orig_cu
    rec["replayed"] = {"us": env.state[side].reward, "them": env.state[1 - side].reward}
    return rec, log


def summarise(rec: dict, log: list, from_day: int) -> None:
    print(f"ep {rec['episode_id']} vs {rec.get('opponent')}: live {rec['rewards']} replayed {rec['replayed']}")
    rev = defaultdict(lambda: [0, 0.0])
    for step, who, op, item, price in log:
        if step // 24 < from_day:
            continue
        sign = 1 if op == "SELL" else -1
        k = (item, who, op)
        rev[k][0] += 1
        rev[k][1] += price
    items = sorted({k[0] for k in rev})
    print(f"  from day {from_day}: item  | us units  $  avg | them units  $  avg | us - them $")
    for it in items:
        u = rev.get((it, "us", "SELL"), [0, 0.0])
        t = rev.get((it, "them", "SELL"), [0, 0.0])
        ub = rev.get((it, "us", "BUY_PRODUCT"), [0, 0.0]) if it in ("WHEAT", "FERTILIZER") else [0, 0.0]
        tb = rev.get((it, "them", "BUY_PRODUCT"), [0, 0.0]) if it in ("WHEAT", "FERTILIZER") else [0, 0.0]
        line = (f"  {it:10s} | {u[0]:5d} {u[1]:8.0f} {u[1]/max(1,u[0]):6.1f} | {t[0]:5d} {t[1]:8.0f} "
                f"{t[1]/max(1,t[0]):6.1f} | {u[1]-t[1]:+8.0f}")
        if ub[0] or tb[0]:
            line += f"   buys us {ub[0]} (${ub[1]:.0f}) them {tb[0]} (${tb[1]:.0f})"
        print(line)
    spend = defaultdict(float)
    for step, who, op, item, price in log:
        if step // 24 >= from_day and op in ("BUY_SEED", "BUY_ANIMAL"):
            spend[(who, op, item)] += price
    if spend:
        print("  other spending:", {f"{k[0]}:{k[2]}": round(v) for k, v in sorted(spend.items())})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", type=int, nargs="+")
    ap.add_argument("--from-day", type=int, default=22)
    ap.add_argument("--dump", default=None, help="write all fills to this json")
    ap.add_argument("--factory", default=None, help="module:function to play our seat (default: our live tape)")
    args = ap.parse_args()
    allfills = {}
    for ep in args.episodes:
        rec, log = fills(ep, args.factory)
        summarise(rec, log, args.from_day)
        allfills[ep] = log
    if args.dump:
        Path(args.dump).write_text(json.dumps(allfills), encoding="utf-8")


if __name__ == "__main__":
    main()
