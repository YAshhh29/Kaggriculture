"""What do the leaders actually *do*? Profiled from the action tape alone.

`tools/data/profile_agents.py` answers the same question but needs a full
30 MB replay, and the live corpus keeps only the 720-action tape. This
reads the tape, so it works on every opponent we have captured, and it
aggregates **across several games of the same player** rather than judging
anyone from one replay -- tape quality was measured to belong to the game
rather than the player (GOAL.md 9k), so a single game is noise.

The comparison it exists to support is elite (2765-2882) against the field
we are drawn from (1917-2108) against our own candidates, on the questions
this project has been guessing at:

* **scale** -- how many hands, how much land, how early;
* **mix** -- which crops and which animals, and when they are bought;
* **selling behaviour** -- and specifically how sale volume is *spread*.
  Whether the leaders dump or pace decides the market demand engine
  argument on evidence instead of on theory: pacing measured negative on
  our own high-volume clones (10.8l), and the open question was whether
  that is a fact about the game or a fact about those clones.
* **idleness** -- the fraction of worker turns spent on PASS or on moving,
  which is the cost side of hiring another hand.

    python -m tools.data.profile_tapes --group band
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TAPES = ROOT / "kaggle_cache" / "live_clones"
INDEX = ROOT / "rl" / "data" / "live_opponents.jsonl"
TURNS_PER_DAY = 24
DAYS = 30
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")
GOODS = CROPS + ("EGG", "MILK", "WOOL", "FERTILIZER")
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}


def load_tape(path: Path) -> list[dict[str, Any]]:
    blob = json.loads(path.read_text(encoding="utf-8"))
    raw = blob.get("actions_zlib_b64")
    if raw:
        return json.loads(zlib.decompress(base64.b64decode(raw)))
    return blob.get("actions") or []


def profile(actions: list[dict[str, Any]]) -> dict[str, Any]:
    """One game, reduced to the numbers that separate strategies."""
    roster: list[int] = []
    hires = 0
    land: list[int] = []
    seeds: Counter[str] = Counter()
    animals: Counter[str] = Counter()
    bought: Counter[str] = Counter()
    sold: Counter[str] = Counter()
    sell_turns = 0
    sell_orders = 0
    sell_by_third = [0, 0, 0]
    first_land_day: int | None = None
    tasks: Counter[str] = Counter()
    worker_turns = 0
    passes = 0
    moves = 0

    for step, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        day = step // TURNS_PER_DAY
        third = min(2, day * 3 // DAYS)
        hands = action.get("hands") or []
        roster.append(len(hands))
        units = [action.get("farmer") or ["PASS"], *hands]
        for unit in units:
            if not isinstance(unit, list) or not unit:
                continue
            worker_turns += 1
            verb = str(unit[0])
            if verb == "PASS":
                passes += 1
            elif verb in MOVES:
                moves += 1
            else:
                tasks[verb] += 1
                if verb == "PLANT" and len(unit) > 1:
                    tasks["PLANT:" + str(unit[1])] += 1

        sold_here = False
        for order in action.get("market") or []:
            if not isinstance(order, list) or not order:
                continue
            verb = str(order[0])
            if verb == "HIRE":
                hires += 1
            elif verb == "BUY_LAND":
                land.append(day)
                if first_land_day is None:
                    first_land_day = day
            elif verb == "BUY_SEED" and len(order) > 2:
                seeds[str(order[1])] += int(order[2])
            elif verb == "BUY_ANIMAL" and len(order) > 2:
                animals[str(order[1])] += int(order[2])
            elif verb == "BUY_PRODUCT" and len(order) > 2:
                bought[str(order[1])] += int(order[2])
            elif verb == "SELL" and len(order) > 2:
                quantity = int(order[2])
                sold[str(order[1])] += quantity
                sell_by_third[third] += quantity
                sell_orders += 1
                sold_here = True
        if sold_here:
            sell_turns += 1

    late = roster[TURNS_PER_DAY * 5:]
    total_sold = sum(sold.values())
    return {
        "peak_hands": max(roster) if roster else 0,
        "mean_hands": statistics.mean(late) if late else 0.0,
        "hires": hires,
        "land_buys": len(land),
        "first_land_day": first_land_day,
        "seeds": dict(seeds),
        "animals": dict(animals),
        "animals_total": sum(animals.values()),
        "bought": dict(bought),
        "sold": dict(sold),
        "sold_total": total_sold,
        "sell_turns": sell_turns,
        "sell_orders": sell_orders,
        "units_per_order": total_sold / sell_orders if sell_orders else 0.0,
        "sell_thirds": [
            round(v / total_sold, 3) if total_sold else 0.0
            for v in sell_by_third
        ],
        "tasks": dict(tasks),
        "worker_turns": worker_turns,
        "pass_rate": passes / worker_turns if worker_turns else 0.0,
        "move_rate": moves / worker_turns if worker_turns else 0.0,
    }


def mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
    return statistics.mean(values) if values else 0.0


def counter_mean(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    total: dict[str, float] = defaultdict(float)
    for row in rows:
        for name, value in (row.get(key) or {}).items():
            total[name] += value
    return {k: v / len(rows) for k, v in total.items()} if rows else {}


def report(label: str, rows: list[dict[str, Any]],
           rewards: list[float]) -> None:
    seeds = counter_mean(rows, "seeds")
    animals = counter_mean(rows, "animals")
    sold = counter_mean(rows, "sold")
    tasks = counter_mean(rows, "tasks")
    thirds = [
        statistics.mean([r["sell_thirds"][i] for r in rows]) for i in range(3)
    ]
    land_day = [
        r["first_land_day"] for r in rows if r["first_land_day"] is not None
    ]
    reward_note = (
        ", reward {:,.0f}".format(statistics.mean(rewards)) if rewards else ""
    )
    print("\n{}   ({} games{})".format(label, len(rows), reward_note))
    print("  crew      peak {:5.1f}   mean(after d5) {:5.1f}   "
          "hire orders {:6.0f}".format(
              mean(rows, "peak_hands"), mean(rows, "mean_hands"),
              mean(rows, "hires")))
    print("  land      buys {:4.1f}   first on day {}".format(
        mean(rows, "land_buys"),
        "{:.1f}".format(statistics.mean(land_day)) if land_day else "never"))
    print("  seeds     " + "  ".join(
        "{} {:5.0f}".format(c, seeds.get(c, 0.0)) for c in CROPS))
    print("  animals   " + "  ".join(
        "{} {:5.1f}".format(a, animals.get(a, 0.0)) for a in ANIMALS)
        + "   total {:5.1f}".format(mean(rows, "animals_total")))
    print("  sold      {:6.0f} units in {:5.0f} orders across {:5.0f} turns "
          "({:5.1f} units/order)".format(
              mean(rows, "sold_total"), mean(rows, "sell_orders"),
              mean(rows, "sell_turns"), mean(rows, "units_per_order")))
    print("            " + "  ".join(
        "{} {:5.0f}".format(g, sold.get(g, 0.0))
        for g in GOODS if sold.get(g, 0.0) >= 1))
    print("  timing    early {:5.1%}  mid {:5.1%}  late {:5.1%}"
          "   of sale volume".format(*thirds))
    print("  labour    PASS {:5.1%}   move {:5.1%}   of {:6.0f} "
          "worker-turns".format(
              mean(rows, "pass_rate"), mean(rows, "move_rate"),
              mean(rows, "worker_turns")))
    top = [kv for kv in sorted(tasks.items(), key=lambda kv: -kv[1])
           if not kv[0].startswith("PLANT:")][:8]
    print("  tasks     " + "  ".join(
        "{} {:.0f}".format(k, v) for k, v in top))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", default="team", choices=("team", "band"))
    parser.add_argument("--min-games", type=int, default=2)
    args = parser.parse_args()

    rows = [json.loads(line)
            for line in INDEX.read_text(encoding="utf-8").splitlines()]
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rewards: dict[str, list[float]] = defaultdict(list)
    ratings: dict[str, float] = {}
    seen: set[int] = set()
    for row in rows:
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists() or row["episode_id"] in seen:
            continue
        seen.add(row["episode_id"])
        if args.group == "team":
            key = "{:6.0f}  {}".format(row["rating"], row["name"][:20])
        else:
            key = "elite 2500+" if row["rating"] >= 2500 else "ladder <2500"
        buckets[key].append(profile(load_tape(path)))
        rewards[key].append(float(row.get("reward") or 0.0))
        ratings[key] = max(ratings.get(key, 0.0), row["rating"])

    for key in sorted(buckets, key=lambda k: -ratings[k]):
        if len(buckets[key]) >= args.min_games:
            report(key, buckets[key], rewards[key])


if __name__ == "__main__":
    main()
