"""Simulator price curve, and what a batch of sales will actually fetch.

Each good's price depends on one market inventory that both players sell
into, and the simulator re-quotes after every unit, so a batch is worth the
sum of the curve rather than the spot price times the count. The curve is
transcribed from `market_price` in the simulator:
`price(inventory) = base -/+ amp * f(|inventory - I0|)`, with
`amp = target * base / f(T)`, floored at 1.

Milk, wool and strawberry reach the 1-coin floor within 50 to 90 units of
oversupply, which is why production should be priced at the margin.
"""

from __future__ import annotations

import math
from typing import Any


# item -> base, I0, T, below_func, below_target, above_func, above_target
MARKET_PARAMS: dict[str, dict[str, Any]] = {
    "WHEAT": dict(base=25, T=400, below="sqrt", below_t=0.80, above="log", above_t=0.20),
    "CARROT": dict(base=35, T=450, below="hinge", below_t=1.00, above="sqrt", above_t=0.70),
    "TOMATO": dict(base=60, T=200, below="hinge", below_t=0.40, above="sqrt", above_t=0.60),
    "STRAWBERRY": dict(base=120, T=100, below="sqrt", below_t=0.70, above="linear", above_t=1.60),
    "MELON": dict(base=250, T=300, below="log", below_t=0.20, above="sq", above_t=3.60),
    "EGG": dict(base=50, T=332, below="hinge", below_t=0.40, above="log", above_t=0.20),
    "MILK": dict(base=160, T=122, below="sqrt", below_t=0.60, above="linear", above_t=1.60),
    "WOOL": dict(base=200, T=105, below="log", below_t=0.20, above="sq", above_t=3.20),
    "FERTILIZER": dict(base=100, T=200, below="linear", below_t=0.40, above="linear", above_t=0.40),
}
MARKET_I0 = 10000
PRICE_FLOOR = 1
HINGE_GAIN = 8.0


def _shape(func: str, x: float, T: float) -> float:
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "hinge":
        if not T or T <= 0:
            return x
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x


def price_at(item: str, inventory: float) -> float:
    """The simulator's quote for `item` at that market inventory."""
    p = MARKET_PARAMS.get(item)
    if p is None:
        return 0.0
    base, T = float(p["base"]), float(p["T"])
    if inventory <= MARKET_I0:
        amp = p["below_t"] * base / _shape(p["below"], T, T)
        value = base + amp * _shape(p["below"], MARKET_I0 - inventory, T)
    else:
        amp = p["above_t"] * base / _shape(p["above"], T, T)
        value = base - amp * _shape(p["above"], inventory - MARKET_I0, T)
    return float(max(PRICE_FLOOR, round(value)))


def inventory_of(observation: dict[str, Any], item: str) -> float:
    """Market inventory of `item`, falling back to equilibrium."""
    market = observation.get("market") or {}
    stock = market.get("inventory") or {}
    value = stock.get(item)
    if isinstance(value, (int, float)):
        return float(value)
    return float(MARKET_I0)


def sale_revenue(
    observation: dict[str, Any],
    item: str,
    units: float,
    sold_already: float = 0.0,
) -> float:
    """Coins from selling `units`, walking the price down as it goes.

    The simulator re-quotes after every single unit, so a batch is the sum
    of the curve over the units, not the spot price times the count.

    `sold_already` shifts the starting point, which is how production is
    valued at the margin: the tenth cow's milk is worth what is left after
    the first nine have flooded the market, and a negative value accounts
    for what the town will still consume before we get there.
    """
    units = int(max(0.0, units))
    if units <= 0:
        return 0.0
    start = inventory_of(observation, item) + sold_already
    return float(sum(price_at(item, start + n) for n in range(units)))


def marginal_price(
    observation: dict[str, Any],
    item: str,
    already: float = 0.0,
) -> float:
    """What the next unit fetches once `already` more have been sold.

    This is the number every production decision should use. Pricing a
    thirteenth melon at the spot quote of the first is what makes an agent
    plant a field of them and sell them for one coin apiece.
    """
    return price_at(item, inventory_of(observation, item) + max(0.0, already))


def headroom(observation: dict[str, Any], item: str, floor: float) -> int:
    """How many units can still be sold before the price drops below `floor`.

    Used to cap production: there is no point growing a fourteenth melon
    tile when the market will only absorb sixty more melons above a price
    worth the tile.
    """
    inventory = inventory_of(observation, item)
    if price_at(item, inventory) < floor:
        return 0
    low, high = 0, 2000
    while low < high:
        mid = (low + high + 1) // 2
        if price_at(item, inventory + mid) >= floor:
            low = mid
        else:
            high = mid - 1
    return low
