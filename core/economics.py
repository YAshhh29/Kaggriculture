"""Public demand, lifecycle, and labor-adjusted economic opportunities."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any


TURNS_PER_DAY = 24
SHOP_INTERVAL = 4
CASHABLE_FINAL_DAY = 28
TOWN_CENTER_DAILY_UNITS = 1
BASE_PRICES = {
    "WHEAT": 25,
    "CARROT": 35,
    "TOMATO": 60,
    "STRAWBERRY": 120,
    "MELON": 250,
    "EGG": 50,
    "MILK": 160,
    "WOOL": 200,
    "FERTILIZER": 100,
}
SALE_REALIZATION = 0.75
PREMIUM_CROP_WINDOWS = {
    "MELON": {
        "productive_ages": frozenset({6, 7, 8, 9, 10}),
        "max_yield": 6,
        "ongoing": False,
    },
    "STRAWBERRY": {
        "productive_ages": frozenset({9, 11, 13, 15}),
        "max_yield": 4,
        "ongoing": True,
    },
}

SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}


@dataclass(frozen=True)
class CropSpec:
    seed_cost: int
    units: int
    harvest_age: int
    service_actions: int
    base_price: int


CROP_SPECS = {
    "WHEAT": CropSpec(10, 4, 4, 6, 25),
    "CARROT": CropSpec(20, 3, 3, 5, 35),
    "TOMATO": CropSpec(50, 4, 11, 11, 60),
    "STRAWBERRY": CropSpec(100, 4, 16, 11, 120),
    "MELON": CropSpec(80, 6, 10, 8, 250),
}


@dataclass(frozen=True)
class AnimalSpec:
    purchase_cost: int
    product: str
    first_yield_day: int
    interval: int
    units_per_cycle: int


ANIMAL_SPECS = {
    "GOOSE": AnimalSpec(300, "EGG", 4, 1, 2),
    "COW": AnimalSpec(400, "MILK", 8, 2, 3),
    "SHEEP": AnimalSpec(500, "WOOL", 6, 3, 4),
}


def fertilizer_marginal_units(day: int, tile: Any) -> int:
    """Estimate extra units from one three-day premium-crop application."""
    if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
        return 0
    crop = str(tile.get("crop", ""))
    spec = PREMIUM_CROP_WINDOWS.get(crop)
    if spec is None or int(tile.get("fertilized_until_day", -1)) >= day:
        return 0
    age = day - int(tile.get("planted_day", day))
    productive_days = sum(
        age + offset in spec["productive_ages"]
        and not (offset == 0 and tile.get("watered_today", False))
        for offset in range(3)
    )
    if spec["ongoing"]:
        return productive_days
    current = int(tile.get("yield_units", 0))
    maximum = int(spec["max_yield"])
    baseline = min(maximum, current + productive_days)
    fertilized = min(maximum, current + 2 * productive_days)
    return max(0, fertilized - baseline)


def fertilizer_net_value(
    observation: dict[str, Any],
    tile: Any,
) -> float:
    """Value extra crop units against selling the fertilizer itself."""
    day = int(observation.get("day", 0))
    marginal_units = fertilizer_marginal_units(day, tile)
    if marginal_units <= 0:
        return float("-inf")
    crop = str(tile["crop"])
    prices = observation.get("market", {}).get("prices", {})
    crop_price = int(prices.get(crop, BASE_PRICES[crop]))
    fertilizer_price = int(
        prices.get("FERTILIZER", BASE_PRICES["FERTILIZER"])
    )
    return SALE_REALIZATION * (
        marginal_units * crop_price - fertilizer_price
    )


def profitable_feed_reserve_days(observation: dict[str, Any]) -> int:
    """Retain more wheat when one feed is worth more than selling it."""
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    if day >= 28:
        return 0
    animals = [
        str(tile["animal"])
        for row in observation["farms"][player].get("tiles", [])
        for tile in row
        if isinstance(tile, dict) and tile.get("animal") in ANIMAL_SPECS
    ]
    if not animals:
        return 0
    prices = observation.get("market", {}).get("prices", {})
    wheat_price = int(prices.get("WHEAT", BASE_PRICES["WHEAT"]))
    feed_values = [
        SALE_REALIZATION
        * int(
            prices.get(
                ANIMAL_SPECS[animal].product,
                BASE_PRICES[ANIMAL_SPECS[animal].product],
            )
        )
        for animal in animals
    ]
    mean_feed_value = sum(feed_values) / len(feed_values)
    wheat_sale_value = SALE_REALIZATION * wheat_price
    if mean_feed_value >= 2 * wheat_sale_value:
        return 3
    if mean_feed_value >= wheat_sale_value:
        return 2
    return 1


@dataclass(frozen=True)
class CropOpportunity:
    crop: str
    feasible: bool
    last_plant_day: int
    days_to_cash: int
    quoted_price: int
    specialist_demand_per_day: int
    opponent_plants: int
    expected_net: int
    score: float


@dataclass(frozen=True)
class AnimalOpportunity:
    animal: str
    feasible: bool
    quoted_product_price: int
    specialist_demand_per_day: int
    opponent_animals: int
    expected_net: int
    score: float


def daily_product_demand(
    unlocked_shops: list[str] | tuple[str, ...],
) -> Counter[str]:
    """Return deterministic town consumption in units per game day."""
    demand = Counter(
        {
            product: TOWN_CENTER_DAILY_UNITS
            for product in (
                "WHEAT",
                "CARROT",
                "TOMATO",
                "STRAWBERRY",
                "MELON",
                "EGG",
                "MILK",
                "WOOL",
            )
        }
    )
    events_per_day = TURNS_PER_DAY // SHOP_INTERVAL
    for shop in unlocked_shops:
        products = SHOP_PRODUCTS.get(str(shop), ())
        multiplier = 2 if len(products) == 1 else 1
        for product in products:
            demand[product] += events_per_day * multiplier
    return demand


def public_production_counts(farm: dict[str, Any]) -> Counter[str]:
    """Count public crops and animals by produced item."""
    counts: Counter[str] = Counter()
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                counts[str(tile.get("crop"))] += 1
            animal = str(tile.get("animal", ""))
            if animal in ANIMAL_SPECS:
                counts[ANIMAL_SPECS[animal].product] += 1
    return counts


def crop_opportunity(
    observation: dict[str, Any],
    crop: str,
) -> CropOpportunity:
    """Measure one crop using only public state and fixed mechanics."""
    spec = CROP_SPECS[crop]
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    prices = observation.get("market", {}).get("prices", {})
    demand = daily_product_demand(
        observation.get("town", {}).get("unlocked_shops", [])
    )
    opponent = public_production_counts(observation["farms"][1 - player])
    quoted_price = int(prices.get(crop, spec.base_price))
    expected_net = spec.units * quoted_price - spec.seed_cost
    specialist = max(0, demand[crop] - TOWN_CENTER_DAILY_UNITS)
    demand_multiplier = (
        0.1 if specialist == 0 and crop != "WHEAT"
        else 1.0 + specialist / (TURNS_PER_DAY // SHOP_INTERVAL)
    )
    saturation = 1.0 + opponent[crop] / max(1.0, 1.0 + specialist / 6.0)
    time_adjusted = expected_net / (
        spec.service_actions * max(1, spec.harvest_age)
    )
    score = time_adjusted * demand_multiplier / saturation
    last_plant_day = CASHABLE_FINAL_DAY - spec.harvest_age
    return CropOpportunity(
        crop=crop,
        feasible=day <= last_plant_day,
        last_plant_day=last_plant_day,
        days_to_cash=spec.harvest_age,
        quoted_price=quoted_price,
        specialist_demand_per_day=specialist,
        opponent_plants=opponent[crop],
        expected_net=expected_net,
        score=round(score, 6),
    )


def rank_crop_opportunities(
    observation: dict[str, Any],
    crops: tuple[str, ...] = tuple(CROP_SPECS),
) -> list[CropOpportunity]:
    """Rank crops by labor, horizon, demand, and supply-adjusted value."""
    opportunities = [crop_opportunity(observation, crop) for crop in crops]
    return sorted(
        opportunities,
        key=lambda opportunity: (
            not opportunity.feasible,
            -opportunity.score,
            opportunity.days_to_cash,
            opportunity.crop,
        ),
    )


def animal_opportunity(
    observation: dict[str, Any],
    animal: str,
) -> AnimalOpportunity:
    """Estimate remaining-season animal value with full feed and CARE."""
    spec = ANIMAL_SPECS[animal]
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    days_remaining = max(0, CASHABLE_FINAL_DAY - day)
    prices = observation.get("market", {}).get("prices", {})
    demand = daily_product_demand(
        observation.get("town", {}).get("unlocked_shops", [])
    )
    opponent = public_production_counts(observation["farms"][1 - player])
    cycles = (
        0
        if days_remaining < spec.first_yield_day
        else 1 + (days_remaining - spec.first_yield_day) // spec.interval
    )
    product_units = cycles * spec.units_per_cycle
    fertilizer_units = max(0, days_remaining - 1)
    feed_cost = days_remaining * int(prices.get("WHEAT", BASE_PRICES["WHEAT"]))
    expected_net = (
        product_units
        * int(prices.get(spec.product, BASE_PRICES[spec.product]))
        + fertilizer_units
        * int(prices.get("FERTILIZER", BASE_PRICES["FERTILIZER"]))
        - feed_cost
        - spec.purchase_cost
    )
    specialist = max(
        0,
        demand[spec.product] - TOWN_CENTER_DAILY_UNITS,
    )
    demand_multiplier = (
        0.25 if specialist == 0 else 1.0 + specialist / 6.0
    )
    saturation = 1.0 + opponent[spec.product] / max(
        1.0, 1.0 + specialist / 6.0
    )
    service_actions = max(1, 3 * days_remaining + cycles + 3)
    score = expected_net * demand_multiplier / (service_actions * saturation)
    return AnimalOpportunity(
        animal=animal,
        feasible=cycles > 0 and expected_net > 0,
        quoted_product_price=int(
            prices.get(spec.product, BASE_PRICES[spec.product])
        ),
        specialist_demand_per_day=specialist,
        opponent_animals=opponent[spec.product],
        expected_net=expected_net,
        score=round(score, 6),
    )


def economic_snapshot(observation: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-ready explanation of all crop and animal opportunities."""
    return {
        "daily_demand": dict(
            sorted(
                daily_product_demand(
                    observation.get("town", {}).get("unlocked_shops", [])
                ).items()
            )
        ),
        "crops": [
            asdict(item) for item in rank_crop_opportunities(observation)
        ],
        "animals": [
            asdict(animal_opportunity(observation, animal))
            for animal in ANIMAL_SPECS
        ],
    }
