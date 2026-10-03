"""Consensus build order from top-rated games, and the farm's shortfall against it.

`tools/data/extract_macro_plan.py` reduces each recorded game to its
cumulative macro decisions per day (hands, land, pastures, coops, animals,
crops) and stores the median across the corpus in `rl/data/macro_plan.json`
(204 games by players rated 2700+). A corpus median averages out the
accidents of any single recording.

This module only reports what the farm is short of against that plan on a
given day; deciding how to close the gap is left to the executor.
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
