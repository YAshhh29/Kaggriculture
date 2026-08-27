"""Premium-crop throughput challenger derived from current top replays."""

from __future__ import annotations

from collections import Counter
from typing import Any

from agents.experimental_center_out_agent import (
    ANIMAL_PLANS,
    CENTER_OUT_BLOCKS,
    CROP_DATA,
    LAND_SEQUENCE,
    _active_plans,
    _assign_fertilized_strawberry,
    _assign_generic_setup,
    _crop_operations,
    _final_day_actions,
    _is_crop,
    _livestock_orders,
    _managed_crop_plans,
    block_to_position,
)
from agents.experimental_hands_agent import _act_at_or_move, _distance
from agents.experimental_scale_agent import (
    LAST_FEEDING_DAY,
    _assign_animal_services,
    _assign_nearest,
    _assign_urgent_feeding,
    _feed_due,
    _inventories,
    _plan_is_active,
    _tile_at,
)
from agents.experimental_throughput_agent import (
    _affordable_market_orders,
    _animal_crew_size,
)
from agents.experimental_zoned_agent import _zoned_hire_orders


TARGET_EXTRA_LAND = 2
FERTILIZER_RESERVE = 0
HAND_TARGETS = (
    5, 4, 4, 4, 4, 4,
    9, 9, 9,
    12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
    12, 12, 12, 12, 12, 12, 12, 12,
    10, 8,
)

DENSE_CROP_TYPES = {
    "NW": (
        *("MELON" for _ in range(5)),
        *("STRAWBERRY" for _ in range(8)),
        *("WHEAT" for _ in range(8)),
    ),
    "NE": (
        *("MELON" for _ in range(5)),
        *("STRAWBERRY" for _ in range(14)),
        *("WHEAT" for _ in range(2)),
    ),
    "SW": (
        *("STRAWBERRY" for _ in range(13)),
        *("WHEAT" for _ in range(8)),
    ),
}
LAST_PLANT_DAYS = {
    "MELON": 7,
    "STRAWBERRY": 11,
    "WHEAT": 22,
    "CARROT": 22,
}

DENSE_CROP_PLANS = tuple(
    {
        "id": f"dense_{quadrant.lower()}_{crop.lower()}_{index}",
        "quadrant": quadrant,
        "block": block,
        "position": block_to_position(block),
        "crop": crop,
        "first_plant_day": (
            23
            if quadrant == "SW" and crop == "WHEAT"
            else 23
            if quadrant == "NE" and crop == "WHEAT"
            else 4
            if quadrant == "NW" and crop == "WHEAT"
            and block in {1, 3, 4, 11}
            else 0
        ),
        **(
            {
                "rotation_crop": "STRAWBERRY",
                "opening_last_plant_day": 1,
            }
            if quadrant == "NW" and crop == "WHEAT"
            else {}
        ),
        "last_plant_day": (
            0
            if crop == "MELON" and quadrant == "NW"
            else LAST_PLANT_DAYS[crop]
        ),
    }
    for quadrant in LAND_SEQUENCE
    for index, (block, crop) in enumerate(
        zip(CENTER_OUT_BLOCKS[quadrant], DENSE_CROP_TYPES[quadrant]),
        start=1,
    )
)


def _dense_crop_plans(
    farm: dict[str, Any],
    day: int = 0,
    reserved_positions: set[tuple[int, int]] | None = None,
    rotation_crop: str = "STRAWBERRY",
    late_rotation_crop: str | None = None,
    rotation_last_plant_day: int | None = None,
    late_rotation_last_plant_day: int | None = None,
    lifecycle_windows: bool = False,
    lifecycle_deadlines_only: bool = False,
) -> tuple[dict[str, Any], ...]:
    managed = _managed_crop_plans(
        farm,
        crop_plans=DENSE_CROP_PLANS,
        max_slots_per_quadrant=None,
    )
    reserved_positions = reserved_positions or set()
    rotation_deadline = (
        LAST_PLANT_DAYS[rotation_crop]
        if rotation_last_plant_day is None
        else rotation_last_plant_day
    )
    late_rotation_deadline = (
        LAST_PLANT_DAYS[late_rotation_crop]
        if late_rotation_crop is not None
        and late_rotation_last_plant_day is None
        else late_rotation_last_plant_day
    )
    plans: list[dict[str, Any]] = []
    for plan in managed:
        if tuple(plan["position"]) in reserved_positions:
            continue
        tile = _tile_at(farm["tiles"], plan["position"])
        current_crop = (
            str(tile.get("crop"))
            if isinstance(tile, dict) and tile.get("kind") == "PLANT"
            else None
        )
        late_rotation_active = (
            late_rotation_crop is not None
            and current_crop == late_rotation_crop
        )
        late_rotation_due = (
            late_rotation_crop is not None
            and tile is None
            and (
                day > int(plan["last_plant_day"])
                or int(plan.get("first_plant_day", 0))
                > int(plan["last_plant_day"])
                or (
                    plan.get("rotation_crop") is not None
                    and day > rotation_deadline
                )
            )
            and late_rotation_deadline is not None
            and day <= late_rotation_deadline
        )
        if late_rotation_active or late_rotation_due:
            plans.append(
                {
                    **plan,
                    "crop": late_rotation_crop,
                    "first_plant_day": 0,
                    "last_plant_day": late_rotation_deadline,
                }
            )
            continue
        if plan.get("rotation_crop") is None:
            plans.append(plan)
            continue
        if current_crop in {str(plan["crop"]), str(rotation_crop)}:
            crop = current_crop
        elif 4 <= day <= rotation_deadline:
            crop = rotation_crop
        else:
            crop = str(plan["crop"])
        plans.append(
            {
                **plan,
                "crop": crop,
                "last_plant_day": (
                    int(plan["opening_last_plant_day"])
                    if crop == str(plan["crop"])
                    and "opening_last_plant_day" in plan
                    else rotation_deadline
                    if crop == rotation_crop
                    else LAST_PLANT_DAYS[crop]
                ),
            }
        )
    if not lifecycle_windows and not lifecycle_deadlines_only:
        return tuple(plans)
    cashable_day = 28
    return tuple(
        {
            **plan,
            "first_plant_day": (
                int(plan.get("first_plant_day", 0))
                if lifecycle_deadlines_only
                else 0
            ),
            "last_plant_day": (
                cashable_day
                - int(CROP_DATA[str(plan["crop"])]["harvest_age"])
            ),
        }
        for plan in plans
    )


