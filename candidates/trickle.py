"""Split each sale into small lots so the same units reach the market over more turns.

The price depends on one inventory shared with the opponent. Selling in a
few large lumps lets the town consume the glut between them and leaves
prices high for the opponent; spreading the same volume over more turns
keeps the price down, which cuts the opponent's income and the cash it has
for buying animals. Each SELL is cut to `per_turn` units and the rest stays
in the shed for later turns, so nothing is withheld. Limits are lifted in
the closing days and when the shed nears its 100-unit cap.

Not used by any shipped agent; whether spreading pays has not been measured.
"""

from __future__ import annotations

from typing import Any

from rl.runtime import AgentAction, Baseline, clone_action

TURNS_PER_DAY = 24
LIVESTOCK = ("COW", "SHEEP", "GOOSE")


def _shed(observation: dict[str, Any]) -> dict[str, int]:
    private = observation.get("private") or {}
    return {str(k): int(v) for k, v in (private.get("shed") or {}).items()}


def trickle_orders(
    observation: dict[str, Any],
    orders: list[list[Any]],
    *,
    per_turn: int,
    closing_day: int,
    shed_pressure: int,
) -> list[list[Any]]:
    """Trim each SELL to `per_turn` units, leaving the rest for later turns.

    Nothing is dropped: the shed keeps what is not sold now and the next
    turn's order draws on it again, so the same stock reaches the market
    over more turns rather than in one lump.
    """
    if per_turn <= 0:
        return orders
    step = int(observation.get("step", 0))
    if step // TURNS_PER_DAY >= closing_day:
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
        if item in LIVESTOCK:
            out.append(order)
            continue
        try:
            quantity = int(order[2])
        except (TypeError, ValueError):
            out.append(order)
            continue
        if quantity > 0:
            out.append(["SELL", item, min(quantity, per_turn)])
    return out


def build_trickle_agent(
    baseline: Baseline,
    *,
    per_turn: int = 4,
    closing_day: int = 28,
    shed_pressure: int = 85,
) -> Baseline:
    """Wrap an agent so it meters each good onto the market."""

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        action["market"] = trickle_orders(
            observation,
            list(action["market"]),
            per_turn=per_turn,
            closing_day=closing_day,
            shed_pressure=shed_pressure,
        )
        return action

    return decide
