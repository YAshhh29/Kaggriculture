"""Opponent- and demand-aware counterpolicy for direct market matchups."""

from __future__ import annotations

from collections import Counter
from typing import Any

from agents.experimental_center_out_agent import ANIMAL_PLANS
from agents.experimental_premium_throughput_agent import decide as decide_premium


ONE_LAND_ANIMAL_PLANS: tuple[dict[str, Any], ...] = tuple(
    plan
    for plan in ANIMAL_PLANS
    if plan["quadrant"] in {"NW", "NE"}
)


def _opponent_crop_counts(
    observation: dict[str, Any],
) -> Counter[str]:
    player = int(observation["player"])
    farms = observation.get("farms", [])
    opponent = farms[1 - player] if len(farms) == 2 else {}
    counts: Counter[str] = Counter()
    for row in opponent.get("tiles", []):
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                counts[str(tile.get("crop", "UNKNOWN"))] += 1
    return counts


def _is_wheat_specialist(observation: dict[str, Any]) -> bool:
    if int(observation.get("day", 0)) < 4:
        return False
    crops = _opponent_crop_counts(observation)
    return sum(
        quantity
        for crop, quantity in crops.items()
        if crop != "WHEAT"
    ) == 0


def _strategy_parameters(
    observation: dict[str, Any],
) -> tuple[int, tuple[dict[str, Any], ...], str]:
    if not _is_wheat_specialist(observation):
        return 2, ANIMAL_PLANS, "STRAWBERRY"
    return 1, ONE_LAND_ANIMAL_PLANS, "STRAWBERRY"


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Select land and livestock pressure from the opponent footprint."""
    target_extra_land, animal_plans, rotation_crop = _strategy_parameters(
        observation
    )
    return decide_premium(
        observation,
        target_extra_land=target_extra_land,
        animal_plans=animal_plans,
        rotation_crop=rotation_crop,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the adaptive market counterpolicy."""
    return decide(observation)
