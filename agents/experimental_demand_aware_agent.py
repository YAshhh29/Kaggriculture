"""Demand-aware crops and expansion animals over learned safe service."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_learned_service_agent import _selected_arm
from agents.experimental_premium_throughput_agent import (
    LAST_PLANT_DAYS,
    decide as decide_premium,
)
from policies.demand_policy import (
    expansion_animal_plans,
    select_expansion_animal,
    select_rotation_crop,
)
from policies.service_policy import ARM_PAIRED


ANIMAL_SELECTION_DAY = 6
CROP_SELECTION_DAY = 9
MIN_MODELED_OPPONENT_MONEY_K = 0.5
_ANIMAL_CHOICES: dict[int, str] = {}
_CROP_CHOICES: dict[int, str] = {}


def _choices(observation: dict[str, Any]) -> tuple[str, str]:
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _ANIMAL_CHOICES.pop(player, None)
        _CROP_CHOICES.pop(player, None)
    if day >= ANIMAL_SELECTION_DAY and player not in _ANIMAL_CHOICES:
        opponent = observation["farms"][1 - player]
        opponent_money_k = float(opponent.get("money", 0)) / 1000.0
        _ANIMAL_CHOICES[player] = (
            "SHEEP"
            if opponent_money_k < MIN_MODELED_OPPONENT_MONEY_K
            else select_expansion_animal(observation)
        )
    if day >= CROP_SELECTION_DAY and player not in _CROP_CHOICES:
        _CROP_CHOICES[player] = select_rotation_crop(observation)
    return (
        _ANIMAL_CHOICES.get(player, "SHEEP"),
        _CROP_CHOICES.get(player, "WHEAT"),
    )


def decide_demand(
    observation: dict[str, Any],
    *,
    use_crop_demand: bool = True,
    use_animal_demand: bool = True,
    hand_targets: tuple[int, ...] = DEADLINE_HAND_TARGETS,
    minimum_fertilizer_sale_price: int | None = None,
    maximum_fertilizer_holdings: int | None = None,
    fertilizer_liquidation_day: int | None = None,
    pair_colocated_strawberry_service: bool = False,
    fertilize_strawberries: bool = False,
    fertilized_strawberries_per_quadrant: int | None = None,
    carried_fertilizer_only: bool = False,
) -> dict[str, Any]:
    """Execute selected demand axes through the deterministic scheduler."""
    animal, crop = _choices(observation)
    if not use_animal_demand:
        animal = "SHEEP"
    if not use_crop_demand:
        crop = "WHEAT"
    service_arm = _selected_arm(observation)
    deadline = LAST_PLANT_DAYS[crop]
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=expansion_animal_plans(animal),
        rotation_crop=crop,
        rotation_last_plant_day=deadline,
        land_reserves=(300, 300),
        late_rotation_crop=crop,
        late_rotation_last_plant_day=deadline,
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=hand_targets,
        minimum_fertilizer_sale_price=minimum_fertilizer_sale_price,
        maximum_fertilizer_holdings=maximum_fertilizer_holdings,
        fertilizer_liquidation_day=fertilizer_liquidation_day,
        pair_colocated_strawberry_service=pair_colocated_strawberry_service,
        fertilize_strawberries=fertilize_strawberries,
        fertilized_strawberries_per_quadrant=(
            fertilized_strawberries_per_quadrant
        ),
        carried_fertilizer_only=carried_fertilizer_only,
        pair_colocated_feed_care=service_arm == ARM_PAIRED,
    )


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Lock both demand choices, then execute deterministic safety."""
    return decide_demand(observation)


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run bounded demand-aware capacity."""
    return decide(observation)
