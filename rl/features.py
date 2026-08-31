"""Stable state-vector contract for learned residual policies."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from policies.live_macro_features import (
    LIVE_FEATURE_NAMES,
    extract_live_macro_features,
)


CLOCK_FEATURE_NAMES = (
    "day_fraction",
    "hour_fraction",
    "episode_fraction",
)
BASELINE_FEATURE_NAMES = (
    "baseline_hands",
    "baseline_moves",
    "baseline_plants",
    "baseline_waters",
    "baseline_harvests",
    "baseline_animal_services",
    "baseline_passes",
    "baseline_market_orders",
    "baseline_hires",
    "baseline_land_orders",
    "baseline_seed_units",
    "baseline_animal_units",
    "baseline_sell_units",
)
STATE_FEATURE_NAMES = (
    *CLOCK_FEATURE_NAMES,
    *LIVE_FEATURE_NAMES,
    *BASELINE_FEATURE_NAMES,
)
MOVE_ACTIONS = {"NORTH", "SOUTH", "EAST", "WEST"}
ANIMAL_SERVICE_ACTIONS = {
    "FEED",
    "CARE",
    "COLLECT_FERTILIZER",
}


@dataclass(frozen=True)
class EncodedState:
    """Named vector passed to a learned policy."""

    names: tuple[str, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.names) != len(self.values):
            raise ValueError("Feature names and values must have equal length")
        if not all(isfinite(value) for value in self.values):
            raise ValueError("RL state contains a non-finite feature")

    def as_dict(self) -> dict[str, float]:
        return dict(zip(self.names, self.values, strict=True))


def _operation(action: Any) -> str:
    if not isinstance(action, list) or not action:
        return "PASS"
    return str(action[0])


def _order_units(order: Any) -> int:
    if not isinstance(order, list):
        return 0
    if len(order) >= 3:
        return max(0, int(order[2]))
    return 1


def summarize_baseline_action(
    action: dict[str, Any],
) -> dict[str, float]:
    """Describe what the trusted policy intends to do this transition."""
    farmer = action.get("farmer", ["PASS"])
    hands = action.get("hands", [])
    unit_operations = [
        _operation(farmer),
        *(_operation(hand_action) for hand_action in hands),
    ]
    market = [
        order
        for order in action.get("market", [])
        if isinstance(order, list) and order
    ]

    def market_units(operation: str) -> int:
        return sum(
            _order_units(order)
            for order in market
            if str(order[0]) == operation
        )

    return {
        "baseline_hands": float(len(hands)),
        "baseline_moves": float(
            sum(operation in MOVE_ACTIONS for operation in unit_operations)
        ),
        "baseline_plants": float(unit_operations.count("PLANT")),
        "baseline_waters": float(unit_operations.count("WATER")),
        "baseline_harvests": float(unit_operations.count("HARVEST")),
        "baseline_animal_services": float(
            sum(
                operation in ANIMAL_SERVICE_ACTIONS
                for operation in unit_operations
            )
        ),
        "baseline_passes": float(unit_operations.count("PASS")),
        "baseline_market_orders": float(len(market)),
        "baseline_hires": float(
            sum(str(order[0]) == "HIRE" for order in market)
        ),
        "baseline_land_orders": float(
            sum(str(order[0]) == "BUY_LAND" for order in market)
        ),
        "baseline_seed_units": float(market_units("BUY_SEED")),
        "baseline_animal_units": float(market_units("BUY_ANIMAL")),
        "baseline_sell_units": float(market_units("SELL")),
    }


def encode_state(
    observation: dict[str, Any],
    baseline_action: dict[str, Any],
) -> EncodedState:
    """Encode legal observation data and the calendar's intended action."""
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    step = int(observation.get("step", day * 24 + hour))
    values = {
        "day_fraction": min(max(day / 29.0, 0.0), 1.0),
        "hour_fraction": min(max(hour / 23.0, 0.0), 1.0),
        "episode_fraction": min(max(step / 718.0, 0.0), 1.0),
        **extract_live_macro_features(observation),
        **summarize_baseline_action(baseline_action),
    }
    return EncodedState(
        names=STATE_FEATURE_NAMES,
        values=tuple(float(values[name]) for name in STATE_FEATURE_NAMES),
    )