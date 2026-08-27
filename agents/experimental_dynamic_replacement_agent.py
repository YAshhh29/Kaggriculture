"""Dynamic capacity replacing harvested cohorts within a serviceable cap."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Replace cashable cohorts without exceeding local service capacity."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        dynamic_land_expansion=True,
        dynamic_lifecycle_deadlines_only=True,
        max_active_crops_per_quadrant=13,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run bounded dynamic cohort replacement."""
    return decide(observation)
