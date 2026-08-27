"""Hold low-price fertilizer with bounded inventory and liquidation."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import _choices, decide_demand
from agents.experimental_future_labor_agent import _selected_hand_targets


MINIMUM_FERTILIZER_SALE_PRICE = 60
MAXIMUM_FERTILIZER_HOLDINGS = 72
FERTILIZER_LIQUIDATION_DAY = 28


def decide_with_threshold(
    observation: dict[str, Any],
    minimum_sale_price: int,
) -> dict[str, Any]:
    """Run future labor with one bounded fertilizer sale threshold."""
    animal, _ = _choices(observation)
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
        hand_targets=_selected_hand_targets(observation, animal),
        minimum_fertilizer_sale_price=minimum_sale_price,
        maximum_fertilizer_holdings=MAXIMUM_FERTILIZER_HOLDINGS,
        fertilizer_liquidation_day=FERTILIZER_LIQUIDATION_DAY,
    )


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Hold fertilizer below 60 unless inventory or horizon releases it."""
    return decide_with_threshold(
        observation,
        MINIMUM_FERTILIZER_SALE_PRICE,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the fertilizer-value challenger."""
    return decide(observation)