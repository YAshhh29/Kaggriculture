"""Candidate G: a farm built around the two goods whose price never falls.

Not a clone. Every agent this project has submitted replays a recorded
route -- C1, C2, D and F are the same guard stack over four different
tapes, which is why they span 2094 to 1375 with no logic differing between
them. Cloning has a ceiling and we are under it.

This is built from the simulator's own constants instead, and it rests on
one fact the entire leaderboard appears to have missed.

**Nine goods, two of which cannot be flooded.** Price is
`base -+ amp * f(|inventory - 10000|)`, and `f` differs per good. Counting
units past equilibrium until the quote reaches the floor of 1:

    WOOL 59, STRAWBERRY 62, MILK 76, MELON 158, FERTILIZER 493,
    TOMATO 529, CARROT 842 ... and EGG and WHEAT **never**, because
    their curves are logarithmic.

The thousandth egg still fetches 38. The seventy-seventh unit of milk
fetches 1.

**So the animal economics are lopsided.** From `ANIMALS` and
`_daily_refresh_animals`: a bird fed *and* cared yields `base 1 + bonus 1`
per interval, and the goose interval is 1 against the cow's 2 and the
sheep's 3, first yield day 4 against 8 and 6, cost 300 against 400 and
500. Twenty head, tended, to day 29:

    20 GEESE -> 1,000 EGG  -> 39,799 coins   (birds cost 6,000)
    20 COWS  ->   630 MILK ->  6,735 coins   (birds cost 8,000)
    20 SHEEP ->   613 WOOL ->  8,482 coins   (birds cost 10,000)

Six to one, for the cheapest animal on the board. The nine top-rated teams
average **2.1 geese** against 7.9 cows and 7.5 sheep, and Agent E buys 22
cows and no geese. The whole field crowds the two commodities that
collapse.

**And every animal drops one fertilizer a day unconditionally** --
`fertilizer_available = True` on the daily refresh whether or not it was
fed -- into a book 493 units deep. So a goose pays twice: eggs into a
market that never saturates, and manure into the deepest book after it.

The design follows from that and from three more rules:

* `BUILD_COOP` costs nothing and only needs an empty tile, so housing is
  free and the flock is limited by feed and labour, not capital;
* an animal unfed for two consecutive days **escapes**, so feed is not
  optional and the wheat area has to track the flock;
* reward is the money on the books at step 720, so everything sells.

It grows melon, carrot and strawberry on ground the flock does not need
(`CROP_TILES`), but it does not chase wool or milk. In a contested game
both collapse: measured across a real D-against-C1 match, milk runs
160 -> 203 -> 13 and wool 200 -> 217 -> 1, while egg goes 50 -> 92 because
the town keeps draining a book nobody floods.

Agent E failed twenty-six times because its economics priced every job by
the coins *it* received and its scheduler could not follow a build order.
This one has a fixed thesis and a scheduler that serves it.
"""

from __future__ import annotations

from typing import Any

from core.routing import distance, step_toward
from rl.demand import remaining_demand
from rl.economics import CROPS
from rl.market import inventory_of, price_at
from rl.runtime import AgentAction

PASS: list[str] = ["PASS"]
BOARD = 10
LAST_DAY = 29
MAX_ORDERS = 10

# --- the thesis, as numbers -------------------------------------------
# Crew ramp, not a constant. Hands are wiped nightly and re-hired at a
# fibonacci wage, so a full roster costs ~376 a day from day one against
# 3,000 of starting capital -- hiring twelve immediately bankrupted the
# farm by day six before it had any income at all. The corpus hires 4 by
# day 2, 8 by day 6 and 11 by day 10, and pays for each from the last.
HAND_RAMP = ((0, 4), (6, 5), (8, 8), (11, 10), (14, 12))
HIRE_UNTIL_DAY = 27          # the crew is wiped nightly; stopping early
                            # starved a 22-bird flock down to five