def _hand_target(
    day: int,
    hand_targets: tuple[int, ...] = HAND_TARGETS,
) -> int:
    return hand_targets[min(max(day, 0), len(hand_targets) - 1)]


def _pair_quadrants(
    day: int,
    farm: dict[str, Any],
) -> tuple[str, ...]:
    unlocked = set(farm.get("unlocked_quadrants", []))
    if "SW" in unlocked:
        return ("NW", "NE", "SW")
    if "NE" in unlocked:
        if day <= 7:
            return ("NW", "NW", "NE")
        return ("NW", "NE", "NE")
    return ("NW", "NW", "NW")


def _crop_priority(day: int, crop: str) -> int:
    if day <= 1:
        return {
            "MELON": 0,
            "WHEAT": 1,
            "CARROT": 1,
            "STRAWBERRY": 2,
        }[crop]
    return {
        "STRAWBERRY": 0,
        "MELON": 1,
        "CARROT": 2,
        "WHEAT": 3,
    }[crop]


def _projected_sale_value(
    sales: list[list[Any]],
    market: dict[str, Any],
) -> float:
    prices = market.get("prices", {})
    return sum(
        0.75 * int(prices.get(str(order[1]), 0)) * int(order[2])
        for order in sales
        if len(order) >= 3 and order[0] == "SELL"
    )


