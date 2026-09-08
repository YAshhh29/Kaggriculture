"""Rank every captured route by how far it departs from elite consensus.

Route choice is worth about seven hundred rating points -- Candidate C1,
C2, D and F are the same architecture over different tapes and scored
2094, 2023, 1936 and 1375 -- and it has been made twice on local panels
that both failed validation against those numbers.

This ranks routes without playing a game. `rl/data/macro_plan.json` holds
the build order 204 games by 27 players rated 2700+ agree on; a route is
scored by the mean relative gap between its own cumulative decisions and
that plan.

**What this can and cannot do, measured on the four routes whose live
scores are known.** Under eight different weightings and day windows, six
put C1 and C2 -- the 2000+ routes -- as the closest two, and D and F as
the furthest. Only one reproduces the exact order. So it is a **filter,
not a ranking**: it reliably tells a 2000-class route from a 1400-class
one and cannot tell C1 from C2. Reported as an average over the eight
configurations so no single choice of weights carries the result, with the
spread shown, because a route the configurations disagree about has not
really been separated from anything.

Selection therefore takes the routes inside the C1/C2 distance band and
breaks the tie on provenance -- a top team beating another strong team by
a wide margin in a ranked game -- which is the only criterion with a live
result behind it (C1's 2094).

    python -m tools.data.rank_routes --top 25
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from rl import macro_plan  # noqa: E402
from tools.data.extract_macro_plan import schedule  # noqa: E402
from tools.data.profile_tapes import INDEX, TAPES, load_tape  # noqa: E402

REFERENCE = [
    ("C1 fog flower", "v1327-public-elite-fogflower-105144807.json", 2094.7),
    ("C2 giulio", "v1327-public-elite-giulio-105144807.json", 2023.7),
    ("D  andrey", "v1327-public-elite-andrey-105520725.json", 1936.4),
    ("F  mhuang", "v1327-live-elite-mhuang-106610780.json", 1375.8),
]


def windows() -> list[tuple[list[str], range]]:
    keys = [k for k in macro_plan.plan()]
    animals = [k for k in keys if k.startswith("animal_")]
    crops = [k for k in keys if k.startswith("plant_")]
    build = [k for k in keys if k in ("pastures", "coops", "hands", "land")]
    return [
        (keys, range(2, 16)), (keys, range(0, 30)), (keys, range(5, 13)),
        (keys, range(15, 30)), (animals, range(2, 16)),
        (build, range(2, 16)), (crops, range(2, 30)),
        ([k for k in keys if k.startswith("seed_")], range(2, 30)),
    ]


def distance(sched: dict[str, list[float]]) -> tuple[float, float]:
    """Mean and spread of the gap across all eight configurations."""
    scores = []
    for keys, days in windows():
        if not keys:
            continue
        total = 0.0
        for key in keys:
            series = sched.get(key)
            if not series:
                continue
            for day in days:
                want = macro_plan.target(key, day)
                got = float(series[min(day, len(series) - 1)])
                total += abs(got - want) / max(1.0, abs(want))
        scores.append(total / max(1, len(days)))
    if not scores:
        return 99.0, 0.0
    return statistics.mean(scores), statistics.pstdev(scores)


def model_actions(filename: str):
    path = ROOT / "models" / filename
    if not path.exists():
        return None
    model = json.loads(path.read_text(encoding="utf-8"))
    return json.loads(
        zlib.decompress(base64.b64decode(model["actions_zlib_b64"])).decode()
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args()

    print("reference routes with known live scores")
    band = []
    for name, filename, live in REFERENCE:
        actions = model_actions(filename)
        if actions is None:
            continue
        mean, spread = distance(schedule(actions))
        print(f"  {name:16s} live {live:7.1f}   distance {mean:6.2f} "
              f"+/- {spread:4.2f}")
        if live >= 2000:
            band.append(mean)
    ceiling = max(band) if band else 99.0
    print(f"\nC1/C2 band: distance <= {ceiling:.2f}\n")

    rows: list[dict[str, Any]] = []
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists() or row["episode_id"] in seen:
            continue
        seen.add(row["episode_id"])
        mean, spread = distance(schedule(load_tape(path)))
        row["distance"] = mean
        row["spread"] = spread
        rows.append(row)

    rows.sort(key=lambda r: r["distance"])
    inside = [r for r in rows if r["distance"] <= ceiling]
    print(f"{len(rows)} routes scored, {len(inside)} inside the C1/C2 band\n")
    print(f"  {'episode':>11} {'team':20s} {'rating':>7} {'dist':>6} "
          f"{'+/-':>5} {'beat':18s} {'their r':>8} {'margin':>9}")
    for row in rows[: args.top]:
        beat = str(row.get("beat") or "-")[:16]
        print(f"  {row['episode_id']:>11} "
              f"{row['name'].encode('ascii', 'replace').decode()[:18]:20s} "
              f"{row.get('rating', 0):7.0f} {row['distance']:6.2f} "
              f"{row['spread']:5.2f} {beat:18s} "
              f"{(row.get('beat_rating') or 0):8.0f} "
              f"{(row.get('margin') or 0):+9,.0f}")


if __name__ == "__main__":
    main()
