"""Hire workers beyond a fixed route's recorded crew and give them service work.

A route only instructs the hands it recorded, so extra hands on the farm
receive no instruction from it. This layer hires them only after the
route's own hiring for the day is done (the roster is append-ordered, so
the route's instructions still reach its own workers) and schedules them by
coins per turn on tiles no route worker occupies: watering, harvesting,
animal care, feeding, collecting fertilizer and digging weeds.

Measured result: not used by any shipped agent. Two extra hands on a strong
route cut reward by about 32%, and the extra hands passed on about 76% of
their turns because the farm had no spare work for them.
"""

from __future__ import annotations

from typing import Any

from core.routing import distance, step_toward
from candidates.economics import (
    care_value,
    collect_fertilizer_value,
    feed_value,
    harvest_value,
    live_price,
    water_value,
)
from rl.runtime import AgentAction, Baseline, clone_action

SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))
LIVESTOCK = ("COW", "SHEEP", "GOOSE")
WORKING_STOCK = ("FERTILIZER", "WHEAT")
MAX_ORDERS = 10
# Hard ceiling on the crew, whatever the route's own hand list says.
ROSTER_CAP = 16
_FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987)


def _shed_adjacent(position: tuple[int, int]) -> bool:
    return any(
        abs(position[0] - x) + abs(position[1] - y) <= 1 for x, y in SHED_TILES
    )


def _positions(farm: dict[str, Any]) -> list[tuple[int, int]]:
    units = [farm.get("farmer"), *(farm.get("hands") or [])]
    out: list[tuple[int, int]] = []
    for unit in units:
        if isinstance(unit, (list, tuple)) and len(unit) >= 2:
            out.append((int(unit[0]), int(unit[1])))
        else:
            out.append((0, 0))
    return out


def _owned(tiles: list[list[Any]], x: int, y: int) -> bool:
    return (
        0 <= y < len(tiles)
        and 0 <= x < len(tiles[y])
        and tiles[y][x] != "LOCKED"
    )


def tile_jobs(
    observation: dict[str, Any],
    tile: Any,
    day: int,
    inventory: dict[str, int],
    at_shed: bool,
    hungry: int,
) -> list[tuple[float, list[Any]]]:
    """Every job a surplus worker could do here, priced in coins.

    Deliberately narrow. `PLANT` and `BUILD` are excluded because they
    would spend seed and ground the route has budgeted for itself, and a
    surplus worker taking the last strawberry seed is a worker stealing
    from the agent it is meant to be helping. What is left is service work
    -- watering, tending animals, collecting -- which only ever adds.
    """
    jobs: list[tuple[float, list[Any]]] = []
    if at_shed and hungry > 0 and int(inventory.get("WHEAT", 0)) <= 0:
        shed = (observation.get("private") or {}).get("shed") or {}
        if int(shed.get("WHEAT", 0)) > 0:
            jobs.append((40.0, ["PICKUP", "WHEAT", min(4, hungry)]))
    if not isinstance(tile, dict):
        return jobs
    kind = tile.get("kind")
    if kind == "PLANT":
        if not tile.get("watered_today"):
            jobs.append((water_value(observation, tile, day), ["WATER"]))
        if int(tile.get("yield_units", 0)) > 0:
            jobs.append((harvest_value(observation, tile, day), ["HARVEST"]))
    elif "animal" in tile:
        if tile.get("fertilizer_available"):
            jobs.append(
                (collect_fertilizer_value(observation, tile),
                 ["COLLECT_FERTILIZER"])
            )
        if int(tile.get("yield_units", 0)) > 0:
            jobs.append((harvest_value(observation, tile, day), ["HARVEST"]))
        if not tile.get("cared_today"):
            jobs.append((care_value(observation, tile, day), ["CARE"]))
        if not tile.get("fed_today") and int(inventory.get("WHEAT", 0)) > 0:
            jobs.append((feed_value(observation, tile, day), ["FEED"]))
    elif kind == "WEED":
        jobs.append((25.0, ["DIG"]))
    return [(value, act) for value, act in jobs if value > 0]


