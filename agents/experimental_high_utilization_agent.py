"""Replay-grounded high-utilization crop replacement policy."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import _choices
from agents.experimental_guarded_colocated_crop_service_agent import (
    _crop_service_selected,
)
from agents.experimental_learned_service_agent import _selected_arm
from agents.experimental_premium_throughput_agent import (
    decide as decide_premium,
)
from policies.demand_policy import expansion_animal_plans
from policies.service_policy import ARM_PAIRED


HIGH_UTILIZATION_HAND_TARGETS = (
    5,
    4, 4, 4, 4, 4,
    9, 9,
    11,
    *([12] * 19),
    10,
    8,
)
HIGH_UTILIZATION_CROP_RESERVES = (
    *([2] * 30),
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Saturate owned land, then recycle short crops through day 27."""
    animal, _ = _choices(observation)
    paired = _selected_arm(observation) == ARM_PAIRED
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=expansion_animal_plans(animal),
        rotation_crop="WHEAT",
        rotation_last_plant_day=27,
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        late_rotation_last_plant_day=27,
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        pair_colocated_strawberry_service=(
            paired and _crop_service_selected(observation)
        ),
        hand_targets=HIGH_UTILIZATION_HAND_TARGETS,
        seed_buffer_multiplier=2,
        extra_wheat_seed_buffer=9,
        crop_worker_reserves_by_day=HIGH_UTILIZATION_CROP_RESERVES,
        opening_fill_nw=True,
        opening_melon_slots=5,
        opening_fill_last_plant_day=0,
        final_crop_liquidation=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the separate high-utilization research policy."""
    return decide(observation)
