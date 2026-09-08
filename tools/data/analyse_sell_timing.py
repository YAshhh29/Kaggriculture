"""When does each good reach the market, and does getting there first pay?

Section 10.8v established that the nine goods have completely different
curves above equilibrium. Wool floors 59 units past it, strawberry 62,
milk 76 -- while wheat and egg never floor at all because their curves are
logarithmic. On a shallow good the first sixty units are worth the whole
book and everything after is worth one coin apiece, so **who sells first
takes essentially all of it.**

That makes sale *timing* a strategy variable, and unlike sale volume it can
be read off a tape honestly. Quantities in a recording are requests the
engine clamps against the shed, so the numbers are meaningless (a tape can
ask to sell 999,999 carrots). The turn on which an order was issued is
exactly what it appears to be.

So this reports, per team and per good, the day the good first reaches the
market and how the selling turns are spread across the season, and it
groups by leaderboard band so the top of the board can be compared with
the field and with our own agents.

    python -m tools.data.analyse_sell_timing --min-games 4
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.data.profile_tapes import (  # noqa: E402
    INDEX,
    TAPES,
    TURNS_PER_DAY,
    load_tape,
)

SHALLOW = ("WOOL", "STRAWBERRY", "MILK", "MELON")
DEEP = ("EGG", "WHEAT", "CARROT", "FERTILIZER", "TOMATO")
GOODS = SHALLOW + DEEP


def timing(actions: list[dict[str, Any]]) -> dict[str, Any]:
    """First sale day and number of selling turns, per good."""
    first: dict[str, int] = {}
    turns: dict[str, int] = defaultdict(int)
    for step, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        day = step // TURNS_PER_DAY
        for order in action.get("market") or []:
            if (not isinstance(order, list) or len(order) < 3
                    or order[0] != "SELL"):
                continue
            try:
                if int(order[2]) <= 0:
                    continue
            except (TypeError, ValueError):
                continue
            good = str(order[1])
            turns[good] += 1
            if good not in first:
                first[good] = day
    return {"first": first, "turns": dict(turns)}


def report(label: str, rows: list[dict[str, Any]]) -> None:
    print(f"\n{label}  ({len(rows)} games)")
    print(f"  {'good':11s} {'first sold on day':>18s} {'selling turns':>14s} "
          f"{'games that sell it':>19s}")
    for good in GOODS:
        days = [r["first"][good] for r in rows if good in r["first"]]
        turns = [r["turns"].get(good, 0) for r in rows]
        if not days:
            print(f"  {good:11s} {'never':>18s} {0:14.0f} "
                  f"{0:>10d}/{len(rows):<8d}")
            continue
        mark = " <- shallow" if good in SHALLOW else ""
        print(f"  {good:11s} {statistics.mean(days):18.1f} "
              f"{statistics.mean(turns):14.1f} "
              f"{len(days):>10d}/{len(rows):<8d}{mark}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-games", type=int, default=4)
    parser.add_argument("--floor", type=float, default=2700.0)
    args = parser.parse_args()

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists() or row["episode_id"] in seen:
            continue
        seen.add(row["episode_id"])
        key = ("top of the board (2700+ by current rank)"
               if row["rating"] >= args.floor else "the field we are drawn from")
        buckets[key].append(timing(load_tape(path)))

    for key in sorted(buckets, reverse=True):
        if len(buckets[key]) >= args.min_games:
            report(key, buckets[key])

    print("\nShallow goods floor 59-158 units past equilibrium, so the "
          "first seller takes the book.\nDeep goods (egg, wheat) never "
          "floor, so timing barely matters for them.")


if __name__ == "__main__":
    main()