# Two fixed purchases behind a reserve. The corpus buys ground the instant
# it is affordable -- median cash 644 at the moment of purchase -- and
# copying that measured 11,083 at three quadrants against 22,438 here,
# because G's limit is worker throughput and it already leaves tiles idle.
# Measured, and it inverts the corpus. Buying ground as soon as affordable
# -- their behaviour -- gives 11,083 at three quadrants and 19,326 at two,
# against 21,235 for two fixed purchases behind a 1,200 reserve. G's limit
# is worker throughput, not ground: it already leaves tiles idle, so a
# quadrant only spends cash and spreads the crew thinner. The elite buy
# early because they have a thousand waterings to put on it.
LAND_DAYS = (4, 9)
LAND_RESERVE = 1200.0
MAX_QUADRANTS = 3
GOOSE_COST = 300
GOOSE_CASH_FLOOR = 450.0    # keep a bird's worth of change in hand
# A wheat tile yields about four units over five days unfertilized, which
# is 0.8 a day. The 1.2 here assumed the fertilized figure (1 + 3x2 = 6),
# and this agent never issues FERTILIZE -- it collects manure and sells
# it. The feed plan was therefore 50% optimistic and the flock chronically
# underfed, which is the same failure that killed Agent E's goose runs.
WHEAT_PER_BIRD = 0.8
# Wheat area is a plan, not a function of the flock. Deriving it from the
# animals standing gave a target of three tiles with no animals, which
# fed no birds, so none were bought, so the target never grew.
WHEAT_TILES = 20
COOPS_AFTER_WHEAT = 8
EARLY_BIRDS = 6
EARLY_COOPS = 6
COOP_LEAD = 2
# Cash crops for the ground the flock does not need. The goose economy is
# an addition to a farm, not a replacement for one: with wheat and coops
# satisfied it was leaving roughly thirty of seventy-one tiles idle all
# game while Candidate D farmed the whole board for ~107,000.
#
# Tile counts come from each good's book depth (10.8v) rather than its
# base price. Melon pays 250 and floors after 158 units; strawberry 120
# and floors after 62; carrot only 35 but absorbs 842, which is why the
# top of the board plants it and the field does not (10.8z).
CROP_TILES = (("MELON", 12), ("CARROT", 16), ("STRAWBERRY", 8))
# Let the town choose, instead of assuming one animal always wins.
#
# `observation["town"]["unlocked_shops"]` is public and exact, and
# `rl/demand.py` turns it into units the town will still absorb before the
# season ends. GOAL.md section 9v measured adapting production to that
# draw as the cleanest correlate of rank there is: +0.672 for teams above
# 2850 and +0.000 below 2400. Nothing this project has shipped uses it.
#
# The flock stays geese by default -- in a contested game egg runs
# 50 -> 92 while milk collapses 160 -> 13 and wool 200 -> 1, because the
# town keeps draining a book nobody floods. But a town that drew YARN_STORE
# twice wants wool badly enough to beat that, and this is how the agent
# notices.
# Below 1.0 the agent leaves egg for a good the town wants even when egg
# still prices higher, and that measures best: on eight seeds 0.8 gives
# 32,693 against 26,971 at 1.6 and 20,783 at 0.65. The seed spread is wide
# (11,415 to 43,007) so treat the peak as approximate, not tuned.
DEMAND_MARGIN = 0.8
# Wheat carried per trip to the shed. At four, PICKUP was the single most
# common action in the game -- 1,270 of them, more than harvest, feed, care
# and collect together -- because every four meals cost a round trip.
# Settled on eight seeds: 12 gives a mean of 21,031 against Candidate D,
# 18 gives 18,150 and 24 gives 19,267. A two-seed comparison had 24 ahead
# by 1,200 and it was noise -- the spread across seeds is 13,000.
FEED_CARRY = 12
# Cap on the crew ramp. Twelve hands cost about 376 a day in fibonacci
# wages, some 10,500 across a season, against roughly 51,000 of gross
# production. Labour is the largest cost in this design, not the birds.
HAND_CAP = 12
HARVEST_AT = 2              # eggs held before a bird is worth the walk
SEED_BUFFER = 10
TRAVEL_EXPONENT = 2.0
# Where a coop or a wheat tile goes matters as much as that it exists.
# Feed comes out of the shed and every meal is a round trip, so a flock
# housed at the far edge spends the season walking: PICKUP was the single
# most frequent action in the game at 1,102, with 3,160 turns of movement
# behind it, against 408 harvests. Ground near the shed is therefore worth
# more than ground far from it, and this is the discount for distance.
# Zoning. Workers pick jobs independently by value over distance squared,
# so they scatter: PICKUP and movement take some 4,200 of 7,000 worker
# turns while feeding, harvesting, watering and collecting share the rest,
# and the farm runs at roughly a third of what its flock is worth. Giving
# each worker a strip of the board to serve and taxing jobs outside it
# should convert walking into work. 1.0 disables the tax.
ZONE_TAX = 1.0
COMPACT = 0.0               # measured: clustering near the shed costs
                            # 5,000 coins, so it stays off

