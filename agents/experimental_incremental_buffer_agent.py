"""Deadline capacity with one funded extra wheat seed per day."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


BUFFER_START_DAY = 10
BUFFER_END_DAY = 18
BUFFER_MIN_MONEY = 2_000


def _extra_wheat_seed(observation: dict[str, Any]) -> int:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    farm = observation["farms"][player]
    return int(
        BUFFER_START_DAY <= day <= BUFFER_END_DAY
        and len(farm.get("unlocked_quadrants", [])) >= 3
        and int(farm.get("money", 0)) >= BUFFER_MIN_MONEY
    )


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Add one funded wheat slot without prebuying a full extra cycle."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        extra_wheat_seed_buffer=_extra_wheat_seed(observation),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run incremental-buffer deadline capacity."""
    return decide(observation)
