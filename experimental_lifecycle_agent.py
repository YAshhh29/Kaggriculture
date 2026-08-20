"""Deadline-aware farming with stable animal and crop crew ownership."""

from __future__ import annotations

from collections import Counter
from typing import Any

from experimental_hands_agent import (
    _act_at_or_move,
    _distance,
    _is_mature_wheat,
    _is_wheat,
)
from experimental_investment_agent import (
    _investment_market_orders,
)
from experimental_scale_agent import (
    LAST_WHEAT_PLANTING_DAY,
    _assign_animal_services,
    _assign_setup,
    _assign_urgent_feeding,
    _feed_due,
    _inventories,
    _land_orders,
    _plan_is_active,
    _protect_feed_reserve,
    _staged_animal_plans,
    _tile_at,
    _unlocked_animal_plans,
)
from experimental_zoned_agent import _unlocked, _zoned_hire_orders
from main import decide as decide_wheat


ANIMAL_CREW_SIZE = 7
CROP_PAIR_COUNT = 3
MAX_WHEAT_PER_PAIR = 6
MAX_ASSIST_DISTANCE = 2
TARGET_DAILY_HANDS = 12
TARGET_COWS = 6
TARGET_SHEEP = 8
TARGET_EXTRA_LAND = 1
WHEAT_DEMAND_SHOPS = {
    "BAKERY",
    "BRUNCH_SPOT",
    "FARMERS_MARKET",
    "ICE_CREAM_SHOP",
    "PIZZA_SHOP",
}