# Priority bands. The chain is feed -> wheat -> housing -> birds, because
# each link is worthless without the one before it, and a coin-valued
# ranking put housing six times above the wheat that keeps its occupant
# alive.
BAND_FEED = 10000.0
BAND_HARVEST = 6000.0
BAND_WHEAT = 4000.0
BAND_PLACE = 3000.0
BAND_SERVICE = 2000.0
BAND_WATER = 1500.0
BAND_BUILD = 800.0
BAND_CROP = 600.0


def _farm(observation: dict[str, Any]) -> dict[str, Any]:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    if player < len(farms) and isinstance(farms[player], dict):
        return farms[player]
    return {}


def _positions(farm: dict[str, Any]) -> list[tuple[int, int]]:
    units = [farm.get("farmer"), *(farm.get("hands") or [])]
    out: list[tuple[int, int]] = []
    for unit in units:
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


def _shed_adjacent(x: int, y: int) -> bool:
    """Standing *on* a shed-access tile, which is what the simulator wants.

    `_is_shed_adjacent` in kaggriculture.py is
    `tuple(pos) in set(_shed_access_tiles(board_size))` -- membership of
    exactly four tiles, not proximity to them. Accepting the twelve tiles
    within one step of the shed made 1,067 of 1,273 PICKUP actions in a
    game silent no-ops: the worker stood next to the right square, asked
    for wheat, got nothing, and walked off to feed birds empty-handed.
    """
    return (x, y) in set(shed_tiles())


def _owned(tiles: list[list[Any]], x: int, y: int) -> bool:
    return (0 <= y < len(tiles) and 0 <= x < len(tiles[y])
            and tiles[y][x] != "LOCKED")


def census(tiles: list[list[Any]]) -> dict[str, int]:
    """Everything the scheduler needs to know about the board, in one pass."""
    out = {
        "geese": 0, "animals": 0, "empty_coops": 0, "empty_pastures": 0,
        "wheat": 0, "free": 0, "unfed": 0, "uncared": 0,
        "manure": 0, "ripe": 0, "dry": 0,
    }
    for row in tiles:
        for tile in row:
            if tile == "LOCKED":
                continue
            if tile is None:
                out["free"] += 1
                continue
            if not isinstance(tile, dict):
                continue
            if "animal" in tile:
                out["animals"] += 1
                if tile.get("animal") == "GOOSE":
                    out["geese"] += 1
                if not tile.get("fed_today"):
                    out["unfed"] += 1
                if not tile.get("cared_today"):
                    out["uncared"] += 1
                if tile.get("fertilizer_available"):
                    out["manure"] += 1
                if int(tile.get("yield_units", 0) or 0) >= HARVEST_AT:
                    out["ripe"] += 1
            elif tile.get("kind") == "COOP":
                out["empty_coops"] += 1
            elif tile.get("kind") == "PASTURE":
                out["empty_pastures"] += 1
            elif tile.get("kind") == "PLANT":
                crop = str(tile.get("crop", ""))
                if crop == "WHEAT":
                    out["wheat"] += 1
                    if not tile.get("watered_today"):
                        out["dry"] += 1
                else:
                    key = "crop_" + crop
                    out[key] = out.get(key, 0) + 1
    return out


