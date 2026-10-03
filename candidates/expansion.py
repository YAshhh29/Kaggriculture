"""Buy the fourth quadrant with a route's idle cash and farm it with new hands.

A route-following agent fills its ground by about day 12 while its cash sits
idle. `build_expansion_agent` wraps such a route: it buys the locked fourth
quadrant from surplus, hires hands beyond the recorded roster, and has them
plant, build and work only inside the new quadrant with their own seed and
livestock, so they never contend with the route's crew or budget.
Measured and not used by any shipped agent: reward is lower with any extra
hands (148,328 with none, 131,934 with one), because the 25 new tiles cannot
be developed in the seventeen days left before cash is counted at step 720.
"""

from __future__ import annotations

from typing import Any

from core.routing import distance, step_toward
from candidates.economics import (
    ANIMALS,
    CROPS,
    LAST_DAY,
    care_value,
    collect_fertilizer_value,
    crop_can_mature,
    feed_value,
    harvest_value,
    live_price,
    plant_value,
    water_value,
)
from rl.runtime import AgentAction, Baseline, clone_action

BOARD = 10
HALF = BOARD // 2
SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))
LIVESTOCK = ("COW", "SHEEP", "GOOSE")
MAX_ORDERS = 10
FOURTH_QUADRANT_COST = 4000
_FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597)


def in_new_quadrant(x: int, y: int) -> bool:
    """The south-east quadrant, which is always the fourth one unlocked.

    `LAND_ORDER` in the simulator is NE, SW, SE, so a farm holding three
    quadrants is missing exactly this one.
    """
    return x >= HALF and y >= HALF


def _positions(farm: dict[str, Any]) -> list[tuple[int, int]]:
    units = [farm.get("farmer"), *(farm.get("hands") or [])]
    out: list[tuple[int, int]] = []
    for unit in units:
        if isinstance(unit, (list, tuple)) and len(unit) >= 2:
            out.append((int(unit[0]), int(unit[1])))
        else:
            out.append((0, 0))
    return out


def _shed_adjacent(position: tuple[int, int]) -> bool:
    return any(
        abs(position[0] - x) + abs(position[1] - y) <= 1 for x, y in SHED_TILES
    )


def _stream_value(observation: dict[str, Any], animal: str, day: int) -> float:
    spec = ANIMALS[animal]
    horizon = max(0, LAST_DAY - day - int(spec["first"]))
    if horizon <= 0:
        return 0.0
    rate = (spec["interval"] + 1.0) / max(1, spec["interval"])
    return (
        live_price(observation, spec["product"]) * rate * horizon * 0.5
        + live_price(observation, "FERTILIZER") * max(0, LAST_DAY - day)
    )


def quadrant_jobs(
    observation: dict[str, Any],
    tile: Any,
    day: int,
    inventory: dict[str, int],
    seeds: dict[str, int],
    shed: dict[str, int],
    at_shed: bool,
    want_pen: bool,
    herd: str,
    hungry: int,
) -> list[tuple[float, list[Any]]]:
    """Every job worth doing on one tile of the new quadrant, in coins."""
    jobs: list[tuple[float, list[Any]]] = []
    if at_shed:
        if int(shed.get(herd, 0)) > 0 and not any(
            int(inventory.get(a, 0)) > 0 for a in LIVESTOCK
        ):
            jobs.append(
                (_stream_value(observation, herd, day), ["PICKUP", herd, 1])
            )
        if (
            hungry > 0
            and int(inventory.get("WHEAT", 0)) <= 0
            and int(shed.get("WHEAT", 0)) > 0
        ):
            jobs.append((60.0, ["PICKUP", "WHEAT", min(4, hungry)]))
        banked = sum(
            live_price(observation, item) * quantity
            for item, quantity in inventory.items()
            if item not in LIVESTOCK and item not in ("WHEAT", "FERTILIZER")
            and quantity > 0
        )
        if banked > 0:
            jobs.append((banked, ["DROP"]))

    if tile is None:
        if want_pen:
            jobs.append(
                (_stream_value(observation, herd, day) * 0.5,
                 ["BUILD_COOP" if ANIMALS[herd]["structure"] == "COOP"
                  else "BUILD_PASTURE"])
            )
        best_crop, best_value = None, 0.0
        for crop in CROPS:
            if int(seeds.get(crop, 0)) <= 0 or not crop_can_mature(crop, day, day):
                continue
            value = plant_value(observation, crop, day)
            if value > best_value:
                best_crop, best_value = crop, value
        if best_crop is not None:
            jobs.append((best_value, ["PLANT", best_crop]))
        return [(v, a) for v, a in jobs if v > 0]

    if not isinstance(tile, dict):
        return [(v, a) for v, a in jobs if v > 0]

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
    elif kind in ("PASTURE", "COOP"):
        for name in LIVESTOCK:
            if ANIMALS[name]["structure"] != kind:
                continue
            if int(inventory.get(name, 0)) > 0:
                jobs.append(
                    (_stream_value(observation, name, day), ["PLACE", name])
                )
    elif kind == "WEED":
        jobs.append((30.0, ["DIG"]))
    return [(v, a) for v, a in jobs if v > 0]


