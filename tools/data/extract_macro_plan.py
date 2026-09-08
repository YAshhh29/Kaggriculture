"""Learn the consensus build order from many elite games, not one tape.

Every clone this project has shipped replays a single recording, and the
live record says why that caps out: Candidate C1, C2, D and F are the same
architecture -- one frozen route under the same A+B guards, since C's
selector is a documented placeholder that never switches -- and they came
in at 2094, 2023, 1936 and 1375. **Only the route differed.** A single
recording is one sample of a strategy, including whatever went wrong that
game, and replaying it into a different game applies decisions taken for
reasons that no longer hold.

A corpus does not have that problem. Across many games of many strong
players the accidents average out and what is left is the build order they
all agree on: how many hands by which day, when the land is bought, how
many of each animal, which crops go in and when. That is a *strategy*
rather than a recording, and an executor can follow it while reacting to
the board in front of it.

This reads every captured tape and reduces it to that macro schedule --
cumulative decisions per day -- then reports the median across the corpus,
which is the plan a consensus elite player follows.

    python -m tools.data.extract_macro_plan --min-rating 2700
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.data.profile_tapes import INDEX, TAPES, load_tape  # noqa: E402

TURNS_PER_DAY = 24
DAYS = 30
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")
OUT = ROOT / "rl" / "data" / "macro_plan.json"


def schedule(actions: list[dict[str, Any]]) -> dict[str, list[float]]:
    """Cumulative macro decisions at the end of each day."""
    hires = [0] * DAYS
    land = [0] * DAYS
    animals = {a: [0] * DAYS for a in ANIMALS}
    seeds = {c: [0] * DAYS for c in CROPS}
    planted = {c: [0] * DAYS for c in CROPS}
    hands = [0] * DAYS
    coops = [0] * DAYS
    pastures = [0] * DAYS

    running_hire = running_land = 0
    running_animals = {a: 0 for a in ANIMALS}
    running_seeds = {c: 0 for c in CROPS}
    running_plant = {c: 0 for c in CROPS}
    running_coop = running_pasture = 0

    for step, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        day = min(DAYS - 1, step // TURNS_PER_DAY)
        units = [action.get("farmer"), *(action.get("hands") or [])]
        for unit in units:
            if not isinstance(unit, list) or not unit:
                continue
            verb = str(unit[0])
            if verb == "PLANT" and len(unit) > 1 and str(unit[1]) in CROPS:
                running_plant[str(unit[1])] += 1
            elif verb == "BUILD_COOP":
                running_coop += 1
            elif verb == "BUILD_PASTURE":
                running_pasture += 1
        hands[day] = max(hands[day], len(action.get("hands") or []))
        for order in action.get("market") or []:
            if not isinstance(order, list) or not order:
                continue
            verb = str(order[0])
            if verb == "HIRE":
                running_hire += 1
            elif verb == "BUY_LAND":
                running_land += 1
            elif verb == "BUY_ANIMAL" and len(order) > 2:
                name = str(order[1])
                if name in running_animals:
                    running_animals[name] += int(order[2])
            elif verb == "BUY_SEED" and len(order) > 2:
                name = str(order[1])
                if name in running_seeds:
                    running_seeds[name] += int(order[2])
        hires[day] = running_hire
        land[day] = running_land
        coops[day] = running_coop
        pastures[day] = running_pasture
        for a in ANIMALS:
            animals[a][day] = running_animals[a]
        for c in CROPS:
            seeds[c][day] = running_seeds[c]
            planted[c][day] = running_plant[c]

    out: dict[str, list[float]] = {
        "hires": [float(v) for v in hires],
        "land": [float(v) for v in land],
        "hands": [float(v) for v in hands],
        "coops": [float(v) for v in coops],
        "pastures": [float(v) for v in pastures],
    }
    for a in ANIMALS:
        out[f"animal_{a}"] = [float(v) for v in animals[a]]
    for c in CROPS:
        out[f"seed_{c}"] = [float(v) for v in seeds[c]]
        out[f"plant_{c}"] = [float(v) for v in planted[c]]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-rating", type=float, default=2700.0)
    parser.add_argument("--min-reward", type=float, default=0.0)
    args = parser.parse_args()

    rows = [json.loads(x) for x in
            INDEX.read_text(encoding="utf-8").splitlines()]
    seen: set[int] = set()
    corpus: list[dict[str, list[float]]] = []
    names: set[str] = set()
    for row in rows:
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists() or row["episode_id"] in seen:
            continue
        if (row.get("rating") or 0) < args.min_rating:
            continue
        if (row.get("reward") or 0) < args.min_reward:
            continue
        seen.add(row["episode_id"])
        names.add(row["name"])
        corpus.append(schedule(load_tape(path)))

    if not corpus:
        raise SystemExit("no tapes match")
    print(f"{len(corpus)} games from {len(names)} players\n")

    keys = sorted(corpus[0])
    plan = {
        key: [statistics.median(g[key][d] for g in corpus)
              for d in range(DAYS)]
        for key in keys
    }
    OUT.write_text(json.dumps(plan, indent=1), encoding="utf-8")

    marks = (2, 4, 6, 8, 10, 12, 15, 18, 22, 26, 29)
    print("consensus build order (median across the corpus)")
    print("  " + "day".ljust(16) + "".join(f"{d:>6}" for d in marks))
    for key in ("hands", "hires", "land", "coops", "pastures",
                "animal_GOOSE", "animal_COW", "animal_SHEEP",
                "seed_WHEAT", "seed_CARROT", "seed_STRAWBERRY",
                "seed_MELON", "seed_TOMATO"):
        if key not in plan:
            continue
        print("  " + key.ljust(16)
              + "".join(f"{plan[key][d]:6.0f}" for d in marks))
    print(f"\nwritten to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