def job_value(
    observation: dict[str, Any],
    tile: Any,
    x: int,
    y: int,
    inventory: dict[str, int],
    day: int,
    shed: dict[str, int],
    seeds: dict[str, int],
    counts: dict[str, int],
    closing: bool,
) -> list[tuple[float, list[Any]]]:
    """Every job available on this tile, in priority bands.

    An earlier version priced each job in coins and let them compete
    directly. That failed for a reason worth recording: building a coop is
    worth a bird's whole remaining output, which outbid planting the wheat
    that bird eats by roughly six to one, so the farm built empty housing,
    never sowed, and its geese starved out on day three.

    The ordering is a dependency chain, not a preference. Feeding beats
    everything because two missed meals lose the animal outright. Wheat
    beats housing because housing without feed kills what it houses.
    Housing beats buying because an unhoused bird sits in the shed. Within
    a band the value still varies with the live price and the distance
    discount still applies, so the schedule stays sane -- but no job can
    ever outbid the thing it depends on.
    """
    jobs: list[tuple[float, list[Any]]] = []
    egg = max(1.0, price_at("EGG", inventory_of(observation, "EGG")))
    manure = max(
        1.0, price_at("FERTILIZER", inventory_of(observation, "FERTILIZER"))
    )
    days_left = max(0, LAST_DAY - day)
    # Wheat the flock needs standing, plus a small buffer to grow into.
    wheat_target = WHEAT_TILES

    if _shed_adjacent(x, y):
        carrying = int(inventory.get("WHEAT", 0))
        if counts["unfed"] > 0 and carrying <= 0 and shed.get("WHEAT", 0) > 0:
            jobs.append((BAND_FEED * 0.9, ["PICKUP", "WHEAT", FEED_CARRY]))
        bird = counts.get("bird", "GOOSE")
        home = "empty_coops" if ANIMAL_HOME[bird] == "COOP"             else "empty_pastures"
        if (int(shed.get(bird, 0)) > 0
                and int(inventory.get(bird, 0)) <= 0
                and counts[home] > 0):
            jobs.append((BAND_PLACE * 0.9, ["PICKUP", bird, 1]))

    if tile is None:
        # Everything built here is worked from the shed for the rest of the
        # season, so near ground is worth more than far ground.
        near = 1.0 / (1.0 + COMPACT * min(
            abs(x - sx) + abs(y - sy) for sx, sy in shed_tiles()
        ))
        if (counts["wheat"] < wheat_target
                and int(seeds.get("WHEAT", 0)) > 0
                and day <= LAST_DAY - 8):
            jobs.append(((BAND_WHEAT + egg) * near, ["PLANT", "WHEAT"]))
        elif (
            counts["empty_coops" if ANIMAL_HOME[counts.get("bird", "GOOSE")]
                   == "COOP" else "empty_pastures"] < COOP_LEAD
            and days_left > 5
            and (
                counts["geese"] + counts["empty_coops"] < EARLY_COOPS
                or counts["wheat"] >= COOPS_AFTER_WHEAT
            )
        ):
            early = counts["geese"] + counts["empty_coops"] < EARLY_COOPS
            jobs.append((
                ((BAND_WHEAT + 1.0 if early else BAND_BUILD) + egg) * near,
                ["BUILD_COOP"
                 if ANIMAL_HOME[counts.get("bird", "GOOSE")] == "COOP"
                 else "BUILD_PASTURE"],
            ))
        else:
            # Spare ground goes to cash crops, best price per tile first,
            # each capped at what its book will actually absorb.
            for crop, cap in CROP_TILES:
                spec = CROPS.get(crop)
                if spec is None or counts.get("crop_" + crop, 0) >= cap:
                    continue
                if int(seeds.get(crop, 0)) <= 0:
                    continue
                if day > LAST_DAY - int(spec["first"]) - 2:
                    continue
                price = price_at(crop, inventory_of(observation, crop))
                jobs.append(((BAND_CROP + price) * near,
                             ["PLANT", crop]))
                break
        return jobs

    if not isinstance(tile, dict):
        return jobs

    kind = tile.get("kind")
    if "animal" in tile:
        held = int(tile.get("yield_units", 0) or 0)
        if not tile.get("fed_today") and int(inventory.get("WHEAT", 0)) > 0:
            jobs.append((BAND_FEED + egg * days_left * 0.1, ["FEED"]))
        if held > 0 and (held >= HARVEST_AT or closing):
            jobs.append((BAND_HARVEST + egg * held, ["HARVEST"]))
        if tile.get("fertilizer_available"):
            jobs.append((BAND_SERVICE + manure, ["COLLECT_FERTILIZER"]))
        if not tile.get("cared_today") and tile.get("fed_today"):
            jobs.append((BAND_SERVICE + egg * 0.9, ["CARE"]))
    elif kind in ("COOP", "PASTURE"):
        for animal, house in ANIMAL_HOME.items():
            if house == kind and int(inventory.get(animal, 0)) > 0:
                jobs.append((BAND_PLACE + egg * days_left * 0.1,
                             ["PLACE", animal]))
                break
    elif kind == "PLANT":
        if not tile.get("watered_today"):
            jobs.append((BAND_WATER + egg * 0.5, ["WATER"]))
        # Only once it is actually ripe. `_new_plant` gives a non-ongoing
        # crop `yield_units = 1` the moment it goes in the ground, so a
        # bare "has yield" test made every worker harvest wheat on the
        # turn it was sown -- one unit taken and the tile destroyed, which
        # is why the farm never had a harvest to sell.
        crop = str(tile.get("crop", ""))
        spec = CROPS.get(crop)
        age = day - int(tile.get("planted_day", day))
        ripe = spec is not None and age >= int(spec["first"])
        if ripe and int(tile.get("yield_units", 0) or 0) > 0:
            jobs.append((BAND_HARVEST + egg * 0.5 * int(tile["yield_units"]),
                         ["HARVEST"]))
    elif kind == "WEED":
        # The corpus digs 36 weeds a game. A weed occupies ground
        # that could hold a coop or a crop for the rest of the season.
        # The corpus digs 36 weeds a game, but raising DIG to compete with
        # watering measured neutral at best (19,326 against 19,583 at two
        # quadrants) and the baseline value is kept.
        jobs.append((BAND_WATER * 0.4, ["DIG"]))

    return [(v, a) for v, a in jobs if v > 0]


