"""Game by game: where did Candidate G lose, and where did it do well?

Aggregate action counts told us what differs on average and produced six
failed experiments in a row. This asks a narrower question of each game
separately: at the moment the margin opened, what was each farm doing?

For every opponent tape it plays the game, samples both farms every day,
and finds the day the gap widened fastest. Then it reports what each side
held at that moment -- tiles, animals, crew, cash -- and what the loss was
made of by good.

The output is meant to be read as a list of failures with causes, not as
a table of averages:

    python -m tools.data.post_mortem --opponents 60 --seeds 2
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")


def farm_snapshot(farm: dict[str, Any]) -> dict[str, int]:
    tiles = farm.get("tiles") or []
    crops = animals = pens = free = 0
    for row in tiles:
        for tile in row:
            if tile is None:
                free += 1
            elif isinstance(tile, dict):
                if "animal" in tile:
                    animals += 1
                elif tile.get("kind") == "PLANT":
                    crops += 1
                elif tile.get("kind") in ("COOP", "PASTURE"):
                    pens += 1
    return {
        "crops": crops, "animals": animals, "pens": pens, "free": free,
        "hands": len(farm.get("hands") or []),
        "money": int(farm.get("money", 0) or 0),
        "land": len(farm.get("unlocked_quadrants") or []),
    }


def one(job):
    name, tape, seed, seat = job
    from kaggle_environments import make

    from tools.eval.measure_panel import resolve
    import rl.candidate_g as G

    opponent = resolve("clone:" + tape)
    agents = [G.agent, opponent] if seat == 0 else [opponent, G.agent]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(agents)

    daily: list[tuple[int, dict, dict]] = []
    for step in range(23, 720, 24):
        if step >= len(env.steps):
            break
        view = env.steps[step][seat]
        observation = view.get("observation") or {}
        farms = observation.get("farms") or []
        if len(farms) < 2:
            continue
        daily.append((observation.get("day", step // 24),
                      farm_snapshot(farms[seat]),
                      farm_snapshot(farms[1 - seat])))

    mine = env.state[seat].reward or 0
    theirs = env.state[1 - seat].reward or 0

    # The day the money gap widened fastest.
    worst_day, worst_swing = 0, 0
    previous = 0
    for day, us, them in daily:
        gap = them["money"] - us["money"]
        if gap - previous > worst_swing:
            worst_swing = gap - previous
            worst_day = day
        previous = gap
    at = next((d for d in daily if d[0] == worst_day), None)
    return {
        "name": name, "seed": seed, "seat": seat,
        "mine": mine, "theirs": theirs, "margin": mine - theirs,
        "worst_day": worst_day, "worst_swing": worst_swing,
        "us": at[1] if at else {}, "them": at[2] if at else {},
        "end_us": daily[-1][1] if daily else {},
        "end_them": daily[-1][2] if daily else {},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponents", type=int, default=60)
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--min-rating", type=float, default=2800.0)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    from tools.eval.wide_panel import best_tape_per_opponent

    field = best_tape_per_opponent(args.opponents, args.min_rating)
    seeds = list(range(11, 11 + args.seeds))
    jobs = [(name, tape, seed, seat)
            for name, tape, _ in field
            for seed in seeds
            for seat in (0, 1)]
    print(f"{len(field)} opponents x {len(seeds)} seeds x 2 seats "
          f"= {len(jobs)} games", flush=True)

    with Pool(args.workers) as pool:
        rows = pool.map(one, jobs)

    wins = [r for r in rows if r["margin"] > 0]
    losses = [r for r in rows if r["margin"] <= 0]
    print(f"\nwon {len(wins)}/{len(rows)}  ({len(wins) / len(rows):.1%})")

    def summarise(label, group, field_name):
        if not group:
            return
        values = [r[field_name] for r in group if r[field_name]]
        if values:
            print(f"    {label:22s} {statistics.mean(values):8.1f}")

    print("\nWHERE THE GAP OPENS")
    days = Counter(r["worst_day"] for r in losses)
    print("  worst day, most common: "
          + ", ".join(f"day {d} ({n})" for d, n in days.most_common(6)))
    print(f"  mean swing on that day: "
          f"{statistics.mean([r['worst_swing'] for r in losses]):,.0f}")

    print("\nAT THAT MOMENT              ours    theirs")
    for key in ("crops", "animals", "pens", "free", "hands", "money", "land"):
        ours = statistics.mean([r["us"].get(key, 0) for r in losses if r["us"]])
        theirs = statistics.mean([r["them"].get(key, 0) for r in losses
                                  if r["them"]])
        print(f"  {key:22s} {ours:9.1f} {theirs:9.1f}")

    print("\nAT THE END                  ours    theirs")
    for key in ("crops", "animals", "pens", "free", "hands", "money", "land"):
        ours = statistics.mean([r["end_us"].get(key, 0) for r in losses
                                if r["end_us"]])
        theirs = statistics.mean([r["end_them"].get(key, 0) for r in losses
                                  if r["end_them"]])
        print(f"  {key:22s} {ours:9.1f} {theirs:9.1f}")

    print("\nCLOSEST LOSSES (most winnable)")
    for r in sorted(losses, key=lambda r: -r["margin"])[:8]:
        print(f"  {r['name'][:24]:26s} seat {r['seat']} "
              f"{r['mine']:>8,.0f} vs {r['theirs']:>8,.0f} "
              f"({r['margin']:+,.0f})  gap opened day {r['worst_day']}")

    if wins:
        print("\nWINS")
        for r in sorted(wins, key=lambda r: -r["margin"])[:8]:
            print(f"  {r['name'][:24]:26s} seat {r['seat']} "
                  f"{r['mine']:>8,.0f} vs {r['theirs']:>8,.0f} "
                  f"({r['margin']:+,.0f})")


if __name__ == "__main__":
    main()
