"""Capacity policy deriving expansion and crop admission from live state."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Expand on occupancy and admit crops only when lifecycle remains."""
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
        dynamic_lifecycle_windows=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run dynamic horizon capacity."""
    return decide(observation)
