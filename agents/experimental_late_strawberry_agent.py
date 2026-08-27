"""Use four spent melon slots for a demanded late strawberry cohort."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import (
    DEADLINE_HAND_TARGETS,
)
from agents.experimental_demand_aware_agent import _choices
from agents.experimental_learned_service_agent import _selected_arm
from agents.experimental_premium_throughput_agent import decide as decide_premium
from policies.demand_policy import expansion_animal_plans
from policies.service_policy import ARM_PAIRED


LATE_STRAWBERRY_SLOTS = 4


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Add a second strawberry cohort only when day-9 demand selects it."""
    animal, crop = _choices(observation)
    use_late_strawberries = crop == "STRAWBERRY"
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
        hand_targets=DEADLINE_HAND_TARGETS,
        pair_colocated_feed_care=service_arm == ARM_PAIRED,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the bounded late-strawberry challenger."""
    return decide(observation)