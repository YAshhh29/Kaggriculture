"""Guard bounded carried-fertilizer routing by public fertilizer value."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import _choices, decide_demand
from agents.experimental_future_labor_agent import _selected_hand_targets
from agents.experimental_guarded_colocated_crop_service_agent import (
    _crop_service_selected,
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Route one carried-fertilizer pair per quadrant when value is low."""
    animal, _ = _choices(observation)
    selected = _crop_service_selected(observation)
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
        hand_targets=_selected_hand_targets(observation, animal),
        pair_colocated_strawberry_service=selected,
        fertilize_strawberries=selected,
        fertilized_strawberries_per_quadrant=1,
        carried_fertilizer_only=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run guarded bounded carried-fertilizer service."""
    return decide(observation)