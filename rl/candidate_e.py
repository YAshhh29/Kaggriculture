"""Candidate E: an agent that decides for itself what this town wants.

Every earlier candidate replays a recorded game. Section 9v proved that
architecture cannot be taught to adapt -- a tape's actions are coupled
through cash, shed space and pickup timing, so even swapping a cow for a
sheep bankrupts it and strands pastures empty. And section 9v measured
what that costs: adapting production to the town's demand draw correlates
+0.672 with buying sheep in a wool town for teams at 2850+, +0.323 in the
middle band, and **+0.000 below 2400**, where every tape necessarily sits.

So E generates its own actions. Two ideas drive it.

**Value, not priority.** Each turn every worker is scored against every
reachable job using `rl.economics`, which prices a job in coins from the
simulator's own constants -- a watering is worth the yield unit it adds
(two if fertilized), feeding a starving animal is worth its whole
remaining production stream, and a crop that cannot mature before the
season ends is worth nothing at all. Jobs are then ranked by coins per
turn spent, travel included, so a worker never idles while paid work
exists and never walks past a good job to reach a better one further
away. Section 9q measured our old engine idling 985 turns a game against
a tape's 322; that is the gap this closes.

**Demand, not habit.** The herd target and the crop choice come from
`rl.demand`, which reads `observation["town"]["unlocked_shops"]` and
computes exactly what the town will still absorb. In a game where
YARN_STORE was drawn twice, wool ends at 239 a unit and E builds sheep; in
a game where it never appeared, wool ends at 1 and E builds cows instead.
That is the behaviour the top of the ladder shows and no clone can.

Deliberately conservative choices, each for a measured reason:

* three quadrants, never four -- section 9i measured 4-quadrant players
  winning 8.3% against 51.2%, and the top 500 use three essentially
  always;
* wheat is grown, not bought, and reserved for feed before sale, because
  winners sell less wheat and buy less of it (section 9m, p=0.031);
* melon is capped, because it appears in no shop and the town absorbs
  only ~30 a game (section 9u) however much is grown.
"""

from __future__ import annotations

from typing import Any

from core.routing import distance, step_toward
from rl.demand import ANIMAL_PRODUCT, remaining_demand
from rl.economics import (
    ANIMALS,
    CROPS,
    LAST_DAY,
    care_value,
    collect_fertilizer_value,
    crop_can_mature,
    feed_value,
    fertilize_value,
    harvest_value,
    live_price,
    plant_rate_value,
    plant_value,
    water_value,
)
from rl.runtime import AgentAction


PASS: list[str] = ["PASS"]
BOARD = 10
MELON_CAP = 12
TARGET_HANDS = 11
TARGET_PASTURES = 14
LAND_SURPLUS = 1500.0
RESCUE_SHARE = 0.45
LIQUIDITY_FLOOR = 1500.0
_FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377)
MIN_CASH = 250.0
SEED_BUFFER = 12
FEED_RESERVE_PER_ANIMAL = 4


# --------------------------------------------------------------------------
# state helpers
# --------------------------------------------------------------------------

def _farm(observation: dict[str, Any]) -> dict[str, Any]:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    if player < len(farms) and isinstance(farms[player], dict):
        return farms[player]
    return {}


def _tiles(farm: dict[str, Any]) -> list[list[Any]]:
    return farm.get("tiles") or []


def _positions(farm: dict[str, Any]) -> list[tuple[int, int]]:
    units = [farm.get("farmer"), *(farm.get("hands") or [])]
    out = []
    for u in units:
        if isinstance(u, (list, tuple)) and len(u) >= 2:
            out.append((int(u[0]), int(u[1])))
        else:
            out.append((0, 0))
    return out


def _inventory(observation: dict[str, Any], worker: int) -> dict[str, int]:
    private = observation.get("private") or {}
    inventories = private.get("inventories") or []
    if worker < len(inventories) and isinstance(inventories[worker], dict):
        return {str(k): int(v) for k, v in inventories[worker].items()}
    return {}