def _seed_orders(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    crop_plans: tuple[dict[str, Any], ...],
    animal_crew_size: int,
    pair_quadrants: tuple[str, ...],
    seed_buffer_multiplier: int = 1,
    wheat_seed_buffer_multiplier: int | None = None,
    extra_wheat_seed_buffer: int = 0,
    reserve_seeds_per_quadrant: bool = False,
    max_active_crops_per_quadrant: int | None = None,
) -> list[list[Any]]:
    available_crop_workers = max(
        0,
        1 + len(farm.get("hands", [])) - animal_crew_size,
    )
    pair_count = min(len(pair_quadrants), available_crop_workers // 2)
    pairs_by_quadrant = Counter(pair_quadrants[:pair_count])
    seeds = Counter(private.get("seeds", {}))
    orders: list[list[Any]] = []
    remaining_wheat_extra = max(0, extra_wheat_seed_buffer)
    reserved_targets: Counter[str] = Counter()
    total_needed: Counter[str] = Counter()

    for quadrant in LAND_SEQUENCE:
        pair_capacity = pairs_by_quadrant[quadrant]
        if pair_capacity <= 0:
            continue
        plans = tuple(
            plan for plan in crop_plans if plan["quadrant"] == quadrant
        )
        remaining_capacity = (
            None
            if max_active_crops_per_quadrant is None
            else max(
                0,
                max_active_crops_per_quadrant
                - sum(
                    _is_crop(
                        _tile_at(farm["tiles"], plan["position"])
                    )
                    for plan in plans
                ),
            )
        )
        plantable = [
            plan
            for plan in plans
            if _tile_at(farm["tiles"], plan["position"]) is None
            and day >= int(plan.get("first_plant_day", 0))
            and day <= int(plan["last_plant_day"])
        ]
        if remaining_capacity is not None:
            plantable = plantable[:remaining_capacity]
        needed = Counter(str(plan["crop"]) for plan in plantable)
        total_needed.update(needed)
        crops = sorted(
            ("MELON", "STRAWBERRY", "CARROT", "WHEAT"),
            key=lambda crop: _crop_priority(day, crop),
        )
        for crop in crops:
            if crop == "STRAWBERRY" and day < 2:
                continue
            base_target = pair_capacity * (
                wheat_seed_buffer_multiplier
                if crop == "WHEAT"
                and wheat_seed_buffer_multiplier is not None
                else seed_buffer_multiplier
            )
            extra_target = (
                min(remaining_wheat_extra, needed[crop])
                if crop == "WHEAT"
                else 0
            )
            target_buffer = min(
                needed[crop],
                base_target + extra_target,
            )
            if crop == "WHEAT":
                remaining_wheat_extra -= max(
                    0,
                    target_buffer - base_target,
                )
            if reserve_seeds_per_quadrant:
                reserved_targets[crop] += target_buffer
                continue
            missing = max(0, target_buffer - seeds[crop])
            if missing <= 0:
                continue
            orders.append(["BUY_SEED", crop, missing])
            seeds[crop] += missing
    if reserve_seeds_per_quadrant:
        reserved_targets["WHEAT"] = min(
            total_needed["WHEAT"],
            reserved_targets["WHEAT"] + remaining_wheat_extra,
        )
        crops = sorted(
            ("MELON", "STRAWBERRY", "CARROT", "WHEAT"),
            key=lambda crop: _crop_priority(day, crop),
        )
        return [
            ["BUY_SEED", crop, reserved_targets[crop] - seeds[crop]]
            for crop in crops
            if reserved_targets[crop] > seeds[crop]
        ]
    return orders


def _assign_crop_tasks(
    day: int,
    farm: dict[str, Any],
    crop_plans: tuple[dict[str, Any], ...],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    *,
    critical: bool,
    prioritize_mature_harvest: bool = False,
    excluded_targets: set[tuple[int, int]] | None = None,
) -> set[tuple[int, int]]:
    tasks: list[tuple[int, tuple[int, int], list[str]]] = []
    for plan in crop_plans:
        target = tuple(plan["position"])
        tile = _tile_at(farm["tiles"], target)
        if tile is None:
            continue
        if not _is_crop(tile, str(plan["crop"])):
            if critical:
                tasks.append((0, target, ["DIG"]))
            continue
        operations = _crop_operations(day, tile)
        age = day - int(tile["planted_day"])
        data = CROP_DATA[str(plan["crop"])]
        final_ongoing_age = (
            bool(data["ongoing"])
            and age >= int(data["spent_age"]) - 1
        )
        proactive_dig = (
            final_ongoing_age
            and int(tile.get("yield_units", 0)) <= 0
        )
        overdue_harvest = (
            "HARVEST" in operations
            and not bool(
                str(plan["crop"]) in {"STRAWBERRY", "TOMATO"}
            )
            and age > 4
        )
        urgent_water = (
            "WATER" in operations
            and int(tile.get("consecutive_unwatered", 0)) >= 1
        )
        if critical:
            if "DIG" in operations or proactive_dig:
                tasks.append((0, target, ["DIG"]))
            elif (
                prioritize_mature_harvest
                and "HARVEST" in operations
                and not bool(data["ongoing"])
            ) or overdue_harvest or (
                final_ongoing_age and "HARVEST" in operations
            ):
                tasks.append((0, target, ["HARVEST"]))
            elif urgent_water:
                tasks.append((1, target, ["WATER"]))
            continue
        if "HARVEST" in operations:
            tasks.append((0, target, ["HARVEST"]))
        elif "WATER" in operations:
            tasks.append((1, target, ["WATER"]))

    reserved = set(excluded_targets or ())
    for worker, action in enumerate(actions):
        if action is not None:
            continue
        available = [task for task in tasks if task[1] not in reserved]
        if not available:
            break
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
            positions[worker],
            target,
            operation,
        )
    return reserved


def _assign_paired_planting(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    crop_plans: tuple[dict[str, Any], ...],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    seed_budget: Counter[str] | None = None,
    max_active_crops: int | None = None,
) -> None:
    free_workers = [
        worker for worker, action in enumerate(actions) if action is None
    ]
    if seed_budget is None:
        seed_budget = Counter(private.get("seeds", {}))
    candidates = [
        plan
        for plan in crop_plans
        if _tile_at(farm["tiles"], plan["position"]) is None
        and day >= int(plan.get("first_plant_day", 0))
        and day <= int(plan["last_plant_day"])
        and seed_budget[str(plan["crop"])] > 0
    ]
    plan_order = {
        str(plan["id"]): index for index, plan in enumerate(crop_plans)
    }
    candidates.sort(
        key=lambda plan: (
            _crop_priority(day, str(plan["crop"])),
            plan_order[str(plan["id"])],
        )
    )
    active_crops = sum(
        _is_crop(_tile_at(farm["tiles"], plan["position"]))
        for plan in crop_plans
    )
    remaining_capacity = (
        len(candidates)
        if max_active_crops is None
        else max(0, max_active_crops - active_crops)
    )
    reserved: set[tuple[int, int]] = set()

    while len(free_workers) >= 2 and remaining_capacity > 0:
        available = [
            plan
            for plan in candidates
            if tuple(plan["position"]) not in reserved
            and seed_budget[str(plan["crop"])] > 0
        ]
        if not available:
            break
        plan = available[0]
        target = tuple(plan["position"])
        workers = sorted(
            free_workers,
            key=lambda worker: (
                _distance(positions[worker], target),
                worker,
            ),
        )[:2]
        if all(positions[worker] == target for worker in workers):
            actions[workers[0]] = ["PLANT", str(plan["crop"])]
            actions[workers[1]] = ["WATER"]
            seed_budget[str(plan["crop"])] -= 1
            remaining_capacity -= 1
        else:
            for worker in workers:
                actions[worker] = _act_at_or_move(
                    positions[worker],
                    target,
                    ["PASS"],
                )
        reserved.add(target)
        free_workers = [
            worker for worker in free_workers if worker not in workers
        ]


