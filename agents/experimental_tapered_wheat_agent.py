"""Wheat-capacity policy with workload-matched late hiring."""

from __future__ import annotations

from typing import Any

from agents.experimental_premium_throughput_agent import (
    HAND_TARGETS,
    decide as decide_premium,
)


TAPERED_HAND_TARGETS = (
    *HAND_TARGETS[:23],
    10,
    9,
    8,
    6,
    5,
    3,
    3,
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Keep wheat capacity while tapering workers after planting closes."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=TAPERED_HAND_TARGETS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the tapered wheat-capacity policy."""
    return decide(observation)