def claim(counts: dict[str, int], action: list[Any]) -> None:
    """Update the board census for a job just handed to a worker.

    Thirteen workers are assigned from one snapshot, so without this every
    one of them sees the same empty board and takes the same job. That is
    literally what happened: all thirteen built a coop on the same turn.
    """
    op = action[0] if action else "PASS"
    if op == "BUILD_PASTURE":
        counts["empty_pastures"] += 1
        counts["free"] = max(0, counts["free"] - 1)
    elif op == "BUILD_COOP":
        counts["empty_coops"] += 1
        counts["free"] = max(0, counts["free"] - 1)
    elif op == "PLANT":
        crop = str(action[1]) if len(action) > 1 else "WHEAT"
        if crop == "WHEAT":
            counts["wheat"] += 1
        else:
            counts["crop_" + crop] = counts.get("crop_" + crop, 0) + 1
        counts["free"] = max(0, counts["free"] - 1)
    elif op == "FEED":
        counts["unfed"] = max(0, counts["unfed"] - 1)
    elif op == "CARE":
        counts["uncared"] = max(0, counts["uncared"] - 1)
    elif op == "COLLECT_FERTILIZER":
        counts["manure"] = max(0, counts["manure"] - 1)
    elif op == "HARVEST":
        counts["ripe"] = max(0, counts["ripe"] - 1)
    elif op == "WATER":
        counts["dry"] = max(0, counts["dry"] - 1)
    elif op == "PLACE":
        animal = str(action[1]) if len(action) > 1 else "GOOSE"
        key = ("empty_coops" if ANIMAL_HOME.get(animal) == "COOP"
               else "empty_pastures")
        counts[key] = max(0, counts[key] - 1)
        counts["animals"] += 1
        counts["geese"] += 1


