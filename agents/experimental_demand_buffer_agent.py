"""Deadline capacity with opponent-aware wheat seed buffering."""

from __future__ import annotations

from typing import Any

from agents.experimental_adaptive_counter_agent import _opponent_crop_counts
from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


BUFFER_START_DAY = 9
BUFFER_END_DAY = 18
BUFFER_MIN_MONEY = 2_000


def _wheat_buffer_multiplier(observation: dict[str, Any]) -> int | None:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    farm = observation["farms"][player]
    crops = _opponent_crop_counts(observation)
    nonwheat = sum(
        quantity for crop, quantity in crops.items() if crop != "WHEAT"
    )
    diversified = nonwheat >= crops["WHEAT"] and nonwheat > 0
    if (
        BUFFER_START_DAY <= day <= BUFFER_END_DAY
        and len(farm.get("unlocked_quadrants", [])) >= 3
        and int(farm.get("money", 0)) >= BUFFER_MIN_MONEY
        and diversified
    ):
        return 2
    return None


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Buffer wheat only when public opponent crops imply lower saturation."""
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
    """Run demand-aware buffered deadline capacity."""
    return decide(observation)
