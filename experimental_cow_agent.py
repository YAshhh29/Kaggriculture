"""Development-only one-cow extension of the two-hand goose policy."""

from __future__ import annotations

from typing import Any

from experimental_goose_agent import (
    _carried,
    _move_toward,
    _shed_access_tiles,
)
from experimental_hands_agent import (
    _coordinated_crop_actions,
    _hire_orders,
)
from main import decide as decide_wheat


TARGET_WHEAT_TILES = 12
LAST_WHEAT_PLANTING_DAY = 21
LAST_FEEDING_DAY = 27
LAST_COLLECTION_DAY = 28

ANIMAL_PLANS = (
    {
        "animal": "GOOSE",
        "structure": "COOP",
        "position": (4, 4),
        "product": "EGG",
        "cost": 300,
        "max_held": 4,
    },
    {
        "animal": "COW",
        "structure": "PASTURE",
        "position": (3, 4),
        "product": "MILK",
        "cost": 400,
        "max_held": 6,
    },
)
LIVESTOCK_TILES = {
    plan["position"]
    for plan in ANIMAL_PLANS
}


def _distance(
    origin: tuple[int, int],
    target: tuple[int, int],
) -> int:
    return abs(origin[0] - target[0]) + abs(origin[1] - target[1])


def _animal_position(
    tiles: list[list[Any]],
    animal: str,
) -> tuple[int, int] | None:
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if isinstance(tile, dict) and tile.get("animal") == animal:
                return x, y
    return None


def _active_animals(
    farm: dict[str, Any],
) -> list[tuple[dict[str, Any], tuple[int, int], dict[str, Any]]]:
    active = []
    for plan in ANIMAL_PLANS:
        position = _animal_position(farm["tiles"], str(plan["animal"]))
        if position is None:
            continue
        tile = farm["tiles"][position[1]][position[0]]
        active.append((plan, position, tile))
    return active


def _nearest_animal(
    farmer: tuple[int, int],
    animals: list[tuple[dict[str, Any], tuple[int, int], dict[str, Any]]],
) -> tuple[dict[str, Any], tuple[int, int], dict[str, Any]]:
    return min(
        animals,
        key=lambda entry: (
            _distance(farmer, entry[1]),
            entry[1][1],
            entry[1][0],
        ),
    )


def _feed_due(day: int, tile: dict[str, Any]) -> bool:
    return (
        day <= LAST_FEEDING_DAY
        and not tile.get("fed_today", False)
        and int(tile.get("consecutive_unfed", 0)) >= 1
    )


def _feed_action(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
) -> list[str] | None:
    farmer = tuple(farm["farmer"])
    due = [
        animal
        for animal in _active_animals(farm)
        if _feed_due(day, animal[2])
    ]
    if not due:
        return None

    if _carried(private, "WHEAT") > 0:
        _, target, _ = _nearest_animal(farmer, due)
        return ["FEED"] if farmer == target else _move_toward(farmer, target)

    shed_wheat = int(private.get("shed", {}).get("WHEAT", 0))
    if shed_wheat <= 0:
        return None
    access_tiles = _shed_access_tiles(len(farm["tiles"]))
    if farmer in access_tiles:
        return ["PICKUP", "WHEAT", min(shed_wheat, len(due))]
    target = min(access_tiles, key=lambda position: _distance(farmer, position))
    return _move_toward(farmer, target)


