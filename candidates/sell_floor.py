"""Hold back sales while a good's price is on the floor, and sell after it recovers.

SELL orders are trimmed to the units that still fetch at least `floor`
coins (`candidates.market.headroom`). The hold is lifted on the closing
day, when the shed nears its 100-unit cap and when cash runs short, and it
never applies to livestock or to goods the town does not consume.

Measured result: -7,336 coins a game over 120 paired games on a high-volume
route-following agent. It pays only for an agent that sells less than the
town absorbs, where held prices have time to recover.
"""

from __future__ import annotations

from typing import Any

from candidates.market import headroom
from rl.runtime import AgentAction, Baseline, clone_action

LIVESTOCK = ("COW", "SHEEP", "GOOSE")
NO_TOWN_DEMAND = ("FERTILIZER",)
TURNS_PER_DAY = 24


def _shed(observation: dict[str, Any]) -> dict[str, int]:
    private = observation.get("private") or {}
    return {str(k): int(v) for k, v in (private.get("shed") or {}).items()}


def _money(observation: dict[str, Any]) -> float:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    if player < len(farms) and isinstance(farms[player], dict):
        return float(farms[player].get("money", 0.0))
    return 0.0


def floor_orders(
    observation: dict[str, Any],
    orders: list[list[Any]],
    *,
    floor: float,
    cash_floor: float,
    shed_pressure: int,
    closing_day: int,
) -> list[list[Any]]:
    """Trim SELL orders down to the units that still fetch `floor` or more."""
    if floor <= 0.0:
        return orders
    step = int(observation.get("step", 0))
    if step // TURNS_PER_DAY >= closing_day:
        return orders
    if _money(observation) < cash_floor:
        return orders
    if sum(_shed(observation).values()) >= shed_pressure:
        return orders

    out: list[list[Any]] = []
    for order in orders:
        if not (isinstance(order, list) and len(order) >= 3
                and order[0] == "SELL"):
            out.append(order)
            continue
        item = str(order[1])
        if item in LIVESTOCK or item in NO_TOWN_DEMAND:
            out.append(order)
            continue
        room = headroom(observation, item, floor)
        quantity = min(int(order[2]), room)
        if quantity > 0:
            out.append(["SELL", item, quantity])
    return out


def build_sell_floor_agent(
    baseline: Baseline,
    *,
    floor: float = 15.0,
    cash_floor: float = 1500.0,
    shed_pressure: int = 80,
    closing_day: int = 29,
) -> Baseline:
    """Wrap any agent so it stops selling into a floored price."""

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        action["market"] = floor_orders(
            observation,
            list(action["market"]),
            floor=floor,
            cash_floor=cash_floor,
            shed_pressure=shed_pressure,
            closing_day=closing_day,
        )
        return action

    return decide