def _shed(observation: dict[str, Any]) -> dict[str, int]:
    private = observation.get("private") or {}
    return {str(k): int(v) for k, v in (private.get("shed") or {}).items()}


def _seeds(observation: dict[str, Any]) -> dict[str, int]:
    private = observation.get("private") or {}
    return {str(k): int(v) for k, v in (private.get("seeds") or {}).items()}


def shed_tiles() -> list[tuple[int, int]]:
    half = BOARD // 2
    return [
        (half - 1, half - 1), (half, half - 1),
        (half - 1, half), (half, half),
    ]


def _owned(tiles: list[list[Any]], x: int, y: int) -> bool:
    return (
        0 <= y < len(tiles)
        and 0 <= x < len(tiles[y])
        and tiles[y][x] != "LOCKED"
    )


# --------------------------------------------------------------------------
# planning
# --------------------------------------------------------------------------

def preferred_herd(observation: dict[str, Any]) -> str:
    """Which pasture animal this town's demand actually rewards."""
    remaining = remaining_demand(observation)
    best, best_value = "COW", -1.0
    for animal in ("COW", "SHEEP"):
        product = ANIMAL_PRODUCT[animal]
        value = remaining.get(product, 0.0) * live_price(observation, product)
        if value > best_value:
            best, best_value = animal, value
    return best


def crop_ranking(observation: dict[str, Any], day: int) -> list[str]:
    """Crops worth planting now, best first.

    Three factors, and the third one matters more than it looks:

    * coins per tile-day, so a cheap fast crop is not out-ranked by an
      expensive slow one merely because its gross value is larger;
    * the town's remaining appetite, so a crop nobody buys is never
      planted however good its base price;
    * **time to first cash, while cash is short.** By rate alone melon
      wins at ~118 coins per tile-day, but it first yields on day 10.
      Planting it with 30 coins in hand froze this agent at 30 coins for
      ten days -- no herd, no land, no compounding -- while wheat would
      have paid on day 2 and recycled every five. When the purse is thin,
      payback speed is worth more than rate.
    """
    remaining = remaining_demand(observation)
    money = float(_farm(observation).get("money", 0.0))
    thin = money < LIQUIDITY_FLOOR
    scored: list[tuple[float, str]] = []
    for crop in CROPS:
        if not crop_can_mature(crop, day, day):
            continue
        value = plant_rate_value(observation, crop, day)
        if value <= 0:
            continue
        appetite = min(1.0, remaining.get(crop, 0.0) / 60.0)
        score = value * (0.25 + 0.75 * appetite)
        if thin:
            score *= 3.0 / (3.0 + CROPS[crop]["first"])
        scored.append((score, crop))
    scored.sort(reverse=True)
    return [c for _, c in scored]


# --------------------------------------------------------------------------
# job scoring
# --------------------------------------------------------------------------

# Fertilizer and wheat are working stock, not produce: fertilizer is
# carried to a plant, wheat is carried to an animal. Counting them as
# bankable made a worker pick a unit up and immediately value dropping
# it again, producing a 327-pickup / 323-drop oscillation that did no
# work at all.
WORKING_STOCK = ("FERTILIZER", "WHEAT")
LIVESTOCK = ("COW", "SHEEP", "GOOSE")


def carried_value(
    observation: dict[str, Any],
    inventory: dict[str, int],
) -> float:
    """What this worker is carrying is worth, if banked and sold."""
    total = 0.0
    for item, quantity in inventory.items():
        if item in LIVESTOCK or item in WORKING_STOCK:
            continue
        total += live_price(observation, item) * max(0, quantity)
    return total


