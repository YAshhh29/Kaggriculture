"""What bracket teams actually do, per day, compared with what K does.

The roster (bracket_roster.py) says who is in the band and which games we
hold. This says what they DO in those games: crew, worked tiles, herd,
money and market traffic, day by day, replayed from their own recorded
actions -- and the same profile for our agent playing the same opponent
on the same seed, so the two columns are comparable rather than two
unrelated numbers.

Findings belong in docs/, not here; this only produces the evidence.

    python -m tools.analysis.bracket_profile --tapes 20 --spec rl.candidate_k:agent
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
import zlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TAPES = ROOT / "kaggle_cache" / "top200_tapes"
TURNS = 24
MARKS = (4, 9, 14, 19, 24, 29)


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def _profile(env, seat: int) -> dict[int, dict[str, float]]:
    """Per-day snapshot of the farm at `seat`."""
    out: dict[int, dict[str, float]] = {}
    for day in range(30):
        index = min(day * TURNS + TURNS - 1, len(env.steps) - 2)
        if index < 0:
            continue
        view = env.steps[index][seat]
        obs = view.get("observation") or {}
        farms = obs.get("farms") or []
        if seat >= len(farms) or not isinstance(farms[seat], dict):
            continue
        farm = farms[seat]
        plants = animals = worked = 0
        for row in farm.get("tiles") or []:
            for tile in row:
                if not isinstance(tile, dict):
                    continue
                if "animal" in tile:
                    animals += 1
                    worked += 1
                elif tile.get("kind") == "PLANT":
                    plants += 1
                    worked += 1
        out[day] = {
            "money": float(farm.get("money", 0) or 0),
            "hands": float(len(farm.get("hands") or [])),
            "plants": float(plants),
            "animals": float(animals),
            "worked": float(worked),
        }
    return out


# A SELL order is filled unit by unit until the shed empties, and only the
# REMAINDER is aborted -- see `_commit_unit` in the engine. So "SELL WHEAT
# 1000" is a legitimate "dump whatever I hold" idiom, not an oversized
# order, and summing requested quantities measures intent rather than
# trade. H2's route uses that idiom 84 times a game; summing it naively
# reported 85,755 units sold against a bracket team's 3,439 and looked
# like a catastrophic bug that was not there. Requested quantity is not
# traffic: count dump orders separately and judge real lot size from the
# orders that name a specific amount.
DUMP = 1000


def _market(env, seat: int) -> dict[str, float]:
    sells = buys = buy_units = dumps = 0
    lots: list[int] = []
    for index in range(len(env.steps) - 1):
        action = env.steps[index][seat].get("action") or {}
        for order in action.get("market") or []:
            if not (isinstance(order, list) and order):
                continue
            if order[0] == "SELL" and len(order) >= 3:
                try:
                    q = int(order[2])
                except (TypeError, ValueError):
                    continue
                sells += 1
                if q >= DUMP:
                    dumps += 1
                else:
                    lots.append(q)
            elif order[0] in ("BUY_PRODUCT",) and len(order) >= 3:
                try:
                    buys += 1
                    buy_units += int(order[2])
                except (TypeError, ValueError):
                    pass
    lots.sort()
    return {"sell_orders": sells, "dump_orders": dumps,
            "sized_units": sum(lots),
            "buy_orders": buys, "buy_units": buy_units,
            "median_lot": statistics.median(lots) if lots else 0.0,
            "p90_lot": lots[int(0.9 * (len(lots) - 1))] if lots else 0.0}


def run_tape(path: Path, spec: str) -> tuple[dict, dict, dict, dict, str] | None:
    from kaggle_environments import make
    from rl.replay_agent import build_replay_agent
    from tools.eval.measure_panel import resolve

    record = json.loads(path.read_text(encoding="utf-8"))
    seat = int(record["seat"])
    theirs = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    opp = build_replay_agent(_unpack(record["opponent_actions_zlib_b64"]))
    cfg = {"episodeSteps": 720, "seed": record["seed"],
           "runTimeout": 36000, "actTimeout": 60}

    players = [None, None]
    players[seat] = theirs
    players[1 - seat] = opp
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run(players)
    them = _profile(env, seat)
    them_mkt = _market(env, seat)

    # Ours, same seed, same opponent recording, same seat.
    mine = resolve(spec)
    players2 = [None, None]
    players2[seat] = mine
    players2[1 - seat] = build_replay_agent(_unpack(
        record["opponent_actions_zlib_b64"]))
    env2 = make("kaggriculture", configuration=cfg, debug=False)
    env2.run(players2)
    us = _profile(env2, seat)
    us_mkt = _market(env2, seat)
    return them, us, them_mkt, us_mkt, str(record.get("source_team", "?"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", default="rl.candidate_k:agent")
    ap.add_argument("--tapes", type=int, default=20)
    ap.add_argument("--low", type=float, default=2600.0)
    ap.add_argument("--high", type=float, default=2900.0)
    args = ap.parse_args()

    chosen: list[Path] = []
    for path in sorted(TAPES.glob("ep*.json")):
        try:
            rating = json.loads(path.read_text(encoding="utf-8"))["team_score"]
        except Exception:
            continue
        if isinstance(rating, (int, float)) and args.low <= rating <= args.high:
            chosen.append(path)
        if len(chosen) >= args.tapes:
            break

    them_all: dict[int, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list))
    us_all: dict[int, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list))
    them_mkts: list[dict] = []
    us_mkts: list[dict] = []
    names: list[str] = []

    for path in chosen:
        try:
            got = run_tape(path, args.spec)
        except Exception as error:
            print(f"  {path.name}: {type(error).__name__} {error}")
            continue
        if not got:
            continue
        them, us, tm, um, name = got
        names.append(name)
        them_mkts.append(tm)
        us_mkts.append(um)
        for day, vals in them.items():
            for k, v in vals.items():
                them_all[day][k].append(v)
        for day, vals in us.items():
            for k, v in vals.items():
                us_all[day][k].append(v)

    print(f"\n{len(names)} bracket games replayed "
          f"({args.low:.0f}-{args.high:.0f}); ours = {args.spec}")
    print(f"teams: {', '.join(sorted(set(names))[:12])}"
          f"{' ...' if len(set(names)) > 12 else ''}\n")

    head = (f"  {'day':>4} | {'THEM hands':>10} {'plants':>7} {'animals':>8} "
            f"{'money':>9} | {'US hands':>9} {'plants':>7} {'animals':>8} "
            f"{'money':>9}")
    print(head)
    for day in MARKS:
        if day not in them_all or day not in us_all:
            continue
        t, u = them_all[day], us_all[day]

        def med(d, k):
            return statistics.median(d[k]) if d.get(k) else 0.0

        print(f"  {day:4d} | {med(t,'hands'):10.1f} {med(t,'plants'):7.1f} "
              f"{med(t,'animals'):8.1f} {med(t,'money'):9,.0f} | "
              f"{med(u,'hands'):9.1f} {med(u,'plants'):7.1f} "
              f"{med(u,'animals'):8.1f} {med(u,'money'):9,.0f}")

    def agg(rows, key):
        vals = [r[key] for r in rows if r]
        return statistics.median(vals) if vals else 0.0

    print("\n  market traffic, median per game:")
    print(f"    {'':22s} {'THEM':>10} {'US':>10}")
    for key, label in (("sell_orders", "sell orders"),
                       ("dump_orders", "of those, dump-all"),
                       ("median_lot", "median sized lot"),
                       ("p90_lot", "p90 sized lot"),
                       ("sized_units", "units in sized lots"),
                       ("buy_orders", "buy orders"),
                       ("buy_units", "units bought")):
        print(f"    {label:22s} {agg(them_mkts, key):10,.1f} "
              f"{agg(us_mkts, key):10,.1f}")


if __name__ == "__main__":
    main()
