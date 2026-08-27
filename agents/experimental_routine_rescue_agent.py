"""Deadline policy using otherwise-idle workers across quadrant boundaries."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Use workers left idle after every local commitment for crop work."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        cross_quadrant_routine_rescue=True,
        hand_targets=DEADLINE_HAND_TARGETS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run routine cross-quadrant crop rescue."""
    return decide(observation)
