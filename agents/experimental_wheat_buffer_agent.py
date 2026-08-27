"""Deadline-tapered capacity with cheap wheat-only seed buffering."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Buffer two wheat cycles without prebuying premium crops."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        wheat_seed_buffer_multiplier=2,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run wheat-buffered deadline capacity."""
    return decide(observation)