def _assign_limited_animal_services(
    animal_plans: tuple[dict[str, Any], ...],
    day: int,
    farm: dict[str, Any],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    *,
    crop_worker_reserve: int = 2,
    care_enabled: bool = True,
    anticipate_daily_feed: bool = False,
) -> None:
    free_workers = [
        worker for worker, action in enumerate(actions) if action is None
    ]
    service_count = max(0, len(free_workers) - crop_worker_reserve)
    if service_count <= 0:
        return
    active_plans = tuple(
        plan
        for plan in animal_plans
        if _plan_is_active(plan, farm["tiles"])
    )
    if not active_plans:
        return
    service_workers = sorted(
        free_workers,
        key=lambda worker: (
            min(
                _distance(positions[worker], plan["position"])
                for plan in active_plans
            ),
            worker,
        ),
    )[:service_count]
    service_positions = [positions[worker] for worker in service_workers]
    service_actions = [actions[worker] for worker in service_workers]
    _assign_animal_services(
        active_plans,
        day,
        farm,
        service_positions,
        service_actions,
        care_enabled,
    )
    if care_enabled and anticipate_daily_feed and day <= LAST_FEEDING_DAY:
        for plan in active_plans:
            tile = _tile_at(farm["tiles"], plan["position"])
            if not tile.get("cared_today", False):
                _assign_nearest(
                    service_positions,
                    service_actions,
                    plan["position"],
                    ["CARE"],
                )
    for service_worker, worker in enumerate(service_workers):
        actions[worker] = service_actions[service_worker]


def _assign_colocated_feed_care(
    animal_plans: tuple[dict[str, Any], ...],
    day: int,
    farm: dict[str, Any],
    positions: list[tuple[int, int]],
    inventories: list[dict[str, Any]],
    actions: list[list[str] | None],
) -> set[str]:
    paired: set[str] = set()
    if day > LAST_FEEDING_DAY:
        return paired
    for plan in animal_plans:
        tile = _tile_at(farm["tiles"], plan["position"])
        if (
            not _plan_is_active(plan, farm["tiles"])
            or tile.get("fed_today", False)
            or tile.get("cared_today", False)
        ):
            continue
        target = tuple(plan["position"])
        colocated = [
            worker
            for worker, position in enumerate(positions)
            if actions[worker] is None and position == target
        ]
        feeder = next(
            (
                worker
                for worker in colocated
                if int(inventories[worker].get("WHEAT", 0)) > 0
            ),
            None,
        )
        if feeder is None:
            continue
        caregiver = next(
            (worker for worker in colocated if worker != feeder),
            None,
        )
        if caregiver is None:
            continue
        actions[feeder] = ["FEED"]
        actions[caregiver] = ["CARE"]
        paired.add(str(plan["id"]))
    return paired


def _assign_animal_care(
    animal_plans: tuple[dict[str, Any], ...],
    day: int,
    farm: dict[str, Any],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
) -> None:
    if day > LAST_FEEDING_DAY:
        return
    tiles = farm["tiles"]
    for plan in animal_plans:
        if not _plan_is_active(plan, tiles):
            continue
        tile = _tile_at(tiles, plan["position"])
        if tile.get("fed_today", False) and not tile.get(
            "cared_today", False
        ):
            _assign_nearest(
                positions,
                actions,
                plan["position"],
                ["CARE"],
            )


