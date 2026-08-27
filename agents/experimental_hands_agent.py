"""Development-only two-hand scaling policy around the one-goose control."""

from __future__ import annotations

from typing import Any

from agents.experimental_goose_agent import (
    _animal_market_orders,
    _service_action,
    _setup_action,
)
from main import decide as decide_wheat


TARGET_DAILY_HANDS = 2
TARGET_WHEAT_TILES = 12
LAST_WHEAT_PLANTING_DAY = 21


def _is_wheat(tile: Any) -> bool:
    return (
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "WHEAT"
    )


def _is_mature_wheat(tile: Any, day: int) -> bool:
    return (
        _is_wheat(tile)
        and day - int(tile["planted_day"]) >= 4
        and int(tile.get("yield_units", 0)) > 0
    )


def _distance(
    origin: tuple[int, int],
    target: tuple[int, int],
) -> int:
    return abs(origin[0] - target[0]) + abs(origin[1] - target[1])


def _act_at_or_move(
    origin: tuple[int, int],
    target: tuple[int, int],
    action: list[str],
) -> list[str]:
    if origin == target:
        return action
    if target[0] < origin[0]:
        return ["WEST"]
    if target[0] > origin[0]:
        return ["EAST"]
    if target[1] < origin[1]:
        return ["NORTH"]
    return ["SOUTH"]


def _task_groups(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    blocked_tiles: set[tuple[int, int]] | None = None,
) -> list[list[tuple[tuple[int, int], list[str]]]]:
    tiles = farm["tiles"]
    blocked_tiles = blocked_tiles or set()
    urgent_water: list[tuple[tuple[int, int], list[str]]] = []
    daily_water: list[tuple[tuple[int, int], list[str]]] = []
    harvest: list[tuple[tuple[int, int], list[str]]] = []
    empty: list[tuple[tuple[int, int], list[str]]] = []

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            position = (x, y)
            if position in blocked_tiles:
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

    planting_open = day <= LAST_WHEAT_PLANTING_DAY
    available_seeds = int(private.get("seeds", {}).get("WHEAT", 0))
    plant_tasks = empty[:available_seeds] if planting_open else []
    return [urgent_water, daily_water, harvest, plant_tasks]


def _coordinated_crop_actions(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    farmer_action: list[str] | None,
    blocked_tiles: set[tuple[int, int]] | None = None,
) -> tuple[list[str], list[list[str]]]:
    positions = [
        tuple(farm["farmer"]),
        *(tuple(position) for position in farm.get("hands", [])),
    ]
    actions: list[list[str] | None] = [farmer_action] + [
        None for _ in farm.get("hands", [])
    ]
    reserved: set[tuple[int, int]] = set()
    task_groups = _task_groups(day, farm, private, blocked_tiles)

    for unit_index, position in enumerate(positions):
        if actions[unit_index] is not None:
            continue
        group = next(
            (
                tasks
                for tasks in task_groups
                if any(target not in reserved for target, _ in tasks)
            ),
            [],
        )
        available = [task for task in group if task[0] not in reserved]
        if not available:
            actions[unit_index] = ["PASS"]
            continue
        target, task_action = min(
            available,
            key=lambda task: (
                _distance(position, task[0]),
                task[0][1],
                task[0][0],
            ),
        )
        reserved.add(target)
        actions[unit_index] = _act_at_or_move(
            position,
            target,
            task_action,
        )

    resolved = [action or ["PASS"] for action in actions]
    return resolved[0], resolved[1:]


def _hire_orders(
    hour: int,
    farm: dict[str, Any],
    target_daily_hands: int = TARGET_DAILY_HANDS,
) -> list[list[str]]:
    if hour != 0:
        return []
    missing = max(0, target_daily_hands - len(farm.get("hands", [])))
    return [["HIRE"] for _ in range(missing)]


def decide(
    observation: dict[str, Any],
    target_wheat_tiles: int = TARGET_WHEAT_TILES,
) -> dict[str, Any]:
    """Run one goose and two daily hands at a chosen wheat workload."""
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
    farmer_action = _setup_action(farm, private)
    if farmer_action is None:
        farmer_action = _service_action(day, farm, private)
    farmer_action, hands_actions = _coordinated_crop_actions(
        day,
        farm,
        private,
        farmer_action,
    )

    market = [
        *_hire_orders(hour, farm),
        *_animal_market_orders(farm, private),
        *baseline["market"],
    ]
    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market,
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run twelve wheat plots and one goose with two cheap daily hands."""
    return decide(observation)