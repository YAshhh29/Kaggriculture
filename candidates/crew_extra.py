"""Actions for hired hands that a recorded route has no instructions for.

A recorded route cannot use workers it did not plan for, yet extra hands are
cheap: the n-th hire of a day costs fib(n) coins (144 for the twelfth) against
about 37 coins earned per job-turn. This module gives each such hand a simple
policy that only has to beat standing still:
  * do the job under its feet if there is one,
  * otherwise step toward the tile whose job is worth most after the walk,
  * and skip tiles the route's own hands are working this turn.
Jobs are valued at what the engine pays for them.
"""

from __future__ import annotations

from typing import Any

MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
PASS: list[str] = ["PASS"]


def _tile(tiles, x: int, y: int):
    if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
        return tiles[y][x]
    return "LOCKED"


def _price(observation: dict[str, Any], item: str) -> float:
    market = observation.get("market") or {}
    prices = market.get("prices") or {}
    try:
        return float(prices.get(item, 1.0))
    except (TypeError, ValueError):
        return 1.0


def job_here(observation: dict[str, Any], tile, carrying: dict,
             day: int) -> tuple[float, list] | None:
    """What the engine would pay for acting on this tile, and the action.

    Only jobs an extra hand can do without co-ordination: nothing that
    consumes a seed the route has counted, nothing that spends the manure
    it means to spread, nothing that moves stock between pens.
    """
    if not isinstance(tile, dict):
        return None
    kind = tile.get("kind")

    if "animal" in tile:
        animal = str(tile.get("animal", ""))
        product = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}.get(animal)
        held = int(tile.get("yield_units", 0) or 0)
        # Harvest first: produce left on an animal at max_held is produce
        # the next production day cannot add to.
        if product and held > 0:
            return (_price(observation, product) * held, ["HARVEST"])
        # A hungry animal is worth more than anything else on the board --
        # two unfed days and it walks off the farm for good.
        if (not tile.get("fed_today")
                and int(carrying.get("WHEAT", 0) or 0) > 0):
            risk = int(tile.get("consecutive_unfed", 0) or 0)
            return (900.0 if risk >= 1 else 120.0, ["FEED"])
        if tile.get("fertilizer_available"):
            return (_price(observation, "FERTILIZER"),
                    ["COLLECT_FERTILIZER"])
        if not tile.get("cared_today") and tile.get("fed_today"):
            return (_price(observation, product or "EGG") * 0.5, ["CARE"])
        return None

    if kind == "PLANT":
        crop = str(tile.get("crop", ""))
        units = int(tile.get("yield_units", 0) or 0)
        dry = int(tile.get("consecutive_unwatered", 0) or 0)
        if units > 0:
            return (_price(observation, crop) * units, ["HARVEST"])
        # A plant one day dry dies tonight and takes everything it has
        # accrued with it.
        if dry >= 1 and not tile.get("watered_today"):
            return (60.0, ["WATER"])
        if not tile.get("watered_today"):
            return (12.0, ["WATER"])
        return None

    return None


def step_toward(here: tuple[int, int], there: tuple[int, int]) -> list:
    """One step, longest axis first, so the walk is a straight line."""
    dx, dy = there[0] - here[0], there[1] - here[1]
    if abs(dx) >= abs(dy):
        if dx:
            return ["EAST"] if dx > 0 else ["WEST"]
        if dy:
            return ["SOUTH"] if dy > 0 else ["NORTH"]
    else:
        if dy:
            return ["SOUTH"] if dy > 0 else ["NORTH"]
        if dx:
            return ["EAST"] if dx > 0 else ["WEST"]
    return list(PASS)


def actions_for(observation: dict[str, Any], seat: int, first: int,
                taken: set[tuple[int, int]], walk_cost: float = 14.0) -> list:
    """An action for every hand from index `first` onward.

    `taken` carries the tiles the route's own hands are working this turn,
    so the spare crew fills gaps instead of colliding with the plan.
    """
    farms = observation.get("farms") or []
    if seat >= len(farms):
        return []
    farm = farms[seat]
    tiles = farm.get("tiles") or []
    hands = farm.get("hands") or []
    private = observation.get("private") or {}
    bags = private.get("inventories") or []
    day = int(observation.get("day", 0))

    out: list = []
    for index in range(first, len(hands)):
        spot = hands[index]
        if not isinstance(spot, (list, tuple)) or len(spot) < 2:
            out.append(list(PASS))
            continue
        here = (int(spot[0]), int(spot[1]))
        # inventories is farmer-first, so hand `index` is inventory index+1.
        carrying = bags[index + 1] if index + 1 < len(bags) else {}

        standing = job_here(observation, _tile(tiles, here[0], here[1]),
                            carrying, day)
        if standing is not None and here not in taken:
            taken.add(here)
            out.append(list(standing[1]))
            continue

        best = None
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if (x, y) in taken:
                    continue
                offer = job_here(observation, _tile(tiles, x, y), carrying,
                                 day)
                if offer is None:
                    continue
                walk = abs(x - here[0]) + abs(y - here[1])
                worth = offer[0] - walk * walk_cost
                if worth <= 0:
                    continue
                if best is None or worth > best[0]:
                    best = (worth, (x, y))
        if best is None:
            out.append(list(PASS))
            continue
        taken.add(best[1])
        out.append(step_toward(here, best[1]))
    return out
