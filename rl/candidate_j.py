"""Candidate J -- a farm scheduled by coins per worker-turn.

Nothing here is replayed. Every action is decided from the observation.

WHY THIS AGENT EXISTS
=====================
Two of our agents were measured against each other in six live games. They
work the same board with the same rules, and the difference is not effort:

    G    7,239 worker turns, 3,011 of them real work (41.6%), score  73,286
    H2   6,745 worker turns, 3,445 of them real work (51.1%), score 121,202

G hires *more* hands and walks 921 turns further; H2 plants more, harvests
more, places more animals, and earns 65% more money. Per turn of real work,
G returns 24.3 coins and H2 returns 35.2. The gap is spread across every
good -- strawberry -17,780, wheat -8,798, milk -6,668, manure -6,702, melon
-4,748 -- and not concentrated in one clever line, which rules out a crop
trick as the answer.

So the scarce resource is a worker-turn, and the agent that spends each one
on the most valuable thing available wins. That is the whole design.

WHAT IS DIFFERENT FROM OUR EARLIER AGENT
----------------------------------------
G ranked jobs by fixed priority bands: feed 10000, harvest 6000, wheat 4000,
and so on. Bands cannot compare a job to the job it displaces, so G would
walk eight tiles to water a plant while a ripe tile stood beside a worker.

J values every job in coins, divides by the turns it costs including the
walk, and takes the best. Three things stay hard constraints rather than
prices, because the engine makes them cliffs rather than slopes:

  * an animal that has already missed a meal escapes tonight if unfed
    (`consecutive_unfed >= 2` in _daily_refresh_animals), forfeiting its
    whole remaining output;
  * an ongoing crop that goes unwatered turns to weed and the tile is lost;
  * goods still in hand at the close are worth zero, so the last trips home
    and the final sale outrank everything.

MEASURED FACTS THIS AGENT IS BUILT ON
-------------------------------------
* Glut curves differ per good. Units from equilibrium to the price floor:
  WOOL 59, STRAWBERRY 62, MILK 76, MELON 158, and WHEAT and EGG effectively
  never, because their curves are logarithmic. Fragile books are metered.
* `_process_market` walks both players' orders by index at the same
  pre-commit inventory, a failed unit aborts its whole order, and orders past
  the tenth are dropped. Sales go first, inventory-priced buys next.
* Hiring is a daily rental on a fibonacci curve that resets each night: ten
  hands cost 143 coins for the day. A hand is only worth hiring while it can
  still work, so hiring stops after hour 2.
* FERTILIZER is in no shop basket and is excluded from the town centre's
  daily consumption, so nothing in the game consumes it: its price only
  decays. It is still worth collecting, because a unit spread on a watered
  wheat tile inside its window is worth two extra wheat.
* The town eats every four steps, so the price steps up at `step % 4 == 1`.
"""

from __future__ import annotations

from typing import Any

from core.routing import distance, step_toward
from rl.demand import remaining_demand
from rl.economics import ANIMALS, CROPS
from rl.market import MARKET_PARAMS, inventory_of, price_at
from rl.runtime import AgentAction

PASS: list[str] = ["PASS"]
BOARD = 10
TURNS = 24
LAST_DAY = 29
LAST_ACT_STEP = 718
MAX_ORDERS = 10
SHED_CAP = 100

# Goods whose price collapses if sold in bulk, with the number of units from
# equilibrium to the floor. Sales of these are metered.
FRAGILE = {"WOOL": 59, "STRAWBERRY": 62, "MILK": 76, "MELON": 158}
FRAGILE_PER_TURN = 3
ANIMAL_HOME = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}

# A worker-turn is the unit of account. This is what one is worth when the
# farm has nothing better to do; jobs below it are not worth the walk.
IDLE_TURN_VALUE = 8.0
# Walking is charged at the same rate, so a job four tiles away must be worth
# four turns more than one underfoot.
WALK_COST = 1.0
# How much a worker prefers the job it is already walking to. Measured on our
# other agent: without it, 17.1% of travelling turns ended in a change of
# destination, and committing was worth +5,142 coins a game.
COMMIT_BONUS = 3.0