def _assign_crop_fertilization(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    crop_plans: tuple[dict[str, Any], ...],
    positions: list[tuple[int, int]],
    inventories: list[dict[str, Any]],
    actions: list[list[str] | None],
    limit: int | None = None,
    carried_only: bool = False,
) -> None:
    candidates = []
    for plan in crop_plans:
        tile = _tile_at(farm["tiles"], plan["position"])
        if not _is_crop(tile, "STRAWBERRY"):
            continue
        operations = _crop_operations(day, tile)
        if {"FERTILIZE", "WATER"}.issubset(operations):
            candidates.append(plan)
    candidates.sort(
        key=lambda plan: (
            min(
                _distance(tuple(plan["position"]), access)
                for access in ((4, 4), (5, 4), (4, 5), (5, 5))
            ),
            int(plan["position"][1]),
            int(plan["position"][0]),
        )
    )
    if limit is not None:
        candidates = candidates[:max(0, limit)]
    for plan in candidates:
        free_workers = [
            worker for worker, action in enumerate(actions)
            if action is None
        ]
        if len(free_workers) < 2:
            return
        target = tuple(plan["position"])
        carriers = [
            worker
            for worker in free_workers
            if int(inventories[worker].get("FERTILIZER", 0)) > 0
        ]
        if carried_only and not carriers:
            continue
        if carriers:
            fertilizer_worker = min(
                carriers,
                key=lambda worker: (
                    _distance(positions[worker], target),
                    worker,
                ),
            )
            water_worker = min(
                (
                    worker
                    for worker in free_workers
                    if worker != fertilizer_worker
                ),
                key=lambda worker: (
                    _distance(positions[worker], target),
                    worker,
                ),
            )
            workers = [fertilizer_worker, water_worker]
        else:
            workers = sorted(
                free_workers,
                key=lambda worker: (
                    _distance(positions[worker], target),
                    worker,
                ),
            )[:2]
        _assign_fertilized_strawberry(
            workers,
            plan,
            farm,
            private,
            positions,
            inventories,
            actions,
        )


def _effective_crop_worker_reserve(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    crop_plans: tuple[dict[str, Any], ...],
    configured_reserve: int,
    *,
    actionable_only: bool = False,
    scale_to_due_work: bool = False,
) -> int:
    due_work = sum(
        bool(_crop_operations(day, tile))
        for plan in crop_plans
        if _is_crop(
            tile := _tile_at(farm["tiles"], plan["position"]),
            str(plan["crop"]),
        )
    )
    if scale_to_due_work and due_work > 0:
        return min(
            configured_reserve + 1,
            max(1, due_work),
        )
    if not actionable_only:
        plantable = any(
            _tile_at(farm["tiles"], plan["position"]) is None
            and day >= int(plan.get("first_plant_day", 0))
            and day <= int(plan["last_plant_day"])
            for plan in crop_plans
        )
        if plantable:
            return configured_reserve
        active_crops = any(
            _is_crop(_tile_at(farm["tiles"], plan["position"]))
            for plan in crop_plans
        )
        return min(configured_reserve, 1) if active_crops else 0

    seeds = Counter(private.get("seeds", {}))
    plantable = any(
        _tile_at(farm["tiles"], plan["position"]) is None
        and day >= int(plan.get("first_plant_day", 0))
        and day <= int(plan["last_plant_day"])
        and seeds[str(plan["crop"])] > 0
        for plan in crop_plans
    )
    if plantable:
        return min(configured_reserve, 2)
    actionable_crops = sum(
        bool(_crop_operations(day, tile))
        for plan in crop_plans
        if _is_crop(
            tile := _tile_at(farm["tiles"], plan["position"]),
            str(plan["crop"]),
        )
    )
    return min(configured_reserve, actionable_crops)


