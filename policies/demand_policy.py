"""Bounded shop-demand choices above deterministic farm execution."""

from __future__ import annotations

from typing import Any

from agents.experimental_center_out_agent import ANIMAL_DATA, ANIMAL_PLANS
from core.economics import animal_opportunity, rank_crop_opportunities


ROTATION_CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY")


def select_rotation_crop(observation: dict[str, Any]) -> str:
    """Choose one feasible rotation crop from public demand and supply."""
    return next(
        opportunity.crop
        for opportunity in rank_crop_opportunities(
            observation,
            ROTATION_CROPS,
        )
        if opportunity.feasible
    )


def select_expansion_animal(observation: dict[str, Any]) -> str:
    """Choose an expansion species only when specialist demand supports it."""
    opportunities = [
        animal_opportunity(observation, animal)
        for animal in ("GOOSE", "COW", "SHEEP")
    ]
    supported = [
        opportunity
        for opportunity in opportunities
        if opportunity.feasible
        and opportunity.specialist_demand_per_day > 0
    ]
    if not supported:
        return "SHEEP"
    return max(
        supported,
        key=lambda opportunity: (
            opportunity.score,
            opportunity.expected_net,
            opportunity.animal,
        ),
    ).animal


def expansion_animal_plans(animal: str) -> tuple[dict[str, Any], ...]:
    """Replace at most one expansion sheep per quadrant with demand species."""
    if animal == "SHEEP":
        return ANIMAL_PLANS
    replaced: set[str] = set()
    plans = []
    for plan in ANIMAL_PLANS:
        quadrant = str(plan["quadrant"])
        replace = (
            quadrant in {"NE", "SW"}
            and plan["animal"] == "SHEEP"
            and quadrant not in replaced
        )
        if not replace:
            plans.append(plan)
            continue
        replaced.add(quadrant)
        plans.append(
            {
                **plan,
                "id": f"{plan['id']}_{animal.lower()}",
                "animal": animal,
                **ANIMAL_DATA[animal],
            }
        )
    return tuple(plans)
