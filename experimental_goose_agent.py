"""Development-only one-goose policy wrapped around the frozen v9 crop loop."""

from __future__ import annotations

from typing import Any

from main import decide


GOOSE_COST = 300
TARGET_WHEAT_TILES = 6
LAST_WHEAT_PLANTING_DAY = 21


def _positions(
    tiles: list[list[Any]],
    predicate: Any,
) -> list[tuple[int, int]]:
    return [
        (x, y)
        for y, row in enumerate(tiles)
        for x, tile in enumerate(row)
        if predicate(tile)
    ]


def _shed_access_tiles(board_size: int) -> list[tuple[int, int]]:
    half = board_size // 2
    return [
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    ]


def _move_toward(
    origin: tuple[int, int],
    target: tuple[int, int],
) -> list[str]:
    origin_x, origin_y = origin
    target_x, target_y = target
    if target_x < origin_x:
        return ["WEST"]
    if target_x > origin_x:
        return ["EAST"]
    if target_y < origin_y:
        return ["NORTH"]
    return ["SOUTH"]


def _carried(private: dict[str, Any], item: str) -> int:
    inventories = private.get("inventories", [])
    if not inventories or not isinstance(inventories[0], dict):
        return 0
    return int(inventories[0].get(item, 0))


def _goose_position(
    tiles: list[list[Any]],
) -> tuple[int, int] | None:
    positions = _positions(
        tiles,
        lambda tile: (
            isinstance(tile, dict) and tile.get("animal") == "GOOSE"
        ),
    )
    return positions[0] if positions else None


def _coop_position(
    tiles: list[list[Any]],
) -> tuple[int, int] | None:
    positions = _positions(
        tiles,
        lambda tile: (
            isinstance(tile, dict) and tile.get("kind") == "COOP"
        ),
    )
    return positions[0] if positions else None


def _setup_action(
    farm: dict[str, Any],
    private: dict[str, Any],
) -> list[str] | None:
    tiles = farm["tiles"]
    farmer = tuple(farm["farmer"])
    coop = _coop_position(tiles)
    if _goose_position(tiles) is not None:
        return None

    target = _shed_access_tiles(len(tiles))[0]
    if coop is None:
        return ["BUILD_COOP"] if farmer == target else _move_toward(
            farmer,
            target,
        )

    if _carried(private, "GOOSE") > 0:
        return ["PLACE", "GOOSE"] if farmer == coop else _move_toward(
            farmer,
            coop,
        )

    if int(private.get("shed", {}).get("GOOSE", 0)) > 0:
        if farmer in _shed_access_tiles(len(tiles)):
            return ["PICKUP", "GOOSE", 1]
        return _move_toward(farmer, target)

    return None


def _service_action(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
) -> list[str] | None:
    tiles = farm["tiles"]
    farmer = tuple(farm["farmer"])
    goose_position = _goose_position(tiles)
    if goose_position is None:
        return None
    goose = tiles[goose_position[1]][goose_position[0]]

    feed_due = (
        not goose.get("fed_today", False)
        and int(goose.get("consecutive_unfed", 0)) >= 1
    )
    if feed_due:
        if _carried(private, "WHEAT") > 0:
            return ["FEED"] if farmer == goose_position else _move_toward(
                farmer,
                goose_position,
            )
        if int(private.get("shed", {}).get("WHEAT", 0)) > 0:
            if farmer in _shed_access_tiles(len(tiles)):
                return ["PICKUP", "WHEAT", 1]
            return _move_toward(
                farmer,
                _shed_access_tiles(len(tiles))[0],
            )

    if day < 29 and goose.get("fertilizer_available", False):
        return (
            ["COLLECT_FERTILIZER"]
            if farmer == goose_position
            else _move_toward(farmer, goose_position)
        )

    if int(goose.get("yield_units", 0)) >= 4:
        return ["HARVEST"] if farmer == goose_position else _move_toward(
            farmer,
            goose_position,
        )

    return None


def _animal_market_orders(
    farm: dict[str, Any],
    private: dict[str, Any],
) -> list[list[Any]]:
    orders: list[list[Any]] = []
    shed = private.get("shed", {})
    tiles = farm["tiles"]
    has_goose = _goose_position(tiles) is not None
    goose_in_transit = (
        int(shed.get("GOOSE", 0)) > 0
        or _carried(private, "GOOSE") > 0
    )
    buying_goose = not (has_goose or goose_in_transit)

    if buying_goose and float(farm["money"]) >= GOOSE_COST:
        orders.append(["BUY_ANIMAL", "GOOSE", 1])

    goose_position = _goose_position(tiles)
    feed_due = False
    if goose_position is not None:
        goose = tiles[goose_position[1]][goose_position[0]]
        feed_due = (
            not goose.get("fed_today", False)
            and int(goose.get("consecutive_unfed", 0)) >= 1
        )
    if feed_due:
        available_feed = int(shed.get("WHEAT", 0)) + _carried(
            private,
            "WHEAT",
        )
        if available_feed == 0:
            orders.append(["BUY_PRODUCT", "WHEAT", 1])

    for item in ("EGG", "FERTILIZER"):
        quantity = int(shed.get(item, 0))
        if quantity > 0:
            orders.append(["SELL", item, quantity])
    return orders


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run one near-shed goose alongside the frozen six-wheat policy."""
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    baseline = decide(
        observation,
        target_wheat_tiles=TARGET_WHEAT_TILES,
        last_planting_day=LAST_WHEAT_PLANTING_DAY,
    )

    farmer_action = _setup_action(farm, private)
    if farmer_action is None:
        farmer_action = _service_action(
            int(observation["day"]),
            farm,
            private,
        )
    if farmer_action is None:
        farmer_action = baseline["farmer"]

    market = [
        *_animal_market_orders(farm, private),
        *baseline["market"],
    ]
    return {"farmer": farmer_action, "hands": [], "market": market}