def _worker_actions(
    animal_plans: tuple[dict[str, Any], ...],
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    crop_plans: tuple[dict[str, Any], ...],
    crop_worker_reserve: int,
    release_idle_crop_reserve: bool,
    actionable_crop_reserve: bool,
    prioritize_mature_harvest: bool,
    fertilize_strawberries: bool,
    fertilized_strawberries_per_quadrant: int | None,
    cross_quadrant_crop_rescue: bool,
    crop_before_routine_animals: bool = False,
    crops_before_care_only: bool = False,
    plant_before_care: bool = False,
    scale_crop_reserve_to_due_work: bool = False,
    cross_quadrant_routine_rescue: bool = False,
    carried_fertilizer_only: bool = False,
    max_active_crops_per_quadrant: int | None = None,
    pair_colocated_feed_care: bool = False,
    anticipate_daily_feed_for_care: bool = False,
) -> tuple[list[str], list[list[str]]]:
    positions = [
        tuple(farm["farmer"]),
        *(tuple(position) for position in farm.get("hands", [])),
    ]
    inventories = _inventories(private, len(positions))
    actions: list[list[str] | None] = [None for _ in positions]
    unlocked = [
        quadrant
        for quadrant in LAND_SEQUENCE
        if quadrant in farm.get("unlocked_quadrants", [])
    ]
    worker_groups = {
        quadrant: list(range(index, len(positions), len(unlocked)))
        for index, quadrant in enumerate(unlocked)
    }
    seed_budget = Counter(private.get("seeds", {}))
    assigned_crop_targets: set[tuple[int, int]] = set()

    for quadrant in unlocked:
        workers = worker_groups[quadrant]
        local_positions = [positions[worker] for worker in workers]
        local_inventories = [inventories[worker] for worker in workers]
        local_actions = [actions[worker] for worker in workers]
        local_animals = tuple(
            plan
            for plan in animal_plans
            if plan["quadrant"] == quadrant
        )
        local_crops = tuple(
            plan
            for plan in crop_plans
            if plan["quadrant"] == quadrant
        )
        emergency = tuple(
            plan
            for plan in local_animals
            if _plan_is_active(plan, farm["tiles"])
            and _feed_due(
                day,
                _tile_at(farm["tiles"], plan["position"]),
                False,
            )
        )
        emergency_ids = {str(plan["id"]) for plan in emergency}
        normal = tuple(
            plan
            for plan in local_animals
            if str(plan["id"]) not in emergency_ids
        )

        paired_feed_care = (
            _assign_colocated_feed_care(
                local_animals,
                day,
                farm,
                local_positions,
                local_inventories,
                local_actions,
            )
            if pair_colocated_feed_care
            else set()
        )
        emergency = tuple(
            plan
            for plan in emergency
            if str(plan["id"]) not in paired_feed_care
        )
        normal = tuple(
            plan
            for plan in normal
            if str(plan["id"]) not in paired_feed_care
        )

        _assign_urgent_feeding(
            emergency,
            day,
            farm,
            private,
            local_positions,
            local_inventories,
            local_actions,
            False,
        )
        assigned_crop_targets.update(_assign_crop_tasks(
            day,
            farm,
            local_crops,
            local_positions,
            local_actions,
            critical=True,
            prioritize_mature_harvest=prioritize_mature_harvest,
        ))
        _assign_urgent_feeding(
            normal,
            day,
            farm,
            private,
            local_positions,
            local_inventories,
            local_actions,
            True,
        )
        _assign_generic_setup(
            local_animals,
            farm,
            private,
            local_positions,
            local_inventories,
            local_actions,
        )
        if fertilize_strawberries:
            _assign_crop_fertilization(
                day,
                farm,
                private,
                local_crops,
                local_positions,
                local_inventories,
                local_actions,
                fertilized_strawberries_per_quadrant,
                carried_fertilizer_only,
            )
        effective_reserve = (
            _effective_crop_worker_reserve(
                day,
                farm,
                private,
                local_crops,
                crop_worker_reserve,
                actionable_only=actionable_crop_reserve,
                scale_to_due_work=scale_crop_reserve_to_due_work,
            )
            if release_idle_crop_reserve
            else crop_worker_reserve
        )
        if crops_before_care_only:
            _assign_limited_animal_services(
                local_animals,
                day,
                farm,
                local_positions,
                local_actions,
                crop_worker_reserve=effective_reserve,
                care_enabled=False,
                anticipate_daily_feed=anticipate_daily_feed_for_care,
            )
        if crop_before_routine_animals or crops_before_care_only:
            assigned_crop_targets.update(_assign_crop_tasks(
                day,
                farm,
                local_crops,
                local_positions,
                local_actions,
                critical=False,
            ))
        if crops_before_care_only and plant_before_care:
            _assign_paired_planting(
                day,
                farm,
                private,
                local_crops,
                local_positions,
                local_actions,
                seed_budget,
                max_active_crops_per_quadrant,
            )
        if crops_before_care_only:
            _assign_animal_care(
                local_animals,
                day,
                farm,
                local_positions,
                local_actions,
            )
        else:
            _assign_limited_animal_services(
                local_animals,
                day,
                farm,
                local_positions,
                local_actions,
                crop_worker_reserve=effective_reserve,
                anticipate_daily_feed=anticipate_daily_feed_for_care,
            )
        if not crop_before_routine_animals and not crops_before_care_only:
            assigned_crop_targets.update(_assign_crop_tasks(
                day,
                farm,
                local_crops,
                local_positions,
                local_actions,
                critical=False,
            ))
        if not (crops_before_care_only and plant_before_care):
            _assign_paired_planting(
                day,
                farm,
                private,
                local_crops,
                local_positions,
                local_actions,
                seed_budget,
                max_active_crops_per_quadrant,
            )
        for local_worker, worker in enumerate(workers):
            actions[worker] = local_actions[local_worker]

    if cross_quadrant_crop_rescue:
        _assign_crop_tasks(
            day,
            farm,
            crop_plans,
            positions,
            actions,
            critical=True,
            prioritize_mature_harvest=prioritize_mature_harvest,
            excluded_targets=assigned_crop_targets,
        )
    if cross_quadrant_routine_rescue:
        _assign_crop_tasks(
            day,
            farm,
            crop_plans,
            positions,
            actions,
            critical=False,
            prioritize_mature_harvest=prioritize_mature_harvest,
            excluded_targets=assigned_crop_targets,
        )

    resolved = [action or ["PASS"] for action in actions]
    return resolved[0], resolved[1:]


