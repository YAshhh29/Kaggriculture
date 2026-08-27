"""Use crop-pressure labor for a bounded second strawberry cohort."""

from __future__ import annotations

from typing import Any

from agents.experimental_crop_pressure_labor_agent import (
    _selected_hand_targets,
)
from agents.experimental_demand_aware_agent import _choices
from agents.experimental_future_labor_agent import FUTURE_HAND_TARGETS
from agents.experimental_learned_service_agent import _selected_arm
from agents.experimental_premium_throughput_agent import decide as decide_premium
from policies.demand_policy import expansion_animal_plans
from policies.service_policy import ARM_PAIRED


LATE_STRAWBERRY_SLOTS = 4


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Backfill four spent melon slots with supported late strawberries."""
    animal, crop = _choices(observation)
    hand_targets = _selected_hand_targets(observation, animal)
    use_late_strawberries = (
        crop == "STRAWBERRY"
        and hand_targets == FUTURE_HAND_TARGETS
    )
    service_arm = _selected_arm(observation)
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=expansion_animal_plans(animal),
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        selective_late_rotation_crop=(
            "STRAWBERRY" if use_late_strawberries else None
        ),
        selective_late_rotation_slots=(
            LATE_STRAWBERRY_SLOTS if use_late_strawberries else 0
        ),
        selective_late_rotation_source_crop="MELON",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=hand_targets,
        pair_colocated_feed_care=service_arm == ARM_PAIRED,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the pressure-funded late-strawberry challenger."""
    return decide(observation)