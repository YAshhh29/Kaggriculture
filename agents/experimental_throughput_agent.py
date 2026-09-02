"""Replay-grounded dense crop throughput challenger."""

from __future__ import annotations

from typing import Any

from agents.experimental_lifecycle_agent import decide as decide_lifecycle


MAX_WHEAT_PER_PAIR = 18
TARGET_COWS = 6
TARGET_SHEEP = 6
TARGET_EXTRA_LAND = 2
MAX_MARKET_ORDERS = 10

HAND_TARGETS = (
    4, 4, 4, 4, 4, 4,
    8, 8, 9, 10, 11,
    12, 12, 12, 12, 12, 12, 12, 12, 12,
    12, 12, 12, 12, 12, 12, 12, 12,
    10, 8,
)
HIRE_COSTS = (
    1, 1, 2, 3, 5, 8, 13, 21,
    34, 55, 89, 144, 233, 377, 610, 987,
)
LAND_COSTS = (1000, 2000, 4000)
ANIMAL_COSTS = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
SEED_COSTS = {
    "WHEAT": 10,
    "CARROT": 20,
    "TOMATO": 50,
    "STRAWBERRY": 100,
    "MELON": 80,
}


def _hand_target(day: int) -> int:
    return HAND_TARGETS[min(max(day, 0), len(HAND_TARGETS) - 1)]


def _animal_crew_size(day: int) -> int:
    if day < 6:
        return 3
    if day < 9:
        return 4
    if day < 11:
        return 5
    return 6


def _purchase_cost(
    order: list[Any],
    observation: dict[str, Any],
    hire_index: int,
) -> int:
    operation = str(order[0])
    if operation == "HIRE":
        return HIRE_COSTS[min(hire_index, len(HIRE_COSTS) - 1)]
    if operation == "BUY_LAND":
        player = int(observation["player"])
        unlocked = len(
            observation["farms"][player].get("unlocked_quadrants", [])
        )
        return LAND_COSTS[min(max(0, unlocked - 1), len(LAND_COSTS) - 1)]
    if len(order) < 3:
        return 0
    item = str(order[1])
    quantity = int(order[2])
    if operation == "BUY_ANIMAL":
        return ANIMAL_COSTS[item] * quantity
    if operation == "BUY_SEED":
        return SEED_COSTS[item] * quantity
    if operation == "BUY_PRODUCT":
        price = int(
            observation.get("market", {}).get("prices", {}).get(item, 0)
        )
        return price * quantity
    return 0


def _affordable_market_orders(
    observation: dict[str, Any],
    orders: list[list[Any]],
    *,
    animals_before_seeds: bool = False,
) -> list[list[Any]]:
    player = int(observation["player"])
    farm = observation["farms"][player]
    current_hands = len(farm.get("hands", []))
    prices = observation.get("market", {}).get("prices", {})
    priority = {
        "SELL": 0,
        "BUY_PRODUCT": 1,
        "HIRE": 2,
        "BUY_LAND": 3,
        "BUY_SEED": 5 if animals_before_seeds else 4,
        "BUY_ANIMAL": 4 if animals_before_seeds else 5,
    }
    ranked = sorted(
        enumerate(orders),
        key=lambda entry: (
            priority.get(str(entry[1][0]), 99),
            entry[0],
        ),
    )
    budget = float(farm.get("money", 0))
    selected: list[list[Any]] = []
    selected_hires = 0

    for _, order in ranked:
        if len(selected) >= MAX_MARKET_ORDERS:
            break
        operation = str(order[0])
        if operation == "SELL":
            selected.append(order)
            if len(order) >= 3:
                item = str(order[1])
                quantity = int(order[2])
                budget += 0.75 * int(prices.get(item, 0)) * quantity
            continue

        hire_index = current_hands + selected_hires
        cost = _purchase_cost(order, observation, hire_index)
        if cost <= budget:
            selected.append(order)
            budget -= cost
            if operation == "HIRE":
                selected_hires += 1
            continue

        if operation not in {"BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"}:
            continue
        unit_order = [operation, order[1], 1]
        unit_cost = _purchase_cost(unit_order, observation, hire_index)
        affordable_quantity = min(
            int(order[2]),
            int(budget // unit_cost) if unit_cost > 0 else 0,
        )
        if affordable_quantity <= 0:
            continue
        selected.append([operation, order[1], affordable_quantity])
        budget -= unit_cost * affordable_quantity

    return selected


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Scale crop pairs, workers, livestock, and land on explicit day gates."""
    day = int(observation["day"])
    decision = decide_lifecycle(
        observation,
        max_wheat_per_pair=MAX_WHEAT_PER_PAIR,
        target_daily_hands=_hand_target(day),
        target_extra_land=TARGET_EXTRA_LAND,
        target_cows=TARGET_COWS,
        target_sheep=TARGET_SHEEP,
        animal_crew_size=_animal_crew_size(day),
    )
    decision["market"] = _affordable_market_orders(
        observation,
        decision["market"],
    )
    return decision


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the separate dense-throughput research challenger."""
    return decide(observation)
