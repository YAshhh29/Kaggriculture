"""Center-out, diversified farming challenger."""

from __future__ import annotations

from collections import Counter
from typing import Any

from experimental_hands_agent import _act_at_or_move, _distance
from experimental_investment_agent import _investment_market_orders
from experimental_lifecycle_agent import _assign_idle_current_animal_services
from experimental_scale_agent import (
    _assign_animal_services,
    _assign_nearest,
    _assign_urgent_feeding,
    _feed_due,
    _inventories,
    _plan_is_active,
    _shed_access_tiles,
    _tile_at,
)
from experimental_zoned_agent import _unlocked, _zoned_hire_orders


BOARD_SIZE = 10
LAND_SEQUENCE = ("NW", "NE", "SW")
MAX_STRAWBERRIES = 4
MAX_MELONS = 2
MAX_CROP_SLOTS_PER_QUADRANT = 6
ANIMAL_CREW_SIZE = 6
TARGET_DAILY_HANDS = 12
TARGET_EXTRA_LAND = 2
MAX_MARKET_ORDERS = 10
FERTILIZER_RESERVE_PER_STRAWBERRY = 2

CROP_DATA = {
    "WHEAT": {
        "seed_cost": 10,
        "first_yield": 2,
        "harvest_age": 4,
        "last_plant_day": 22,
        "productive_ages": {2, 3, 4},
        "ongoing": False,
    },
    "CARROT": {
        "seed_cost": 20,
        "first_yield": 2,
        "harvest_age": 3,
        "last_plant_day": 22,
        "productive_ages": {2, 3},
        "ongoing": False,
    },
    "TOMATO": {
        "seed_cost": 50,
        "first_yield": 8,
        "harvest_age": 11,
        "last_plant_day": 17,
        "productive_ages": {7, 8, 9, 10},
        "spent_age": 12,
        "ongoing": True,
    },
    "STRAWBERRY": {
        "seed_cost": 100,
        "first_yield": 10,
        "harvest_age": 16,
        "last_plant_day": 12,
        "productive_ages": {9, 11, 13, 15},
        "spent_age": 17,
        "ongoing": True,
    },
    "MELON": {
        "seed_cost": 80,
        "first_yield": 10,
        "harvest_age": 10,
        "last_plant_day": 18,
        "productive_ages": {6, 7, 8, 9, 10},
        "ongoing": False,
    },
}

ANIMAL_DATA = {
    "GOOSE": {
        "structure": "COOP",
        "product": "EGG",
        "cost": 300,
        "max_held": 4,
    },
    "COW": {
        "structure": "PASTURE",
        "product": "MILK",
        "cost": 400,
        "max_held": 6,
    },
    "SHEEP": {
        "structure": "PASTURE",
        "product": "WOOL",
        "cost": 500,
        "max_held": 6,
    },
}

CORE_ANIMAL_BLOCKS = {
    "NW": (34, 35, 44, 45),
    "NE": (36, 37, 46, 47),
    "SW": (54, 55, 64, 65),
}

CENTER_OUT_BLOCKS = {
    "NW": (
        25, 24, 23, 33, 43,
        15, 14, 13, 12, 22, 32, 42,
        5, 4, 3, 2, 1, 11, 21, 31, 41,
    ),
    "NE": (
        26, 27, 28, 38, 48,
        16, 17, 18, 19, 29, 39, 49,
        6, 7, 8, 9, 10, 20, 30, 40, 50,
    ),
    "SW": (
        53, 63, 73, 74, 75,
        52, 62, 72, 82, 83, 84, 85,
        51, 61, 71, 81, 91, 92, 93, 94, 95,
    ),
}

ANIMAL_BLOCK_LAYOUT = {
    "NW": ((45, "COW"), (44, "COW"), (35, "SHEEP"), (34, "SHEEP")),
    "NE": ((46, "COW"), (47, "COW"), (36, "SHEEP"), (37, "SHEEP")),
    "SW": ((55, "COW"), (65, "COW"), (54, "SHEEP"), (64, "SHEEP")),
}

