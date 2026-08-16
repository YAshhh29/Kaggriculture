"""A deterministic, submission-ready baseline agent for Kaggriculture."""

from __future__ import annotations

from typing import Any


TARGET_WHEAT_TILES = 6
WHEAT_SEED_COST = 10
WHEAT_MAX_YIELD_AGE = 4
LAST_WHEAT_PLANTING_DAY = 24
MINIMUM_WHEAT_SALE_PRICE = 35
MAXIMUM_WHEAT_HOLDINGS = 72
WHEAT_LIQUIDATION_DAY = 25


def _market_orders(
    day: int,
    market: dict[str, Any],
    farm: dict[str, Any],
    private: dict[str, Any],
    target_wheat_tiles: int,
    last_planting_day: int | None,
    minimum_wheat_sale_price: int | None,
    maximum_wheat_holdings: int | None,
    wheat_liquidation_day: int | None,
) -> list[list[Any]]:
    orders: list[list[Any]] = []

    wheat_in_shed = int(private.get("shed", {}).get("WHEAT", 0))
    wheat_price = int(market.get("prices", {}).get("WHEAT", 0))
    price_is_good = (
        minimum_wheat_sale_price is None
        or wheat_price >= minimum_wheat_sale_price
    )
    inventory_is_full = (
        maximum_wheat_holdings is not None
        and wheat_in_shed >= maximum_wheat_holdings
    )
    liquidation_started = (
        wheat_liquidation_day is not None
        and day >= wheat_liquidation_day
    )
    if wheat_in_shed > 0 and (
        price_is_good or inventory_is_full or liquidation_started
    ):
        orders.append(["SELL", "WHEAT", wheat_in_shed])

    planted_wheat = sum(
        1
        for row in farm["tiles"]
        for tile in row
        if _is_wheat(tile)
    )
    wheat_seeds = int(private.get("seeds", {}).get("WHEAT", 0))
    seeds_needed = max(0, target_wheat_tiles - planted_wheat - wheat_seeds)
    affordable_seeds = int(float(farm["money"]) // WHEAT_SEED_COST)
    seeds_to_buy = min(seeds_needed, affordable_seeds)

    if seeds_to_buy > 0 and _planting_is_open(day, last_planting_day):
        orders.append(["BUY_SEED", "WHEAT", seeds_to_buy])

    return orders


def _farmer_action(
    day: int,
    farm: dict[str, Any],
    private: dict[str, Any],
    last_planting_day: int | None,
    harvest_watered_current_first: bool,
) -> list[str]:
    tiles = farm["tiles"]
    position = tuple(farm["farmer"])

    urgent_water = _positions(
        tiles,
        lambda tile: (
            _is_wheat(tile)
            and not tile.get("watered_today", False)
            and int(tile.get("consecutive_unwatered", 0)) >= 1
        ),
    )
    if urgent_water:
        target = _nearest(position, urgent_water)
        return _act_at_or_move(position, target, ["WATER"])

    current_tile = tiles[position[1]][position[0]]
    if (
        harvest_watered_current_first
        and _is_mature_wheat(current_tile, day)
        and current_tile.get("watered_today", False)
    ):
        return ["HARVEST"]

    daily_water = _positions(
        tiles,
        lambda tile: _is_wheat(tile) and not tile.get("watered_today", False),
    )
    if daily_water:
        target = _nearest(position, daily_water)
        return _act_at_or_move(position, target, ["WATER"])

    mature_wheat = _positions(
        tiles,
        lambda tile: _is_mature_wheat(tile, day),
    )
    if mature_wheat:
        target = _nearest(position, mature_wheat)
        return _act_at_or_move(position, target, ["HARVEST"])

    wheat_seeds = int(private.get("seeds", {}).get("WHEAT", 0))
    if wheat_seeds > 0 and _planting_is_open(day, last_planting_day):
        empty_tiles = _positions(tiles, lambda tile: tile is None)
        if empty_tiles:
            return _act_at_or_move(
                position,
                _nearest(position, empty_tiles),
                ["PLANT", "WHEAT"],
            )

    return ["PASS"]


def _planting_is_open(day: int, last_planting_day: int | None) -> bool:
    return last_planting_day is None or day <= last_planting_day


def _is_wheat(tile: Any) -> bool:
    return (
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "WHEAT"
    )


def _is_mature_wheat(tile: Any, day: int) -> bool:
    return (
        _is_wheat(tile)
        and day - int(tile["planted_day"]) >= WHEAT_MAX_YIELD_AGE
        and int(tile.get("yield_units", 0)) > 0
    )


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


def _nearest(
    origin: tuple[int, int],
    positions: list[tuple[int, int]],
) -> tuple[int, int]:
    origin_x, origin_y = origin
    return min(
        positions,
        key=lambda position: (
            abs(position[0] - origin_x) + abs(position[1] - origin_y),
            position[1],
            position[0],
        ),
    )


def _act_at_or_move(
    origin: tuple[int, int],
    target: tuple[int, int],
    action: list[str],
) -> list[str]:
    if origin == target:
        return action

    origin_x, origin_y = origin
    target_x, target_y = target
    if target_x < origin_x:
        return ["WEST"]
    if target_x > origin_x:
        return ["EAST"]
    if target_y < origin_y:
        return ["NORTH"]
    return ["SOUTH"]


def decide(
    observation: dict[str, Any],
    target_wheat_tiles: int = TARGET_WHEAT_TILES,
    last_planting_day: int | None = LAST_WHEAT_PLANTING_DAY,
    harvest_watered_current_first: bool = False,
    minimum_wheat_sale_price: int | None = MINIMUM_WHEAT_SALE_PRICE,
    maximum_wheat_holdings: int | None = MAXIMUM_WHEAT_HOLDINGS,
    wheat_liquidation_day: int | None = WHEAT_LIQUIDATION_DAY,
) -> dict[str, Any]:
    """Choose actions using a specific wheat workload target."""
    player = observation["player"]
    farm = observation["farms"][player]
    private = observation["private"]

    day = observation["day"]
    market = _market_orders(
        day,
        observation["market"],
        farm,
        private,
        target_wheat_tiles,
        last_planting_day,
        minimum_wheat_sale_price,
        maximum_wheat_holdings,
        wheat_liquidation_day,
    )
    farmer_action = _farmer_action(
        day,
        farm,
        private,
        last_planting_day,
        harvest_watered_current_first,
    )

    return {"farmer": farmer_action, "hands": [], "market": market}


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Choose actions for the submission's default six-plot policy."""
    return decide(observation)
