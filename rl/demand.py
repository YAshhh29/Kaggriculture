"""Read the town's demand for each product from the live observation.

The simulator's demand engine (`_town_consume` in kaggriculture.py) is
fully deterministic and fully observable:

* every `townShopSellInterval` (4) steps, each unlocked shop instance
  removes one unit of each product it sells -- **two** if the shop sells
  only a single product, which is YARN_STORE (wool) and PET_CAFE (carrot);
* every `townCenterSellInterval` (24) steps the town centre removes one
  unit of every product except FERTILIZER;
* shops unlock roughly every three days, drawn **at random with
  replacement** from the eight types and capped at eight instances.

Because the draw is random per episode, every game has a different demand
profile, and because `observation["town"]["unlocked_shops"]` lists the
instances, that profile can be computed exactly rather than guessed.

Why this matters (rl/GOAL.md section 9u and 9v): the resulting price
swings are enormous -- wool ends a game worth 1 coin or 239 depending on
whether YARN_STORE was drawn, milk 5 or 110 -- and adaptation to it is
the single cleanest correlate of leaderboard rank we have measured:
wool-demand-to-sheep-bought runs +0.672 for teams at 2850+, +0.323 for
2400-2849 and **+0.000 below 2400**. A frozen tape scores structurally
zero there, which is where every candidate this project has shipped sits.
"""

from __future__ import annotations

from typing import Any


SHOPS: dict[str, tuple[str, ...]] = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
PRODUCTS: tuple[str, ...] = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER",
)
# The town centre buys everything except fertilizer, which is why
# fertilizer has no natural demand at all and every unit sold sits in the
# market permanently depressing its price.
TOWN_CENTRE: tuple[str, ...] = tuple(p for p in PRODUCTS if p != "FERTILIZER")
SHOP_INTERVAL = 4
CENTRE_INTERVAL = 24
EPISODE_STEPS = 720
ANIMAL_PRODUCT = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}


def unlocked_shops(observation: dict[str, Any]) -> list[str]:
    town = observation.get("town") or {}
    shops = town.get("unlocked_shops") or []
    return [str(s) for s in shops if str(s) in SHOPS]


def shop_demand_per_event(shops: list[str]) -> dict[str, int]:
    """Units each product loses every `SHOP_INTERVAL` steps."""
    demand = {p: 0 for p in PRODUCTS}
    for shop in shops:
        products = SHOPS.get(shop)
        if not products:
            continue
        multiplier = 2 if len(products) == 1 else 1
        for product in products:
            demand[product] += multiplier
    return demand


def demand_rate(observation: dict[str, Any]) -> dict[str, float]:
    """Units per step the town will absorb, at the current shop set."""
    per_event = shop_demand_per_event(unlocked_shops(observation))
    rate = {p: per_event[p] / SHOP_INTERVAL for p in PRODUCTS}
    for product in TOWN_CENTRE:
        rate[product] += 1.0 / CENTRE_INTERVAL
    return rate


def remaining_demand(observation: dict[str, Any]) -> dict[str, float]:
    """Units the town will still absorb between now and the final step.

    Held at the *current* shop set, so this understates late demand while
    shops are still unlocking. That bias is deliberate: it never promises
    demand that has not been observed yet.
    """
    step = int(observation.get("step", 0))
    left = max(0, EPISODE_STEPS - step)
    return {p: r * left for p, r in demand_rate(observation).items()}


def preferred_animal(
    observation: dict[str, Any],
    candidates: tuple[str, ...] = ("COW", "SHEEP"),
    *,
    margin: float = 1.25,
) -> str | None:
    """Which pasture animal this town actually wants, if either clearly is.

    Compares expected remaining revenue per animal product -- demand still
    to come, valued at the live price -- and only names a winner when it
    leads by `margin`. Below that the two are close enough that switching
    is not worth disturbing a proven route.
    """
    market = observation.get("market") or {}
    prices = market.get("prices") or {}
    remaining = remaining_demand(observation)
    scored: list[tuple[float, str]] = []
    for animal in candidates:
        product = ANIMAL_PRODUCT.get(animal)
        if product is None:
            continue
        price = float(prices.get(product, 0.0))
        scored.append((remaining.get(product, 0.0) * price, animal))
    if len(scored) < 2:
        return None
    scored.sort(reverse=True)
    best, second = scored[0], scored[1]
    if second[0] <= 0:
        return best[1] if best[0] > 0 else None
    return best[1] if best[0] >= second[0] * margin else None
