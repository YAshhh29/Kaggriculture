"""Candidate B: order-safe premium market residual over Candidate A."""

from __future__ import annotations

import itertools
import math
from typing import Any

from agents.experimental_calendar_recovery_agent import agent as candidate_a
from rl.runtime import AgentAction, Baseline, clone_action


MAX_MARKET_ORDERS = 10
TERMINAL_MARKET_STEP = 717
PREMIUM_PRODUCTS = {"MELON", "MILK", "WOOL", "STRAWBERRY"}
MARKET_I0 = 10_000
PRICE_FLOOR = 1
MARKET_PARAMS = {
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
}


def _shape(function: str, value: float, scale: int) -> float:
    value = max(0.0, value)
    if function == "linear":
        return value
    if function == "sq":
        return value * value
    if function == "sqrt":
        return math.sqrt(value)
    if function == "log":
        return math.log(1.0 + value)
    if function == "hinge":
        unit = value / scale
        return unit + 8.0 * max(0.0, unit - 1.0) ** 2
    return value


def _market_price(product: str, inventory: int) -> int:
    base, scale, below_function, below_target, above_function, above_target = (
        MARKET_PARAMS[product]
    )
    if inventory < MARKET_I0:
        function = below_function
        target = below_target
        distance = MARKET_I0 - inventory
    else:
        function = above_function
        target = above_target
        distance = inventory - MARKET_I0
    amplitude = target * base / _shape(function, scale, scale)
    signed_change = (1 if inventory < MARKET_I0 else -1) * amplitude
    return max(
        PRICE_FLOOR,
        int(round(base + signed_change * _shape(function, distance, scale))),
    )


def _premium_sell_order(order: list[Any]) -> bool:
    return (
        len(order) >= 3
        and str(order[0]) == "SELL"
        and str(order[1]) in PREMIUM_PRODUCTS
        and int(order[2]) > 0
    )


def _premium_ordering(
    observation: dict[str, Any],
    market_orders: list[list[Any]],
) -> list[list[Any]]:
    """Reorder only a pure premium-sale batch; otherwise preserve the plan."""
    if int(observation.get("step", 0)) >= TERMINAL_MARKET_STEP:
        return market_orders
    if not market_orders or len(market_orders) > MAX_MARKET_ORDERS:
        return market_orders
    if not all(_premium_sell_order(order) for order in market_orders):
        return market_orders
    market = observation.get("market", {})
    inventory = market.get("inventory", {})
    if any(str(order[1]) not in inventory for order in market_orders):
        return market_orders

    best_orders = [list(order) for order in market_orders]
    best_value = _sale_value(best_orders, inventory)
    for permutation in itertools.permutations(market_orders):
        candidate = [list(order) for order in permutation]
        value = _sale_value(candidate, inventory)
        if value > best_value:
            best_orders = candidate
            best_value = value
    return best_orders


def _sale_value(orders: list[list[Any]], inventory: dict[str, Any]) -> int:
    projected = {str(item): int(quantity) for item, quantity in inventory.items()}
    value = 0
    for order in orders:
        product = str(order[1])
        for _ in range(int(order[2])):
            value += _market_price(product, projected[product])
            projected[product] += 1
    return value


def build_candidate_b_agent(*, baseline: Baseline = candidate_a) -> Baseline:
    """Create Candidate A plus the isolated premium ordering residual."""
    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        action["market"] = _premium_ordering(
            observation,
            action["market"],
        )
        return action

    return decide


agent = build_candidate_b_agent()