CROP_BLOCK_LAYOUT = {
    "NW": (
        (25, "WHEAT"), (24, "WHEAT"), (43, "CARROT"),
        (15, "TOMATO"), (14, "STRAWBERRY"), (13, "MELON"),
    ),
    "NE": (
        (26, "WHEAT"), (27, "WHEAT"), (48, "CARROT"),
        (16, "TOMATO"), (17, "STRAWBERRY"), (18, "MELON"),
    ),
    "SW": (
        (53, "STRAWBERRY"), (63, "STRAWBERRY"),
        (73, "WHEAT"), (74, "WHEAT"),
        (75, "CARROT"), (52, "TOMATO"),
    ),
}


def block_to_position(block: int) -> tuple[int, int]:
    """Convert a one-based row-major block number into an (x, y) tile."""
    if not 1 <= block <= BOARD_SIZE * BOARD_SIZE:
        raise ValueError(f"Block must be between 1 and 100: {block}")
    index = block - 1
    return index % BOARD_SIZE, index // BOARD_SIZE


def _animal_plan(
    quadrant: str,
    block: int,
    animal: str,
    index: int,
) -> dict[str, Any]:
    data = ANIMAL_DATA[animal]
    return {
        "id": f"{quadrant.lower()}_{animal.lower()}_{index}",
        "quadrant": quadrant,
        "block": block,
        "position": block_to_position(block),
        "animal": animal,
        **data,
    }


ANIMAL_PLANS = tuple(
    _animal_plan(quadrant, block, animal, index)
    for quadrant in LAND_SEQUENCE
    for index, (block, animal) in enumerate(
        ANIMAL_BLOCK_LAYOUT[quadrant],
        start=1,
    )
)

CROP_PLANS = tuple(
    {
        "id": f"{quadrant.lower()}_{crop.lower()}_{index}",
        "quadrant": quadrant,
        "block": block,
        "position": block_to_position(block),
        "crop": crop,
    }
    for quadrant in LAND_SEQUENCE
    for index, (block, crop) in enumerate(
        CROP_BLOCK_LAYOUT[quadrant],
        start=1,
    )
)


