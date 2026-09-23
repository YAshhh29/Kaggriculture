"""How much of a standing ripe batch actually gets sold in the next few turns.

J's forecast of what a rival is about to sell (`ctx["rival_batch"]`) reads
their current ripe units off the public tiles and clamps it with
`min(24.0, max(8.0, units))` -- a hand-picked guess, never checked against
a real game. A public notebook studying this ladder independently found
real value in predicting an opponent's coming sale from historical
behaviour rather than guessing at it; this is the tractable version of
that idea. Doing the matching LIVE, during a game, against the whole tape
corpus is too expensive to fit inside a turn's budget. So the correlation
is measured OFFLINE, once, from real recorded games -- both sides, not a
team against a passive opponent -- and reduced to a small table the agent
can look up cheaply at runtime.

For every step of a replayed game, for BOTH sides: how many ripe units of
each good are standing on their own tiles right now, and how many units
of that good do they actually sell somewhere in the next WINDOW turns.
Bucketed by the standing amount, this gives an honest, data-backed
conversion curve instead of a guess.

    python -m tools.analysis.calibrate_sale_conversion --tapes 40
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import zlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")
ANIMAL_PRODUCT = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}
WINDOW = 8  # turns to look ahead for "did they actually sell it"


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def _ripe(farm: dict) -> dict:
    out = {g: 0 for g in GOODS}
    for row in farm.get("tiles") or []:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            units = int(tile.get("yield_units", 0) or 0)
            if units <= 0:
                continue
            if "animal" in tile:
                item = ANIMAL_PRODUCT.get(str(tile.get("animal", "")))
            elif tile.get("kind") == "PLANT":
                item = str(tile.get("crop", ""))
            else:
                item = None
            if item in out:
                out[item] += units
    return out


def study(path: Path) -> list[tuple[int, str, int]]:
    """(ripe units standing, good, units actually sold in the next WINDOW)."""
    from rl.replay_agent import build_replay_agent
    from kaggle_environments import make

    record = json.loads(path.read_text(encoding="utf-8"))
    a = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    b = build_replay_agent(_unpack(record["opponent_actions_zlib_b64"]))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run([a, b])

    # For each seat, a list of (step, ripe-by-good) and, separately, the
    # actual SELL quantities issued at each step (from the action log,
    # which is exact -- no need to infer anything from board deltas).
    samples: list[tuple[int, str, int]] = []
    for seat in (0, 1):
        ripe_at: dict[int, dict] = {}
        sold_at: dict[int, dict] = defaultdict(lambda: defaultdict(int))
        for index in range(len(env.steps) - 1):
            obs = env.steps[index][seat]["observation"]
            farm = (obs.get("farms") or [None, None])[seat]
            if isinstance(farm, dict):
                ripe_at[index] = _ripe(farm)
            action = env.steps[index][seat].get("action") or {}
            for order in action.get("market") or []:
                if (isinstance(order, list) and len(order) >= 3
                        and order[0] == "SELL" and order[1] in GOODS):
                    try:
                        sold_at[index][order[1]] += int(order[2])
                    except (TypeError, ValueError):
                        pass
        steps = sorted(ripe_at)
        for index in steps:
            for good, standing in ripe_at[index].items():
                if standing <= 0:
                    continue
                sold = sum(sold_at[s].get(good, 0)
                          for s in range(index, min(index + WINDOW,
                                                    len(env.steps) - 1)))
                samples.append((standing, good, sold))
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tapes", type=int, default=40)
    args = parser.parse_args()

    tapes = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    all_samples: list[tuple[int, str, int]] = []
    for tape in tapes[: args.tapes]:
        try:
            all_samples.extend(study(tape))
        except Exception as error:
            print(f"  {tape.name}: {type(error).__name__} {error}")

    print(f"\n{len(all_samples)} (standing, good, sold-within-{WINDOW}) "
          f"samples from {args.tapes} games\n")

    # Bucket by standing amount, per good, and report the median conversion
    # -- median rather than mean, because a few teams that dump everything
    # at once would otherwise dominate a small sample.
    buckets = (1, 3, 6, 10, 16, 24, 999)
    by_good: dict[str, dict[int, list[int]]] = defaultdict(
        lambda: defaultdict(list))
    for standing, good, sold in all_samples:
        for edge in buckets:
            if standing <= edge:
                by_good[good][edge].append(min(sold, standing))
                break

    import statistics
    print(f"  {'good':11s} {'standing<=':>10s} {'n':>6s} {'median sold':>12s} "
          f"{'mean sold':>10s} {'ratio':>7s}")
    table: dict[str, dict[int, float]] = defaultdict(dict)
    for good in GOODS:
        for edge in buckets:
            rows = by_good[good].get(edge)
            if not rows:
                continue
            med = statistics.median(rows)
            mean = statistics.mean(rows)
            table[good][edge] = med
            print(f"  {good:11s} {edge:10d} {len(rows):6d} {med:12.1f} "
                  f"{mean:10.1f} {mean / edge:7.2f}")

    print("\n  as a Python literal, for direct use in candidate_j.py:")
    print("  CONVERSION_TABLE = {")
    for good in GOODS:
        if table[good]:
            print(f"      {good!r}: {dict(sorted(table[good].items()))!r},")
    print("  }")


if __name__ == "__main__":
    main()
