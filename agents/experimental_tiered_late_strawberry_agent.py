"""Combine tiered fertilizer with demanded late strawberry slots."""

from __future__ import annotations

from typing import Any

from agents.experimental_tiered_value_fertilizer_agent import (
    decide as decide_tiered,
)
from policies.macro_policy import extract_macro_features


SELECTION_DAY = 6
MIN_STRAWBERRY_PRICE_MULTIPLIER = 1.30
LATE_STRAWBERRY_SLOTS = 8
_LATE_STRAWBERRY_CHOICES: dict[int, bool] = {}


def _late_strawberry_selected(observation: dict[str, Any]) -> bool:
    """Lock whether public day-6 strawberry value supports late slots."""
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _LATE_STRAWBERRY_CHOICES.pop(player, None)
    if day < SELECTION_DAY:
        return False
    if player not in _LATE_STRAWBERRY_CHOICES:
        features = extract_macro_features(observation)
        _LATE_STRAWBERRY_CHOICES[player] = (
            features["price_strawberry"]
            >= MIN_STRAWBERRY_PRICE_MULTIPLIER
        )
    return _LATE_STRAWBERRY_CHOICES[player]


def decide_with_slots(
    observation: dict[str, Any],
    slots: int,
) -> dict[str, Any]:
    """Backfill a bounded number of demand-supported melon slots."""
    return decide_tiered(
        observation,
        late_strawberry_slots=slots,
    )


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Backfill eight melon slots only when strawberry demand is selected."""
    return decide_with_slots(
        observation,
        LATE_STRAWBERRY_SLOTS
        if _late_strawberry_selected(observation)
        else 0,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run tiered fertilizer plus demanded late strawberries."""
    return decide(observation)