def hands_target(day: int) -> int:
    """How large the crew should be today, ramped with income."""
    wanted = HAND_RAMP[0][1]
    for start, size in HAND_RAMP:
        if day >= start:
            wanted = size
    return min(wanted, HAND_CAP)


def preferred_bird(observation: dict[str, Any]) -> str:
    """Goose unless this town's own draw clearly wants otherwise.

    `observation["town"]["unlocked_shops"]` is public and exact, and
    `rl/demand.py` turns it into the units the town will still absorb.
    Section 9v measured adapting production to that draw as the cleanest
    correlate of rank in the data: +0.672 for teams above 2850, +0.000
    below 2400.

    Egg is the default because in a contested game it runs 50 -> 92 while
    milk collapses 160 -> 13 and wool 200 -> 1 -- the town keeps draining a
    book neither player floods. It takes a clear margin to beat that.
    """
    demand = remaining_demand(observation)
    best, score = "GOOSE", demand.get("EGG", 0.0) * price_at(
        "EGG", inventory_of(observation, "EGG"))
    for animal, product in (("SHEEP", "WOOL"), ("COW", "MILK")):
        pull = demand.get(product, 0.0) * price_at(
            product, inventory_of(observation, product))
        if pull > score * DEMAND_MARGIN:
            best, score = animal, pull
    return best


ANIMAL_HOME = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}


def crop_priority(observation: dict[str, Any]) -> list[tuple[str, int]]:
    """Crops worth ground here, best first, with the tile cap for each.

    The same argument as the animal choice. A fixed list plants melon in a
    town that never draws a PIZZA_SHOP and carrot in one that draws three,
    which is planting by habit. `remaining_demand` says what this town will
    still absorb; multiplying by the live price gives the coins actually
    available in each crop, and the cap keeps us from filling a book we
    have already saturated.

    Wheat is excluded deliberately: it is feed, and its acreage is set by
    the size of the flock rather than by what the town wants.
    """
    demand = remaining_demand(observation)
    ranked = []
    for crop, cap in CROP_TILES:
        pull = demand.get(crop, 0.0) * price_at(
            crop, inventory_of(observation, crop))
        ranked.append((pull, crop, cap))
    ranked.sort(reverse=True)
    return [(crop, cap) for pull, crop, cap in ranked if pull > 0]


