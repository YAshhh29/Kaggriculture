"""Wheat in the band games, gross and net of purchases.

tools/analysis/sales_race.py counts SELL units and revenue only. Many
2600-2700 teams buy wheat right before the town's 4-step draw and sell it one
step later, so their gross wheat sales include units they bought a step
earlier. This replays the same faithful band games (Agent A against a
recorded 2600-2700 team, exact: action stored at t+1 is applied at step t)
and prints, per game (A minus team, median over games): wheat harvested,
wheat SELL units and revenue (what sales_race shows), wheat BUY units and
cost, and the net.

    python -m tools.analysis.l2_wheat_band_net --workers 1
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.arena.arena import CONFIG, GAMES, _unpack  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "wheat"


def replay(job):
    game_id, ours = job
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine

    record = json.loads((GAMES / f"{game_id}.json").read_text(encoding="utf-8"))
    tapes = [_unpack(t) for t in record["tapes"]]
    env = make("kaggriculture", configuration={**CONFIG, "seed": record["seed"]}, debug=False)
    env.reset()
    book = {s: {"harvest": 0, "sold": 0, "sold_$": 0.0, "bought": 0, "bought_$": 0.0}
            for s in (0, 1)}
    now = {"farms": None}
    raw_commit, raw_unit, raw_market = engine._commit_unit, engine._apply_unit_action, engine._process_market

    def seat_of(farm):
        return next((i for i, f in enumerate(now["farms"] or []) if f is farm), None)

    def process_market(state, env_):
        now["farms"] = state[0].observation.farms
        return raw_market(state, env_)

    def commit(op, item, price, farm, private, market, *rest):
        ok = raw_commit(op, item, price, farm, private, market, *rest)
        if ok and item == "WHEAT":
            s = seat_of(farm)
            if s is not None and op == "SELL":
                book[s]["sold"] += 1
                book[s]["sold_$"] += price
            elif s is not None and op == "BUY_PRODUCT":
                book[s]["bought"] += 1
                book[s]["bought_$"] += price
        return ok

    def unit(farm, private, idx, action, *rest):
        before = int(private["inventories"][idx].get("WHEAT", 0)) if idx < len(private["inventories"]) else 0
        out = raw_unit(farm, private, idx, action, *rest)
        if isinstance(action, list) and action and action[0] == "HARVEST":
            after = int(private["inventories"][idx].get("WHEAT", 0)) if idx < len(private["inventories"]) else 0
            if after > before:
                s = seat_of(farm)
                if s is not None:
                    book[s]["harvest"] += after - before
        return out

    def interpreter_wrap(raw):
        def inner(state, e):
            now["farms"] = state[0].observation.farms if getattr(state[0].observation, "farms", None) else None
            return raw(state, e)
        return inner

    engine._commit_unit, engine._apply_unit_action, engine._process_market = commit, unit, process_market
    env.interpreter = interpreter_wrap(env.interpreter)
    try:
        for t in range(719):
            env.step([tapes[0][t + 1], tapes[1][t + 1]])
    finally:
        engine._commit_unit, engine._apply_unit_action, engine._process_market = raw_commit, raw_unit, raw_market
    final = [float(env.state[i].reward or 0) for i in (0, 1)]
    return {"game_id": game_id, "ours": ours, "book": book, "final": final}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", default="A")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    rows = [r for r in json.loads((ROOT / "rl/data/band_panel/band_2600_2900.json").read_text(encoding="utf-8"))
            if r.get("agent") == args.agent and "ours" in r and r["score"] < 2700
            and r["theirs"] >= 0.9 * r["recorded"]]
    with Pool(args.workers, maxtasksperchild=4) as pool:
        games = list(pool.imap_unordered(replay, [(r["game_id"], 1 - r["seat"]) for r in rows]))
    out = []
    for label, keep in (("A LOST", False), ("A WON", True), ("ALL", None)):
        sel = [g for g in games if keep is None or (g["final"][g["ours"]] > g["final"][1 - g["ours"]]) == keep]
        if not sel:
            continue
        print(f"\n{args.agent} {label}: {len(sel)} band games, us minus team (median / mean per game)")
        for k in ("harvest", "sold", "sold_$", "bought", "bought_$"):
            d = [g["book"][g["ours"]][k] - g["book"][1 - g["ours"]][k] for g in sel]
            print(f"   wheat {k:10s} {statistics.median(d):+10,.1f} {statistics.mean(d):+10,.1f}")
        net = [(g["book"][g["ours"]]["sold_$"] - g["book"][g["ours"]]["bought_$"])
               - (g["book"][1 - g["ours"]]["sold_$"] - g["book"][1 - g["ours"]]["bought_$"]) for g in sel]
        netu = [(g["book"][g["ours"]]["sold"] - g["book"][g["ours"]]["bought"])
                - (g["book"][1 - g["ours"]]["sold"] - g["book"][1 - g["ours"]]["bought"]) for g in sel]
        fin = [g["final"][g["ours"]] - g["final"][1 - g["ours"]] for g in sel]
        print(f"   wheat net units    {statistics.median(netu):+10,.1f} {statistics.mean(netu):+10,.1f}")
        print(f"   wheat net $        {statistics.median(net):+10,.1f} {statistics.mean(net):+10,.1f}")
        print(f"   final margin       {statistics.median(fin):+10,.1f} {statistics.mean(fin):+10,.1f}")
        out.append({"label": label, "games": len(sel)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"band_net_{args.agent}.json").write_text(json.dumps(games, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
