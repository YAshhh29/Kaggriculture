"""Investment-focused land, labor, and livestock expansion candidate."""

from __future__ import annotations

from collections import Counter
from typing import Any

from agents.experimental_scale_agent import (
    LAST_WHEAT_PLANTING_DAY,
    MAX_MARKET_ORDERS,
    _feed_due,
    _hire_orders,
    _land_orders,
    _plan_is_active,
    _protect_feed_reserve,
    _quadrant,
    _staged_animal_plans,
    _unlocked_animal_plans,
    _worker_actions,
)
from main import decide as decide_wheat


TARGET_DAILY_HANDS = 10
TARGET_WHEAT_TILES = 12
TARGET_COWS = 6
TARGET_SHEEP = 12
TARGET_EXTRA_LAND = 3
TARGET_TOTAL_MARKET_ANIMALS = 18


def _animal_count(farm: dict[str, Any]) -> int:
    return sum(
        isinstance(tile, dict) and bool(tile.get("animal"))
        for row in farm.get("tiles", [])
        for tile in row
    )


def _animal_counts(farm: dict[str, Any]) -> Counter[str]:
    return Counter(
        str(tile["animal"])
        for row in farm.get("tiles", [])
        for tile in row
        if isinstance(tile, dict) and tile.get("animal")
    )


def _pressure_targets(
    observation: dict[str, Any],
    player: int,
    maximum_hands: int,
    target_market_animals: int = TARGET_TOTAL_MARKET_ANIMALS,
) -> tuple[int, int, int, int]:
    opponent = observation["farms"][1 - player]
    own_counts = _animal_counts(observation["farms"][player])
    opponent_animals = _animal_count(opponent)
    target_animals = max(
        8,
        target_market_animals - opponent_animals,
        sum(own_counts.values()),
    )
    target_cows = max(
        own_counts["COW"],
        min(6, max(4, (target_animals + 2) // 3)),
    )
    target_sheep = max(
        own_counts["SHEEP"],
        target_animals - target_cows,
    )
    target_hands = min(
        maximum_hands,
        8 + max(0, target_animals - 8 + 4) // 5,
    )
    plans = _staged_animal_plans(29, target_cows, target_sheep)
    land_order = {"NE": 1, "SW": 2, "SE": 3}
    target_land = max(
        (
            land_order.get(_quadrant(plan["position"], 10), 0)
            for plan in plans
        ),
        default=0,
    )
    return target_cows, target_sheep, target_hands, target_land


def _investment_livestock_orders(
    animal_plans: tuple[dict[str, Any], ...],
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
) -> tuple[list[list[Any]], list[list[Any]]]:
    tiles = farm["tiles"]
    shed = private.get("shed", {})
    carried = Counter()
    for inventory in private.get("inventories", []):
        if isinstance(inventory, dict):
            carried.update(inventory)

    urgent: list[list[Any]] = []
    sales: list[list[Any]] = []
    if day <= 20:
        desired = Counter(str(plan["animal"]) for plan in animal_plans)
        present = Counter(
            str(plan["animal"])
            for plan in animal_plans
            if _plan_is_active(plan, tiles)
        )
        for animal in ("COW", "SHEEP"):
            missing = max(
                0,
                desired[animal]
                - present[animal]
                - int(shed.get(animal, 0))
                - int(carried.get(animal, 0)),
            )
            if missing > 0:
                urgent.append(["BUY_ANIMAL", animal, min(missing, 2)])

    feed_needed = sum(
        _feed_due(day, tiles[plan["position"][1]][plan["position"][0]], True)
        for plan in animal_plans
        if _plan_is_active(plan, tiles)
    )
    available_feed = int(shed.get("WHEAT", 0)) + int(
        carried.get("WHEAT", 0)
    )
    if feed_needed > available_feed:
        urgent.append(
            ["BUY_PRODUCT", "WHEAT", feed_needed - available_feed]
        )

    for item in ("MILK", "WOOL", "FERTILIZER"):
        quantity = int(shed.get(item, 0))
        if quantity > 0:
            sales.append(["SELL", item, quantity])
    return urgent, sales


def _investment_market_orders(
    sales: list[list[Any]],
    urgent: list[list[Any]],
    land: list[list[Any]],
    hires: list[list[Any]],
    baseline: list[list[Any]],
) -> list[list[Any]]:
    orders = [*sales, *urgent, *land, *hires, *baseline]
    priority = {
        "SELL": 0,
        "BUY_PRODUCT": 1,
        "BUY_LAND": 2,
        "BUY_ANIMAL": 3,
        "HIRE": 4,
        "BUY_SEED": 5,
    }
    ranked = sorted(
        enumerate(orders),
        key=lambda entry: (
            priority.get(str(entry[1][0]), 99),
            entry[0],
        ),
    )
    return [order for _, order in ranked[:MAX_MARKET_ORDERS]]


def decide(
    observation: dict[str, Any],
    target_wheat_tiles: int = TARGET_WHEAT_TILES,
    target_daily_hands: int = TARGET_DAILY_HANDS,
    pressure_aware: bool = True,
    target_market_animals: int = TARGET_TOTAL_MARKET_ANIMALS,
) -> dict[str, Any]:
    """Invest in all land, replay-staged livestock, and adaptive labor."""
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    day = int(observation["day"])
    hour = int(observation["hour"])

    if pressure_aware:
        (
            target_cows,
            target_sheep,
            target_daily_hands,
            target_extra_land,
        ) = _pressure_targets(
            observation,
            player,
            target_daily_hands,
            target_market_animals,
        )
    else:
        target_cows = TARGET_COWS
        target_sheep = TARGET_SHEEP
        target_extra_land = TARGET_EXTRA_LAND

    desired_plans = _staged_animal_plans(day, target_cows, target_sheep)
    active_plans = _unlocked_animal_plans(desired_plans, farm)
    baseline = decide_wheat(
        observation,
        target_wheat_tiles=target_wheat_tiles,
        last_planting_day=LAST_WHEAT_PLANTING_DAY,
    )
    baseline_market = _protect_feed_reserve(
        baseline["market"],
        active_plans,
        day,
        farm,
        private,
        True,
    )
    farmer_action, hands_actions = _worker_actions(
        active_plans,
        {plan["position"] for plan in desired_plans},
        day,
        farm,
        private,
        True,
        True,
    )
    urgent, sales = _investment_livestock_orders(
        active_plans,
        day,
        farm,
        private,
    )
    market = _investment_market_orders(
        sales,
        urgent,
        _land_orders(day, hour, farm, target_extra_land),
        _hire_orders(day, hour, farm, target_daily_hands, True),
        baseline_market,
    )
    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market,
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the investment-focused candidate."""
    return decide(observation)