"""Deadline capacity with cash-gated midgame wheat buffering."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


BUFFER_START_DAY = 12
BUFFER_END_DAY = 18
BUFFER_MIN_MONEY = 5_000


def _wheat_buffer_multiplier(observation: dict[str, Any]) -> int:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    money = int(observation["farms"][player].get("money", 0))
    return int(
        BUFFER_START_DAY <= day <= BUFFER_END_DAY
        and money >= BUFFER_MIN_MONEY
    ) + 1


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Buffer wheat only in the funded midgame capacity window."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        wheat_seed_buffer_multiplier=_wheat_buffer_multiplier(observation),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run cash-gated midgame wheat capacity."""
    return decide(observation)