_EN_ROUTE: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}


# --- reading the world -------------------------------------------------

def _farm(observation: dict[str, Any]) -> dict[str, Any]:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    return farms[player] if player < len(farms) and isinstance(
        farms[player], dict) else {}


def _positions(farm: dict[str, Any]) -> list[tuple[int, int]]:
    out = []
    for unit in [farm.get("farmer"), *(farm.get("hands") or [])]:
        if isinstance(unit, (list, tuple)) and len(unit) >= 2:
            out.append((int(unit[0]), int(unit[1])))
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
    return [(half - 1, half - 1), (half, half - 1),
            (half - 1, half), (half, half)]


def _on_shed(x: int, y: int) -> bool:
    return (x, y) in set(shed_tiles())


def _owned(tiles: list[list[Any]], x: int, y: int) -> bool:
    return (0 <= y < len(tiles) and 0 <= x < len(tiles[y])
            and tiles[y][x] != "LOCKED")


def census(tiles: list[list[Any]], day: int) -> dict[str, Any]:
    """One pass over the board: what exists, and what is in danger."""
    out: dict[str, Any] = {
        "free": 0, "owned": 0, "animals": 0, "at_risk": 0, "unfed": 0,
        "empty_coops": 0, "empty_pastures": 0, "wheat": 0, "ripe_units": 0,
    }
    for animal in ANIMAL_HOME:
        out["have_" + animal] = 0
    for crop in CROPS:
        out["crop_" + crop] = 0
    for row in tiles:
        for tile in row:
            if tile == "LOCKED":
                continue
            out["owned"] += 1
            if tile is None:
                out["free"] += 1
            elif not isinstance(tile, dict):
                continue
            elif "animal" in tile:
                out["animals"] += 1
                out["have_" + str(tile.get("animal", ""))] = out.get(
                    "have_" + str(tile.get("animal", "")), 0) + 1
                if not tile.get("fed_today"):
                    out["unfed"] += 1
                    if int(tile.get("consecutive_unfed", 0) or 0) >= 1:
                        out["at_risk"] += 1
                out["ripe_units"] += int(tile.get("yield_units", 0) or 0)
            elif tile.get("kind") == "COOP":
                out["empty_coops"] += 1
            elif tile.get("kind") == "PASTURE":
                out["empty_pastures"] += 1
            elif tile.get("kind") == "PLANT":
                crop = str(tile.get("crop", ""))
                out["crop_" + crop] = out.get("crop_" + crop, 0) + 1
                if crop == "WHEAT":
                    out["wheat"] += 1
                out["ripe_units"] += int(tile.get("yield_units", 0) or 0)
    return out


# --- what things are worth ---------------------------------------------

def unit_price(observation: dict[str, Any], item: str) -> float:
    return max(1.0, float(price_at(item, inventory_of(observation, item))))


