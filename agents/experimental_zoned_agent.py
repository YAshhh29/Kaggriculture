"""Center-first crop layout with persistent near and far worker zones."""

from __future__ import annotations

from typing import Any

from agents.experimental_hands_agent import (
    _act_at_or_move,
    _distance,
    _is_mature_wheat,
    _is_wheat,
)
from agents.experimental_investment_agent import (
    _investment_livestock_orders,
    _investment_market_orders,
)
from agents.experimental_scale_agent import (
    LAST_WHEAT_PLANTING_DAY,
    TARGET_COWS,
    TARGET_DAILY_HANDS,
    TARGET_SHEEP,
    TARGET_WHEAT_TILES,
    _assign_animal_services,
    _assign_setup,
    _assign_urgent_feeding,
    _inventories,
    _land_orders,
    _protect_feed_reserve,
    _staged_animal_plans,
    _unlocked_animal_plans,
)
from main import decide as decide_wheat


NEAR_CREW_SIZE = 5
SHED_CENTER = (4, 4)


def _zoned_hire_orders(
    farm: dict[str, Any],
    target_daily_hands: int,
) -> list[list[str]]:
    missing = max(0, target_daily_hands - len(farm.get("hands", [])))
    return [["HIRE"] for _ in range(missing)]


def _unlocked(position: tuple[int, int], farm: dict[str, Any]) -> bool:
    x, y = position
    half = len(farm["tiles"]) // 2
    quadrant = ("N" if y < half else "S") + ("W" if x < half else "E")
    return quadrant in farm.get("unlocked_quadrants", [])


def _crop_priority(
    position: tuple[int, int],
    zone: str,
) -> tuple[int, int, int, int]:
    x, y = position
    half = 5
    preferred = (
        zone == "near" and x < half and y < half
    ) or (
        zone == "far" and x >= half and y < half
    )
    return (
        0 if preferred else 1,
        _distance(position, SHED_CENTER),
        abs(y - 4),
        abs(x - 4),
    )


def _zoned_task_groups(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    livestock_tiles: set[tuple[int, int]],
    zone: str,
) -> list[list[tuple[tuple[int, int], list[str]]]]:
    urgent_water: list[tuple[tuple[int, int], list[str]]] = []
    daily_water: list[tuple[tuple[int, int], list[str]]] = []
    harvest: list[tuple[tuple[int, int], list[str]]] = []
    empty: list[tuple[tuple[int, int], list[str]]] = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            position = (x, y)
            if position in livestock_tiles or not _unlocked(position, farm):
                continue
            if _is_wheat(tile) and not tile.get("watered_today", False):
                target = (position, ["WATER"])
                if int(tile.get("consecutive_unwatered", 0)) >= 1:
                    urgent_water.append(target)
                else:
                    daily_water.append(target)
            elif _is_mature_wheat(tile, day):
                harvest.append((position, ["HARVEST"]))
            elif tile is None:
                empty.append((position, ["PLANT", "WHEAT"]))

    global_key = lambda task: (
        _distance(task[0], SHED_CENTER),
        task[0][1],
        task[0][0],
    )
    urgent_water.sort(key=global_key)
    daily_water.sort(key=global_key)
    harvest.sort(key=global_key)
    key = lambda task: _crop_priority(task[0], zone)
    empty.sort(key=key)
    planting_open = day <= LAST_WHEAT_PLANTING_DAY
    available_seeds = int(private.get("seeds", {}).get("WHEAT", 0))
    plants = empty[:available_seeds] if planting_open else []
    return [urgent_water, daily_water, harvest, plants]


