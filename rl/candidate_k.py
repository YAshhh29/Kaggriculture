"""Candidate K: H2's farm, sold at J's prices.

The two agents this project has are each missing exactly what the other has.

H2 grows. It works 58.0 of its 60.3 tiles where J works 50.7 of 61, stands
18.7 strawberry to J's 10.5 and 6.1 cows to J's 3.5, puts 65,630 coins a
game of inputs through the market to J's 17,620, and turns over 181,907 of
goods to J's 115,336. On the honest breadth panel it wins 27 of 48 clean
games where J wins 5 of 47, and head to head it beats J by 67,202 a game.

And then it gives the crop away. Its own audit, per game:

    strawberry   249 units at 109.6 coins, 9% BELOW base, 92 of them
                 under a quarter of base
    wool         169 units at 167.0, 16% below base, 38 under a quarter
    milk         190 units at 131.1, 18% below base, 76 under a quarter

J sells those same goods at 189.7, 227.5 and 96.6 -- strawberry 58% ABOVE
base, wool 14% above -- because it meters each book against its own depth.
The books are shallow beyond belief: wool gives up a quarter of its price
over 51 units and strawberry over 48, while wheat takes two thousand. H2
sells whatever its route projects, in one lot, into a book sixteen units
deep.

Strawberry alone is 249 units at 80 coins of difference. So K is H2,
unaltered, with one thing added: before the action leaves, every sale of a
fragile good is cut back to what the book will pay for. The route, the
timing layers and the opening are untouched.

Two rules from J's measurements come with it, both learned expensively:

* The meter lifts when the shed is tight. Holding stock to protect a price
  loses -- the hundred-slot shed is what binds late, and a freed slot is
  worth more than the coins the freeing unit gives up. Measured twice in J,
  at 78,490 and 80,385 against 80,730.
* Wheat, egg and carrot are never metered. Their books are bottomless, the
  town eats some nine hundred wheat a game, and J sells every unit of those
  three above base already.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from rl.economics import BASE_PRICE
from rl.market import MARKET_PARAMS, inventory_of, price_at

_PATH = (Path(__file__).resolve().parents[1] / "submissions"
         / "candidate-h2" / "main.py")
_spec = importlib.util.spec_from_file_location("candidate_k_h2_core", _PATH)
_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)

# The books worth protecting, and the share of base below which a sale is not
# worth making on an ordinary turn. Fertilizer is deliberately absent: it is
# the one good the town never eats, so holding it only costs a shed slot, and
# metering it was measured in J and lost.
FRAGILE = ("WOOL", "STRAWBERRY", "MILK", "MELON")
FLOOR = 0.55
SHED_CAP = 100
# Above this the shed is the binding constraint and the meter comes off.
CRAMPED = SHED_CAP - 12


def _shed_total(observation: dict[str, Any]) -> int:
    private = observation.get("private") or {}
    shed = private.get("shed") or {}
    try:
        return sum(int(v) for v in shed.values())
    except (TypeError, ValueError):
        return 0


def meter(observation: dict[str, Any], market: list) -> list:
    """Cut each fragile sale back to what its book will actually pay for.

    Price is a function of inventory alone -- there is no recovery with time
    -- so a unit sold raises the inventory permanently and only the town
    eating brings it down again. Selling past the floor is not impatience,
    it is handing over the rest of the game's production at a lower price.
    """
    if not market:
        return market
    if _shed_total(observation) >= CRAMPED:
        return market
    out = []
    for order in market:
        if (not isinstance(order, (list, tuple)) or len(order) < 3
                or order[0] != "SELL" or order[1] not in FRAGILE):
            out.append(list(order) if isinstance(order, (list, tuple))
                       else order)
            continue
        item = order[1]
        try:
            want = int(order[2])
        except (TypeError, ValueError):
            out.append(list(order))
            continue
        if want <= 0:
            out.append(list(order))
            continue
        inventory = inventory_of(observation, item)
        base = float(MARKET_PARAMS.get(item, {}).get(
            "base", BASE_PRICE.get(item, 1)))
        allowed = 0
        while allowed < want:
            if price_at(item, inventory + allowed) < base * FLOOR:
                break
            allowed += 1
        # A zero-quantity order is kept rather than dropped: H2's own layers
        # index into this list, and a shorter one shifts every order behind
        # it into a different slot of the ten the engine reads.
        out.append(["SELL", item, allowed])
    return out


def agent(observation: dict[str, Any], configuration: Any = None):
    """Entry point. Must stay the last callable defined in this module."""
    action = _core.agent(observation, configuration)
    try:
        if isinstance(action, dict) and action.get("market"):
            action["market"] = meter(observation, action["market"])
    except Exception:
        return action
    return action
