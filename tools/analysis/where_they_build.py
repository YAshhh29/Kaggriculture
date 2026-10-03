"""Where the best farms put their animals and their crops.

The shed sits in the middle of the board, on the four centre tiles, and it
is where every hand respawns at dawn and where every sale has to pass
through. So distance from the centre is not decoration: it is paid twice a
day, every day, by every asset that needs tending.

An animal is the hungriest asset there is. It wants feeding, caring for and
relieving of its manure -- three visits a day, every day, for the rest of
the season, and it walks off the farm entirely if it misses two meals. A
crop wants watering, which is one visit, and is worth nothing at all if it
is missed twice. If the strong farms know this, their animals will sit
closer to the shed than their crops, and the difference will be visible.

This replays recorded games with both sides as they were played -- which
reproduces the original result to the coin -- and reads the board at dusk
each day, counting what stands in each ring around the shed.

    python -m tools.analysis.where_they_build --tapes 8
    python -m tools.analysis.where_they_build --tapes 6 --agent candidates.candidate_j:agent
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def ring(x: int, y: int) -> int:
    """Chebyshev distance from the shed block, which is what a walk costs."""
    return max(abs(x - 4), abs(y - 4), abs(x - 5), abs(y - 5)) - 1


def study(path: Path, spec: str | None = None) -> dict | None:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    from rl.replay_agent import build_replay_agent

    record = json.loads(path.read_text(encoding="utf-8"))
    if spec:
        from tools.eval.measure_panel import resolve
        mine = resolve(spec)
    else:
        mine = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    other = record.get("opponent_actions_zlib_b64")
    rival = build_replay_agent(_unpack(other)) if other else "random"
    seat = int(record.get("seat", 0) or 0)

    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    animals: Counter = Counter()
    crops: Counter = Counter()
    pens: Counter = Counter()
    days = [0]
    raw_day = engine._end_of_day

    def end_of_day(state, env_, day):
        farm = state[0].observation.farms[seat]
        days[0] += 1
        for y, row in enumerate(farm["tiles"]):
            for x, tile in enumerate(row):
                if not isinstance(tile, dict):
                    continue
                where = ring(x, y)
                if "animal" in tile:
                    animals[where] += 1
                elif tile.get("kind") == "PLANT":
                    crops[where] += 1
                elif tile.get("kind") in ("COOP", "PASTURE"):
                    pens[where] += 1
        return raw_day(state, env_, day)

    engine._end_of_day = end_of_day
    try:
        env.run([mine, rival] if seat == 0 else [rival, mine])
    finally:
        engine._end_of_day = raw_day

    got = float(env.state[seat].reward or 0)
    want = float(record["rewards"]["them"])

    def mean(counter: Counter) -> float:
        total = sum(counter.values())
        if not total:
            return 0.0
        return sum(k * v for k, v in counter.items()) / total

    return {
        "team": (spec.split(":")[0].split(".")[-1] if spec
                 else record.get("source_team")),
        "rating": record.get("team_score"),
        "faithful": abs(got - want) < 1.0,
        "score": got,
        "animal_ring": mean(animals), "crop_ring": mean(crops),
        "pen_ring": mean(pens),
        "animals": animals, "crops": crops,
        "animal_days": sum(animals.values()) / max(1, days[0]),
        "crop_days": sum(crops.values()) / max(1, days[0]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tapes", type=int, default=8)
    parser.add_argument("--agent", default=None)
    args = parser.parse_args()

    files = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    scored = []
    for path in files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if record.get("won") and record.get("opponent_actions_zlib_b64"):
            scored.append((float(record.get("team_score") or 0), path))
    scored.sort(reverse=True)

    rows = []
    for _rating, path in scored[: args.tapes]:
        try:
            row = study(path, args.agent)
        except Exception as error:
            print(f"  {path.name}: {type(error).__name__} {error}")
            continue
        if row:
            rows.append(row)
    if not rows:
        print("no games studied")
        return

    print(f"\nWhere the farm is built, in rings from the shed "
          f"({len(rows)} games)\n")
    print(f"  {'team':18s} {'rated':>7s} {'ok':>3s} {'animals':>9s} "
          f"{'crops':>8s} {'pens':>7s} | {'head':>6s} {'plants':>7s}")
    for row in rows:
        print(f"  {str(row['team'])[:18]:18s} {row['rating']:7.0f} "
              f"{'Y' if row['faithful'] else 'n':>3s} "
              f"{row['animal_ring']:9.2f} {row['crop_ring']:8.2f} "
              f"{row['pen_ring']:7.2f} | {row['animal_days']:6.1f} "
              f"{row['crop_days']:7.1f}")

    n = len(rows)
    a_ring = sum(r["animal_ring"] for r in rows) / n
    c_ring = sum(r["crop_ring"] for r in rows) / n
    print(f"\n  animals sit {a_ring:.2f} rings out, crops {c_ring:.2f} "
          f"-- animals are {'CLOSER' if a_ring < c_ring else 'FURTHER'} "
          f"by {abs(c_ring - a_ring):.2f}")

    animals: Counter = Counter()
    crops: Counter = Counter()
    for row in rows:
        animals.update(row["animals"])
        crops.update(row["crops"])
    a_total = max(1, sum(animals.values()))
    c_total = max(1, sum(crops.values()))
    print(f"\n  {'ring':>5s} {'animals':>9s} {'crops':>9s}")
    for k in range(6):
        print(f"  {k:5d} {animals.get(k, 0) / a_total:9.1%} "
              f"{crops.get(k, 0) / c_total:9.1%}")


if __name__ == "__main__":
    main()
