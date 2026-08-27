"""Deadline capacity with an elite-inspired cow-heavy herd."""

from __future__ import annotations

from collections import Counter
from typing import Any

from agents.experimental_center_out_agent import ANIMAL_DATA, ANIMAL_PLANS
from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def _cow_heavy_plan(plan: dict[str, Any]) -> dict[str, Any]:
    animal = str(plan["animal"])
    if animal == "SHEEP" and plan["quadrant"] in {"NE", "SW"}:
        animal = "COW"
    return {
        **plan,
        "animal": animal,
        **ANIMAL_DATA[animal],
    }


COW_HEAVY_ANIMAL_PLANS = tuple(
    _cow_heavy_plan(plan) for plan in ANIMAL_PLANS
)
assert Counter(
    str(plan["animal"]) for plan in COW_HEAVY_ANIMAL_PLANS
) == {"COW": 10, "SHEEP": 2}


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Run deadline wheat capacity with ten cows and two sheep."""
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=COW_HEAVY_ANIMAL_PLANS,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run cow-heavy deadline capacity."""
    return decide(observation)
