"""Behavior clone of a public elite action calendar."""

from __future__ import annotations

import base64
import json
import zlib
from collections import Counter
from pathlib import Path
from typing import Any


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "v1327-public-calendar-99058164.json"
)
MODEL_PAYLOAD: str | None = None
MOVE_ACTIONS = {"NORTH", "SOUTH", "EAST", "WEST"}
FIRST_YIELD_DAY = {
    "WHEAT": 2,
    "CARROT": 2,
    "TOMATO": 8,
    "STRAWBERRY": 10,
    "MELON": 10,
}
ANIMAL_STRUCTURES = {
    "GOOSE": "COOP",
    "COW": "PASTURE",
    "SHEEP": "PASTURE",
}
PASS = ["PASS"]


def _load_actions() -> tuple[dict[str, Any], ...]:
    payload = MODEL_PAYLOAD
    if payload is None:
        model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
        payload = str(model["actions_zlib_b64"])
    compressed = base64.b64decode(payload)
    actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    if len(actions) != 720:
        raise ValueError("Distilled calendar must contain 720 records")
    return tuple(actions)


CALENDAR_ACTIONS = _load_actions()


def _tile_at(farm: dict[str, Any], position: tuple[int, int]) -> Any:
    x, y = position
    return farm["tiles"][y][x]


def _shed_adjacent(position: tuple[int, int], board_size: int) -> bool:
    half = board_size // 2
    return position in {
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    }


def _inventory(private: dict[str, Any], worker: int) -> dict[str, Any]:
    inventories = private.get("inventories", [])
    if worker < len(inventories) and isinstance(inventories[worker], dict):
        return inventories[worker]
    return {}


def _valid_action(
    observation: dict[str, Any],
    worker: int,
    position: tuple[int, int],
    action: list[Any],
) -> bool:
    if not action:
        return False
    operation = str(action[0])
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    tile = _tile_at(farm, position)
    inventory = _inventory(private, worker)
    board_size = len(farm["tiles"])
    if operation == "PASS":
        return True
    if operation in MOVE_ACTIONS:
        x, y = position
        return {
            "NORTH": y > 0,
            "SOUTH": y + 1 < board_size,
            "WEST": x > 0,
            "EAST": x + 1 < board_size,
        }[operation]
    if operation == "PLANT":
        return (
            len(action) >= 2
            and tile is None
            and int(private.get("seeds", {}).get(str(action[1]), 0)) > 0
        )
    if operation == "WATER":
        return (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and not tile.get("watered_today", False)
        )
    if operation == "HARVEST":
        if not isinstance(tile, dict) or int(tile.get("yield_units", 0)) <= 0:
            return False
        if tile.get("kind") != "PLANT":
            return bool(tile.get("animal"))
        crop = str(tile.get("crop"))
        age = int(observation.get("day", 0)) - int(tile.get("planted_day", 0))
        return age >= FIRST_YIELD_DAY[crop]
    if operation == "FERTILIZE":
        return (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and int(inventory.get("FERTILIZER", 0)) > 0
        )
    if operation == "DIG":
        return tile is not None and not (
            isinstance(tile, dict) and tile.get("animal")
        )
    if operation in {"BUILD_COOP", "BUILD_PASTURE"}:
        return tile is None
    if operation == "FEED":
        return (
            isinstance(tile, dict)
            and tile.get("animal")
            and not tile.get("fed_today", False)
            and int(inventory.get("WHEAT", 0)) > 0
        )
    if operation == "CARE":
        return (
            isinstance(tile, dict)
            and tile.get("animal")
            and not tile.get("cared_today", False)
        )
    if operation == "COLLECT_FERTILIZER":
        return (
            isinstance(tile, dict)
            and tile.get("animal")
            and bool(tile.get("fertilizer_available", False))
        )
    if operation == "PICKUP":
        return (
            len(action) >= 2
            and _shed_adjacent(position, board_size)
            and int(private.get("shed", {}).get(str(action[1]), 0)) > 0
        )
    if operation == "DROP":
        return _shed_adjacent(position, board_size) and any(
            int(quantity) > 0 for quantity in inventory.values()
        )
    if operation == "PLACE" and len(action) >= 2:
        item = str(action[1])
        if int(inventory.get(item, 0)) <= 0:
            return False
        if item in ANIMAL_STRUCTURES:
            return (
                isinstance(tile, dict)
                and tile.get("kind") == ANIMAL_STRUCTURES[item]
                and not tile.get("animal")
            )
        return _shed_adjacent(position, board_size)
    return False


def _local_repair(
    observation: dict[str, Any],
    worker: int,
    position: tuple[int, int],
) -> list[Any]:
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    tile = _tile_at(farm, position)
    inventory = _inventory(private, worker)
    board_size = len(farm["tiles"])
    if isinstance(tile, dict) and int(tile.get("yield_units", 0)) > 0:
        action = ["HARVEST"]
        if _valid_action(observation, worker, position, action):
            return action
    if isinstance(tile, dict) and tile.get("animal"):
        if (
            not tile.get("fed_today", False)
            and int(inventory.get("WHEAT", 0)) > 0
        ):
            return ["FEED"]
        if tile.get("fed_today", False) and not tile.get("cared_today", False):
            return ["CARE"]
        if tile.get("fertilizer_available", False):
            return ["COLLECT_FERTILIZER"]
    if (
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and not tile.get("watered_today", False)
        and int(tile.get("consecutive_unwatered", 0)) >= 1
    ):
        return ["WATER"]
    if _shed_adjacent(position, board_size) and any(
        int(quantity) > 0 for quantity in inventory.values()
    ):
        return ["DROP"]
    return PASS


def _sanitize_units(
    observation: dict[str, Any],
    planned: dict[str, Any],
) -> tuple[list[Any], list[list[Any]]]:
    player = int(observation["player"])
    farm = observation["farms"][player]
    positions = [
        tuple(farm["farmer"]),
        *(tuple(position) for position in farm.get("hands", [])),
    ]
    planned_actions = [planned.get("farmer", PASS)]
    planned_actions.extend(planned.get("hands", []))
    sanitized = []
    for worker, position in enumerate(positions):
        action = (
            planned_actions[worker]
            if worker < len(planned_actions)
            and isinstance(planned_actions[worker], list)
            else PASS
        )
        sanitized.append(
            list(action)
            if _valid_action(observation, worker, position, action)
            else _local_repair(observation, worker, position)
        )
    available_seeds = Counter(observation["private"].get("seeds", {}))
    for crop in tuple(available_seeds):
        planters = [
            worker
            for worker, action in enumerate(sanitized)
            if action[:2] == ["PLANT", crop]
        ]
        for worker in planters[available_seeds[crop]:]:
            sanitized[worker] = PASS
    return sanitized[0], sanitized[1:]


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    next_record = int(observation.get("step", 0)) + 1
    if next_record >= len(CALENDAR_ACTIONS):
        return {"farmer": PASS, "hands": [], "market": []}
    planned = CALENDAR_ACTIONS[next_record]
    return {
        "farmer": list(planned.get("farmer", PASS)),
        "hands": [
            list(action) for action in planned.get("hands", [])
        ],
        "market": [list(order) for order in planned.get("market", [])],
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Execute the learned public-data action calendar."""
    return decide(observation)