def market_orders(
    observation: dict[str, Any],
    day: int,
    counts: dict[str, int],
    shed: dict[str, int],
    seeds: dict[str, int],
    money: float,
    hands: int,
) -> list[list[Any]]:
    """Sell the deep books, then buy the flock that fills them."""
    orders: list[list[Any]] = []
    closing = day >= LAST_DAY - 1
    budget = money

    # 1. Sell. Egg and fertilizer are the thesis; wheat above the feed
    #    reserve is surplus. Nothing is held back: both books are deep
    #    enough that waiting only forfeits the sale (10.8ad measured
    #    metering the same units onto more turns as strictly worse).
    reserve = 0 if closing else int(counts["animals"] * 2)
    for item in ("EGG", "FERTILIZER", "MILK", "WOOL", "CARROT",
                 "TOMATO", "STRAWBERRY", "MELON"):
        held = int(shed.get(item, 0))
        if held > 0:
            orders.append(["SELL", item, held])
    wheat = int(shed.get("WHEAT", 0))
    if wheat > reserve:
        orders.append(["SELL", "WHEAT", wheat - reserve])

    if closing:
        return orders[:MAX_ORDERS]

    # 2. Crew. Hands are hired daily and wiped nightly, and the cost is
    #    fibonacci in the number hired today, so the early ones are almost
    #    free and the schedule is what limits the farm, not the wage.
    # Once a day, not once a turn. Hands are wiped nightly and the fibonacci
    # wage restarts each morning, so the roster has to be rebuilt daily --
    # but issuing the order every turn hires seventy-two times a day and
    # took the opening purse from 2,846 to nothing by day eight, leaving
    # one hand to work the whole farm.
    hour = int(observation.get("step", 0)) % 24
    target = hands_target(day)
    if day <= HIRE_UNTIL_DAY and hands < target and hour <= 2:
        wanted = min(target - hands, 4)
        for _ in range(wanted):
            if len(orders) >= MAX_ORDERS:
                break
            orders.append(["HIRE"])

    # 3. Ground, as soon as it is affordable.
    quadrants = len(
        (observation.get("farms") or [{}])[
            int(observation.get("player", 0))
        ].get("unlocked_quadrants") or []
    )
    if (
        day in LAND_DAYS
        and quadrants < MAX_QUADRANTS
        and budget > LAND_RESERVE
        and len(orders) < MAX_ORDERS
    ):
        orders.append(["BUY_LAND"])
        budget -= LAND_RESERVE

    # 4a. Which bird. Geese unless the town's own draw says otherwise by a
    #     clear margin -- a coop and a pasture are both free to build, so
    #     the only cost of following the town is noticing in time.
    bird = counts.get("bird", "GOOSE")
    demand = remaining_demand(observation)
    egg_pull = demand.get("EGG", 0.0) * price_at(
        "EGG", inventory_of(observation, "EGG"))
    for other, product in (("SHEEP", "WOOL"), ("COW", "MILK")):
        pull = demand.get(product, 0.0) * price_at(
            product, inventory_of(observation, product))
        if pull > egg_pull * DEMAND_MARGIN:
            bird, egg_pull = other, pull

    # 4. Birds. One per turn, only into a coop that is standing empty and
    #    only while the wheat area can feed what we already have -- the
    #    flock must never outrun its feed, because two missed meals lose
    #    the animal outright.
    in_shed = int(shed.get(bird, 0))
    feedable = counts["wheat"] * WHEAT_PER_BIRD + shed.get("WHEAT", 0) / 3.0
    if (
        counts["empty_coops" if ANIMAL_HOME[bird] == "COOP"
               else "empty_pastures"] > in_shed
        and budget > GOOSE_COST + GOOSE_CASH_FLOOR
        and (counts["animals"] + in_shed < EARLY_BIRDS
             or counts["animals"] + in_shed < feedable)
        and day <= LAST_DAY - 5
        and len(orders) < MAX_ORDERS
    ):
        orders.append(["BUY_ANIMAL", bird, 1])
        budget -= GOOSE_COST

    # 5. Seed, wheat only. Every other crop grows into a book that floors
    #    before the season ends; wheat feeds the flock and its own curve
    #    never falls.
    # Seed, wheat only, and once a day. Ordering it every turn bought two
    # hundred seeds a day and drained the opening purse into ground that
    # was never sown.
    hour = int(observation.get("step", 0)) % 24
    if (
        hour == 1
        and int(seeds.get("WHEAT", 0)) < SEED_BUFFER
        and budget > GOOSE_CASH_FLOOR
        and day <= LAST_DAY - 8
        and len(orders) < MAX_ORDERS
    ):
        want = SEED_BUFFER - int(seeds.get("WHEAT", 0))
        orders.append(["BUY_SEED", "WHEAT", want])
    if hour == 2 and budget > 1500.0 and day <= LAST_DAY - 10:
        for crop, cap in CROP_TILES:
            if len(orders) >= MAX_ORDERS:
                break
            if counts.get("crop_" + crop, 0) < cap                     and int(seeds.get(crop, 0)) < 4:
                orders.append(["BUY_SEED", crop, 4])

    # 6. Emergency ration, so a late harvest never costs a bird.
    if (
        counts["unfed"] > 0
        and int(shed.get("WHEAT", 0)) <= 0
        and budget > 400.0
        and len(orders) < MAX_ORDERS
    ):
        orders.append(["BUY_PRODUCT", "WHEAT", min(counts["unfed"], 6)])

    return orders[:MAX_ORDERS]


