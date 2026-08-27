"""Future labor plus zero-travel ordered strawberry service bundles."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import _choices, decide_demand
from agents.experimental_future_labor_agent import _selected_hand_targets


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Add crop service only when workers and fertilizer are co-located."""
    animal, _ = _choices(observation)
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
        hand_targets=_selected_hand_targets(observation, animal),
        pair_colocated_strawberry_service=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the zero-travel crop-service challenger."""
    return decide(observation)