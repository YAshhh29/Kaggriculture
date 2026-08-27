"""Learned day-4 selector over deterministic capacity templates."""

from __future__ import annotations

from typing import Any

from policies.capacity_policy import ARM_STRAWBERRY, decide_capacity_arm
from policies.learned_capacity_model import CAPACITY_MODEL
from policies.macro_policy import extract_macro_features, select_macro_arm


SELECTION_DAY = 4
_SELECTED_ARMS: dict[int, int] = {}


def _selected_arm(observation: dict[str, Any]) -> int:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _SELECTED_ARMS.pop(player, None)
    if day < SELECTION_DAY:
        return ARM_STRAWBERRY
    if player not in _SELECTED_ARMS:
        _SELECTED_ARMS[player] = select_macro_arm(
            CAPACITY_MODEL,
            extract_macro_features(observation),
        )
    return _SELECTED_ARMS[player]


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Select one learned throughput template, then execute it safely."""
    return decide_capacity_arm(observation, _selected_arm(observation))


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the learned hierarchical capacity policy."""
    return decide(observation)