def crop_tile_value(observation: dict[str, Any], crop: str, day: int) -> float:
    """Coins a fresh tile of this crop still returns, if it is worked.

    Non-ongoing crops yield `max_yield` once and destroy the tile; ongoing
    crops yield one unit per interval until the season ends. Both are capped
    by what the season has left.
    """
    spec = CROPS.get(crop)
    if spec is None:
        return 0.0
    price = unit_price(observation, crop)
    left = LAST_DAY - day
    first = int(spec["first"])
    if left <= first:
        return 0.0
    if spec["ongoing"]:
        interval = max(1, int(spec["interval"]))
        cycles = min(int(spec["max_yield"]), (left - first) // interval + 1)
        return price * max(0, cycles)
    return price * float(spec["max_yield"])


def animal_value(observation: dict[str, Any], animal: str, day: int) -> float:
    """Coins an animal still returns from today to the close."""
    spec = ANIMALS.get(animal)
    if spec is None:
        return 0.0
    interval = max(1, int(spec["interval"]))
    left = max(0, LAST_DAY - day - int(spec["first"]))
    cycles = left // interval + (1 if left >= 0 else 0)
    return unit_price(observation, ANIMAL_PRODUCT[animal]) * cycles


def crop_targets(observation: dict[str, Any], day: int,
                 counts_for_feed: dict[str, Any] | None = None) -> list[tuple[str, float]]:
    """Crops worth sowing today, best value per tile first.

    The town is the only consumer, so a crop is worth what the town will
    still absorb at the price it will still pay. `remaining_demand` turns
    the unlocked shops into units the town will eat before the season ends.
    """
    demand = remaining_demand(observation)
    out = []
    # Feed before profit. A wheat tile yields about four units over its
    # window, an animal eats one a day, and two missed meals lose the animal
    # outright -- so while the flock is short, wheat outranks every cash crop
    # no matter what the books say.
    need = counts_for_feed.get("animals", 0) if counts_for_feed else 0
    standing = counts_for_feed.get("wheat", 0) if counts_for_feed else 0
    stored = counts_for_feed.get("shed_wheat", 0) if counts_for_feed else 0
    if need > 0 and standing * 4 + stored < need * 3 and day <= LAST_DAY - 3:
        return [("WHEAT", 10_000.0)]
    for crop in CROPS:
        value = crop_tile_value(observation, crop, day)
        if value <= 0:
            continue
        # A crop nobody eats floods its own book: melon is in no shop basket
        # at all, so only the town centre's one unit a day supports it.
        appetite = float(demand.get(crop, 0.0))
        standing = 0.0
        out.append((crop, value * (1.0 + min(1.0, appetite / 60.0)) - standing))
    out.sort(key=lambda kv: -kv[1])
    return out


# --- jobs, priced in coins and turns -----------------------------------

def job_offers(observation: dict[str, Any], tile: Any, x: int, y: int,
               inventory: dict[str, int], day: int, step: int,
               shed: dict[str, int], seeds: dict[str, int],
               counts: dict[str, Any]) -> list[tuple[float, float, list[Any]]]:
    """Every job this tile offers, as (coins, turns, action).

    Coins are what the job puts on the books before the season ends; turns
    are what it costs to do, excluding the walk, which the caller adds.
    """
    jobs: list[tuple[float, float, list[Any]]] = []
    closing = step >= LAST_ACT_STEP - 6
    # Goods being carried as inputs are not cargo: wheat while the flock is
    # unfed, manure while there is a tile worth spreading it on. Counting
    # them sent workers into a loop -- 130 pickups and 49 drops in one day,
    # the same grain travelling back and forth.
    holding_back = set()
    if counts["unfed"] > 0 or counts["at_risk"] > 0:
        holding_back.add("WHEAT")
    carried_value = sum(
        int(qty) * unit_price(observation, item)
        for item, qty in inventory.items()
        if int(qty) > 0 and item in MARKET_PARAMS
        and item not in holding_back)

    if _on_shed(x, y):
        # Anything still in hand at the close is thrown away.
        # A harvest in a worker's hands cannot be sold: only the shed feeds
        # the market, and the nightly tip discards whatever overflows. So a
        # full pair of hands is worth exactly what it is carrying, and the
        # walk back is priced like any other journey.
        if carried_value > 0:
            jobs.append((carried_value, 1.0, ["DROP"]))
        need_feed = counts["unfed"] + counts["at_risk"]
        if (need_feed > 0 and int(inventory.get("WHEAT", 0)) <= 0
                and int(shed.get("WHEAT", 0)) > 0 and not closing
                and not any(int(inventory.get(a, 0)) > 0 for a in ANIMAL_HOME)):
            carry = min(12, int(shed.get("WHEAT", 0)), max(2, need_feed))
            # Picking wheat up is only worth what the meals it enables save.
            worth = sum(animal_value(observation, a, day) * 0.12
                        for a in ANIMAL_HOME
                        for _ in range(counts.get("have_" + a, 0)))
            jobs.append((max(40.0, worth * 0.25), 1.0,
                         ["PICKUP", "WHEAT", carry]))
        for animal in ANIMAL_HOME:
            waiting = int(shed.get(animal, 0))
            house = "empty_coops" if ANIMAL_HOME[animal] == "COOP" else "empty_pastures"
            if waiting > 0 and counts[house] > 0 and not closing:
                jobs.append((animal_value(observation, animal, day), 1.0,
                             ["PICKUP", animal, min(3, waiting)]))
                break

    if tile is None:
        if closing:
            return jobs
        if (counts.get("labour_used", 0) + 1.25
                > counts.get("work_turns", 0)):
            return jobs
        for crop, value in crop_targets(observation, day, counts):
            if int(seeds.get(crop, 0)) <= 0:
                continue
            spec = CROPS[crop]
            # A tile is sown once and watered on the days that pay; charge
            # the sowing turn plus the waterings it will demand.
            waters = (min(int(spec["max_yield"]),
                          max(1, LAST_DAY - day - int(spec["first"])))
                      if spec["ongoing"] else
                      max(1, int(spec["max_day"]) - (int(spec["max_day"]) + 1) // 2 + 1))
            jobs.append((value, 1.0 + waters * 0.5, ["PLANT", crop]))
            break
        # Housing. A pen costs nothing but the turn, and an animal cannot be
        # bought without one standing empty -- the purchase rule needs the
        # room first. Build for an animal already waiting in the shed, or for
        # one the purse can afford, but never more than a couple ahead of the
        # flock: an empty pen is a tile that grows nothing.
        purse = float(counts.get("money", 0.0))
        for animal, house in ANIMAL_HOME.items():
            waiting = int(shed.get(animal, 0))
            room = (counts["empty_coops"] if house == "COOP"
                    else counts["empty_pastures"])
            affordable = purse >= float(ANIMALS[animal]["cost"]) + 60
            spare = counts["empty_coops"] + counts["empty_pastures"]
            if spare >= max(1, waiting + 1):
                continue
            if (counts.get("labour_used", 0) + 3.0
                    > counts.get("work_turns", 0)) and not waiting:
                continue
            if waiting > 0 or (affordable and room < 2):
                value = animal_value(observation, animal, day)
                if value > float(ANIMALS[animal]["cost"]) * 0.5:
                    jobs.append((value * 0.8, 1.0,
                                 ["BUILD_COOP" if house == "COOP"
                                  else "BUILD_PASTURE"]))
                    break
        return jobs

    if not isinstance(tile, dict):
        return jobs

    kind = tile.get("kind")
    if "animal" in tile:
        animal = str(tile.get("animal", ""))
        product = ANIMAL_PRODUCT.get(animal, "EGG")
        held = int(tile.get("yield_units", 0) or 0)
        price = unit_price(observation, product)
        if not tile.get("fed_today") and int(inventory.get("WHEAT", 0)) > 0:
            if int(tile.get("consecutive_unfed", 0) or 0) >= 1:
                # It escapes tonight if this is missed: the whole stream.
                jobs.append((animal_value(observation, animal, day), 1.0,
                             ["FEED"]))
            else:
                jobs.append((price * 0.6, 1.0, ["FEED"]))
        if held > 0:
            jobs.append((price * held, 1.0, ["HARVEST"]))
        if tile.get("fertilizer_available"):
            jobs.append((unit_price(observation, "FERTILIZER"), 1.0,
                         ["COLLECT_FERTILIZER"]))
        if not tile.get("cared_today") and tile.get("fed_today") and not closing:
            # The care bonus lands as an extra unit on a fed production day.
            jobs.append((price * 0.5, 1.0, ["CARE"]))
    elif kind in ("COOP", "PASTURE"):
        for animal, house in ANIMAL_HOME.items():
            if house == kind and int(inventory.get(animal, 0)) > 0:
                jobs.append((animal_value(observation, animal, day), 1.0,
                             ["PLACE", animal]))
                break
    elif kind == "PLANT":
        crop = str(tile.get("crop", ""))
        spec = CROPS.get(crop)
        if spec is None:
            return jobs
        price = unit_price(observation, crop)
        age = day - int(tile.get("planted_day", day))
        units = int(tile.get("yield_units", 0) or 0)
        if not tile.get("watered_today"):
            if spec["ongoing"]:
                # Unwatered ongoing crops go to weed and the tile is lost.
                jobs.append((crop_tile_value(observation, crop, day) * 0.5,
                             1.0, ["WATER"]))
            else:
                start = (int(spec["max_day"]) + 1) // 2
                if start <= age <= int(spec["max_day"]):
                    gain = 2 if int(tile.get("fertilized_until_day", -1)) >= day else 1
                    room = max(0, int(spec["max_yield"]) - units)
                    jobs.append((price * min(gain, room), 1.0, ["WATER"]))
                else:
                    jobs.append((price * 0.4, 1.0, ["WATER"]))
        if (int(inventory.get("FERTILIZER", 0)) > 0 and not spec["ongoing"]
                and int(tile.get("fertilized_until_day", -1)) < day):
            start = (int(spec["max_day"]) + 1) // 2
            left = int(spec["max_day"]) - max(age, start) + 1
            room = max(0, int(spec["max_yield"]) - units - max(0, left))
            gain = min(room, min(3, max(0, left)))
            if gain > 0:
                worth = gain * price - unit_price(observation, "FERTILIZER")
                if worth > 0:
                    jobs.append((worth, 1.0, ["FERTILIZE"]))
        if units > 0 and age >= int(spec["first"]):
            done = units >= int(spec["max_yield"])
            ripe = age >= int(spec["max_day"]) or done or closing
            if spec["ongoing"] or ripe:
                jobs.append((price * units, 1.0, ["HARVEST"]))
            elif counts["at_risk"] > 0 and crop == "WHEAT" and not shed.get("WHEAT"):
                jobs.append((price * units, 1.0, ["HARVEST"]))
    elif kind == "WEED":
        if not closing:
            jobs.append((crop_tile_value(observation, "CARROT", day) * 0.3,
                         1.0, ["DIG"]))
    return jobs


# --- the market ---------------------------------------------------------

def hands_wanted(day: int) -> int:
    """Ten hands cost 143 coins for a day and are wiped each night.

    The limit is daylight, not money: a hand hired late cannot finish a
    watering tour, so the roster is built in the first hours and then left
    alone. The field plateaus around eleven.
    """
    if day <= 0:
        return 5
    if day <= 4:
        return 7
    if day <= 8:
        return 9
    return 11


def market_orders(observation: dict[str, Any], day: int, step: int,
                  counts: dict[str, Any], shed: dict[str, int],
                  seeds: dict[str, int], money: float,
                  hands: int) -> list[list[Any]]:
    """Sales first, inventory-priced buys next, fixed-price orders last.

    `_process_market` walks both players' orders by index and quotes each
    side at the same pre-commit inventory, so a sale at a low index brings in
    cash and frees shed room before anything that needs either. A unit that
    fails aborts its whole order, and the tenth order is the last one read.
    """
    sells: list[list[Any]] = []
    buys: list[list[Any]] = []
    fixed: list[list[Any]] = []
    budget = money
    closing = step >= LAST_ACT_STEP - 10
    total_shed = sum(int(v) for v in shed.values())

    # 1. Sales. Wheat and egg absorb thousands of units; the fragile books
    #    are metered, because selling sixty units of wool takes it from 200
    #    coins to 1 and leaves it there for the rest of the game.
    feed_reserve = 0 if closing else min(12, counts["animals"] * 2)
    for item in ("EGG", "FERTILIZER", "MILK", "WOOL", "STRAWBERRY",
                 "MELON", "CARROT", "TOMATO", "WHEAT"):
        held = int(shed.get(item, 0))
        if item == "WHEAT":
            held = max(0, held - feed_reserve)
        if held <= 0:
            continue
        price = unit_price(observation, item)
        if price < 2 and not closing:
            continue
        if item in FRAGILE and not closing and total_shed < SHED_CAP - 15:
            held = min(held, FRAGILE_PER_TURN)
        sells.append(["SELL", item, held])

    if closing:
        return sells[:MAX_ORDERS]

    # 2. Feed bought from the market, but only what the flock needs now:
    #    wheat carries an obligation no other good has.
    short = counts["animals"] * 2 - int(shed.get("WHEAT", 0))
    if short > 0 and budget > 60 and total_shed < SHED_CAP - 5:
        want = min(short, 8, int((budget - 30) // 30))
        if want > 0:
            buys.append(["BUY_PRODUCT", "WHEAT", want])
            budget -= 30.0 * want

    # 3. Crew, in the first hours only.
    hour = step % TURNS
    target = hands_wanted(day)
    target = min(target, max(3, (counts["owned"] - counts["free"]) // 4 + 3))
    if hour <= 2 and hands < target:
        for _ in range(min(4, target - hands)):
            fixed.append(["HIRE"])

    # 4. Ground. Every one of the top two hundred teams owns a second
    #    quadrant by day 5 or 6 and a third by day 8 to 11, and ground is
    #    what a crew converts into goods. The first costs 1,000, the second
    #    2,000, the third 4,000.
    price_of_land = (1000.0, 2000.0, 4000.0)
    bought = max(0, (counts["owned"] - 25) // 25)
    if (bought < 3 and day >= (5, 8, 11)[bought] and counts["free"] <= 14
            and budget > price_of_land[bought] + 250):
        fixed.append(["BUY_LAND"])
        budget -= price_of_land[bought]

    # 5. Animals. These are the farm's engine and they must start on day
    #    zero: a cow costs 400 and returns milk from day 8 every second day,
    #    a sheep 500 and wool from day 6, a goose 300 and an egg a day from
    #    day 4. Every top team owns cows and sheep within three days. The
    #    floor here is only what the next meal costs, not a working balance.
    if hour <= 4 and budget > 380:
        best, gain = None, 0.0
        for animal, house in ANIMAL_HOME.items():
            room = (counts["empty_coops"] if house == "COOP"
                    else counts["empty_pastures"])
            if room <= int(shed.get(animal, 0)):
                continue
            if (counts.get("labour_used", 0) + 3.0
                    > counts.get("work_turns", 0)):
                continue
            feed_ready = (counts.get("wheat", 0) * 4
                          + int(shed.get("WHEAT", 0))
                          >= (counts["animals"] + 1) * 2)
            if not (feed_ready or budget > float(ANIMALS[animal]["cost"]) + 400):
                continue
            payback = animal_value(observation, animal, day) - float(
                ANIMALS[animal]["cost"])
            if payback > gain:
                best, gain = animal, payback
        if best is not None and budget > float(ANIMALS[best]["cost"]) + 60:
            fixed.append(["BUY_ANIMAL", best, 1])
            budget -= float(ANIMALS[best]["cost"])

    # 6. Seed for the ground we can actually sow and water.
    if hour in (1, 2) and budget > 60:
        for crop, _value in crop_targets(observation, day, counts):
            if len(fixed) >= 6:
                break
            spec = CROPS[crop]
            if day > LAST_DAY - int(spec["first"]) - 1:
                continue
            in_hand = int(seeds.get(crop, 0))
            room = max(0, counts["free"] - sum(int(v) for v in seeds.values()))
            want = min(4, room, int((budget - 40) // max(1, int(spec["seed"]))))
            if in_hand < 3 and want > 0:
                fixed.append(["BUY_SEED", crop, want])
                budget -= float(spec["seed"]) * want

    return (sells + buys + fixed)[:MAX_ORDERS]


# --- the turn -----------------------------------------------------------

def decide(observation: dict[str, Any]) -> AgentAction:
    farm = _farm(observation)
    tiles = farm.get("tiles") or []
    player = int(observation.get("player", 0))
    step = int(observation.get("step", 0))
    if step == 0:
        _EN_ROUTE.clear()
    if not tiles:
        return {"farmer": list(PASS), "hands": [], "market": []}

    day = int(observation.get("day", step // TURNS))
    positions = _positions(farm)
    shed = _shed(observation)
    seeds = _seeds(observation)
    counts = census(tiles, day)
    money = float(farm.get("money", 0.0) or 0.0)
    counts["money"] = money
    counts["shed_wheat"] = int(shed.get("WHEAT", 0))
    # The labour budget, which is what the whole farm is really limited by.
    # A crew of n hands has n * 24 turns in a day and spends roughly half of
    # them walking, so only about half are work. An animal wants feeding,
    # caring and collecting -- call it three turns a day -- and a growing
    # tile wants watering and eventually harvesting, call it one and a
    # quarter. A farm that buys past this line starves: 35 animals bought on
    # one run needed 105 turns a day against 130 available, the crops got
    # nothing, and half the herd escaped.
    crew = len(farm.get("hands") or []) + 1
    counts["work_turns"] = crew * TURNS * 0.5
    planted = sum(counts.get("crop_" + crop, 0) for crop in CROPS)
    counts["planted"] = planted
    counts["labour_used"] = counts["animals"] * 3.0 + planted * 1.25

    # Every (worker, job) pair, priced in coins per turn including the walk.
    candidates: list[tuple[float, int, tuple[int, int], list[Any]]] = []
    for worker, position in enumerate(positions):
        inventory = _inventory(observation, worker)
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if not _owned(tiles, x, y) and not _on_shed(x, y):
                    continue
                travel = distance(position, (x, y))
                for coins, turns, action in job_offers(
                        observation, tiles[y][x], x, y, inventory, day, step,
                        shed, seeds, counts):
                    cost = turns + travel * WALK_COST
                    rate = coins / max(0.5, cost)
                    held = _EN_ROUTE.get((player, worker))
                    if (held is not None and held[0] == (x, y)
                            and held[1] == action[0]):
                        rate *= COMMIT_BONUS
                    if rate > IDLE_TURN_VALUE:
                        candidates.append((rate, worker, (x, y), list(action)))

    candidates.sort(key=lambda c: -c[0])
    chosen: dict[int, list[Any]] = {}
    claimed: set[tuple[int, int]] = set()
    booked: list[tuple[int, tuple[int, int], list[Any], int]] = []
    for _rate, worker, cell, action in candidates:
        if worker in chosen or cell in claimed:
            continue
        if action[0] == "PLANT" and int(seeds.get(action[1], 0)) <= 0:
            continue
        if action[0] == "PICKUP" and int(shed.get(action[1], 0)) <= 0:
            continue
        travel = distance(positions[worker], cell)
        chosen[worker] = (action if travel == 0
                          else step_toward(positions[worker], cell, action))
        booked.append((worker, cell, action, travel))
        if action[0] not in ("DROP", "PICKUP"):
            claimed.add(cell)
        # Claim the consumable this job will spend, so two workers do not
        # both plan to sow the last seed.
        if action[0] == "PLANT":
            seeds[action[1]] = max(0, int(seeds.get(action[1], 0)) - 1)
        elif action[0] == "PICKUP" and len(action) > 2:
            shed[action[1]] = max(0, int(shed.get(action[1], 0)) - int(action[2]))
        elif action[0] == "FEED":
            counts["unfed"] = max(0, counts["unfed"] - 1)

    for worker, cell, action, travel in booked:
        if travel > 0:
            _EN_ROUTE[(player, worker)] = (cell, action[0])
        else:
            _EN_ROUTE.pop((player, worker), None)
    for worker in range(len(positions)):
        if worker not in chosen:
            _EN_ROUTE.pop((player, worker), None)

    actions = [chosen.get(w, list(PASS)) for w in range(len(positions))]
    return {
        "farmer": actions[0] if actions else list(PASS),
        "hands": actions[1:],
        "market": market_orders(observation, day, step, counts, shed, seeds,
                                money, len(farm.get("hands") or [])),
    }


def agent(observation: dict[str, Any], configuration: Any = None) -> AgentAction:
    """Entry point. Must stay the last callable defined in this module.

    kaggle_environments loads a submitted file with `get_last_callable`,
    which takes the final callable in the module rather than the one named
    agent. A helper defined below this line would be run as the agent, every
    action would be rejected as malformed, and the farm would sit still for
    thirty days. That has happened once in this project already.
    """
    try:
        return decide(observation)
    except Exception:
        farm = _farm(observation)
        hands = len(farm.get("hands") or [])
        return {"farmer": list(PASS),
                "hands": [list(PASS) for _ in range(hands)], "market": []}
