"""Saturated wheat capacity with crop reserve scaled to current due work."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Protect a third crop worker only when the local queue needs one."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        scale_crop_reserve_to_due_work=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        reserve_seeds_per_quadrant=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run due-work-aware saturated wheat capacity."""
    return decide(observation)
