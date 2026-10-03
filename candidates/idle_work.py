"""Fill a route's PASS turns with fertilizing, watering and fertilizer pickups.

Rules fire only where the wrapped route already emitted PASS, so they never
displace a scheduled action, move a worker or desynchronise a step-indexed
route. In priority order: fertilize a wheat or carrot plant the worker is
standing on (when holding fertilizer), water a plant inside its yield
window, and pick up one fertilizer when idling on a shed tile.

Crop yield-window constants are transcribed from the simulator's CROPS table.
"""

from __future__ import annotations

from typing import Any

from rl.runtime import AgentAction, Baseline, clone_action


# crop -> (first_yield_day, max_yield_day, max_yield, ongoing)
CROPS: dict[str, tuple[int, int, int, bool]] = {
    "WHEAT": (2, 4, 6, False),
    "CARROT": (2, 3, 4, False),
    "TOMATO": (8, 8, 4, True),
    "STRAWBERRY": (10, 10, 4, True),
    "MELON": (10, 12, 6, False),
}
FERTILIZE_TARGETS = ("WHEAT", "CARROT")
PASS: list[str] = ["PASS"]


def _shed_tiles(board_size: int) -> set[tuple[int, int]]:
    half = board_size // 2
    return {
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    }


def _tile_at(tiles: list[list[Any]], x: int, y: int) -> Any:
    if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
        return tiles[y][x]
    return None


def _in_yield_window(tile: dict[str, Any], day: int) -> bool:
    crop = tile.get("crop")
    spec = CROPS.get(str(crop))
    if spec is None:
        return False
    first, max_yield_day, max_yield, ongoing = spec
    age = day - int(tile.get("planted_day", day))
    if ongoing:
        return age >= first
    window_start = (max_yield_day + 1) // 2
    if not (window_start <= age <= max_yield_day):
        return False
    return int(tile.get("yield_units", 0)) < max_yield


def _fertilizable(tile: Any, day: int) -> bool:
    if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
        return False
    if str(tile.get("crop")) not in FERTILIZE_TARGETS:
        return False
    if int(tile.get("fertilized_until_day", -1)) >= day:
        return False
    spec = CROPS.get(str(tile.get("crop")))
    if spec is None:
        return False
    first, max_yield_day, _max_yield, ongoing = spec
    age = day - int(tile.get("planted_day", day))
    if ongoing:
        return age >= first
    # Worth fertilizing from just before the window opens: the boost is
    # consumed by waterings inside it and lasts three days.
    return age <= max_yield_day


def _waterable(tile: Any, day: int) -> bool:
    if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
        return False
    if tile.get("watered_today"):
        return False
    return _in_yield_window(tile, day)


def build_idle_work_agent(
    baseline: Baseline,
    *,
    fertilize: bool = True,
    water: bool = True,
    restock: bool = True,
) -> Baseline:
    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        player = int(observation.get("player", 0))
        farms = observation.get("farms") or []
        if player >= len(farms) or not isinstance(farms[player], dict):
            return action
        farm = farms[player]
        tiles = farm.get("tiles") or []
        if not tiles:
            return action
        day = int(observation.get("day", 0))
        private = observation.get("private") or {}
        shed = private.get("shed") or {}
        inventories = private.get("inventories") or []
        shed_tiles = _shed_tiles(len(tiles))
        shed_fertilizer = int(shed.get("FERTILIZER", 0))

        positions = [farm.get("farmer"), *(farm.get("hands") or [])]
        planned = [action["farmer"], *action["hands"]]

        for index, (position, unit_action) in enumerate(
            zip(positions, planned)
        ):
            if not (isinstance(unit_action, list) and unit_action):
                continue
            if unit_action[0] != "PASS":
                continue
            if not (isinstance(position, (list, tuple)) and len(position) >= 2):
                continue
            x, y = int(position[0]), int(position[1])
            tile = _tile_at(tiles, x, y)
            inventory = (
                inventories[index]
                if index < len(inventories)
                and isinstance(inventories[index], dict)
                else {}
            )
            held = int(inventory.get("FERTILIZER", 0))

            if fertilize and held > 0 and _fertilizable(tile, day):
                planned[index] = ["FERTILIZE"]
                continue
            if water and _waterable(tile, day):
                planned[index] = ["WATER"]
                continue
            if (
                restock
                and held == 0
                and shed_fertilizer > 0
                and (x, y) in shed_tiles
            ):
                planned[index] = ["PICKUP", "FERTILIZER", 1]
                shed_fertilizer -= 1
                continue

        return {
            "farmer": planned[0],
            "hands": planned[1:],
            "market": action["market"],
        }

    return decide