def _active_plans(
    plans: tuple[dict[str, Any], ...],
    farm: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    unlocked = set(farm.get("unlocked_quadrants", []))
    return tuple(plan for plan in plans if plan["quadrant"] in unlocked)


def _is_crop(tile: Any, crop: str | None = None) -> bool:
    return (
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and (crop is None or tile.get("crop") == crop)
    )


def _managed_crop_plans(
    farm: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    unlocked = set(farm.get("unlocked_quadrants", []))
    return tuple(
        plan
        for quadrant in LAND_SEQUENCE
        if quadrant in unlocked
        for plan in tuple(
            candidate
            for candidate in CROP_PLANS
            if candidate["quadrant"] == quadrant
        )[:MAX_CROP_SLOTS_PER_QUADRANT]
    )


def _crop_operations(day: int, tile: dict[str, Any]) -> set[str]:
    if not _is_crop(tile):
        return set()
    crop = str(tile["crop"])
    data = CROP_DATA[crop]
    age = day - int(tile["planted_day"])
    operations: set[str] = set()
    productive = age in data["productive_ages"]

    if data["ongoing"] and age >= int(data["spent_age"]):
        return {"HARVEST"} if int(tile.get("yield_units", 0)) > 0 else {"DIG"}
    if (
        not data["ongoing"]
        and age > int(data["harvest_age"])
        and int(tile.get("yield_units", 0)) > 0
    ):
        return {"HARVEST"}

    if not tile.get("watered_today", False) and (
        int(tile.get("consecutive_unwatered", 0)) >= 1 or productive
    ):
        operations.add("WATER")

    if data["ongoing"]:
        if int(tile.get("yield_units", 0)) > 0:
            operations.add("HARVEST")
        if (
            crop == "STRAWBERRY"
            and productive
            and int(tile.get("fertilized_until_day", -1)) < day
        ):
            operations.add("FERTILIZE")
    elif (
        age >= int(data["harvest_age"])
        and int(tile.get("yield_units", 0)) > 0
        and not (
            productive and not tile.get("watered_today", False)
        )
    ):
        operations.add("HARVEST")

    return operations


def _crop_task_groups(
    day: int,
    farm: dict[str, Any],
    plans: tuple[dict[str, Any], ...],
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        "urgent_water": [],
        "deadline_harvest": [],
        "harvest": [],
        "dig": [],
        "fertilize_water": [],
        "productive_water": [],
        "plant": [],
    }
    active_one_time = sum(
        _is_crop(
            _tile_at(farm["tiles"], plan["position"]),
            str(plan["crop"]),
        )
        and not CROP_DATA[str(plan["crop"])]["ongoing"]
        for plan in plans
    )
    for plan in plans:
        position = tuple(plan["position"])
        tile = _tile_at(farm["tiles"], position)
        crop = str(plan["crop"])
        data = CROP_DATA[crop]
        if tile is None:
            capacity_open = not (
                plan["quadrant"] == "NW"
                and crop in {"WHEAT", "CARROT"}
                and active_one_time >= 2
            ) and not (
                crop == "CARROT"
                and active_one_time >= 3
            )
            if day <= int(data["last_plant_day"]) and capacity_open:
                groups["plant"].append(plan)
            continue
        if not _is_crop(tile, crop):
            groups["dig"].append(plan)
            continue

        operations = _crop_operations(day, tile)
        age = day - int(tile["planted_day"])
        if "WATER" in operations and int(
            tile.get("consecutive_unwatered", 0)
        ) >= 1:
            groups["urgent_water"].append(plan)
        if "HARVEST" in operations:
            target_age = int(data["harvest_age"])
            group = "deadline_harvest" if age > target_age else "harvest"
            groups[group].append(plan)
        if "DIG" in operations:
            groups["dig"].append(plan)
        if "FERTILIZE" in operations and "WATER" in operations:
            groups["fertilize_water"].append(plan)
            if plan in groups["urgent_water"]:
                groups["urgent_water"].remove(plan)
        elif (
            "WATER" in operations
            and plan not in groups["urgent_water"]
        ):
            groups["productive_water"].append(plan)
    return groups


def _assign_group(
    workers: list[int],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    plans: list[dict[str, Any]],
    operation: list[str],
    reserved: set[tuple[int, int]],
) -> None:
    for worker in workers:
        if actions[worker] is not None:
            continue
        available = [
            plan
            for plan in plans
            if tuple(plan["position"]) not in reserved
        ]
        if not available:
            return
        plan = min(
            available,
            key=lambda candidate: (
                _distance(positions[worker], candidate["position"]),
                candidate["block"],
            ),
        )
        target = tuple(plan["position"])
        reserved.add(target)
        actions[worker] = _act_at_or_move(
            positions[worker],
            target,
            operation,
        )


def _assign_fertilized_strawberry(
    workers: list[int],
    plan: dict[str, Any],
    farm: dict[str, Any],
    private: dict[str, Any],
    positions: list[tuple[int, int]],
    inventories: list[dict[str, Any]],
    actions: list[list[str] | None],
) -> bool:
    if len(workers) < 2 or any(actions[worker] is not None for worker in workers):
        return False
    target = tuple(plan["position"])
    fertilizer_workers = [
        worker
        for worker in workers
        if int(inventories[worker].get("FERTILIZER", 0)) > 0
    ]
    if fertilizer_workers:
        fertilizer_worker = fertilizer_workers[0]
        water_worker = next(
            worker for worker in workers if worker != fertilizer_worker
        )
        if all(positions[worker] == target for worker in workers):
            actions[fertilizer_worker] = ["FERTILIZE"]
            actions[water_worker] = ["WATER"]
        else:
            for worker in workers:
                actions[worker] = _act_at_or_move(
                    positions[worker],
                    target,
                    ["PASS"],
                )
        return True

    if int(private.get("shed", {}).get("FERTILIZER", 0)) > 0:
        access_tiles = _shed_access_tiles(len(farm["tiles"]))
        pickup_worker = min(
            workers,
            key=lambda worker: min(
                _distance(positions[worker], access)
                for access in access_tiles
            ),
        )
        route_worker = next(
            worker for worker in workers if worker != pickup_worker
        )
        access = min(
            access_tiles,
            key=lambda candidate: _distance(
                positions[pickup_worker], candidate
            ),
        )
        actions[pickup_worker] = _act_at_or_move(
            positions[pickup_worker],
            access,
            ["PICKUP", "FERTILIZER", 1],
        )
        actions[route_worker] = _act_at_or_move(
            positions[route_worker],
            target,
            ["PASS"],
        )
        return True

    water_worker = min(
        workers,
        key=lambda worker: _distance(positions[worker], target),
    )
    actions[water_worker] = _act_at_or_move(
        positions[water_worker],
        target,
        ["WATER"],
    )
    return True


def _assign_dual_crop_operation(
    workers: list[int],
    plan: dict[str, Any],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    first: list[str],
    second: list[str],
) -> bool:
    if len(workers) < 2 or any(actions[worker] is not None for worker in workers):
        return False
    target = tuple(plan["position"])
    if all(positions[worker] == target for worker in workers):
        actions[workers[0]] = first
        actions[workers[1]] = second
    else:
        for worker in workers:
            actions[worker] = _act_at_or_move(
                positions[worker], target, ["PASS"]
            )
    return True


def _assign_center_out_crops(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    positions: list[tuple[int, int]],
    inventories: list[dict[str, Any]],
    actions: list[list[str] | None],
    *,
    animal_crew_size: int,
) -> None:
    crop_workers = list(range(animal_crew_size, len(positions)))
    pair_count = min(len(LAND_SEQUENCE), len(crop_workers) // 2)
    reserved: set[tuple[int, int]] = set()
    seed_budget = Counter(private.get("seeds", {}))

    for pair in range(pair_count):
        quadrant = LAND_SEQUENCE[pair]
        if quadrant not in farm.get("unlocked_quadrants", []):
            continue
        workers = crop_workers[2 * pair:2 * pair + 2]
        plans = tuple(
            plan
            for plan in _managed_crop_plans(farm)
            if plan["quadrant"] == quadrant
        )
        groups = _crop_task_groups(day, farm, plans)

        for group_name, operation in (
            ("deadline_harvest", ["HARVEST"]),
            ("dig", ["DIG"]),
        ):
            _assign_group(
                workers,
                positions,
                actions,
                groups[group_name],
                operation,
                reserved,
            )

        tomato_dual = [
            plan
            for plan in groups["harvest"]
            if (
                plan["crop"] == "TOMATO"
                and plan in groups["urgent_water"]
                and tuple(plan["position"]) not in reserved
            )
        ]
        if tomato_dual and _assign_dual_crop_operation(
            workers,
            tomato_dual[0],
            positions,
            actions,
            ["WATER"],
            ["HARVEST"],
        ):
            reserved.add(tuple(tomato_dual[0]["position"]))

        for group_name, operation in (
            ("urgent_water", ["WATER"]),
            ("harvest", ["HARVEST"]),
        ):
            _assign_group(
                workers,
                positions,
                actions,
                groups[group_name],
                operation,
                reserved,
            )

        combos = [
            plan
            for plan in groups["fertilize_water"]
            if tuple(plan["position"]) not in reserved
        ]
        if combos and _assign_fertilized_strawberry(
            workers,
            combos[0],
            farm,
            private,
            positions,
            inventories,
            actions,
        ):
            reserved.add(tuple(combos[0]["position"]))

        _assign_group(
            workers,
            positions,
            actions,
            groups["productive_water"],
            ["WATER"],
            reserved,
        )

        if len(workers) < 2 or any(
            actions[worker] is not None for worker in workers
        ):
            continue
        candidates = [
            plan
            for plan in groups["plant"]
            if seed_budget[str(plan["crop"])] > 0
            and tuple(plan["position"]) not in reserved
        ]
        if not candidates:
            continue
        plan = candidates[0]
        target = tuple(plan["position"])
        reserved.add(target)
        if all(positions[worker] == target for worker in workers):
            actions[workers[0]] = ["PLANT", str(plan["crop"])]
            actions[workers[1]] = ["WATER"]
            seed_budget[str(plan["crop"])] -= 1
        else:
            for worker in workers:
                actions[worker] = _act_at_or_move(
                    positions[worker],
                    target,
                    ["PASS"],
                )

    urgent_targets = [
        tuple(plan["position"])
        for plan in _managed_crop_plans(farm)
        if (
            _is_crop(_tile_at(farm["tiles"], plan["position"]))
            and not _tile_at(
                farm["tiles"], plan["position"]
            ).get("watered_today", False)
            and int(
                _tile_at(
                    farm["tiles"], plan["position"]
                ).get("consecutive_unwatered", 0)
            ) >= 1
        )
    ]
    for worker, action in enumerate(actions):
        if action is not None:
            continue
        nearby = [
            target
            for target in urgent_targets
            if target not in reserved
            and _distance(positions[worker], target) <= 2
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
            positions[worker], target, ["WATER"]
        )


def _assign_global_crop_deadlines(
    day: int,
    farm: dict[str, Any],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
) -> None:
    tasks: list[tuple[int, tuple[int, int], list[str]]] = []
    for plan in _managed_crop_plans(farm):
        position = tuple(plan["position"])
        tile = _tile_at(farm["tiles"], position)
        if not _is_crop(tile, str(plan["crop"])):
            continue
        operations = _crop_operations(day, tile)
        crop = str(plan["crop"])
        age = day - int(tile["planted_day"])
        if "HARVEST" in operations and (
            not CROP_DATA[crop]["ongoing"]
            and age > int(CROP_DATA[crop]["harvest_age"])
        ):
            tasks.append((0, position, ["HARVEST"]))
        elif "DIG" in operations:
            tasks.append((1, position, ["DIG"]))
        elif (
            "WATER" in operations
            and int(tile.get("consecutive_unwatered", 0)) >= 1
            and "FERTILIZE" not in operations
        ):
            tasks.append((2, position, ["WATER"]))

    reserved: set[tuple[int, int]] = set()
    for worker, action in enumerate(actions):
        if action is not None:
            continue
        available = [task for task in tasks if task[1] not in reserved]
        if not available:
            return
        _, target, operation = min(
            available,
            key=lambda task: (
                task[0],
                _distance(positions[worker], task[1]),
                task[1][1],
                task[1][0],
            ),
        )
        reserved.add(target)
        actions[worker] = _act_at_or_move(
            positions[worker], target, operation
        )


def _assign_generic_setup(
    animal_plans: tuple[dict[str, Any], ...],
    farm: dict[str, Any],
    private: dict[str, Any],
    positions: list[tuple[int, int]],
    inventories: list[dict[str, Any]],
    actions: list[list[str] | None],
) -> None:
    tiles = farm["tiles"]
    reserved: set[str] = set()

    for worker, inventory in enumerate(inventories):
        if actions[worker] is not None:
            continue
        for animal in ANIMAL_DATA:
            if int(inventory.get(animal, 0)) <= 0:
                continue
            plan = next(
                (
                    candidate
                    for candidate in animal_plans
                    if candidate["animal"] == animal
                    and candidate["id"] not in reserved
                    and not _plan_is_active(candidate, tiles)
                    and isinstance(
                        _tile_at(tiles, candidate["position"]), dict
                    )
                    and _tile_at(
                        tiles, candidate["position"]
                    ).get("kind") == candidate["structure"]
                    and "animal" not in _tile_at(
                        tiles, candidate["position"]
                    )
                ),
                None,
            )
            if plan is None:
                continue
            actions[worker] = _act_at_or_move(
                positions[worker],
                plan["position"],
                ["PLACE", animal],
            )
            reserved.add(str(plan["id"]))
            break

    for plan in animal_plans:
        if _plan_is_active(plan, tiles) or plan["id"] in reserved:
            continue
        tile = _tile_at(tiles, plan["position"])
        structure_ready = (
            isinstance(tile, dict)
            and tile.get("kind") == plan["structure"]
            and "animal" not in tile
        )
        if structure_ready:
            continue
        operation = (
            [f"BUILD_{plan['structure']}"] if tile is None else ["DIG"]
        )
        if _assign_nearest(
            positions,
            actions,
            plan["position"],
            operation,
        ) is not None:
            reserved.add(str(plan["id"]))

    virtual_shed = Counter(private.get("shed", {}))
    for inventory in inventories:
        for animal in ANIMAL_DATA:
            virtual_shed[animal] -= int(inventory.get(animal, 0))
    access_tiles = _shed_access_tiles(len(tiles))
    for plan in animal_plans:
        if _plan_is_active(plan, tiles) or plan["id"] in reserved:
            continue
        tile = _tile_at(tiles, plan["position"])
        if not (
            isinstance(tile, dict)
            and tile.get("kind") == plan["structure"]
            and "animal" not in tile
            and virtual_shed[str(plan["animal"])] > 0
        ):
            continue
        available = [
            worker
            for worker, action in enumerate(actions)
            if action is None
        ]
        if not available:
            break
        worker = min(
            available,
            key=lambda index: min(
                _distance(positions[index], access)
                for access in access_tiles
            ),
        )
        access = min(
            access_tiles,
            key=lambda candidate: _distance(
                positions[worker], candidate
            ),
        )
        actions[worker] = _act_at_or_move(
            positions[worker],
            access,
            ["PICKUP", str(plan["animal"]), 1],
        )
        virtual_shed[str(plan["animal"])] -= 1
        reserved.add(str(plan["id"]))


def _worker_actions(
    animal_plans: tuple[dict[str, Any], ...],
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
) -> tuple[list[str], list[list[str]]]:
    positions = [
        tuple(farm["farmer"]),
        *(tuple(position) for position in farm.get("hands", [])),
    ]
    inventories = _inventories(private, len(positions))
    actions: list[list[str] | None] = [None for _ in positions]
    tiles = farm["tiles"]
    emergency = tuple(
        plan
        for plan in animal_plans
        if _plan_is_active(plan, tiles)
        and _feed_due(day, _tile_at(tiles, plan["position"]), False)
    )
    emergency_ids = {str(plan["id"]) for plan in emergency}
    _assign_urgent_feeding(
        emergency,
        day,
        farm,
        private,
        positions,
        inventories,
        actions,
        False,
    )
    crew_count = min(ANIMAL_CREW_SIZE, len(positions))
    crew_positions = positions[:crew_count]
    crew_inventories = inventories[:crew_count]
    crew_actions = actions[:crew_count]
    normal = tuple(
        plan
        for plan in animal_plans
        if str(plan["id"]) not in emergency_ids
    )
    _assign_urgent_feeding(
        normal,
        day,
        farm,
        private,
        crew_positions,
        crew_inventories,
        crew_actions,
        True,
    )
    _assign_generic_setup(
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

    _assign_global_crop_deadlines(
        day,
        farm,
        positions,
        actions,
    )

    _assign_center_out_crops(
        day,
        farm,
        private,
        positions,
        inventories,
        actions,
        animal_crew_size=ANIMAL_CREW_SIZE,
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


def _daily_hand_target(
    day: int,
    farm: dict[str, Any],
    maximum_hands: int,
) -> int:
    if day >= 29:
        return min(maximum_hands, 4)
    return min(maximum_hands, 11)


def _land_orders(
    day: int,
    farm: dict[str, Any],
    target_extra_land: int,
) -> list[list[str]]:
    unlocked_extra = max(0, len(farm.get("unlocked_quadrants", [])) - 1)
    if unlocked_extra >= min(target_extra_land, 2) or day > 20:
        return []
    earliest = (6, 11)
    costs = (1000, 2000)
    reserves = (1200, 2200)
    if day < earliest[unlocked_extra]:
        return []
    if float(farm["money"]) < costs[unlocked_extra] + reserves[unlocked_extra]:
        return []
    return [["BUY_LAND"]]


def _livestock_orders(
    animal_plans: tuple[dict[str, Any], ...],
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
) -> list[list[Any]]:
    tiles = farm["tiles"]
    shed = private.get("shed", {})
    carried = Counter()
    for inventory in private.get("inventories", []):
        if isinstance(inventory, dict):
            carried.update(inventory)
    orders: list[list[Any]] = []
    if day <= 20:
        desired = Counter(str(plan["animal"]) for plan in animal_plans)
        present = Counter(
            str(plan["animal"])
            for plan in animal_plans
            if _plan_is_active(plan, tiles)
        )
        for animal in ANIMAL_DATA:
            missing = max(
                0,
                desired[animal]
                - present[animal]
                - int(shed.get(animal, 0))
                - int(carried.get(animal, 0)),
            )
            if missing > 0:
                orders.append(
                    ["BUY_ANIMAL", animal, min(missing, 2)]
                )

    feed_needed = sum(
        _feed_due(day, _tile_at(tiles, plan["position"]), True)
        for plan in animal_plans
        if _plan_is_active(plan, tiles)
    )
    available_feed = int(shed.get("WHEAT", 0)) + int(
        carried.get("WHEAT", 0)
    )
    if feed_needed > available_feed:
        orders.insert(
            0,
            ["BUY_PRODUCT", "WHEAT", feed_needed - available_feed],
        )
    return orders


def _crop_seed_orders(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
) -> list[list[Any]]:
    seeds = Counter(private.get("seeds", {}))
    orders: list[list[Any]] = []
    for quadrant in LAND_SEQUENCE:
        if quadrant not in farm.get("unlocked_quadrants", []):
            continue
        plans = [
            plan
            for plan in _managed_crop_plans(farm)
            if plan["quadrant"] == quadrant
        ]
        next_plan = next(
            iter(_crop_task_groups(day, farm, tuple(plans))["plant"]),
            None,
        )
        if next_plan is None:
            continue
        crop = str(next_plan["crop"])
        if seeds[crop] <= 0:
            orders.append(["BUY_SEED", crop, 1])
            seeds[crop] += 1
    return orders


def _fertilizer_reserve(
    day: int,
    farm: dict[str, Any],
) -> int:
    if day >= 28:
        return 0
    strawberries = sum(
        plan["crop"] == "STRAWBERRY"
        and day <= int(CROP_DATA["STRAWBERRY"]["last_plant_day"]) + 16
        for plan in _active_plans(CROP_PLANS, farm)
    )
    return strawberries * FERTILIZER_RESERVE_PER_STRAWBERRY


def _sales_orders(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    animal_plans: tuple[dict[str, Any], ...],
    projected_drop_workers: set[int] | None = None,
) -> list[list[Any]]:
    shed = private.get("shed", {})
    quantities = Counter(
        {
            item: int(shed.get(item, 0))
            for item in (
                "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                "EGG", "MILK", "WOOL", "FERTILIZER",
            )
        }
    )
    inventories = private.get("inventories", [])
    for worker in projected_drop_workers or set():
        if worker < len(inventories) and isinstance(
            inventories[worker], dict
        ):
            quantities.update(inventories[worker])

    active_animals = sum(
        _plan_is_active(plan, farm["tiles"])
        for plan in animal_plans
    )
    feed_reserve = 0 if day >= 28 else 2 * active_animals
    quantities["WHEAT"] = max(
        0, quantities["WHEAT"] - feed_reserve
    )
    quantities["FERTILIZER"] = max(
        0,
        quantities["FERTILIZER"] - _fertilizer_reserve(day, farm),
    )
    return [
        ["SELL", item, quantities[item]]
        for item in (
            "MELON", "STRAWBERRY", "WOOL", "MILK", "EGG",
            "TOMATO", "CARROT", "FERTILIZER", "WHEAT",
        )
        if quantities[item] > 0
    ]


def _final_day_actions(
    animal_plans: tuple[dict[str, Any], ...],
    hour: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    market: dict[str, Any],
) -> tuple[list[str], list[list[str]]]:
    positions = [
        tuple(farm["farmer"]),
        *(tuple(position) for position in farm.get("hands", [])),
    ]
    inventories = _inventories(private, len(positions))
    shed_tiles = _shed_access_tiles(len(farm["tiles"]))
    prices = market.get("prices", {})
    products = {str(plan["product"]) for plan in animal_plans}
    reserved: set[tuple[str, str]] = set()
    actions: list[list[str]] = []

    for position, inventory in zip(positions, inventories):
        candidates: list[
            tuple[float, int, int, str, tuple[int, int], list[str]]
        ] = []
        for plan in animal_plans:
            if not _plan_is_active(plan, farm["tiles"]):
                continue
            target = tuple(plan["position"])
            distance = _distance(position, target)
            return_distance = min(
                _distance(target, shed_tile) for shed_tile in shed_tiles
            )
            if hour + distance + 1 + return_distance > 22:
                continue
            tile = _tile_at(farm["tiles"], target)
            plan_id = str(plan["id"])
            units = int(tile.get("yield_units", 0))
            if units > 0 and (plan_id, "HARVEST") not in reserved:
                value = int(prices.get(plan["product"], 0)) * units
                candidates.append(
                    (
                        value / (distance + 1), value, -distance,
                        plan_id, target, ["HARVEST"],
                    )
                )
            if (
                tile.get("fertilizer_available", False)
                and (plan_id, "COLLECT_FERTILIZER") not in reserved
            ):
                value = int(prices.get("FERTILIZER", 0))
                candidates.append(
                    (
                        value / (distance + 1), value, -distance,
                        plan_id, target, ["COLLECT_FERTILIZER"],
                    )
                )
        if candidates:
            _, _, _, plan_id, target, operation = max(
                candidates,
                key=lambda candidate: (
                    candidate[0], candidate[1], candidate[2],
                    -candidate[4][1], -candidate[4][0],
                ),
            )
            reserved.add((plan_id, operation[0]))
            actions.append(
                _act_at_or_move(position, target, operation)
            )
            continue

        carried = sum(
            int(inventory.get(item, 0))
            for item in products | {"FERTILIZER"}
        )
        if carried <= 0:
            actions.append(["PASS"])
            continue
        target = min(
            shed_tiles,
            key=lambda candidate: (
                _distance(position, candidate),
                candidate[1], candidate[0],
            ),
        )
        if position == target:
            actions.append(["DROP"])
        elif hour + _distance(position, target) <= 22:
            actions.append(
                _act_at_or_move(position, target, ["DROP"])
            )
        else:
            actions.append(["PASS"])
    return actions[0], actions[1:]


def decide(
    observation: dict[str, Any],
    *,
    target_daily_hands: int = TARGET_DAILY_HANDS,
    target_extra_land: int = TARGET_EXTRA_LAND,
) -> dict[str, Any]:
    """Run diversified center-out cores through NW, NE, then SW."""
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    day = int(observation["day"])
    active_animals = _active_plans(ANIMAL_PLANS, farm)

    if day == 29:
        farmer_action, hands_actions = _final_day_actions(
            active_animals,
            int(observation["hour"]),
            farm,
            private,
            observation.get("market", {}),
        )
    else:
        farmer_action, hands_actions = _worker_actions(
            active_animals,
            day,
            farm,
            private,
        )

    worker_actions = [farmer_action, *hands_actions]
    drop_workers = {
        worker
        for worker, action in enumerate(worker_actions)
        if action == ["DROP"]
    }
    market = _investment_market_orders(
        _sales_orders(
            day,
            farm,
            private,
            active_animals,
            drop_workers,
        ),
        _livestock_orders(
            active_animals,
            day,
            farm,
            private,
        ),
        _land_orders(day, farm, target_extra_land),
        _zoned_hire_orders(
            farm,
            _daily_hand_target(day, farm, target_daily_hands),
        ),
        _crop_seed_orders(day, farm, private),
    )
    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market[:MAX_MARKET_ORDERS],
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the separate center-out diversified research challenger."""
    return decide(observation)