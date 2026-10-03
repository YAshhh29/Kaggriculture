"""Candidate K2: Candidate K plus extra sales the live market proves safe.

K is H2's recorded route; every attempt to improve it by turning a statistic
from stronger players into a rule has lost. K2 acts only where a check against
this turn's board shows the action cannot be worse than not taking it: in order
slots the route left unused, it sells pure outputs while the live price stays
at or above PREMIUM times base, walking the curve unit by unit (at most
MAX_TAKE per good). It never moves a hand, never displaces a route order, and
never sells WHEAT or FERTILIZER, which the route consumes.

PREMIUM = 0.0 disables the override and is K exactly.
"""

from __future__ import annotations

from typing import Any

import candidates.candidate_k as K
from candidates.economics import BASE_PRICE
from candidates.market import MARKET_PARAMS, inventory_of, price_at

# Share of base the book must pay before a unit is worth taking off the
# shed. One means "only sell into a book at or above its anchor price".
PREMIUM = 1.0
# Most units to take in any one turn, so a single premium book is drained
# across several turns rather than in one lot that walks its own price
# down. The bracket's median sized lot is four and its p90 is thirteen.
MAX_TAKE = 6
# Orders the engine reads in a turn. Anything appended past this is
# dropped, so the route's own orders must always fit first.
MAX_ORDERS = 10
# Goods the route CONSUMES, which this must never touch however well the
# book pays. Wheat is feed -- every animal eats one a day and starves in
# two -- and fertilizer is spread on the crops. The first version of this
# file checked only that the price cleared base and sold the herd's grain
# out from under the route at a handsome price: 36,299 against K's
# 123,930 on the same seed, and 63,422 against 140,708 on another. A
# trade being good is not the same as a trade being safe, and an
# invariant that only proves the first is not an invariant at all. Only
# pure outputs are sold here -- things the farm makes to sell and uses
# for nothing else.
NEVER_SELL = ("WHEAT", "FERTILIZER")


def premium_sales(observation: dict[str, Any], market: list) -> list:
    """Append sales the live book proves are worth making, in spare slots."""
    if PREMIUM <= 0.0 or len(market) >= MAX_ORDERS:
        return market
    private = observation.get("private") or {}
    shed = private.get("shed") or {}
    if not shed:
        return market

    offers: list[tuple[float, str, int]] = []
    for item, count in shed.items():
        try:
            count = int(count)
        except (TypeError, ValueError):
            continue
        if count <= 0 or item not in MARKET_PARAMS or item in NEVER_SELL:
            continue
        base = float(MARKET_PARAMS.get(item, {}).get(
            "base", BASE_PRICE.get(item, 1)))
        if base <= 0:
            continue
        inventory = inventory_of(observation, item)
        # Walk the live curve. Stop at the unit that would price below the
        # bar, so every unit in the order is individually justified.
        take = 0
        gained = 0.0
        while take < min(count, MAX_TAKE):
            price = price_at(item, inventory + take)
            if price < base * PREMIUM:
                break
            gained += price
            take += 1
        if take > 0:
            offers.append((gained, item, take))

    if not offers:
        return market
    # Best book first, so if slots run out the trade given up is the
    # smallest one.
    offers.sort(reverse=True)
    out = list(market)
    for _gained, item, take in offers:
        if len(out) >= MAX_ORDERS:
            break
        out.append(["SELL", item, int(take)])
    return out


def agent(observation: dict[str, Any], configuration: Any = None):
    """Entry point. Must stay the last callable defined in this module."""
    action = K.agent(observation, configuration)
    try:
        if isinstance(action, dict) and PREMIUM > 0.0:
            action["market"] = premium_sales(
                observation, action.get("market") or [])
    except Exception:
        return action
    return action
