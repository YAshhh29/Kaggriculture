"""Learned macro selector over deterministic safe farming policies."""

from __future__ import annotations

from typing import Any

from agents.experimental_adaptive_counter_agent import ONE_LAND_ANIMAL_PLANS
from agents.experimental_premium_throughput_agent import decide as decide_premium
from policies.learned_macro_model import MACRO_MODEL
from policies.macro_policy import (
    ARM_COMPACT,
    ARM_COMPACT_CROP,
    ARM_EXPANDED,
    ARM_EXPANDED_CROP,
    extract_macro_features,
    select_macro_arm,
)


SELECTION_DAY = 9
_SELECTED_ARMS: dict[int, int] = {}


def _selected_arm(observation: dict[str, Any]) -> int:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _SELECTED_ARMS.pop(player, None)
    if day < SELECTION_DAY:
        return ARM_EXPANDED
    if player not in _SELECTED_ARMS:
        _SELECTED_ARMS[player] = select_macro_arm(
            MACRO_MODEL,
            extract_macro_features(observation),
        )
    return _SELECTED_ARMS[player]


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Select a learned capital footprint, then use deterministic execution."""
    arm = _selected_arm(observation)
    if arm == ARM_COMPACT:
        return decide_premium(
            observation,
            target_extra_land=1,
            animal_plans=ONE_LAND_ANIMAL_PLANS,
        )
    if arm == ARM_EXPANDED:
        return decide_premium(observation)
    if arm == ARM_COMPACT_CROP:
        return decide_premium(
            observation,
            target_extra_land=1,
            animal_plans=ONE_LAND_ANIMAL_PLANS,
            crop_worker_reserve=3,
        )
    if arm == ARM_EXPANDED_CROP:
        return decide_premium(observation, crop_worker_reserve=3)
    raise ValueError(f"Unknown learned macro arm: {arm}")


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the learned macro policy with deterministic safety controls."""
    return decide(observation)
