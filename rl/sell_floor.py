"""Hold a unit back while its price is on the floor, and sell it later.

This is the market demand engine aimed at the only thing the live ladder
actually rewards: **a few thousand coins**.

Measured from 166 real games of our own live submission, the ladder is not
won by better play in any broad sense. Our mean reward is 85,499 against
opponents' 82,954 -- we out-produce the field -- and we still win only
45.2% of games, because the margins are tiny:

    median winning margin    1,151 coins
    median losing margin     2,889 coins
    losses inside   500 coins    17  -> flipping them gives 55.4%
    losses inside 2,500 coins    43  -> 71.1%
    losses inside 5,000 coins    61  -> 81.9%

So **+2,500 coins a game is worth about 26 points of win rate**, and a
gain that looked like noise on a panel of weak tapes is decisive here.

The mechanism is the shared market. Price is a function of one inventory
both players sell into, and the town's consumption is the only force
pushing it back up. Dumping a unit while its price is already on the floor
realises almost nothing for it; holding until the town has eaten some of
the glut realises the recovered price instead.

Four guards make the hold safe, and each one exists because a held unit is
worthless if it fires:

* the closing day sells everything, because reward is the money on the
  books at step 720;
* a shed nearing its 100-unit cap sells, because the end-of-day drop
  discards the overflow;
* short cash sells, because the route's own purchases must never fail;
* a product the town does not consume sells, because its price will not
  recover -- fertilizer has no shop and no town-centre demand at all.

Unlike `rl/demand_sales.py`, which caps *how much* may be sold per turn
against the town's absorption rate, this caps *at what price* -- and on a
high-volume route that distinction is the difference between deferring a
loss and avoiding one. Pacing measured negative on a clone (GOAL.md
10.8l); this is the other half of the idea and is measured separately.
"""

from __future__ import annotations

from typing import Any

from rl.market import headroom
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
