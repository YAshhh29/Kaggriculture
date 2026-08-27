"""Research-only day-6 demand-animal shadow controller."""

from __future__ import annotations

from typing import Any

from policies.demand_animal_policy import ARM_BALANCED, extract_demand_animal_features
from policies.macro_policy import select_macro_arm


SELECTION_DAY = 6
MIN_MODELED_OPPONENT_MONEY_K = 0.5
SHADOW_MODEL = {
    "feature": "opportunity_cow",
    "threshold": 74.4285715,
    "left": {
        "feature": "shops_carrot",
        "threshold": 1.5,
        "left": {"arm": 0},
        "right": {"arm": 2},
    },
    "right": {"arm": 1},
}
_SELECTED_ARMS: dict[int, int] = {}


def select_shadow_arm(observation: dict[str, Any]) -> int:
    """Lock the rejected tree's recommendation without bypassing safe arms."""
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _SELECTED_ARMS.pop(player, None)
    if day < SELECTION_DAY:
        return ARM_BALANCED
    if player not in _SELECTED_ARMS:
        features = extract_demand_animal_features(observation)
        _SELECTED_ARMS[player] = (
            ARM_BALANCED
            if features["opponent_money_k"] < MIN_MODELED_OPPONENT_MONEY_K
            else select_macro_arm(SHADOW_MODEL, features)
        )
    return _SELECTED_ARMS[player]