def decide(observation: dict[str, Any]) -> AgentAction:
    farm = _farm(observation)
    tiles = farm.get("tiles") or []
    if not tiles:
        return {"farmer": PASS, "hands": [], "market": []}

    day = int(observation.get("day", int(observation.get("step", 0)) // 24))
    closing = day >= LAST_DAY - 1
    positions = _positions(farm)
    shed = _shed(observation)
    seeds = _seeds(observation)
    counts = census(tiles)
    money = float(farm.get("money", 0.0) or 0.0)
    # Which animal this town actually wants. The scheduler needs to know
    # before it builds anything, because a cow needs a pasture and a goose
    # needs a coop -- buying the animal the town wants and then housing it
    # nowhere leaves it standing in the shed, which is exactly what the
    # first attempt at this did.
    counts["bird"] = preferred_bird(observation)
    # crop_priority is deliberately not used to reorder planting. Ranking
    # crops by remaining demand times price measured 24,257 against 32,693
    # for the fixed order, because that product is the coins available in a
    # crop while the binding constraint is *tiles*: melon's demand is small
    # and it still pays 250 a unit, so a total-coins ranking buries it
    # under carrot. The animal choice does not have this problem -- a pen
    # is a pen -- which is why demand drives that and not this.

    # Workers are assigned in order, each taking the best job left on the
    # board. Claimed tiles are struck out so two workers never walk to the
    # same job and waste a turn between them.
    claimed: set[tuple[int, int]] = set()
    actions: list[list[Any]] = []
    for worker, position in enumerate(positions):
        inventory = _inventory(observation, worker)
        best_score = 0.0
        best: list[Any] = list(PASS)
        best_cell: tuple[int, int] | None = None
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if (x, y) in claimed or not _owned(tiles, x, y):
                    continue
                travel = distance(position, (x, y))
                # Each worker serves a vertical strip. Jobs outside it are
                # still legal -- a hungry bird anywhere still beats an
                # empty tile next door -- but they are taxed, so the crew
                # spreads across the board instead of chasing the same
                # corner.
                if ZONE_TAX < 1.0 and len(positions) > 1:
                    width = max(1, len(tiles[y]) // len(positions))
                    home = worker * width
                    in_zone = home <= x < home + width
                else:
                    in_zone = True
                for value, act in job_value(
                    observation, tiles[y][x], x, y, inventory, day,
                    shed, seeds, counts, closing,
                ):
                    score = value / (travel + 1.0) ** TRAVEL_EXPONENT
                    if not in_zone:
                        score *= ZONE_TAX
                    if score > best_score:
                        best_score = score
                        best_cell = (x, y)
                        best = (list(act) if travel == 0
                                else step_toward(position, (x, y), list(act)))
        if best_cell is not None:
            claimed.add(best_cell)
            claim(counts, best)
        actions.append(best)

    return {
        "farmer": actions[0] if actions else list(PASS),
        "hands": actions[1:],
        "market": market_orders(
            observation, day, counts, shed, seeds, money,
            len(farm.get("hands") or []),
        ),
    }


def agent(observation: dict[str, Any]) -> AgentAction:
    """Run the goose economy."""
    return decide(observation)
