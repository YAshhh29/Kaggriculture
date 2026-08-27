"""Discrete throughput templates for hierarchical policy learning."""

from __future__ import annotations

from typing import Any

from agents.experimental_center_out_agent import ANIMAL_PLANS
from agents.experimental_premium_throughput_agent import decide as decide_premium


ARM_STRAWBERRY = 0
ARM_WHEAT = 1
ARM_STRAWBERRY_RESERVE3 = 2
ARM_WHEAT_RESERVE3 = 3
CAPACITY_ARMS = (
    ARM_STRAWBERRY,
    ARM_WHEAT,
    ARM_STRAWBERRY_RESERVE3,
    ARM_WHEAT_RESERVE3,
)
ARM_NAMES = {
    ARM_STRAWBERRY: "strawberry-rotation",
    ARM_WHEAT: "wheat-rotation",
    ARM_STRAWBERRY_RESERVE3: "strawberry-rotation-reserve3",
    ARM_WHEAT_RESERVE3: "wheat-rotation-reserve3",
}


def decide_capacity_arm(
    observation: dict[str, Any],
    arm: int,
) -> dict[str, Any]:
    """Execute one throughput template through the safe scheduler."""
    if arm not in CAPACITY_ARMS:
        raise ValueError(f"Unknown capacity arm: {arm}")
    reserve_three = arm in {
        ARM_STRAWBERRY_RESERVE3,
        ARM_WHEAT_RESERVE3,
    }
    rotation_crop = (
        "WHEAT"
        if arm in {ARM_WHEAT, ARM_WHEAT_RESERVE3}
        else "STRAWBERRY"
    )
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=ANIMAL_PLANS,
        rotation_crop=rotation_crop,
        land_reserves=(300, 300),
        crop_worker_reserve=3 if reserve_three else 2,
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
    )
