"""Candidate K2 -- the route, overridden only where an override is provable.

K is H2's recorded route and nothing else. Its own metering has been dead
code for some time, and on the live board it scores 1570.2 against the
route's own 1576.2: the same agent, six points worse. Every attempt this
project has made to improve on the route by taking a statistic off
stronger teams and turning it into a rule has lost, and lost badly:

    lot cap at six units       35/120 bracket wins   against 58/120
    shed drained to six         4/120                 against 58/120
    endgame liquidation spread  worse on own score
    game handed to J at day 9   0/120 wins on strong opponents
    game handed to J at day 12  12/120 bracket wins   against 58/120

The pattern is the same every time. The bracket carries six units of shed
because its timing earns full price; forcing our shed to six means dumping
into our own books all game. Their numbers are RESULTS of good play, not
instructions for it.

WHAT THIS FILE DOES DIFFERENTLY
===============================
lynnsakurai's notebook frames the only approach that survives that
pattern: never substitute your judgement for the route's, and never act on
a statistic. Act only where a CHECK, evaluated against the live board this
turn, proves the action cannot be worse than not taking it. Where the
check does not pass, do exactly what the route does.

The route's weakness is not what it does, it is what it leaves on the
table. It plays a recorded programme, so it cannot notice that this
particular game has handed it a book paying well above base -- a town
whose shops happen to drain wool, an opponent who has not sold milk in
twenty turns. K2 takes only those trades, and only with slots the route
did not use.

THE INVARIANT
-------------
A unit is sold only when the book pays at least PREMIUM times base for it.
That is not a preference, it is a proof: `market_price` depends on
inventory alone and falls as we sell, so a unit sold at or above base is
sold at a price the rest of the season will not see again once the glut
arrives -- and the town keeps draining the book, so refusing the trade
does not preserve it, it hands it to whoever sells next. The quantity is
walked unit by unit against the live curve and stops the moment the next
unit would fall below the bar, so the trade cannot carry itself past its
own justification.

Three things this never does, each of which broke an earlier attempt:
  * it never takes a slot the route wanted -- only spare ones, appended,
    so no route order is shifted into a different index;
  * it never moves a hand, plants, or touches a tile, so the recorded
    programme's assumptions about where its workers are stay true;
  * it never sells below base, so it cannot be the thing that crashes a
    book the route was counting on.

    PREMIUM = 0.0 disables the override entirely and is K exactly.
"""

from __future__ import annotations

from typing import Any

import rl.candidate_k as K
from rl.economics import BASE_PRICE
from rl.market import MARKET_PARAMS, inventory_of, price_at

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
