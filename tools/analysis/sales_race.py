"""Who wins the market in near-mirror games: every unit sold, by item and day.

Replays arena games exactly and logs each unit the engine commits (player,
step, buy/sell, item, price) by wrapping the engine's own _commit_unit. Then,
for the named agent against its opponent, prints per item the difference in
units sold, revenue and average price, split into early / middle / late game,
for games it lost and games it won.

    python -m tools.analysis.sales_race A --results rl/data/band_panel/band_2600_2900.json --high 2700
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.arena.arena import CONFIG, GAMES, _unpack  # noqa: E402

PHASES = (("d0-14", 0, 15), ("d15-24", 15, 25), ("d25-29", 25, 30))


def race(job) -> dict:
    game_id, ours = job
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine

    record = json.loads((GAMES / f"{game_id}.json").read_text(encoding="utf-8"))
    tapes = [_unpack(t) for t in record["tapes"]]
    env = make("kaggriculture", configuration={**CONFIG, "seed": record["seed"]},
               debug=False)
    env.reset()
    log = []
    now = {"step": 0}
    original = engine._commit_unit
    original_market = engine._process_market

    def process_market(state, env_):
        # The interpreter works on its own copies of the farms; remember the
        # list the market step is using so each committed unit can be placed.
        now["farms"] = state[0].observation.farms
        return original_market(state, env_)

    def commit(op, item, price, farm, private, market, *rest):
        ok = original(op, item, price, farm, private, market, *rest)
        if ok:
            player = next(i for i, f in enumerate(now["farms"]) if f is farm)
            log.append((player, now["step"], op, item, price))
        return ok

    engine._commit_unit = commit
    engine._process_market = process_market
    try:
        for t in range(719):
            now["step"] = t
            env.step([tapes[0][t + 1], tapes[1][t + 1]])
    finally:
        engine._commit_unit = original
        engine._process_market = original_market
    out = defaultdict(lambda: [0, 0.0, 0, 0.0])   # units, revenue (ours), units, revenue (theirs)
    for player, step, op, item, price in log:
        if op != "SELL":
            continue
        phase = next(p for p, lo, hi in PHASES if lo <= step // 24 < hi)
        cell = out[f"{item}|{phase}"]
        k = 0 if player == ours else 2
        cell[k] += 1
        cell[k + 1] += price
    final = [float(env.state[i].reward or 0) for i in (0, 1)]
    return {"game_id": game_id, "won": final[ours] > final[1 - ours], "sales": dict(out)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agent")
    ap.add_argument("--results", default="rl/data/band_panel/band_2600_2900.json")
    ap.add_argument("--low", type=int, default=2600)
    ap.add_argument("--high", type=int, default=2700)
    ap.add_argument("--min-fidelity", type=float, default=0.9)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    rows = [r for r in json.loads((ROOT / args.results).read_text(encoding="utf-8"))
            if r.get("agent") == args.agent and "ours" in r
            and args.low <= r["score"] < args.high
            and r["theirs"] >= args.min_fidelity * r["recorded"]]
    with Pool(args.workers, maxtasksperchild=2) as pool:
        games = list(pool.imap_unordered(race, [(r["game_id"], 1 - r["seat"]) for r in rows]))

    for label, keep in (("LOST", False), ("WON", True)):
        group = [g for g in games if g["won"] == keep]
        if not group:
            continue
        keys = sorted({k for g in group for k in g["sales"]})
        print(f"\n{args.agent} {label} {len(group)} games: per game, us minus them "
              f"(median over games)")
        print(f"  {'item':12s} {'phase':7s} {'units':>7s} {'revenue':>9s} {'our avg $':>10s} {'their avg $':>12s}")
        rows_out = []
        for key in keys:
            item, phase = key.split("|")
            cells = [g["sales"].get(key, [0, 0, 0, 0]) for g in group]
            du = statistics.median(c[0] - c[2] for c in cells)
            dr = statistics.median(c[1] - c[3] for c in cells)
            ou = sum(c[0] for c in cells)
            tu = sum(c[2] for c in cells)
            oa = sum(c[1] for c in cells) / ou if ou else 0
            ta = sum(c[3] for c in cells) / tu if tu else 0
            rows_out.append((abs(dr), item, phase, du, dr, oa, ta))
        for _, item, phase, du, dr, oa, ta in sorted(rows_out, reverse=True)[:18]:
            print(f"  {item:12s} {phase:7s} {du:+7.1f} {dr:+9,.0f} {oa:10.1f} {ta:12.1f}")


if __name__ == "__main__":
    main()