def _land_orders(
    day: int,
    farm: dict[str, Any],
    market: dict[str, Any],
    sales: list[list[Any]],
    target_extra_land: int = TARGET_EXTRA_LAND,
    reserves: tuple[int, int] = (300, 700),
    dynamic_expansion: bool = False,
    expansion_occupancy_threshold: float = 0.64,
) -> list[list[str]]:
    unlocked_extra = max(0, len(farm.get("unlocked_quadrants", [])) - 1)
    if unlocked_extra >= target_extra_land:
        return []
    costs = (1000, 2000)
    if dynamic_expansion:
        frontier = LAND_SEQUENCE[unlocked_extra]
        half = len(farm["tiles"]) // 2
        x_start = half if frontier.endswith("E") else 0
        y_start = half if frontier.startswith("S") else 0
        tiles = [
            farm["tiles"][y][x]
            for y in range(y_start, y_start + half)
            for x in range(x_start, x_start + half)
        ]
        productive = sum(
            isinstance(tile, dict)
            and tile.get("kind") in {"PLANT", "COOP", "PASTURE"}
            for tile in tiles
        )
        occupancy = productive / len(tiles)
        degraded = any(
            isinstance(tile, dict) and tile.get("kind") == "WEED"
            for tile in tiles
        )
        animal_emergency = any(
            tile.get("kind") in {"COOP", "PASTURE"}
            and tile.get("animal") is not None
            and int(tile.get("consecutive_unfed", 0)) >= 2
            for tile in tiles
            if isinstance(tile, dict)
        )
        if (
            occupancy < expansion_occupancy_threshold
            or degraded
            or animal_emergency
        ):
            return []
    else:
        earliest_days = (5, 9)
        if day < earliest_days[unlocked_extra]:
            return []
    available = float(farm.get("money", 0)) + _projected_sale_value(
        sales,
        market,
    )
    if available < costs[unlocked_extra] + reserves[unlocked_extra]:
        return []
    return [["BUY_LAND"]]


def _sales_orders(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    animal_plans: tuple[dict[str, Any], ...],
    projected_drop_workers: set[int],
    crop_plans: tuple[dict[str, Any], ...] = (),
    fertilizer_reserve_per_strawberry: int = 0,
    fertilizer_reserve_limit: int | None = None,
    wheat_market_price: int | None = None,
    wheat_trade_target: int = 0,
    wheat_trade_sell_price: int | None = None,
) -> list[list[Any]]:
    items = (
        "MELON",
        "STRAWBERRY",
        "WOOL",
        "MILK",
        "EGG",
        "TOMATO",
        "CARROT",
        "FERTILIZER",
        "WHEAT",
    )
    shed = private.get("shed", {})
    quantities = Counter({item: int(shed.get(item, 0)) for item in items})
    inventories = private.get("inventories", [])
    for worker in projected_drop_workers:
        if worker < len(inventories) and isinstance(
            inventories[worker], dict
        ):
            quantities.update(inventories[worker])

    active_animals = sum(
        _plan_is_active(plan, farm["tiles"])
        for plan in animal_plans
    )
    feed_reserve = 0 if day >= 28 else 2 * active_animals
    wheat_reserve = feed_reserve
    if (
        day < 28
        and wheat_trade_target > 0
        and wheat_trade_sell_price is not None
        and wheat_market_price is not None
        and wheat_market_price < wheat_trade_sell_price
    ):
        wheat_reserve = max(wheat_reserve, wheat_trade_target)
    quantities["WHEAT"] = max(0, quantities["WHEAT"] - wheat_reserve)
    active_strawberries = sum(
        _is_crop(_tile_at(farm["tiles"], plan["position"]), "STRAWBERRY")
        for plan in crop_plans
    )
    fertilizer_reserve = (
        0
        if day >= 28
        else max(
            FERTILIZER_RESERVE,
            fertilizer_reserve_per_strawberry * active_strawberries,
        )
    )
    if fertilizer_reserve_limit is not None:
        fertilizer_reserve = min(
            fertilizer_reserve,
            max(0, fertilizer_reserve_limit),
        )
    quantities["FERTILIZER"] = max(
        0,
        quantities["FERTILIZER"] - fertilizer_reserve,
    )
    return [
        ["SELL", item, quantities[item]]
        for item in items
        if quantities[item] > 0
    ]


