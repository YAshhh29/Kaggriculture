"""Learned day-1 selector over safe animal-service templates."""

from __future__ import annotations

from typing import Any

from policies.learned_service_model import SERVICE_MODEL
from policies.macro_policy import extract_macro_features, select_macro_arm
from policies.service_policy import ARM_BASELINE, decide_service_arm


SELECTION_DAY = 1
MIN_MODELED_OPPONENT_MONEY_K = 0.5
_SELECTED_ARMS: dict[int, int] = {}


def _selected_arm(observation: dict[str, Any]) -> int:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _SELECTED_ARMS.pop(player, None)
    if day < SELECTION_DAY:
        return ARM_BASELINE
    if player not in _SELECTED_ARMS:
        features = extract_macro_features(observation)
        _SELECTED_ARMS[player] = (
            ARM_BASELINE
            if features["opponent_money_k"]
            < MIN_MODELED_OPPONENT_MONEY_K
            else select_macro_arm(SERVICE_MODEL, features)
        )
    return _SELECTED_ARMS[player]


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Select one service template, then execute deterministic safety."""
    return decide_service_arm(observation, _selected_arm(observation))


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the learned service policy."""
    return decide(observation)