def build_extra_hands_agent(
    baseline: Baseline,
    *,
    extra: int = 2,
    start_day: int = 10,
    cash_floor: float = 12000.0,
    travel_exponent: float = 3.0,
    sell_surplus: bool = True,
) -> Baseline:
    """Wrap a route so it works a larger crew than it recorded.

    `extra` surplus hands are hired once the farm is past `start_day` and
    holding more than `cash_floor`, and they are scheduled by coins per
    turn with travel discounted by `travel_exponent` -- the same rule and
    the same exponent Agent E measured best (10.8e).
    """

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
        money = float(farm.get("money", 0.0))
        positions = _positions(farm)
        on_roster = len(positions) - 1  # hands, excluding the farmer
        route_hands = len(action["hands"])

        # --- hire the surplus, after whatever the route hired ----------
        orders = [list(o) for o in action["market"]]
        # Wait until the route has finished hiring for the day. `hands` is
        # append-ordered and wiped every night, so a hire of ours placed
        # while the route is still filling its own crew lands *before* its
        # remaining hires -- every later instruction then addresses the
        # wrong worker. That mistake cost 137,000 coins a game when this
        # layer was first tried, so the condition is deliberately strict:
        # the route must be issuing no HIRE this turn, and the roster must
        # already match the crew its action is written for.
        route_hiring = any(
            isinstance(o, list) and o and o[0] == "HIRE" for o in orders
        )
        # An absolute cap on the roster, not a relative one. The route's
        # own hand-list length swings between 0 and 12 across a day as it
        # hires, so a rule phrased as "route_hands + extra" re-arms every
        # time the two happen to line up: the roster ran away to nineteen
        # hands, 409 hire orders against the route's 280, and a daily wage
        # near 13,000 coins that bankrupted the farm.
        cap = min(ROSTER_CAP, route_hands + extra)
        if (
            day >= start_day
            and money > cash_floor
            and not route_hiring
            and on_roster >= route_hands
            and on_roster < cap
            and extra > 0
            and len(orders) < MAX_ORDERS
        ):
            budget = money - cash_floor
            for step in range(cap - on_roster):
                if len(orders) >= MAX_ORDERS:
                    break
                cost = _FIB[min(on_roster + step, len(_FIB) - 1)]
                if budget < cost:
                    break
                orders.append(["HIRE"])
                budget -= cost

        # --- drive whatever surplus is already standing ----------------
        surplus = list(range(route_hands + 1, len(positions)))
        if surplus:
            private = observation.get("private") or {}
            inventories = private.get("inventories") or []
            hungry = sum(
                1
                for row in tiles
                for t in row
                if isinstance(t, dict) and "animal" in t
                and not t.get("fed_today")
            )
            # Never target a tile a route worker occupies: it may be about
            # to act there, and two workers on one tile waste a turn.
            claimed = {positions[i] for i in range(route_hands + 1)}
            filled: list[list[Any]] = []
            for worker in surplus:
                position = positions[worker]
                inventory = (
                    {str(k): int(v) for k, v in inventories[worker].items()}
                    if worker < len(inventories)
                    and isinstance(inventories[worker], dict)
                    else {}
                )
                best_score = 0.0
                best: list[Any] = ["PASS"]
                best_cell: tuple[int, int] | None = None
                for y in range(len(tiles)):
                    for x in range(len(tiles[y])):
                        if (x, y) in claimed or not _owned(tiles, x, y):
                            continue
                        travel = distance(position, (x, y))
                        for value, act in tile_jobs(
                            observation, tiles[y][x], day, inventory,
                            _shed_adjacent((x, y)), hungry,
                        ):
                            score = value / (travel + 1.0) ** travel_exponent
                            if score > best_score:
                                best_score = score
                                best_cell = (x, y)
                                best = (
                                    list(act) if travel == 0
                                    else step_toward(position, (x, y), list(act))
                                )
                if best_cell is not None:
                    claimed.add(best_cell)
                filled.append(best)
            action["hands"] = list(action["hands"]) + filled

        # --- sell what the surplus produced ----------------------------
        # The route's own sell orders were sized for the crop its own crew
        # brings in, so the extra production would otherwise sit in the
        # shed and score nothing at all.
        if sell_surplus and len(orders) < MAX_ORDERS:
            shed = {
                str(k): int(v)
                for k, v in ((observation.get("private") or {}).get("shed")
                             or {}).items()
            }
            already = {
                str(o[1]) for o in orders
                if len(o) >= 2 and o[0] == "SELL"
            }
            keep_wheat = min(24, hungry_total(tiles) * 2)
            for item, quantity in sorted(
                shed.items(), key=lambda kv: -live_price(observation, kv[0])
            ):
                if len(orders) >= MAX_ORDERS:
                    break
                if quantity <= 0 or item in LIVESTOCK or item in already:
                    continue
                sellable = quantity
                if item == "WHEAT":
                    sellable = max(0, quantity - keep_wheat)
                if sellable > 0:
                    orders.append(["SELL", item, sellable])

        action["market"] = orders[:MAX_ORDERS]
        return action

    return decide


def hungry_total(tiles: list[list[Any]]) -> int:
    """Animals standing on the farm, which is what the feed reserve sizes to."""
    return sum(
        1 for row in tiles for tile in row
        if isinstance(tile, dict) and "animal" in tile
    )
