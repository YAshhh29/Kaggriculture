"""Deadline policy expanding from productive occupancy instead of fixed days."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Expand a serviced frontier quadrant once it is productively full."""
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
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run occupancy-driven expansion."""
    return decide(observation)