def _assign_zoned_crops(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    positions: list[tuple[int, int]],
    actions: list[list[str] | None],
    livestock_tiles: set[tuple[int, int]],
) -> None:
    reserved: set[tuple[int, int]] = set()
    for worker, position in enumerate(positions):
        if actions[worker] is not None:
            continue
        zone = "near" if worker < NEAR_CREW_SIZE else "far"
        groups = _zoned_task_groups(
            day,
            farm,
            private,
            livestock_tiles,
            zone,
        )
        group = next(
            (
                tasks
                for tasks in groups[:-1]
                if any(target not in reserved for target, _ in tasks)
            ),
            [],
        )
        available = [task for task in group if task[0] not in reserved]
        if not available:
            continue
        target, operation = min(
            available,
            key=lambda task: (
                (
                    _crop_priority(task[0], zone)
                    if task[1][0] == "PLANT"
                    else (0, 0, 0, 0)
                ),
                _distance(position, task[0]),
            ),
        )
        reserved.add(target)
        actions[worker] = _act_at_or_move(position, target, operation)

    available_seeds = int(private.get("seeds", {}).get("WHEAT", 0))
    for zone in ("near", "far"):
        workers = [
            worker
            for worker, action in enumerate(actions)
            if action is None
            and ("near" if worker < NEAR_CREW_SIZE else "far") == zone
        ]
        while len(workers) >= 2 and available_seeds > 0:
            planter, waterer = workers[:2]
            workers = workers[2:]
            plants = _zoned_task_groups(
                day,
                farm,
                private,
                livestock_tiles,
                zone,
            )[-1]
            candidates = [
                task for task in plants if task[0] not in reserved
            ]
            if not candidates:
                break
            target, _ = min(
                candidates,
                key=lambda task: (
                    _crop_priority(task[0], zone),
                    max(
                        _distance(positions[planter], task[0]),
                        _distance(positions[waterer], task[0]),
                    ),
                    _distance(positions[planter], task[0])
                    + _distance(positions[waterer], task[0]),
                ),
            )
            reserved.add(target)
            if positions[planter] == target and positions[waterer] == target:
                actions[planter] = ["PLANT", "WHEAT"]
                actions[waterer] = ["WATER"]
                available_seeds -= 1
                continue
            actions[planter] = (
                ["PASS"]
                if positions[planter] == target
                else _act_at_or_move(positions[planter], target, ["PASS"])
            )
            actions[waterer] = (
                ["PASS"]
                if positions[waterer] == target
                else _act_at_or_move(positions[waterer], target, ["PASS"])
            )

    for worker, action in enumerate(actions):
        if action is None:
            actions[worker] = ["PASS"]


def _zoned_worker_actions(
    animal_plans: tuple[dict[str, Any], ...],
    livestock_tiles: set[tuple[int, int]],
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
    _assign_urgent_feeding(
        animal_plans,
        day,
        farm,
        private,
        positions,
        inventories,
        actions,
        True,
    )
    _assign_setup(
        animal_plans,
        farm,
        private,
        positions,
        inventories,
        actions,
    )
    _assign_animal_services(
        animal_plans,
        day,
        farm,
        positions,
        actions,
        True,
    )
    _assign_zoned_crops(
        day,
        farm,
        private,
        positions,
        actions,
        livestock_tiles,
    )
    resolved = [action or ["PASS"] for action in actions]
    return resolved[0], resolved[1:]


def decide(
    observation: dict[str, Any],
    target_wheat_tiles: int = TARGET_WHEAT_TILES,
    target_daily_hands: int = TARGET_DAILY_HANDS,
    target_extra_land: int = 0,
    target_cows: int = TARGET_COWS,
    target_sheep: int = TARGET_SHEEP,
) -> dict[str, Any]:
    """Run pressure-aware investment with center-first zoned crop crews."""
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    day = int(observation["day"])
    hour = int(observation["hour"])
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
    farmer_action, hands_actions = _zoned_worker_actions(
        active_plans,
        {plan["position"] for plan in desired_plans},
        day,
        farm,
        private,
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
        _zoned_hire_orders(farm, target_daily_hands),
        baseline_market,
    )
    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market,
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the separate zoned routing candidate."""
    return decide(observation)