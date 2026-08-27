"""Trim expansion sheep when the opponent leads crop capacity."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import (
    DEADLINE_HAND_TARGETS,
)
from agents.experimental_demand_aware_agent import _choices
from agents.experimental_learned_service_agent import _selected_arm
from agents.experimental_premium_throughput_agent import decide as decide_premium
from policies.demand_policy import expansion_animal_plans
from policies.macro_policy import extract_macro_features
from policies.service_policy import ARM_PAIRED


PRESSURE_SELECTION_DAY = 6
CROP_LEAD_TRIGGER = 4
_LEAN_CHOICES: dict[int, bool] = {}


def _own_crop_count(observation: dict[str, Any]) -> int:
    player = int(observation["player"])
    return sum(
        isinstance(tile, dict) and tile.get("kind") == "PLANT"
        for row in observation["farms"][player].get("tiles", [])
        for tile in row
    )


def _pressure_detected(observation: dict[str, Any]) -> bool:
    features = extract_macro_features(observation)
    opponent_crops = int(
        features["opponent_wheat"] + features["opponent_nonwheat"]
    )
    return opponent_crops >= _own_crop_count(observation) + CROP_LEAD_TRIGGER


def _lean_selected(observation: dict[str, Any]) -> bool:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _LEAN_CHOICES.pop(player, None)
    if day < PRESSURE_SELECTION_DAY:
        return False
    if player not in _LEAN_CHOICES:
        _LEAN_CHOICES[player] = _pressure_detected(observation)
    return _LEAN_CHOICES[player]


def lean_expansion_animal_plans(
    animal: str,
) -> tuple[dict[str, Any], ...]:
    """Remove one remaining expansion sheep from NE and SW."""
    removed: set[str] = set()
    plans = []
    for plan in reversed(expansion_animal_plans(animal)):
        quadrant = str(plan["quadrant"])
        remove = (
            quadrant in {"NE", "SW"}
            and plan["animal"] == "SHEEP"
            and quadrant not in removed
        )
        if remove:
            removed.add(quadrant)
        else:
            plans.append(plan)
    return tuple(reversed(plans))


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Use a ten-animal herd only under a locked crop-pressure signal."""
    animal, _ = _choices(observation)
    plans = (
        lean_expansion_animal_plans(animal)
        if _lean_selected(observation)
        else expansion_animal_plans(animal)
    )
    service_arm = _selected_arm(observation)
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=plans,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        pair_colocated_feed_care=service_arm == ARM_PAIRED,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the crop-pressure lean-herd challenger."""
    return decide(observation)