"""Opponent-aware labor extended with a public crop-pressure trigger."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import (
    DEADLINE_HAND_TARGETS,
)
from agents.experimental_demand_aware_agent import _choices, decide_demand
from agents.experimental_future_labor_agent import FUTURE_HAND_TARGETS
from policies.macro_policy import extract_macro_features


LABOR_SELECTION_DAY = 6
CROP_LEAD_TRIGGER = 4
_PRESSURE_CHOICES: dict[int, bool] = {}


def _own_crop_count(observation: dict[str, Any]) -> int:
    player = int(observation["player"])
    return sum(
        isinstance(tile, dict) and tile.get("kind") == "PLANT"
        for row in observation["farms"][player].get("tiles", [])
        for tile in row
    )


def labor_supported_by_pressure(
    observation: dict[str, Any],
    animal: str,
) -> bool:
    """Fund peak labor for cheap herds or a material crop deficit."""
    features = extract_macro_features(observation)
    opponent_crops = int(
        features["opponent_wheat"] + features["opponent_nonwheat"]
    )
    crop_pressure = opponent_crops >= _own_crop_count(observation) + CROP_LEAD_TRIGGER
    cheap_diversified_herd = (
        animal != "SHEEP"
        and features["opponent_nonwheat"] > features["opponent_wheat"]
    )
    return crop_pressure or cheap_diversified_herd


def _selected_hand_targets(
    observation: dict[str, Any],
    animal: str,
) -> tuple[int, ...]:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _PRESSURE_CHOICES.pop(player, None)
    if day < LABOR_SELECTION_DAY:
        return DEADLINE_HAND_TARGETS
    if player not in _PRESSURE_CHOICES:
        _PRESSURE_CHOICES[player] = labor_supported_by_pressure(
            observation,
            animal,
        )
    return (
        FUTURE_HAND_TARGETS
        if _PRESSURE_CHOICES[player]
        else DEADLINE_HAND_TARGETS
    )


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Respond once to day-6 herd economics and opponent crop pressure."""
    animal, _ = _choices(observation)
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
        hand_targets=_selected_hand_targets(observation, animal),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the crop-pressure labor challenger."""
    return decide(observation)