def _wheat_trade_orders(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    market: dict[str, Any],
    sales: list[list[Any]],
    target: int,
    buy_price: int | None,
    cash_reserve: int,
) -> list[list[Any]]:
    if (
        target <= 0
        or buy_price is None
        or day >= 27
        or len(farm.get("unlocked_quadrants", [])) < 3
        or any(order[:2] == ["SELL", "WHEAT"] for order in sales)
    ):
        return []
    price = int(market.get("prices", {}).get("WHEAT", 0))
    if price <= 0 or price > buy_price:
        return []
    shed_wheat = int(private.get("shed", {}).get("WHEAT", 0))
    missing = max(0, target - shed_wheat)
    spendable = max(0, int(farm.get("money", 0)) - cash_reserve)
    quantity = min(missing, spendable // price)
    return [["BUY_PRODUCT", "WHEAT", quantity]] if quantity > 0 else []


def decide(
    observation: dict[str, Any],
    target_extra_land: int = TARGET_EXTRA_LAND,
    animal_plans: tuple[dict[str, Any], ...] = ANIMAL_PLANS,
    rotation_crop: str = "STRAWBERRY",
    land_reserves: tuple[int, int] = (300, 700),
    crop_worker_reserve: int = 2,
    late_rotation_crop: str | None = None,
    rotation_last_plant_day: int | None = None,
    late_rotation_last_plant_day: int | None = None,
    release_idle_crop_reserve: bool = False,
    actionable_crop_reserve: bool = False,
    prioritize_mature_harvest: bool = False,
    fertilize_strawberries: bool = False,
    fertilized_strawberries_per_quadrant: int | None = None,
    cross_quadrant_crop_rescue: bool = False,
    crop_before_routine_animals: bool = False,
    crops_before_care_only: bool = False,
    plant_before_care: bool = False,
    scale_crop_reserve_to_due_work: bool = False,
    cross_quadrant_routine_rescue: bool = False,
    carried_fertilizer_only: bool = False,
    fertilizer_reserve_per_strawberry: int = 0,
    fertilizer_reserve_limit: int | None = None,
    hand_targets: tuple[int, ...] = HAND_TARGETS,
    seed_buffer_multiplier: int = 1,
    wheat_seed_buffer_multiplier: int | None = None,
    extra_wheat_seed_buffer: int = 0,
    reserve_seeds_per_quadrant: bool = False,
    dynamic_land_expansion: bool = False,
    expansion_occupancy_threshold: float = 0.64,
    dynamic_lifecycle_windows: bool = False,
    dynamic_lifecycle_deadlines_only: bool = False,
    max_active_crops_per_quadrant: int | None = None,
    wheat_trade_target: int = 0,
    wheat_trade_buy_price: int | None = None,
    wheat_trade_sell_price: int | None = None,
    wheat_trade_cash_reserve: int = 3000,
    pair_colocated_feed_care: bool = False,
    anticipate_daily_feed_for_care: bool = False,
) -> dict[str, Any]:
    """Fill paid land with replay-grounded premium crops and stable crews."""
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    market_state = observation.get("market", {})
    day = int(observation["day"])
    desired_animals = tuple(
        plan
        for plan in animal_plans
        if day >= int(plan.get("activation_day", 0))
    )
    active_animals = _active_plans(desired_animals, farm)
    crop_plans = _dense_crop_plans(
        farm,
        day,
        {tuple(plan["position"]) for plan in desired_animals},
        rotation_crop,
        late_rotation_crop,
        rotation_last_plant_day,
        late_rotation_last_plant_day,
        dynamic_lifecycle_windows,
        dynamic_lifecycle_deadlines_only,
    )
    animal_crew_size = _animal_crew_size(day)
    pair_quadrants = _pair_quadrants(day, farm)

    if day == 29:
        farmer_action, hands_actions = _final_day_actions(
            active_animals,
            int(observation["hour"]),
            farm,
            private,
            market_state,
        )
    else:
        farmer_action, hands_actions = _worker_actions(
            active_animals,
            day,
            farm,
            private,
            crop_plans,
            crop_worker_reserve,
            release_idle_crop_reserve,
            actionable_crop_reserve,
            prioritize_mature_harvest,
            fertilize_strawberries,
            fertilized_strawberries_per_quadrant,
            cross_quadrant_crop_rescue,
            crop_before_routine_animals,
            crops_before_care_only,
            plant_before_care,
            scale_crop_reserve_to_due_work,
            cross_quadrant_routine_rescue,
            carried_fertilizer_only,
            max_active_crops_per_quadrant,
            pair_colocated_feed_care,
            anticipate_daily_feed_for_care,
        )

    worker_actions = [farmer_action, *hands_actions]
    drop_workers = {
        worker
        for worker, action in enumerate(worker_actions)
        if action == ["DROP"]
    }
    sales = _sales_orders(
        day,
        farm,
        private,
        active_animals,
        drop_workers,
        crop_plans,
        fertilizer_reserve_per_strawberry,
        fertilizer_reserve_limit,
        int(market_state.get("prices", {}).get("WHEAT", 0)),
        wheat_trade_target,
        wheat_trade_sell_price,
    )
    market = _affordable_market_orders(
        observation,
        [
            *sales,
            *_livestock_orders(active_animals, day, farm, private),
            *_wheat_trade_orders(
                day,
                farm,
                private,
                market_state,
                sales,
                wheat_trade_target,
                wheat_trade_buy_price,
                wheat_trade_cash_reserve,
            ),
            *_land_orders(
                day,
                farm,
                market_state,
                sales,
                target_extra_land,
                land_reserves,
                dynamic_land_expansion,
                expansion_occupancy_threshold,
            ),
            *_zoned_hire_orders(farm, _hand_target(day, hand_targets)),
            *_seed_orders(
                day,
                farm,
                private,
                crop_plans,
                animal_crew_size,
                pair_quadrants,
                seed_buffer_multiplier,
                wheat_seed_buffer_multiplier,
                extra_wheat_seed_buffer,
                reserve_seeds_per_quadrant,
                max_active_crops_per_quadrant,
            ),
        ],
    )
    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market,
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the separate premium-throughput research challenger."""
    return decide(observation)
