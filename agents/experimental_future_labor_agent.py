"""Demand-animal policy that reinvests cheaper herd capital in labor."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import (
    DEADLINE_HAND_TARGETS,
)
from agents.experimental_demand_aware_agent import _choices, decide_demand
from policies.macro_policy import extract_macro_features


FUTURE_HAND_TARGETS = tuple(
    13 if 9 <= day <= 22 else target
    for day, target in enumerate(DEADLINE_HAND_TARGETS)
)
LABOR_SELECTION_DAY = 6
_LABOR_CHOICES: dict[int, bool] = {}


def hand_targets_for_animal(animal: str) -> tuple[int, ...]:
    """Use extra labor only when demand replaces expensive sheep."""
    return (
        DEADLINE_HAND_TARGETS
        if animal == "SHEEP"
        else FUTURE_HAND_TARGETS
    )


def labor_supported_by_context(
    observation: dict[str, Any],
    animal: str,
) -> bool:
    """Avoid extra crop labor against wheat-saturated opponents."""
    if animal == "SHEEP":
        return False
    features = extract_macro_features(observation)
    return (
        features["opponent_nonwheat"]
        > features["opponent_wheat"]
    )


def _selected_hand_targets(
    observation: dict[str, Any],
    animal: str,
) -> tuple[int, ...]:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _LABOR_CHOICES.pop(player, None)
    if day < LABOR_SELECTION_DAY:
        return DEADLINE_HAND_TARGETS
    if player not in _LABOR_CHOICES:
        _LABOR_CHOICES[player] = labor_supported_by_context(
            observation,
            animal,
        )
    return (
        FUTURE_HAND_TARGETS
        if _LABOR_CHOICES[player]
        else DEADLINE_HAND_TARGETS
    )


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Reinvest cow/goose substitution savings in one peak hand."""
    animal, _ = _choices(observation)
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
        hand_targets=_selected_hand_targets(observation, animal),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the demand-funded labor challenger."""
    return decide(observation)