def build_expansion_agent(
    baseline: Baseline,
    raw_route: Baseline | None = None,
    *,
    extra_hands: int = 4,
    roster_cap: int = 16,
    expand_day: int = 11,
    land_reserve: float = 6000.0,
    spend_floor: float = 4000.0,
    pens: int = 4,
    herd: str = "COW",
    travel_exponent: float = 2.0,
) -> Baseline:
    """Wrap a route so its idle capital buys and works a fourth quadrant.

    `raw_route` is the *unwrapped* tape. It is needed because Candidate A
    and B pad the hand list out to the live roster, so the wrapped action
    always has exactly as many hand instructions as there are hands -- and
    "hands the route does not control" cannot be read off it. Asking the
    raw tape how many hands it recorded is the only reliable way to know
    which workers are ours to drive.
    """
    crew = {"size": 0}

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
        unlocked = len(farm.get("unlocked_quadrants") or [])
        positions = _positions(farm)
        on_roster = len(positions) - 1
        if raw_route is not None:
            try:
                recorded = raw_route(observation)
                crew["size"] = max(
                    crew["size"], len(recorded.get("hands") or [])
                )
            except Exception:
                pass
        route_hands = (
            min(crew["size"], len(action["hands"]))
            if raw_route is not None else len(action["hands"])
        )
        private = observation.get("private") or {}
        shed = {str(k): int(v) for k, v in (private.get("shed") or {}).items()}
        seeds = {str(k): int(v) for k, v in (private.get("seeds") or {}).items()}
        inventories = private.get("inventories") or []
        orders = [list(o) for o in action["market"]]
        route_hiring = any(
            isinstance(o, list) and o and o[0] == "HIRE" for o in orders
        )

        # ---- 1. buy the fourth quadrant out of genuine surplus --------
        if (
            unlocked == 3
            and day >= expand_day
            and money >= FOURTH_QUADRANT_COST + land_reserve
            and len(orders) < MAX_ORDERS
        ):
            orders.append(["BUY_LAND"])
            money -= FOURTH_QUADRANT_COST

        opened = unlocked >= 4
        new_tiles = [
            (x, y)
            for y in range(len(tiles))
            for x in range(len(tiles[y]))
            if in_new_quadrant(x, y) and tiles[y][x] != "LOCKED"
        ]

        if opened and new_tiles:
            standing = [
                tiles[y][x] for x, y in new_tiles
                if isinstance(tiles[y][x], dict)
            ]
            our_pens = sum(
                1 for t in standing
                if t.get("kind") in ("PASTURE", "COOP") or "animal" in t
            )
            our_animals = sum(1 for t in standing if "animal" in t)
            hungry = sum(
                1 for t in standing
                if "animal" in t and not t.get("fed_today")
            )
            empty_pens = sum(
                1 for t in standing
                if t.get("kind") == ANIMALS[herd]["structure"]
                and "animal" not in t
            )
            open_ground = sum(
                1 for x, y in new_tiles if tiles[y][x] is None
            )

            # ---- 2. staff it ------------------------------------------
            cap = min(roster_cap, route_hands + extra_hands)
            if (
                not route_hiring
                and on_roster >= route_hands
                and on_roster < cap
                and money > spend_floor
                and len(orders) < MAX_ORDERS
            ):
                budget = money - spend_floor
                for step in range(cap - on_roster):
                    if len(orders) >= MAX_ORDERS:
                        break
                    cost = _FIB[min(on_roster + step, len(_FIB) - 1)]
                    if budget < cost:
                        break
                    orders.append(["HIRE"])
                    budget -= cost
                    money -= cost

            # ---- 3. stock it, from surplus only -----------------------
            if money > spend_floor and len(orders) < MAX_ORDERS:
                for crop in ("WHEAT", "CARROT", "MELON"):
                    if len(orders) >= MAX_ORDERS or open_ground <= 0:
                        break
                    if not crop_can_mature(crop, day, day):
                        continue
                    want = min(open_ground, 10) - int(seeds.get(crop, 0))
                    cost = CROPS[crop]["seed"]
                    if want > 0 and money - spend_floor > cost * want:
                        orders.append(["BUY_SEED", crop, want])
                        money -= cost * want
            if (
                money > spend_floor + ANIMALS[herd]["cost"]
                and empty_pens > int(shed.get(herd, 0))
                and day <= LAST_DAY - ANIMALS[herd]["first"] - 1
                and len(orders) < MAX_ORDERS
            ):
                orders.append(["BUY_ANIMAL", herd, 1])
                money -= ANIMALS[herd]["cost"]

            # ---- 4. work it, with the hands the route does not own ----
            surplus = list(range(route_hands + 1, len(positions)))
            if surplus:
                want_pen = (
                    our_pens < pens
                    and our_pens <= our_animals + int(shed.get(herd, 0))
                    and day <= LAST_DAY - ANIMALS[herd]["first"] - 2
                )
                claimed: set[tuple[int, int]] = set()
                filled: list[list[Any]] = []
                budgeted = dict(seeds)
                for worker in surplus:
                    position = positions[worker]
                    inventory = (
                        {str(k): int(v)
                         for k, v in inventories[worker].items()}
                        if worker < len(inventories)
                        and isinstance(inventories[worker], dict)
                        else {}
                    )
                    best_score = 0.0
                    best: list[Any] = ["PASS"]
                    best_cell: tuple[int, int] | None = None
                    best_job: list[Any] = ["PASS"]
                    for x, y in new_tiles:
                        if (x, y) in claimed:
                            continue
                        travel = distance(position, (x, y))
                        for value, act in quadrant_jobs(
                            observation, tiles[y][x], day, inventory,
                            budgeted, shed, _shed_adjacent((x, y)),
                            want_pen, herd, hungry,
                        ):
                            score = value / (travel + 1.0) ** travel_exponent
                            if score > best_score:
                                best_score = score
                                best_cell = (x, y)
                                best_job = list(act)
                                best = (
                                    list(act) if travel == 0
                                    else step_toward(
                                        position, (x, y), list(act)
                                    )
                                )
                    if best_cell is not None:
                        claimed.add(best_cell)
                    if len(best_job) > 1 and best_job[0] == "PLANT":
                        crop = str(best_job[1])
                        budgeted[crop] = budgeted.get(crop, 0) - 1
                    filled.append((worker, best))
                # Overwrite in place rather than append. Candidate A and B
                # have already padded the hand list out to the live roster,
                # so appending produces a list longer than the crew and
                # every instruction in the tail is silently discarded --
                # which is why the surplus sat on PASS for a whole game.
                hands = list(action["hands"])
                for worker, act in filled:
                    index = worker - 1
                    while len(hands) <= index:
                        hands.append(["PASS"])
                    hands[index] = act
                action["hands"] = hands

        action["market"] = orders[:MAX_ORDERS]
        return action

    return decide
