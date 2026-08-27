"""Deadline capacity with bounded near-shed strawberry fertilization."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Fertilize at most one nearby strawberry per owned quadrant."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        fertilize_strawberries=True,
        fertilized_strawberries_per_quadrant=1,
        fertilizer_reserve_per_strawberry=2,
        fertilizer_reserve_limit=6,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run bounded-fertilizer deadline capacity."""
    return decide(observation)
