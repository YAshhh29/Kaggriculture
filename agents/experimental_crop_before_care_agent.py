"""Saturated capacity preserving animal collection before crop service."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Collect animal outputs, service crops, then spend slack on CARE."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        crops_before_care_only=True,
        plant_before_care=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        reserve_seeds_per_quadrant=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run crop-before-CARE saturated capacity."""
    return decide(observation)
