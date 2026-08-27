"""Wheat-capacity policy tapered around the final harvest deadline."""

from __future__ import annotations

from typing import Any

from agents.experimental_premium_throughput_agent import (
    HAND_TARGETS,
    decide as decide_premium,
)


DEADLINE_HAND_TARGETS = (
    *HAND_TARGETS[:23],
    10,
    10,
    10,
    10,
    8,
    4,
    3,
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Protect the last wheat cohort, then taper for liquidation."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run deadline-safe tapered wheat capacity."""
    return decide(observation)
