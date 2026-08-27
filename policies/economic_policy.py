"""Economic templates for contextual policy selection."""

from __future__ import annotations

from typing import Any

from agents.experimental_center_out_agent import ANIMAL_PLANS
from agents.experimental_cow_heavy_deadline_agent import COW_HEAVY_ANIMAL_PLANS
from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


ARM_WHEAT_BALANCED = 0
ARM_STRAWBERRY_BALANCED = 1
ARM_WHEAT_COW_HEAVY = 2
ARM_MELON_BALANCED = 3
ECONOMIC_ARMS = (
    ARM_WHEAT_BALANCED,
    ARM_STRAWBERRY_BALANCED,
    ARM_WHEAT_COW_HEAVY,
    ARM_MELON_BALANCED,
)
ARM_NAMES = {
    ARM_WHEAT_BALANCED: "wheat-balanced",
    ARM_STRAWBERRY_BALANCED: "strawberry-balanced",
    ARM_WHEAT_COW_HEAVY: "wheat-cow-heavy",
    ARM_MELON_BALANCED: "melon-balanced",
}


def decide_economic_arm(
    observation: dict[str, Any],
    arm: int,
) -> dict[str, Any]:
    """Execute one economic template through deterministic safety."""
    if arm not in ECONOMIC_ARMS:
        raise ValueError(f"Unknown economic arm: {arm}")
    rotation_crop = {
        ARM_WHEAT_BALANCED: "WHEAT",
        ARM_STRAWBERRY_BALANCED: "STRAWBERRY",
        ARM_WHEAT_COW_HEAVY: "WHEAT",
        ARM_MELON_BALANCED: "MELON",
    }[arm]
    melon_arm = arm == ARM_MELON_BALANCED
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=(
            COW_HEAVY_ANIMAL_PLANS
            if arm == ARM_WHEAT_COW_HEAVY
            else ANIMAL_PLANS
        ),
        rotation_crop=rotation_crop,
        rotation_last_plant_day=18 if melon_arm else None,
        land_reserves=(300, 300),
        late_rotation_crop="MELON" if melon_arm else "WHEAT",
        late_rotation_last_plant_day=18 if melon_arm else None,
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
    )
