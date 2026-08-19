"""Measured NE expansion bundle using safe zoned crop routing."""

from __future__ import annotations

from typing import Any

from experimental_zoned_agent import decide


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run one NE quadrant, fourteen animals, and ten daily hands."""
    return decide(
        observation,
        target_wheat_tiles=16,
        target_daily_hands=10,
        target_extra_land=1,
        target_cows=6,
        target_sheep=8,
    )