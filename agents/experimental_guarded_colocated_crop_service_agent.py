"""Guard zero-travel strawberry service by public fertilizer value."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import _choices, decide_demand
from agents.experimental_future_labor_agent import _selected_hand_targets
from policies.macro_policy import extract_macro_features


SELECTION_DAY = 6
MAX_FERTILIZER_PRICE_MULTIPLIER = 0.965
_CROP_SERVICE_CHOICES: dict[int, bool] = {}


def _crop_service_selected(observation: dict[str, Any]) -> bool:
    """Lock one conservative crop-service choice for the episode."""
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _CROP_SERVICE_CHOICES.pop(player, None)
    if day < SELECTION_DAY:
        return False
    if player not in _CROP_SERVICE_CHOICES:
        features = extract_macro_features(observation)
        _CROP_SERVICE_CHOICES[player] = (
            features["price_fertilizer"]
            <= MAX_FERTILIZER_PRICE_MULTIPLIER
        )
    return _CROP_SERVICE_CHOICES[player]


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Run future labor with conservatively guarded crop service."""
    animal, _ = _choices(observation)
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
        hand_targets=_selected_hand_targets(observation, animal),
        pair_colocated_strawberry_service=(
            _crop_service_selected(observation)
        ),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the guarded zero-travel crop-service challenger."""
    return decide(observation)