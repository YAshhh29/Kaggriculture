"""What does each opponent do, and how much does it vary?

One tape per opponent tells you what that agent did in one game. With
many tapes each, two further questions open up, and both matter more for
building against them than any average:

* **consistency** -- does this agent play one plan every game, or does it
  adapt to the town it is drawn into? A fixed plan can be beaten by a
  fixed counter; an adaptive one cannot.
* **spread** -- how much of the difference between their score and ours
  is the strategy, and how much is the draw? A gap smaller than their own
  game-to-game variance is not a strategy gap at all.

Both are invisible with one game per opponent, which is what this project
has been working from.

    python -m tools.data.opponent_profile --min-games 6
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")


def tape_fingerprint(actions) -> dict[str, float]:
    """A few numbers that characterise how a game was played."""
    verbs: Counter[str] = Counter()
    planted: Counter[str] = Counter()
    bought: Counter[str] = Counter()
    hires = 0
    land = 0
    first_land = None
    for step, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        for unit in [action.get("farmer"), *(action.get("hands") or [])]:
            if isinstance(unit, list) and unit:
                verbs[str(unit[0])] += 1
                if str(unit[0]) == "PLANT" and len(unit) > 1:
                    planted[str(unit[1])] += 1
        for order in action.get("market") or []:
            if not isinstance(order, list) or not order:
                continue
            if order[0] == "HIRE":
                hires += 1
            elif order[0] == "BUY_LAND":
                land += 1
                if first_land is None:
                    first_land = step // 24
            elif order[0] == "BUY_ANIMAL" and len(order) > 2:
                bought[str(order[1])] += int(order[2])
    total = sum(verbs.values()) or 1
    out = {
        "hires": hires,
        "land": land,
        "first_land": first_land if first_land is not None else -1,
        "water": verbs.get("WATER", 0),
        "harvest": verbs.get("HARVEST", 0),
        "move_share": sum(verbs[d] for d in
                          ("NORTH", "SOUTH", "EAST", "WEST")) / total,
        "animals": sum(bought.values()),
    }
    for crop in CROPS:
        out["plant_" + crop] = planted.get(crop, 0)
    for animal in ANIMALS:
        out["buy_" + animal] = bought.get(animal, 0)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-games", type=int, default=6)
    parser.add_argument("--top", type=int, default=12)
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    from tools.data.profile_tapes import INDEX, TAPES, load_tape

    by_name: dict[str, list[dict]] = defaultdict(list)
    rewards: dict[str, list[float]] = defaultdict(list)
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["episode_id"] in seen:
            continue
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists():
            continue
        seen.add(row["episode_id"])
        by_name[str(row.get("name"))].append(row)
        rewards[str(row.get("name"))].append(float(row.get("reward") or 0))

    deep = {n: rs for n, rs in by_name.items() if len(rs) >= args.min_games}
    print(f"{len(by_name)} opponents held, {len(deep)} with "
          f"{args.min_games}+ games\n")
    if not deep:
        print("fetch more games per opponent first")
        return

    ranked = sorted(deep.items(),
                    key=lambda kv: -statistics.mean(
                        r["rating"] for r in kv[1]))[:args.top]

    print(f"{'opponent':24s}{'games':>6}{'rating':>8}{'reward':>10}"
          f"{'spread':>9}{'cv':>7}")
    for name, rows in ranked:
        rs = [float(r.get("reward") or 0) for r in rows]
        rating = statistics.mean(float(r.get("rating") or 0) for r in rows)
        spread = statistics.pstdev(rs) if len(rs) > 1 else 0.0
        mean = statistics.mean(rs)
        print(f"  {name[:22]:22s}{len(rows):6d}{rating:8.0f}{mean:10,.0f}"
              f"{spread:9,.0f}{spread / max(1, mean):7.2f}")

    print("\nhow fixed is each plan? (spread across their own games)")
    print(f"{'opponent':24s}{'wheat':>8}{'carrot':>8}{'straw':>8}"
          f"{'animals':>9}{'land day':>10}")
    for name, rows in ranked:
        prints = []
        for row in rows[:12]:
            path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
            prints.append(tape_fingerprint(load_tape(path)))
        def spread(key):
            vals = [p[key] for p in prints]
            return statistics.pstdev(vals) if len(vals) > 1 else 0.0
        def mid(key):
            return statistics.median(p[key] for p in prints)
        print(f"  {name[:22]:22s}"
              f"{mid('plant_WHEAT'):5.0f}+-{spread('plant_WHEAT'):<3.0f}"
              f"{mid('plant_CARROT'):5.0f}+-{spread('plant_CARROT'):<3.0f}"
              f"{mid('plant_STRAWBERRY'):5.0f}+-{spread('plant_STRAWBERRY'):<3.0f}"
              f"{mid('animals'):6.0f}+-{spread('animals'):<3.0f}"
              f"{mid('first_land'):7.0f}+-{spread('first_land'):<3.0f}")


if __name__ == "__main__":
    main()