def _jobs_for_tile(
    observation: dict[str, Any],
    tile: Any,
    day: int,
    inventory: dict[str, int],
    *,
    at_shed: bool,
    want_pasture: bool,
    herd: str,
    fertilizable: int = 0,
    hungry: int = 0,
) -> list[tuple[float, list[Any]]]:
    """Every job this worker could do standing on this tile, priced."""
    jobs: list[tuple[float, list[Any]]] = []

    if at_shed:
        # Banking is what turns a harvest into money; without it goods sit
        # in a worker's hands and are never sold at all.
        banked = carried_value(observation, inventory)
        if banked > 0:
            jobs.append((banked, ["DROP"]))
        shed = _shed(observation)
        if int(shed.get(herd, 0)) > 0 and int(inventory.get(herd, 0)) == 0:
            # An animal bought into the shed is worth its whole production
            # stream once it reaches a pasture.
            product = ANIMAL_PRODUCT[herd]
            jobs.append(
                (
                    live_price(observation, product)
                    * max(0, LAST_DAY - day)
                    / max(1, ANIMALS[herd]["interval"]),
                    ["PICKUP", herd, 1],
                )
            )
        if (
            int(shed.get("FERTILIZER", 0)) > 0
            and int(inventory.get("FERTILIZER", 0)) == 0
            and fertilizable > 0
        ):
            jobs.append(
                (live_price(observation, "FERTILIZER") * 1.5,
                 ["PICKUP", "FERTILIZER", 1])
            )
        if (
            int(shed.get("WHEAT", 0)) > 0
            and int(inventory.get("WHEAT", 0)) < 2
            and hungry > 0
        ):
            product = ANIMAL_PRODUCT[herd]
            preserved = (
                live_price(observation, product)
                * max(0, LAST_DAY - day)
                / max(1, ANIMALS[herd]["interval"])
            )
            jobs.append(
                (preserved * min(hungry, 2) * 0.5, ["PICKUP", "WHEAT", 4])
            )

    if tile is None:
        if want_pasture:
            product = ANIMAL_PRODUCT[herd]
            jobs.append(
                (
                    live_price(observation, product)
                    * max(0, LAST_DAY - day)
                    / max(2, ANIMALS[herd]["interval"] * 2),
                    ["BUILD_PASTURE"],
                )
            )
        return [(v, a) for v, a in jobs if v > 0]

    if not isinstance(tile, dict):
        return [(v, a) for v, a in jobs if v > 0]

    kind = tile.get("kind")
    if kind == "PLANT":
        if not tile.get("watered_today"):
            jobs.append((water_value(observation, tile, day), ["WATER"]))
        if int(inventory.get("FERTILIZER", 0)) > 0:
            jobs.append(
                (fertilize_value(observation, tile, day), ["FERTILIZE"])
            )
        if int(tile.get("yield_units", 0)) > 0:
            jobs.append((harvest_value(observation, tile, day), ["HARVEST"]))
    elif "animal" in tile:
        if int(tile.get("yield_units", 0)) > 0:
            jobs.append((harvest_value(observation, tile, day), ["HARVEST"]))
        if not tile.get("fed_today") and int(inventory.get("WHEAT", 0)) > 0:
            jobs.append((feed_value(observation, tile, day), ["FEED"]))
        if not tile.get("cared_today"):
            jobs.append((care_value(observation, tile, day), ["CARE"]))
        if tile.get("fertilizer_available"):
            jobs.append(
                (
                    collect_fertilizer_value(observation, tile),
                    ["COLLECT_FERTILIZER"],
                )
            )
    elif kind == "PASTURE" and "animal" not in tile:
        held = int(inventory.get(herd, 0))
        if held > 0:
            product = ANIMAL_PRODUCT[herd]
            jobs.append(
                (
                    live_price(observation, product)
                    * max(0, LAST_DAY - day)
                    / max(1, ANIMALS[herd]["interval"]),
                    ["PLACE", herd],
                )
            )
    elif kind == "WEED":
        jobs.append((25.0, ["DIG"]))
    return [(v, a) for v, a in jobs if v > 0]


