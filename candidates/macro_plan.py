"""Follow the build order 204 elite games agree on, not one recording.

Candidate C1, C2, D and F are the same architecture -- one frozen route
under the same A+B guards, since Candidate C's selector is a documented
placeholder that never switches. They scored 2094, 2023, 1936 and 1375
live. **Only the route differed**, which is the whole six-hundred-point
spread, and route choice has now been made twice on local panels that both
failed validation.

A single recording is one sample of a strategy, complete with whatever
went wrong that game, and replaying it into a different game applies
decisions taken for reasons that no longer hold. A corpus does not have
that problem: across many games by many strong players the accidents
average out, and what survives is the build order they all agree on.

`tools/data/extract_macro_plan.py` reduces every captured tape to its
cumulative macro decisions per day and takes the median across the corpus.
From 204 games by 27 players rated 2700+:

    day             2    4    6    8   10   12   15   18   22   26   29
    hands           4    5    8    9   11   11   11   12   12   11   11
    land            0    0    1    1    1    2    2    2    2    2    2
    pastures        6    6   12   13   14   14   14   14   14   14   14
    coops           0    0    0    0    3    3    3    3    3    3    3
    COW             3    4    6    7    8    8    8    8    8    8    8
    SHEEP           2    2    2    4    5    6    6    6    6    6    6
    GOOSE           0    0    0    0    2    2    3    3    3    3    3

Six pastures and three cows standing by **day two** is far earlier than
anything this project builds, and it matches what the live games say
decides a match: 67 real games showed we win with 17 animals at day 12 and
lose with 14.6 against an opponent's 16.4, with nothing else separating
the two (10.8af).

This module answers only "what is the farm short of, against that plan,
today". It decides nothing about how to get it -- that stays with the
executor, which reads the board and prices the work. A plan says what to
own; it cannot say which worker should walk where.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "rl" / "data" / "macro_plan.json"
DAYS = 30
ANIMALS = ("GOOSE", "COW", "SHEEP")
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")

_PLAN: dict[str, list[float]] | None = None


def plan() -> dict[str, list[float]]:
    """The consensus schedule, loaded once."""
    global _PLAN
    if _PLAN is None:
        if PLAN_PATH.exists():
            _PLAN = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        else:
            _PLAN = {}
    return _PLAN


def target(key: str, day: int) -> float:
    """What the corpus had by the end of `day`, 0 when the key is absent."""
    series = plan().get(key)
    if not series:
        return 0.0
    return float(series[min(max(day, 0), len(series) - 1)])


def animal_deficit(day: int, counts: dict[str, int]) -> dict[str, float]:
    """How far each animal is behind the plan, per kind."""
    return {
        name: target(f"animal_{name}", day) - float(counts.get(name, 0))
        for name in ANIMALS
    }


def next_animal(day: int, counts: dict[str, int]) -> tuple[str, float]:
    """The animal the farm is furthest behind on, and by how much.

    Ties break toward the goose deliberately. A goose costs 300 against a
    cow's 400 and a sheep's 500, starts yielding on day 4 rather than 8 or
    6, and produces on every day rather than every second or third -- and
    egg is one of only two goods whose price curve is logarithmic, so it
    never floors, where milk bottoms out 76 units past equilibrium and
    wool at 59 (10.8v, 10.8af).
    """
    deficits = animal_deficit(day, counts)
    order = {"GOOSE": 0, "COW": 1, "SHEEP": 2}
    best = max(
        ANIMALS, key=lambda a: (deficits[a], -order[a])
    )
    return best, deficits[best]


def crop_order(day: int, planted: dict[str, int]) -> list[str]:
    """Crops ranked by how far the ground is behind the plan.

    Anything already at its planned count drops out entirely rather than
    ranking last, so a crop the corpus stops planting is not quietly
    revived by a tie-break later in the season.
    """
    deficits = [
        (target(f"plant_{crop}", day) - float(planted.get(crop, 0)), crop)
        for crop in CROPS
    ]
    return [crop for deficit, crop in sorted(deficits, reverse=True)
            if deficit > 0]


def structures_wanted(day: int) -> tuple[int, int]:
    """Pastures and coops the plan has standing by this day."""
    return int(target("pastures", day)), int(target("coops", day))


def hands_wanted(day: int) -> int:
    return int(target("hands", day))


def land_wanted(day: int) -> int:
    return int(target("land", day))


def available() -> bool:
    """Whether a plan was actually loaded; callers fall back if not."""
    return bool(plan())
