"""Select bounded carried-fertilizer routing in supported contexts."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import _choices, decide_demand
from agents.experimental_future_labor_agent import _selected_hand_targets
from agents.experimental_guarded_colocated_crop_service_agent import (
    _crop_service_selected,
)
from policies.macro_policy import extract_macro_features


SELECTION_DAY = 6
MIN_WHEAT_PRICE_MULTIPLIER = 1.30
MAX_WOOL_SHOPS = 0.5
MAX_OPPONENT_WHEAT = 3.0
_CARRIED_SERVICE_CHOICES: dict[int, bool] = {}


def _carried_service_selected(observation: dict[str, Any]) -> bool:
    """Lock the conservative routed-service choice at day 6."""
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _CARRIED_SERVICE_CHOICES.pop(player, None)
    if day < SELECTION_DAY:
        return False
    if player not in _CARRIED_SERVICE_CHOICES:
        features = extract_macro_features(observation)
        _CARRIED_SERVICE_CHOICES[player] = (
            features["price_wheat"] > MIN_WHEAT_PRICE_MULTIPLIER
            and features["shops_wool"] <= MAX_WOOL_SHOPS
            and features["opponent_wheat"] <= MAX_OPPONENT_WHEAT
        )
    return _CARRIED_SERVICE_CHOICES[player]


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Use routed service only in the frozen supported context."""
    animal, _ = _choices(observation)
    paired = _crop_service_selected(observation)
    carried = _carried_service_selected(observation)
    routed = paired and carried
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
        hand_targets=_selected_hand_targets(observation, animal),
        pair_colocated_strawberry_service=paired,
        fertilize_strawberries=routed,
        fertilized_strawberries_per_quadrant=1,
        carried_fertilizer_only=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run contextual carried-fertilizer crop service."""
    return decide(observation)