def _plant_jobs(
    observation: dict[str, Any],
    day: int,
    ranking: list[str],
    seeds: dict[str, int],
    melons_planted: int,
) -> tuple[float, list[Any]] | None:
    for crop in ranking:
        if seeds.get(crop, 0) <= 0:
            continue
        if crop == "MELON" and melons_planted >= MELON_CAP:
            continue
        return (plant_value(observation, crop, day), ["PLANT", crop])
    return None


# --------------------------------------------------------------------------
# market
# --------------------------------------------------------------------------

def _market_orders(
    observation: dict[str, Any],
    day: int,
    step: int,
    herd: str,
    ranking: list[str],
) -> list[list[Any]]:
    """Spend in a fixed priority order out of one running budget.

    Independent per-line thresholds deadlocked this agent twice: seeds
    gated behind 300 coins meant it never planted and so never earned,
    and an ungated land rule spent the entire 3,000 opening on two
    quadrants it had no labour to farm. Priority order with a shared
    running balance avoids both, because every later item only sees what
    the earlier ones left behind.

    Order: labour, then seed for fast crops, then feed, then livestock,
    then land last -- land is the only purchase that produces nothing by
    itself, so it is bought out of genuine surplus.
    """
    farm = _farm(observation)
    budget = float(farm.get("money", 0.0))
    hands = len(farm.get("hands") or [])
    tiles = _tiles(farm)
    shed = _shed(observation)
    seeds = _seeds(observation)
    orders: list[list[Any]] = []

    plants = sum(
        1 for row in tiles for t in row
        if isinstance(t, dict) and t.get("kind") == "PLANT"
    )
    animals_on_farm = sum(
        1 for row in tiles for t in row
        if isinstance(t, dict) and "animal" in t
    )
    empty_pasture = sum(
        1 for row in tiles for t in row
        if isinstance(t, dict)
        and t.get("kind") == "PASTURE"
        and "animal" not in t
    )
    open_ground = sum(
        1
        for y in range(len(tiles))
        for x in range(len(tiles[y]))
        if _owned(tiles, x, y) and tiles[y][x] is None
    )

    # 0. Sell first. The market list is capped at ten orders, so anything
    #    placed after the purchases gets truncated away -- selling last
    #    produced 1,506 harvests and 76 units sold, with the shed
    #    overflowing its 100-unit cap and the surplus discarded. Proceeds
    #    also fund everything below, which is why this runs first.
    wheat_needed = animals_on_farm * FEED_RESERVE_PER_ANIMAL
    for item, quantity in sorted(shed.items()):
        if quantity <= 0 or item in ("COW", "SHEEP", "GOOSE"):
            continue
        sellable = quantity
        if item == "WHEAT":
            sellable = max(0, quantity - wheat_needed)
        if sellable > 0:
            orders.append(["SELL", item, sellable])
            budget += live_price(observation, item) * sellable

    # 1. Labour. The nth hire of a day costs fib(n) with a multiplier of 1,
    #    so the first hands are close to free and each one multiplies every
    #    other purchase. Nothing outranks this.
    if hands < TARGET_HANDS:
        for index in range(min(3, TARGET_HANDS - hands)):
            cost = _FIB[min(index + hands, len(_FIB) - 1)]
            if budget < cost + 30:
                break
            orders.append(["HIRE"])
            budget -= cost

    # 2. Seed, cheapest-and-fastest first. Ranking is by coins per
    #    tile-day, so wheat leads early and the slow premium crops only
    #    appear once there is ground and time to spare.
    for crop in ranking[:3]:
        if open_ground <= 0:
            break
        have = seeds.get(crop, 0)
        cost = CROPS[crop]["seed"]
        want = min(SEED_BUFFER - have, open_ground)
        affordable = int(min(want, budget // max(1, cost * 2)))
        if affordable > 0:
            orders.append(["BUY_SEED", crop, affordable])
            budget -= cost * affordable

    # 3. Feed, so the animals already owned keep producing.
    wheat_needed = animals_on_farm * FEED_RESERVE_PER_ANIMAL
    wheat_have = shed.get("WHEAT", 0)
    if animals_on_farm and wheat_have < wheat_needed and budget > 400:
        want = min(6, wheat_needed - wheat_have)
        if want > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", want])
            budget -= 40 * want

    # 4. Livestock for pens that already exist and are still worth filling.
    cost = ANIMALS[herd]["cost"]
    in_shed = int(shed.get(herd, 0))
    if (
        empty_pasture > in_shed
        and budget > cost + 200
        and day <= LAST_DAY - ANIMALS[herd]["first"] - 1
    ):
        want = int(min(2, empty_pasture - in_shed, budget // cost))
        if want > 0:
            orders.append(["BUY_ANIMAL", herd, want])
            budget -= cost * want

    # 5. Land, last and only out of surplus, and only once the ground we
    #    already own is genuinely in use. Three quadrants, never four
    #    (section 9i).
    unlocked = len(farm.get("unlocked_quadrants") or [])
    price = {1: 1000, 2: 2000}.get(unlocked)
    if (
        unlocked < 3
        and price
        and budget > price + LAND_SURPLUS
        and open_ground <= 4
        and plants >= 12 * unlocked
    ):
        orders.append(["BUY_LAND"])
        budget -= price

    return orders[:10]


# --------------------------------------------------------------------------
# the agent
# --------------------------------------------------------------------------

def decide(observation: dict[str, Any]) -> AgentAction:
    farm = _farm(observation)
    tiles = _tiles(farm)
    if not tiles:
        return {"farmer": PASS, "hands": [], "market": []}

    day = int(observation.get("day", 0))
    step = int(observation.get("step", 0))
    positions = _positions(farm)
    shed = _shed(observation)
    seeds = _seeds(observation)
    herd = preferred_herd(observation)
    ranking = crop_ranking(observation, day)

    melons = sum(
        1
        for row in tiles
        for t in row
        if isinstance(t, dict) and t.get("crop") == "MELON"
    )
    pastures = sum(
        1
        for row in tiles
        for t in row
        if isinstance(t, dict) and t.get("kind") == "PASTURE"
    )
    open_tiles = sum(
        1
        for y in range(len(tiles))
        for x in range(len(tiles[y]))
        if _owned(tiles, x, y) and tiles[y][x] is None
    )
    # Livestock pays back over the rest of the season, so a pasture built
    # late never earns out. Build them while there is time, and only while
    # there is still open ground for crops too.
    # A pasture is worth nothing without an animal standing in it, and the
    # animal costs several times what the ground does. Building ahead of
    # what we can stock spent the whole purse on empty pens and cost the
    # land purchases as well, so build only one pen ahead of the herd and
    # only with an animal's price already in hand.
    money = float(farm.get("money", 0.0))
    animals_now = sum(
        1
        for row in tiles
        for t in row
        if isinstance(t, dict) and "animal" in t
    )
    want_pasture = (
        pastures < TARGET_PASTURES
        and pastures <= animals_now + 1
        and money > ANIMALS[herd]["cost"] * 2
        and day <= LAST_DAY - ANIMALS[herd]["first"] - 2
    )

    fertilizable = sum(
        1
        for row in tiles
        for t in row
        if isinstance(t, dict)
        and t.get("kind") == "PLANT"
        and int(t.get("fertilized_until_day", -1)) < day
    )
    hungry = sum(
        1
        for row in tiles
        for t in row
        if isinstance(t, dict) and "animal" in t and not t.get("fed_today")
    )

    claimed: set[tuple[int, int]] = set()
    actions: list[list[Any]] = [None] * len(positions)  # type: ignore[list-item]
    shed_set = set(shed_tiles())
    unassigned = set(range(len(positions)))

    # ---- reserved capacity -------------------------------------------
    # A plant that misses two consecutive days becomes a weed and forfeits
    # everything it would still have produced; an animal unfed for two days
    # escapes. Both are cheap to prevent and ruinous to ignore, but pricing
    # them high enough to win a value auction made the agent monomaniacal
    # (it watered all game and banked nothing, reward 0). So rescue work is
    # given guaranteed labour up front, capped so it can never consume the
    # whole crew, and everything else competes for what is left.
    rescue: list[tuple[int, int]] = []
    for y in range(len(tiles)):
        for x in range(len(tiles[y])):
            if not _owned(tiles, x, y):
                continue
            tile = tiles[y][x]
            if not isinstance(tile, dict):
                continue
            if (
                tile.get("kind") == "PLANT"
                and not tile.get("watered_today")
                and int(tile.get("consecutive_unwatered", 0)) >= 1
            ):
                rescue.append((x, y))
            elif (
                "animal" in tile
                and not tile.get("fed_today")
                and int(tile.get("consecutive_unfed", 0)) >= 1
            ):
                rescue.append((x, y))

    reserve_cap = max(1, int(len(positions) * RESCUE_SHARE))
    for target in sorted(
        rescue, key=lambda c: min(distance(p, c) for p in positions)
    )[:reserve_cap]:
        if not unassigned:
            break
        worker = min(unassigned, key=lambda w: distance(positions[w], target))
        tile = tiles[target[1]][target[0]]
        job = ["FEED"] if "animal" in tile else ["WATER"]
        if job == ["FEED"] and int(
            _inventory(observation, worker).get("WHEAT", 0)
        ) <= 0:
            # Redirect to fetch feed rather than skip: a starving animal
            # forfeits its whole remaining production stream.
            if int(_shed(observation).get("WHEAT", 0)) <= 0:
                continue
            position = positions[worker]
            depot = min(shed_set, key=lambda c: distance(position, c))
            actions[worker] = (
                ["PICKUP", "WHEAT", 4]
                if position == depot
                else step_toward(position, depot, ["PICKUP", "WHEAT", 4])
            )
            unassigned.discard(worker)
            continue
        position = positions[worker]
        actions[worker] = (
            list(job)
            if position == target
            else step_toward(position, target, list(job))
        )
        claimed.add(target)
        unassigned.discard(worker)

    for worker in sorted(unassigned):
        position = positions[worker]
        inventory = _inventory(observation, worker)
        best_score = 0.0
        best_action: list[Any] = list(PASS)
        best_target: tuple[int, int] | None = None

        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if not _owned(tiles, x, y):
                    continue
                if (x, y) in claimed:
                    continue
                tile = tiles[y][x]
                travel = distance(position, (x, y))
                options = _jobs_for_tile(
                    observation,
                    tile,
                    day,
                    inventory,
                    at_shed=(x, y) in shed_set,
                    want_pasture=want_pasture,
                    herd=herd,
                    fertilizable=fertilizable,
                    hungry=hungry,
                )
                if tile is None:
                    planted = _plant_jobs(
                        observation, day, ranking, seeds, melons
                    )
                    if planted is not None:
                        options = options + [planted]
                for value, act in options:
                    score = value / (travel + 1.0)
                    if score > best_score:
                        best_score = score
                        best_target = (x, y)
                        best_action = (
                            list(act)
                            if travel == 0
                            else step_toward(position, (x, y), list(act))
                        )

        if best_target is not None:
            claimed.add(best_target)
        actions[worker] = best_action

    for worker, act in enumerate(actions):
        if act is None:
            actions[worker] = list(PASS)

    return {
        "farmer": actions[0],
        "hands": actions[1:],
        "market": _market_orders(observation, day, step, herd, ranking),
    }


def agent(observation: dict[str, Any]) -> AgentAction:
    """Candidate E: demand-driven, value-scheduled, self-generated play."""
    return decide(observation)