def _setup_action(
    farm: dict[str, Any],
    private: dict[str, Any],
) -> list[str] | None:
    tiles = farm["tiles"]
    farmer = tuple(farm["farmer"])
    access_tiles = _shed_access_tiles(len(tiles))
    shed = private.get("shed", {})

    for plan in ANIMAL_PLANS:
        animal = str(plan["animal"])
        if _animal_position(tiles, animal) is not None:
            continue

        target = plan["position"]
        target_tile = tiles[target[1]][target[0]]
        structure_ready = (
            isinstance(target_tile, dict)
            and target_tile.get("kind") == plan["structure"]
            and "animal" not in target_tile
        )
        if not structure_ready:
            if isinstance(target_tile, dict) and "animal" in target_tile:
                continue
            if target_tile is None:
                action = [f"BUILD_{plan['structure']}"]
            else:
                action = ["DIG"]
            return action if farmer == target else _move_toward(farmer, target)

        if _carried(private, animal) > 0:
            return (
                ["PLACE", animal]
                if farmer == target
                else _move_toward(farmer, target)
            )
        if int(shed.get(animal, 0)) > 0:
            if farmer in access_tiles:
                return ["PICKUP", animal, 1]
            access = min(
                access_tiles,
                key=lambda position: _distance(farmer, position),
            )
            return _move_toward(farmer, access)

    return None


def _collection_action(
    day: int,
    farm: dict[str, Any],
) -> list[str] | None:
    farmer = tuple(farm["farmer"])
    active = _active_animals(farm)

    if day <= LAST_COLLECTION_DAY:
        fertilizer = [
            animal
            for animal in active
            if animal[2].get("fertilizer_available", False)
        ]
        if fertilizer:
            _, target, _ = _nearest_animal(farmer, fertilizer)
            return (
                ["COLLECT_FERTILIZER"]
                if farmer == target
                else _move_toward(farmer, target)
            )

    harvestable = [
        animal
        for animal in active
        if day <= LAST_COLLECTION_DAY
        and int(animal[2].get("yield_units", 0)) > 0
        and (
            day == LAST_COLLECTION_DAY
            or int(animal[2].get("yield_units", 0))
            >= int(animal[0]["max_held"])
        )
    ]
    if harvestable:
        _, target, _ = _nearest_animal(farmer, harvestable)
        return ["HARVEST"] if farmer == target else _move_toward(farmer, target)
    return None


def _livestock_market_orders(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
) -> list[list[Any]]:
    orders: list[list[Any]] = []
    shed = private.get("shed", {})
    money = float(farm["money"])

    if day == 0:
        for plan in ANIMAL_PLANS:
            animal = str(plan["animal"])
            present = _animal_position(farm["tiles"], animal) is not None
            in_transit = (
                int(shed.get(animal, 0)) > 0
                or _carried(private, animal) > 0
            )
            cost = int(plan["cost"])
            if not (present or in_transit) and money >= cost:
                orders.append(["BUY_ANIMAL", animal, 1])
                money -= cost

    feed_needed = sum(
        _feed_due(day, tile)
        for _, _, tile in _active_animals(farm)
    )
    available_feed = int(shed.get("WHEAT", 0)) + _carried(
        private,
        "WHEAT",
    )
    if feed_needed > available_feed:
        orders.append(
            ["BUY_PRODUCT", "WHEAT", feed_needed - available_feed]
        )

    for item in ("EGG", "MILK", "FERTILIZER"):
        quantity = int(shed.get(item, 0))
        if quantity > 0:
            orders.append(["SELL", item, quantity])
    return orders


def decide(
    observation: dict[str, Any],
    target_wheat_tiles: int = TARGET_WHEAT_TILES,
    target_daily_hands: int = 2,
) -> dict[str, Any]:
    """Run one goose, one cow, two daily hands, and a wheat workload."""
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    day = int(observation["day"])
    hour = int(observation["hour"])

    baseline = decide_wheat(
        observation,
        target_wheat_tiles=target_wheat_tiles,
        last_planting_day=LAST_WHEAT_PLANTING_DAY,
    )
    farmer_action = _feed_action(day, farm, private)
    if farmer_action is None:
        farmer_action = _setup_action(farm, private)
    if farmer_action is None:
        farmer_action = _collection_action(day, farm)
    farmer_action, hands_actions = _coordinated_crop_actions(
        day,
        farm,
        private,
        farmer_action,
        LIVESTOCK_TILES,
    )

    market = [
        *_hire_orders(hour, farm, target_daily_hands),
        *_livestock_market_orders(day, farm, private),
        *baseline["market"],
    ]
    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market,
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the isolated plain-cow candidate without land or animal care."""
    return decide(observation)