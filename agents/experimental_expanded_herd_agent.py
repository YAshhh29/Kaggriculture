"""Deadline capacity with two delayed cows on harvested melon slots."""

from __future__ import annotations

from collections import Counter
from typing import Any

from agents.experimental_center_out_agent import (
    ANIMAL_DATA,
    ANIMAL_PLANS,
    block_to_position,
)
from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


EXTRA_COW_PLANS = tuple(
    {
        "id": f"expanded_nw_cow_{index}",
        "quadrant": "NW",
        "block": block,
        "position": block_to_position(block),
        "animal": "COW",
        "activation_day": 11,
        **ANIMAL_DATA["COW"],
    }
    for index, block in enumerate((25, 24), start=1)
)
EXPANDED_HERD_PLANS = (*ANIMAL_PLANS, *EXTRA_COW_PLANS)
assert Counter(
    str(plan["animal"]) for plan in EXPANDED_HERD_PLANS
) == {"COW": 8, "SHEEP": 6}


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Add two cows after the opening melon cycle is harvestable."""
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=EXPANDED_HERD_PLANS,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run expanded-herd deadline capacity."""
    return decide(observation)
