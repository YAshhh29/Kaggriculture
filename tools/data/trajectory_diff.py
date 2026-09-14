"""Day by day, where does Candidate G fall behind the plan the field plays?

The dominant strategy on this ladder is deterministic -- seven named
opponents run it with a standard deviation of zero -- and it banks about
95,000 in contested games where G banks 51,000. Those 45,000 coins are
the whole problem, and no aggregate count locates them.

This runs both in the *same* game conditions and records the same
quantities every day: money, tiles, animals, crew, and what has actually
been sold. The point is to find the day the trajectories separate and
what each farm was doing at that moment, rather than comparing totals at
step 720 and guessing.

    python -m tools.data.trajectory_diff --games 5
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

FIXED_PLAN = {"kanno", "pensukesan", "Yusuke Hayashi", "Himanshu Kumar",
              "cooked", "Squirrel", "supr3mum"}
MARKS = tuple(range(0, 30, 3))


def walk(steps, side: int) -> dict[int, dict[str, Any]]:
    """State at the end of each sampled day, plus cumulative sales."""
    sold: Counter[str] = Counter()
    earned: Counter[str] = Counter()
    out: dict[int, dict[str, Any]] = {}
    before: dict[str, int] = {}
    quoted: dict[str, float] = {}
    for index, step in enumerate(steps):
        if side >= len(step):
            continue
        view = step[side]
        observation = view.get("observation") or {}
        # The action stored on a step produced that step's state, so sales
        # are clamped to the shed as it stood a step earlier, at the price
        # quoted a step earlier.
        shed = dict(before)
        before = dict(((observation.get("private") or {}).get("shed")) or {})
        prices = dict(quoted)
        market = step[0].get("observation", {}).get("market") or {}
        quoted = dict(market.get("prices") or {})
        action = view.get("action")
        if isinstance(action, dict):
            for order in action.get("market") or []:
                if (isinstance(order, list) and len(order) > 2
                        and order[0] == "SELL"):
                    try:
                        good = str(order[1])
                        fill = min(int(order[2]), int(shed.get(good, 0) or 0))
                    except (TypeError, ValueError):
                        continue
                    if fill > 0:
                        sold[good] += fill
                        earned[good] += fill * float(prices.get(good, 0) or 0)
                        shed[good] = int(shed.get(good, 0)) - fill
        day = index // 24
        if index % 24 != 23 or day not in MARKS:
            continue
        farms = observation.get("farms") or []
        if side >= len(farms) or not isinstance(farms[side], dict):
            continue
        farm = farms[side]
        crops = animals = pens = empty = weeds = 0
        by_crop: Counter[str] = Counter()
        for row in farm.get("tiles") or []:
            for tile in row:
                if tile is None:
                    empty += 1
                elif isinstance(tile, dict):
                    if "animal" in tile:
                        animals += 1
                    elif tile.get("kind") == "PLANT":
                        crops += 1
                        by_crop[str(tile.get("crop"))] += 1
                    elif tile.get("kind") in ("COOP", "PASTURE"):
                        pens += 1
                    elif tile.get("kind") == "WEED":
                        weeds += 1
        out[day] = {
            "quadrants": len(farm.get("unlocked_quadrants") or []),
            "money": float(farm.get("money", 0) or 0),
            "crops": crops, "animals": animals, "pens": pens,
            "empty": empty, "weeds": weeds,
            "hands": len(farm.get("hands") or []),
            "sold": sum(sold.values()),
            "earned": dict(earned),
            **{"crop_" + c: n for c, n in by_crop.items()},
        }
    return out


# Every coin that moves, as the engine moves it. Pricing a tape's SELL
# orders at the quote before the sale overstates large batches -- each
# unit sells lower than the last -- and says nothing of wages, land or
# stock, which is where a farm that sells more and banks less is losing.
LEDGER: list[tuple[int, str, str, float]] = []


def install_ledger() -> None:
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    if getattr(engine, "_ledger_installed", False):
        return
    current: dict[str, Any] = {"farms": [], "step": 0}
    market = engine._process_market
    commit = engine._commit_unit
    hire = engine._do_hire
    land = engine._do_buy_land

    def seat(farm) -> int:
        for index, candidate in enumerate(current["farms"]):
            if candidate is farm:
                return index
        return -1

    def process_market(state, env):
        current["farms"] = state[0].observation.farms
        current["step"] = int(state[0].observation.step or 0)
        return market(state, env)

    def commit_unit(op, item, price, farm, *rest, **kw):
        ok = commit(op, item, price, farm, *rest, **kw)
        if ok:
            sign = 1.0 if op == "SELL" else -1.0
            LEDGER.append((seat(farm), op, str(item), sign * float(price)))
        return ok

    def do_hire(farm, *rest, **kw):
        before = farm["money"]
        hire(farm, *rest, **kw)
        if farm["money"] != before:
            LEDGER.append((seat(farm), "HIRE", "HAND", farm["money"] - before))

    def do_buy_land(farm, *rest, **kw):
        before = farm["money"]
        land(farm, *rest, **kw)
        if farm["money"] != before:
            LEDGER.append((seat(farm), "BUY_LAND", "LAND",
                           farm["money"] - before))

    engine._process_market = process_market
    engine._commit_unit = commit_unit
    engine._do_hire = do_hire
    engine._do_buy_land = do_buy_land
    engine._ledger_installed = True


def books(side: int) -> Counter[str]:
    """Coins in and out for one seat, by what moved them."""
    out: Counter[str] = Counter()
    for who, op, item, amount in LEDGER:
        if who != side:
            continue
        key = ("sell " + item if op == "SELL"
               else "hire" if op == "HIRE"
               else "land" if op == "BUY_LAND"
               else op.lower().replace("_", " ") + " " + item)
        out[key] += amount
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=5)
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    import rl.candidate_g as G
    from rl.replay_agent import build_replay_agent
    from tools.data.profile_tapes import INDEX, TAPES, load_tape
    from tools.eval.measure_panel import resolve

    plan_tapes, seen = [], set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("name") not in FIXED_PLAN or row["episode_id"] in seen:
            continue
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists():
            continue
        seen.add(row["episode_id"])
        plan_tapes.append(path)
        if len(plan_tapes) >= args.games:
            break
    if not plan_tapes:
        raise SystemExit("no tapes of the fixed plan held")

    install_ledger()
    plan_rows, ours_rows = [], []
    plan_books, ours_books = [], []
    for index, path in enumerate(plan_tapes[:args.games]):
        # Both farms face the same opponent in each game, so the comparison
        # is of the two farms and not of who drew the easier one. The
        # opponent changes from game to game: G is deterministic, and one
        # fixed foil would make its five games one game five times.
        foil = resolve("clone:" + str(plan_tapes[(index + 1) % len(plan_tapes)]))
        agent = build_replay_agent(tuple(load_tape(path)))
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": 11},
                   debug=False)
        LEDGER.clear()
        env.run([agent, foil])
        plan_rows.append(walk(env.steps, 0))
        plan_books.append(books(0))

        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": 11},
                   debug=False)
        LEDGER.clear()
        env.run([G.agent, foil])
        ours_rows.append(walk(env.steps, 0))
        ours_books.append(books(0))

    def med(rows, day, field):
        vals = [r[day].get(field, 0) for r in rows if day in r]
        return statistics.median(vals) if vals else 0.0

    print(f"{len(plan_rows)} games, both against the same foil\n")
    print(f"{'day':>4} | {'money G/plan':>18} | {'crops':>9} | "
          f"{'animals':>9} | {'hands':>7} | {'sold':>11}")
    for day in MARKS:
        if not any(day in r for r in ours_rows):
            continue
        print(f"{day:>4} | "
              f"{med(ours_rows, day, 'money'):8,.0f}/"
              f"{med(plan_rows, day, 'money'):<9,.0f} | "
              f"{med(ours_rows, day, 'crops'):4.0f}/"
              f"{med(plan_rows, day, 'crops'):<4.0f} | "
              f"{med(ours_rows, day, 'animals'):4.0f}/"
              f"{med(plan_rows, day, 'animals'):<4.0f} | "
              f"{med(ours_rows, day, 'hands'):3.0f}/"
              f"{med(plan_rows, day, 'hands'):<3.0f} | "
              f"{med(ours_rows, day, 'sold'):5.0f}/"
              f"{med(plan_rows, day, 'sold'):<5.0f}")

    gaps = [(day, med(plan_rows, day, "money") - med(ours_rows, day, "money"))
            for day in MARKS if any(day in r for r in ours_rows)]
    print("\nmoney gap opens fastest on:")
    steps_ = [(gaps[i][0], gaps[i][1] - gaps[i - 1][1])
              for i in range(1, len(gaps))]
    for day, delta in sorted(steps_, key=lambda kv: -kv[1])[:4]:
        print(f"  days {day - 3} to {day}: {delta:+,.0f}")

    # What the ground is doing: which crop holds each tile, and how much
    # unlocked ground is standing bare or gone to weed.
    kinds = ("WHEAT", "CARROT", "STRAWBERRY", "MELON", "TOMATO")
    print("\nground, G/plan")
    print(f"{'day':>4} | " + " | ".join(f"{k[:6]:>9}" for k in kinds)
          + f" | {'pens':>7} | {'empty':>7} | {'weeds':>7}")
    for day in MARKS:
        if not any(day in r for r in ours_rows):
            continue
        cells = [f"{med(ours_rows, day, 'crop_' + k):4.0f}/"
                 f"{med(plan_rows, day, 'crop_' + k):<4.0f}" for k in kinds]
        print(f"{day:>4} | " + " | ".join(cells)
              + f" | {med(ours_rows, day, 'pens'):3.0f}/"
                f"{med(plan_rows, day, 'pens'):<3.0f}"
              + f" | {med(ours_rows, day, 'empty'):3.0f}/"
                f"{med(plan_rows, day, 'empty'):<3.0f}"
              + f" | {med(ours_rows, day, 'weeds'):3.0f}/"
                f"{med(plan_rows, day, 'weeds'):<3.0f}")

    print("\nquadrants held, G/plan: " + "  ".join(
        f"d{day} {med(ours_rows, day, 'quadrants'):.0f}/"
        f"{med(plan_rows, day, 'quadrants'):.0f}"
        for day in MARKS if any(day in r for r in ours_rows)))

    # The engine's own ledger for the whole game: exact per-unit fills,
    # and every coin spent on hands, land, seed, stock and feed.
    keys = sorted({k for b in ours_books + plan_books for k in b},
                  key=lambda k: (not k.startswith("sell"), k))
    print("\nfull-season ledger, G/plan (median over games)")
    net_mine = net_theirs = 0.0
    for key in keys:
        mine = statistics.median(b.get(key, 0.0) for b in ours_books)
        theirs = statistics.median(b.get(key, 0.0) for b in plan_books)
        net_mine += mine
        net_theirs += theirs
        print(f"  {key:22s} {mine:+10,.0f} / {theirs:<+10,.0f} "
              f"plan ahead by {theirs - mine:+9,.0f}")
    print(f"  {'sum of medians':22s} {net_mine:+10,.0f} / {net_theirs:<+10,.0f}")


if __name__ == "__main__":
    main()