def _pair_owner(position: tuple[int, int], pair_count: int) -> int:
    x, _ = position
    return min(pair_count - 1, x * pair_count // 10)


def _effective_pair_count(
    target_daily_hands: int,
    animal_crew_size: int,
) -> int:
    total_workers = 1 + target_daily_hands
    crop_workers = max(0, total_workers - animal_crew_size)
    return min(CROP_PAIR_COUNT, crop_workers // 2)


def _plant_priority(
    position: tuple[int, int],
    pair: int,
    pair_count: int,
) -> tuple[int, int, int]:
    center_x = min(9, (2 * pair + 1) * 10 // (2 * pair_count))
    return (
        _distance(position, (center_x, 4)),
        abs(position[1] - 4),
        position[0],
    )


def _demand_capacity(observation: dict[str, Any]) -> int:
    shops = observation.get("town", {}).get("unlocked_shops", [])
    wheat_shops = sum(shop in WHEAT_DEMAND_SHOPS for shop in shops)
    wheat_price = int(
        observation.get("market", {}).get("prices", {}).get("WHEAT", 0)
    )
    return 6 if wheat_shops >= 2 or wheat_price >= 35 else 5


def _daily_hand_target(day: int, maximum_hands: int) -> int:
    if day >= 29:
        return 0
    if day == 28:
        return min(maximum_hands, 5)
    if day >= 26:
        return min(maximum_hands, 8)
    if day == 25:
        return min(maximum_hands, 10)
    return maximum_hands


def _crop_task_groups(
    day: int,
    farm: dict[str, Any],
    livestock_tiles: set[tuple[int, int]],
    *,
    pair: int,
    pair_count: int,
    max_wheat_per_pair: int = MAX_WHEAT_PER_PAIR,
) -> dict[str, list[tuple[int, int]]]:
    groups: dict[str, list[tuple[int, int]]] = {
        "urgent_water": [],
        "deadline_harvest": [],
        "harvest": [],
        "yield_water": [],
        "plant": [],
    }
    active_wheat = 0
    ages: dict[tuple[int, int], int] = {}

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            position = (x, y)
            if (
                position in livestock_tiles
                or not _unlocked(position, farm)
                or _pair_owner(position, pair_count) != pair
            ):
                continue
            if _is_wheat(tile):
                active_wheat += 1
                age = day - int(tile["planted_day"])
                ages[position] = age
                if _is_mature_wheat(tile, day) and age >= 5:
                    groups["deadline_harvest"].append(position)
                elif not tile.get("watered_today", False):
                    if int(tile.get("consecutive_unwatered", 0)) >= 1:
                        groups["urgent_water"].append(position)
                    elif 2 <= age <= 4:
                        groups["yield_water"].append(position)
                elif _is_mature_wheat(tile, day):
                    groups["harvest"].append(position)
            elif tile is None:
                groups["plant"].append(position)

    task_key = lambda position: (
        _plant_priority(position, pair, pair_count),
        position[1],
        position[0],
    )
    groups["urgent_water"].sort(
        key=lambda position: (-ages[position], task_key(position))
    )
    groups["deadline_harvest"].sort(
        key=lambda position: (-ages[position], task_key(position))
    )
    groups["harvest"].sort(
        key=lambda position: (-ages[position], task_key(position))
    )
    groups["yield_water"].sort(
        key=lambda position: (-ages[position], task_key(position))
    )
    groups["plant"].sort(key=task_key)
    if active_wheat >= max_wheat_per_pair or day > LAST_WHEAT_PLANTING_DAY:
        groups["plant"] = []
    return groups


def _assign_tasks(
    workers: list[int],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    targets: list[tuple[int, int]],
    operation: list[str],
    reserved: set[tuple[int, int]],
) -> None:
    for worker in workers:
        if actions[worker] is not None:
            continue
        available = [target for target in targets if target not in reserved]
        if not available:
            return
        target = min(
            available,
            key=lambda candidate: (
                _distance(positions[worker], candidate),
                candidate[1],
                candidate[0],
            ),
        )
        reserved.add(target)
        actions[worker] = _act_at_or_move(
            positions[worker],
            target,
            operation,
        )


def _assign_lifecycle_crops(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    livestock_tiles: set[tuple[int, int]],
    *,
    animal_crew_size: int,
    max_wheat_per_pair: int,
) -> None:
    crop_workers = list(range(animal_crew_size, len(positions)))
    pair_count = min(CROP_PAIR_COUNT, len(crop_workers) // 2)
    if pair_count <= 0:
        return
    reserved: set[tuple[int, int]] = set()
    pair_groups = [
        _crop_task_groups(
            day,
            farm,
            livestock_tiles,
            pair=pair,
            pair_count=pair_count,
            max_wheat_per_pair=max_wheat_per_pair,
        )
        for pair in range(pair_count)
    ]
    operation_by_group = {
        "urgent_water": ["WATER"],
        "deadline_harvest": ["HARVEST"],
        "harvest": ["HARVEST"],
        "yield_water": ["WATER"],
    }

    for pair, groups in enumerate(pair_groups):
        workers = crop_workers[2 * pair:2 * pair + 2]
        for group_name in (
            "urgent_water",
            "deadline_harvest",
            "harvest",
            "yield_water",
        ):
            _assign_tasks(
                workers,
                positions,
                actions,
                groups[group_name],
                operation_by_group[group_name],
                reserved,
            )

    urgent_targets = [
        target
        for groups in pair_groups
        for target in groups["urgent_water"]
        if target not in reserved
    ]
    for worker, action in enumerate(actions):
        if action is not None:
            continue
        nearby = [
            target
            for target in urgent_targets
            if target not in reserved
            and _distance(positions[worker], target) <= MAX_ASSIST_DISTANCE
        ]
        if not nearby:
            continue
        target = min(
            nearby,
            key=lambda candidate: (
                _distance(positions[worker], candidate),
                candidate[1],
                candidate[0],
            ),
        )
        reserved.add(target)
        actions[worker] = _act_at_or_move(
            positions[worker],
            target,
            ["WATER"],
        )

    seed_budget = int(private.get("seeds", {}).get("WHEAT", 0))
    for pair, groups in enumerate(pair_groups):
        workers = crop_workers[2 * pair:2 * pair + 2]
        if (
            len(workers) < 2
            or any(actions[worker] is not None for worker in workers)
        ):
            continue
        candidates = [
            target for target in groups["plant"] if target not in reserved
        ]
        if seed_budget <= 0:
            continue
        if not candidates:
            continue
        target = min(
            candidates,
            key=lambda candidate: (
                max(
                    _distance(positions[workers[0]], candidate),
                    _distance(positions[workers[1]], candidate),
                ),
                sum(
                    _distance(positions[worker], candidate)
                    for worker in workers
                ),
                candidate[1],
                candidate[0],
            ),
        )
        reserved.add(target)
        if all(positions[worker] == target for worker in workers):
            actions[workers[0]] = ["PLANT", "WHEAT"]
            actions[workers[1]] = ["WATER"]
            seed_budget -= 1
        else:
            for worker in workers:
                actions[worker] = (
                    ["PASS"]
                    if positions[worker] == target
                    else _act_at_or_move(
                        positions[worker],
                        target,
                        ["PASS"],
                    )
                )


def _assign_idle_current_animal_services(
    animal_plans: tuple[dict[str, Any], ...],
    day: int,
    farm: dict[str, Any],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    *,
    first_assistant: int,
) -> None:
    reserved: set[str] = set()
    for worker in range(first_assistant, len(positions)):
        if actions[worker] is not None:
            continue
        candidates: list[tuple[int, int, dict[str, Any], list[str]]] = []
        for order, plan in enumerate(animal_plans):
            if str(plan["id"]) in reserved or not _plan_is_active(
                plan,
                farm["tiles"],
            ):
                continue
            distance = _distance(positions[worker], plan["position"])
            if distance > MAX_ASSIST_DISTANCE:
                continue
            tile = _tile_at(farm["tiles"], plan["position"])
            operation = None
            priority = 99
            if tile.get("fertilizer_available", False) and day <= 28:
                operation = ["COLLECT_FERTILIZER"]
                priority = 0
            elif int(tile.get("yield_units", 0)) >= int(plan["max_held"]):
                operation = ["HARVEST"]
                priority = 1
            elif (
                day <= 27
                and tile.get("fed_today", False)
                and not tile.get("cared_today", False)
            ):
                operation = ["CARE"]
                priority = 2
            if operation is not None:
                candidates.append((priority, distance, plan, operation))
        if not candidates:
            continue
        _, _, plan, operation = min(
            candidates,
            key=lambda candidate: (
                candidate[0],
                candidate[1],
                candidate[2]["position"][1],
                candidate[2]["position"][0],
            ),
        )
        reserved.add(str(plan["id"]))
        actions[worker] = _act_at_or_move(
            positions[worker],
            plan["position"],
            operation,
        )


def _lifecycle_worker_actions(
    animal_plans: tuple[dict[str, Any], ...],
    livestock_tiles: set[tuple[int, int]],
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    max_wheat_per_pair: int,
    animal_crew_size: int,
) -> tuple[list[str], list[list[str]]]:
    positions = [
        tuple(farm["farmer"]),
        *(tuple(position) for position in farm.get("hands", [])),
    ]
    inventories = _inventories(private, len(positions))
    actions: list[list[str] | None] = [None for _ in positions]
    tiles = farm["tiles"]
    emergency_plans = tuple(
        plan
        for plan in animal_plans
        if _plan_is_active(plan, tiles)
        and _feed_due(day, _tile_at(tiles, plan["position"]), False)
    )
    emergency_ids = {str(plan["id"]) for plan in emergency_plans}
    _assign_urgent_feeding(
        emergency_plans,
        day,
        farm,
        private,
        positions,
        inventories,
        actions,
        False,
    )

    crew_count = min(animal_crew_size, len(positions))
    crew_positions = positions[:crew_count]
    crew_inventories = inventories[:crew_count]
    crew_actions = actions[:crew_count]
    normal_plans = tuple(
        plan
        for plan in animal_plans
        if str(plan["id"]) not in emergency_ids
    )
    _assign_urgent_feeding(
        normal_plans,
        day,
        farm,
        private,
        crew_positions,
        crew_inventories,
        crew_actions,
        True,
    )
    _assign_setup(
        animal_plans,
        farm,
        private,
        crew_positions,
        crew_inventories,
        crew_actions,
    )
    _assign_animal_services(
        animal_plans,
        day,
        farm,
        crew_positions,
        crew_actions,
        True,
    )
    actions[:crew_count] = crew_actions

    _assign_lifecycle_crops(
        day,
        farm,
        private,
        positions,
        actions,
        livestock_tiles,
        animal_crew_size=animal_crew_size,
        max_wheat_per_pair=max_wheat_per_pair,
    )
    _assign_idle_current_animal_services(
        animal_plans,
        day,
        farm,
        positions,
        actions,
        first_assistant=crew_count,
    )
    resolved = [action or ["PASS"] for action in actions]
    return resolved[0], resolved[1:]


def _lifecycle_livestock_orders(
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
        _feed_due(day, _tile_at(tiles, plan["position"]), True)
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


def decide(
    observation: dict[str, Any],
    max_wheat_per_pair: int = MAX_WHEAT_PER_PAIR,
    target_daily_hands: int = TARGET_DAILY_HANDS,
    target_extra_land: int = TARGET_EXTRA_LAND,
    target_cows: int = TARGET_COWS,
    target_sheep: int = TARGET_SHEEP,
    animal_crew_size: int = ANIMAL_CREW_SIZE,
) -> dict[str, Any]:
    """Run stable crews with crop lifecycle admission control."""
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    day = int(observation["day"])
    hour = int(observation["hour"])
    target_wheat_tiles = max(
        0,
        _effective_pair_count(
            target_daily_hands,
            animal_crew_size,
        )
        * max_wheat_per_pair,
    )
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
    farmer_action, hands_actions = _lifecycle_worker_actions(
        active_plans,
        {plan["position"] for plan in desired_plans},
        day,
        farm,
        private,
        max_wheat_per_pair,
        animal_crew_size,
    )
    urgent, sales = _lifecycle_livestock_orders(
        active_plans,
        day,
        farm,
        private,
    )
    market = _investment_market_orders(
        sales,
        urgent,
        _land_orders(day, hour, farm, target_extra_land),
        _zoned_hire_orders(
            farm,
            _daily_hand_target(day, target_daily_hands),
        ),
        baseline_market,
    )
    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market,
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the lifecycle-managed NE research candidate."""
    return decide(observation)