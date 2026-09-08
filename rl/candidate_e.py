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
from rl.demand_sales import paced_orders
from rl.market import headroom, marginal_price, sale_revenue
from rl.economics import (
    ANIMALS,
    CROPS,
    LAST_DAY,
    care_value,
    collect_fertilizer_value,
    crop_can_mature,
    days_left,
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
LAND_SURPLUS = 300.0
LAND_OPEN_TRIGGER = 6
TILES_PER_HAND = 6
HERD_FORCE: str | None = None
MIXED_CAP: int | None = None
RANKING_MODE = "payback"
TRAVEL_MODE = "square"
TRAVEL_EXPONENT = 3.0
TURN_COST = 30.0
WHEAT_HOARD_CAP = 24
SELL_FLOOR = 15.0
# Multiplier on the value of picking up a dropped fertilizer unit.
# Every animal drops one a day unconditionally, so it is the cheapest
# volume on the board, and volume is what E is short of: it sells 977
# units a game against Candidate D's 2,138 and lets the same frozen
# opponent bank 142,772 coins where D holds it to 59,943 (10.8t). 1.0
# leaves the schedule exactly as it was measured.
COLLECT_WEIGHT = 1.0
SELL_PACE = 24.0
SELL_CASH_FLOOR = 1500.0
SHED_PRESSURE = 70
WHEAT_UNITS_PER_TILE_DAY = 0.6
WORKING_CAPITAL = 400.0
MAX_ORDERS = 10
HIRE_FLOOR = 20.0
RESCUE_SHARE = 0.45
LIQUIDITY_FLOOR = 1500.0
_FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377)
MIN_CASH = 250.0
SEED_BUFFER = 12
SEED_SPEND_SHARE = 0.15
EMERGENCY_FEED_FLOOR = 600.0
WHEAT_TILE_CAP = 22
FEED_RESERVE_PER_ANIMAL = 4
HERD_CREW = 0
FERTILIZER_HOLD_CAP = 0
OPENING_LAND_DAY = 1
OPENING_LAND_RESERVE = 900.0


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

# Care is only worth taking if the animal is also fed, and the bonus is
# banked and paid out on the next production day, so an animal that is fed
# and cared for every day yields (interval + 1) units every `interval`
# days: two a day for a goose, three every two days for a cow, four every
# three for a sheep.
def units_per_day(animal: str) -> float:
    spec = ANIMALS[animal]
    interval = max(1, int(spec["interval"]))
    return (interval + 1.0) / interval


def herd_census(tiles: list[list[Any]]) -> tuple[dict[str, int], dict[str, int]]:
    """Animals standing, and empty structures, both counted by kind."""
    animals = {"GOOSE": 0, "COW": 0, "SHEEP": 0}
    pens = {"COOP": 0, "PASTURE": 0}
    for row in tiles:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if "animal" in tile:
                name = str(tile["animal"])
                if name in animals:
                    animals[name] += 1
            elif tile.get("kind") in pens:
                pens[str(tile["kind"])] += 1
    return animals, pens


def animal_value(
    observation: dict[str, Any],
    animal: str,
    day: int,
    animals: dict[str, int],
) -> float:
    """Coins one more of this animal returns, priced at the margin.

    This is the calculation that decides Agent E's whole shape, and it is
    the one every recorded route gets wrong. Valuing an animal at its
    product's spot price says a sheep is worth 200 a unit and a goose 50,
    so every tape builds sheep and cows. But the market is a shared
    depleting pool: wool falls to a single coin after roughly 59 units are
    sold into it and milk after 76, while egg -- alone among the nine
    products -- has a logarithmic curve with the largest T in the game and
    is still paying 40 coins at the four-hundredth unit.

    Priced properly, against the herd already standing:

        existing herd    1st animal     5th animal    17th animal
        cow (milk)            3,888             30            30
        sheep (wool)          4,879             26            26
        goose (egg)           2,244          2,049         1,900

    So a few cows and sheep are worth having for the steep part of their
    curves, and after that every further pen should hold a goose. In real
    games against elite opposition egg finishes 150 to 300 units *below*
    equilibrium at 59 to 68 coins -- above its own base -- because none of
    them keep geese at all.
    """
    spec = ANIMALS[animal]
    horizon = LAST_DAY - day - int(spec["first"])
    if horizon <= 0:
        return -1.0
    product = spec["product"]
    rate = units_per_day(animal)
    units = rate * horizon
    # What the herd we already own will pour into this product first, less
    # what the town will lift back out of the market before we get there.
    committed = sum(
        count * units_per_day(kind) * max(0, LAST_DAY - day - ANIMALS[kind]["first"])
        for kind, count in animals.items()
        if ANIMALS[kind]["product"] == product
    )
    absorbed = float(remaining_demand(observation).get(product, 0.0))
    # `committed - absorbed` goes negative whenever the town's appetite
    # exceeds our own supply, which prices the next unit *above* base.
    # That looks indefensible and it is: it values a thirteenth cow's milk
    # at 6,813 coins where its own margin is 27, because milk floors 76
    # units past equilibrium. Clamping it at zero was measured and costs E
    # two thirds of its coins (10.8w) -- the herd is not being paid for
    # milk, it is being paid for the fertilizer every animal drops daily,
    # and the overvaluation is what sizes it. Left exactly as measured.
    revenue = sale_revenue(observation, product, units, committed - absorbed)

    # Every surviving animal drops one fertilizer a day, unconditionally --
    # the simulator sets `fertilizer_available` on the daily refresh whether
    # or not the animal was fed. It is the same for all three kinds, so it
    # does not pick between them, but it is most of why a pen pays at all.
    days = max(0, LAST_DAY - day)
    fertilizer_committed = sum(animals.values()) * days
    manure = sale_revenue(
        observation, "FERTILIZER", days, fertilizer_committed
    )
    return revenue + manure - float(spec["cost"])


def herd_plan(
    observation: dict[str, Any],
    day: int,
    animals: dict[str, int],
) -> tuple[str, float]:
    """The animal worth buying next, and what it is worth."""
    if HERD_FORCE is not None:
        return HERD_FORCE, animal_value(observation, HERD_FORCE, day, animals)
    best, best_value = "GOOSE", -1e9
    for animal in ("GOOSE", "COW", "SHEEP"):
        if MIXED_CAP is not None and animal != "GOOSE":
            if animals.get(animal, 0) >= MIXED_CAP:
                continue
        value = animal_value(observation, animal, day, animals)
        if value > best_value:
            best, best_value = animal, value
    return best, best_value


def preferred_herd(observation: dict[str, Any]) -> str:
    """Backwards-compatible single-animal choice."""
    animals, _ = herd_census(_tiles(_farm(observation)))
    return herd_plan(observation, int(observation.get("day", 0)), animals)[0]


def crop_cycle(crop: str) -> tuple[float, float]:
    """Units a fully-tended tile yields, and the days it holds the tile."""
    spec = CROPS[crop]
    if spec["ongoing"]:
        units = float(spec["max_yield"])
        span = float(spec["first"] + spec["interval"] * spec["max_yield"])
    else:
        window = spec["max_day"] - (spec["max_day"] + 1) // 2 + 1
        units = float(min(spec["max_yield"], window))
        span = float(spec["max_day"] + 1)
    return units, max(1.0, span)


def crop_rate_value(
    observation: dict[str, Any],
    crop: str,
    day: int,
    standing: int,
) -> float:
    """Coins per tile-day from planting this crop now, priced at the margin.

    This is the calculation Agent E's whole field plan rests on, and it is
    three things at once that no spot-price ranking can be.

    It is **marginal**: a crop is valued at what its units will fetch after
    everything already growing has been sold into the same market, so the
    thirteenth melon tile is correctly worth a fraction of the first. It is
    **demand-aware**: the town lifts inventory back out of the market all
    game, and that absorption is subtracted before the price is read, which
    is why carrot is worth planting in a PET_CAFE town and worthless in
    another. And it is **per tile-day**, so a cheap fast crop is not
    out-ranked by an expensive slow one merely for having a bigger number
    on the label.

    Measured against an elite route, this is where the money actually is --
    realised coins per unit sold, not base price:

        melon 180, tomato 111, carrot 70, strawberry 59, wheat 43,
        wool 11, milk 11

    Wheat holds 43 against a base of 25 all game because five of the eight
    shops buy it and both players are short of it for feed. Melon pays 180
    but the market only absorbs about 150 a game between both players.
    Wool and milk, which every recorded route builds its herd around, are
    worth eleven coins a unit.
    """
    spec = CROPS.get(crop)
    if spec is None or not crop_can_mature(crop, day, day):
        return 0.0
    units, span = crop_cycle(crop)
    remaining = days_left(day)
    if remaining <= 0:
        return 0.0
    # Everything already in the ground reaches the market before this does.
    committed = standing * units * max(1.0, remaining / span)
    absorbed = float(remaining_demand(observation).get(crop, 0.0))
    # Same offset as animal_value, and the same measured verdict (10.8w).
    revenue = sale_revenue(observation, crop, units, committed - absorbed)
    horizon = min(span, float(remaining))
    return (revenue - spec["seed"]) / max(1.0, horizon)


def crop_ranking(observation: dict[str, Any], day: int) -> list[str]:
    """Crops worth planting now, best first.

    Two rankings are implemented and both are honest attempts; which one
    wins is a measured question, not an obvious one.

    `marginal` prices a crop at what its units will really fetch once
    everything already growing has been sold into the same market, net of
    what the town lifts back out. It is the more correct model and it says
    melon is worth 123 coins a tile-day and wheat 25.

    `payback` is the older rule: coins per tile-day at the spot quote,
    scaled by the town's appetite and, while cash is short, by how soon the
    crop first pays. It is cruder, but it measured 5,000 coins a game
    better on a fair panel, because this agent lives hand to mouth for the
    first three weeks and a model that is right about the season is worth
    less to it than one that is right about tomorrow.
    """
    tiles = _tiles(_farm(observation))
    standing: dict[str, int] = {c: 0 for c in CROPS}
    for row in tiles:
        for tile in row:
            if isinstance(tile, dict) and tile.get("crop") in standing:
                standing[str(tile["crop"])] += 1
    scored: list[tuple[float, str]] = []
    if RANKING_MODE == "marginal":
        for crop in CROPS:
            value = crop_rate_value(observation, crop, day, standing[crop])
            if value > 0:
                scored.append((value, crop))
        scored.sort(reverse=True)
        return [c for _, c in scored]

    remaining = remaining_demand(observation)
    money = float(_farm(observation).get("money", 0.0))
    thin = money < LIQUIDITY_FLOOR
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


def _travel_score(value: float, travel: int) -> float:
    """Rank a job by what it is worth net of getting there.

    Dividing a job's value by the distance to it -- the obvious rule, and
    the one this agent used -- rates a 600-coin job eight tiles away above
    a 100-coin job next door. That is how a crew ends up crossing the farm
    past work it could have finished, and it measured 2.0 steps walked for
    every task done against a good route's 0.94.

    Three models were tried on a fair panel of 36 games. Discounting by the
    square of the distance is the clear winner, and not by a little:

        value / (d+1)          37,756 mean, floor    673
        value / (d+1)^2      **45,934 mean, floor 14,417**
        value - 15*d           32,863 mean, floor  9,676
        value - 40*d           22,732 mean, floor  7,367

    The floor is the tell. A linear discount lets a distant prize pull the
    whole crew off the near work, and the near work here is watering --
    miss a tile two days running and the plant is a weed, so the losses
    compound into whole-farm collapses. Squaring keeps everyone local
    enough that the fields survive.
    """
    if TRAVEL_MODE == "linear":
        return value / (travel + 1.0)
    if TRAVEL_MODE == "net":
        return value - travel * TURN_COST
    return value / (travel + 1.0) ** TRAVEL_EXPONENT


def _worth_saving(tile: dict[str, Any], day: int) -> bool:
    """Has this plant any yield left to give?

    A one-shot crop only gains units while it is inside its watering
    window, so a wheat plant older than four days will never produce
    another thing however faithfully it is watered -- keeping it alive is
    pure overhead, and worse, it holds the tile against a replant. The
    reserved rescue crew was spending its guaranteed labour on exactly
    those plants, because the old rule rescued anything that had missed a
    day. Let them go to weed and dig them out instead.
    """
    crop = str(tile.get("crop", ""))
    spec = CROPS.get(crop)
    if spec is None:
        return False
    if int(tile.get("yield_units", 0)) >= spec["max_yield"]:
        return False
    age = day - int(tile.get("planted_day", day))
    if spec["ongoing"]:
        return age < spec["first"] + spec["interval"] * spec["max_yield"]
    return age < spec["max_day"]


def _stream_value(
    observation: dict[str, Any], animal: str, day: int
) -> float:
    """What the rest of this animal's season is worth, product and manure.

    Priced at the margin rather than at the spot quote, because the fifth
    cow's milk sells into a market the first four have already flattened.
    """
    spec = ANIMALS[animal]
    horizon = max(0, LAST_DAY - day - int(spec["first"]))
    product = spec["product"]
    units = units_per_day(animal) * horizon
    return (
        marginal_price(observation, product) * units * 0.5
        + marginal_price(observation, "FERTILIZER") * max(0, LAST_DAY - day)
    )


def _jobs_for_tile(
    observation: dict[str, Any],
    tile: Any,
    day: int,
    inventory: dict[str, int],
    *,
    at_shed: bool,
    pen_kind: str | None,
    herd: str,
    empty_pens: dict[str, int],
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
        carrying_animal = any(int(inventory.get(a, 0)) > 0 for a in LIVESTOCK)
        if not carrying_animal:
            # An animal bought into the shed earns nothing until it reaches
            # a pen, so fetching one is worth its whole production stream --
            # but only if a pen of the right kind is standing empty.
            for name in LIVESTOCK:
                if int(shed.get(name, 0)) <= 0:
                    continue
                if empty_pens.get(ANIMALS[name]["structure"], 0) <= 0:
                    continue
                jobs.append((_stream_value(observation, name, day),
                             ["PICKUP", name, 1]))
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
        if pen_kind is not None:
            # Structures are free -- the simulator charges nothing for
            # BUILD_COOP or BUILD_PASTURE -- so a pen is worth half the
            # stream of the animal that will stand in it, discounted only
            # for the turn it costs and the wait for the animal.
            jobs.append(
                (_stream_value(observation, herd, day) * 0.5,
                 ["BUILD_COOP" if pen_kind == "COOP" else "BUILD_PASTURE"])
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
                    COLLECT_WEIGHT
                    * collect_fertilizer_value(observation, tile),
                    ["COLLECT_FERTILIZER"],
                )
            )
    elif kind in ("PASTURE", "COOP") and "animal" not in tile:
        for name in LIVESTOCK:
            if ANIMALS[name]["structure"] != kind:
                continue
            if int(inventory.get(name, 0)) <= 0:
                continue
            jobs.append(
                (_stream_value(observation, name, day), ["PLACE", name])
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
    """The best crop this worker could sow here, if a seed is spare.

    `seeds` is decremented by the caller as each worker is committed. It
    has to be: the seed store is shared, and without reserving against it
    every idle worker in the crew would independently decide to plant the
    same single strawberry. That is not hypothetical -- it produced 215
    PLANT actions for one crop in a game that could never have paid for a
    fifth of them, and all but a handful were no-ops that cost a
    worker-turn each.
    """
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
    herd: str,
    ranking: list[str],
    starving: int = 0,
    herd_worth: float = 0.0,
    fertilizable: int = 0,
) -> list[list[Any]]:
    """Spend in a fixed priority order out of one running budget.

    Independent per-line thresholds deadlocked this agent twice: seeds
    gated behind 300 coins meant it never planted and so never earned,
    and an ungated land rule spent the entire 3,000 opening on two
    quadrants it had no labour to farm. Priority order with a shared
    running balance avoids both, because every later item only sees what
    the earlier ones left behind.

    Order: sell, then labour, then land, then livestock, then seed, then
    emergency feed. Selling runs first because the order list is capped at
    ten a turn and its proceeds fund everything under it. Livestock sits
    above seed because an animal drops a fertilizer every day it lives.
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
    wheat_tiles = sum(
        1 for row in tiles for t in row
        if isinstance(t, dict) and t.get("crop") == "WHEAT"
    )
    animals_on_farm = sum(
        1 for row in tiles for t in row
        if isinstance(t, dict) and "animal" in t
    )
    herd_counts, empty_pens = herd_census(tiles)
    empty_pasture = sum(empty_pens.values())
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
    #    Reward is nothing but the money on the books at step 720, so
    #    anything still in the shed when the whistle blows scored zero.
    #    This agent finished a game holding 60 wheat, 14 milk, 14
    #    fertilizer and four unplaced cows -- several thousand coins left
    #    on the table -- so the last day sells the lot.
    closing = day >= LAST_DAY
    wheat_needed = 0 if closing else min(
        animals_on_farm * FEED_RESERVE_PER_ANIMAL, WHEAT_HOARD_CAP
    )
    # Fertilizer doubles what every watering adds for three days, so a
    # unit spread on wheat is worth about three extra units at wheat's
    # realised price against 36-53 sold. Holding it back was tried once
    # before and cost 12,000 coins, but that was a capital-starved agent
    # that needed the cash for animals; this one is not the same agent.
    fertilizer_needed = 0 if closing else min(fertilizable, FERTILIZER_HOLD_CAP)
    for item, quantity in sorted(shed.items()):
        if quantity <= 0 or item in ("COW", "SHEEP", "GOOSE"):
            continue
        sellable = quantity
        if item == "WHEAT":
            sellable = max(0, quantity - wheat_needed)
        elif item == "FERTILIZER":
            sellable = max(0, quantity - fertilizer_needed)
        # Selling is where this agent already beats every tape: it
        # realises 170 coins a unit on wool where a good route gets 34,
        # and 112 on strawberry against 69, because it sells less into a
        # less crowded market. The market is a shared pool the town drains
        # all game, so a unit held while its price is on the floor is
        # worth more a few days later. Sell down to the point where the
        # next unit stops paying -- unless cash is short, the shed is
        # filling toward its 100-unit cap, or the season is over.
        if (
            sellable > 0
            and SELL_FLOOR > 0.0
            and budget > SELL_CASH_FLOOR
            and sum(shed.values()) < SHED_PRESSURE
        ):
            sellable = min(sellable, headroom(observation, item, SELL_FLOOR))
        if sellable > 0:
            orders.append(["SELL", item, sellable])
            budget += live_price(observation, item) * sellable
    if SELL_PACE > 0.0:
        # Pace the whole list against what the town will actually eat.
        # E sells roughly a thousand units a game where the town absorbs
        # some 3,800 across both players, so unlike a high-volume tape it
        # is genuinely inside the town's appetite -- which is exactly the
        # condition under which holding a unit back raises its price
        # rather than merely postponing it. See rl/demand_sales.py.
        orders = paced_orders(
            observation, orders, pace=SELL_PACE,
            cash_floor=SELL_CASH_FLOOR, shed_pressure=SHED_PRESSURE,
            closing_day=LAST_DAY,
        )
    # 1. Labour. The nth hire of a day costs fib(n) with a multiplier of 1,
    #    so the first hands are close to free and each one multiplies every
    #    other purchase. Nothing outranks this.
    #    The crew does not persist: the simulator empties `farm["hands"]`
    #    at every day boundary and resets the hire counter with it, so the
    #    whole crew is re-hired each morning and the Fibonacci price starts
    #    again from one. Hiring three a turn therefore left this agent
    #    working short-handed through the first quarter of every single
    #    day. Fill the crew in the opening turn instead, up to the ten
    #    market orders a turn allows.
    room = MAX_ORDERS - len(orders)
    if hands < TARGET_HANDS and room > 0:
        for index in range(min(room, TARGET_HANDS - hands)):
            cost = _FIB[min(index + hands, len(_FIB) - 1)]
            if budget < cost + HIRE_FLOOR:
                break
            orders.append(["HIRE"])
            budget -= cost

    if closing:
        # Nothing bought on the final day can pay for itself, but the crew
        # still has a full day of harvesting and selling to do -- and the
        # hands are wiped every night, so skipping the hire here left the
        # farmer working the last day alone.
        return orders[:10]

    # 2. Land, as soon as the ground we hold is full. A quadrant is 25
    #    tiles for 1,000 coins and then 2,000; against eleven hands that is
    #    the cheapest capacity in the game, and it is the purchase this
    #    agent kept never making. Under the old rule -- 1,500 clear surplus
    #    on top of the price -- it farmed a single 25-tile quadrant for a
    #    whole season while a good route farmed 75, because it never held
    #    2,500 coins at once until day 22. Three quadrants, never four
    #    (section 9i).
    unlocked = len(farm.get("unlocked_quadrants") or [])
    land_price = {1: 1000, 2: 2000}.get(unlocked)
    used = plants + empty_pasture + animals_on_farm
    # The opening quadrant is 25 tiles, of which the pens take six, so a
    # crew of ten has nineteen crop tiles to work for the first third of
    # the game -- and it shows: 95 to 144 idle worker-turns a day through
    # day eleven, because there is genuinely nothing left to do. The second
    # quadrant costs 1,000 out of a 3,000 opening and doubles the board.
    # Waiting to earn it the slow way means never earning it, because the
    # farm that would earn it is the one being bought.
    opening = (
        unlocked < 3
        and land_price is not None
        and day <= OPENING_LAND_DAY
        and budget >= land_price + OPENING_LAND_RESERVE
    )
    if (
        unlocked < 3
        and land_price
        and (
            opening
            or (
                budget >= land_price + LAND_SURPLUS
                and open_ground <= LAND_OPEN_TRIGGER
                and used >= 18 * unlocked
            )
        )
    ):
        orders.append(["BUY_LAND"])
        budget -= land_price
        open_ground += 25

    # 3. Livestock, ahead of seed. An animal yields one fertilizer every
    #    single day it survives -- unconditionally, whether or not it was
    #    fed -- on top of its own product, so it is the highest-return
    #    purchase in the game and the only one whose return compounds with
    #    the days remaining. Buying seed first is what pinned this agent at
    #    ten coins from day two to day twenty: it spent the whole 3,000
    #    opening on melon and strawberry seed and could then afford neither
    #    hands nor animals.
    #    An animal eats one wheat every day and bolts after two missed
    #    meals, so the herd cannot outrun the feed supply. A wheat tile
    #    returns about six units every five days once it is watered through
    #    its window, so roughly one animal per wheat tile is what the farm
    #    can actually carry.
    #
    #    Ignoring that is how this agent lost whole games. On one seed it
    #    sold its melon crop on day eleven, spent every coin of it on
    #    eleven cows inside two turns, and then had neither the wheat to
    #    feed them nor the money to buy any: the herd starved from eleven
    #    head to zero by day fifteen, the crew abandoned the fields to
    #    chase the dying animals, all thirty-four plants went to weed, and
    #    the game ended on 485 coins. Buy one at a time, only against feed
    #    the farm can grow, and never down to the last coin.
    cost = ANIMALS[herd]["cost"]
    pen_free = int(empty_pens.get(str(ANIMALS[herd]["structure"]), 0))
    in_shed = sum(int(shed.get(a, 0)) for a in LIVESTOCK)
    carryable = int(
        wheat_tiles * WHEAT_UNITS_PER_TILE_DAY + shed.get("WHEAT", 0) / 4.0
    )
    if (
        herd_worth > 0
        and pen_free > in_shed
        and budget > cost + WORKING_CAPITAL
        and animals_on_farm + in_shed < carryable
        and day <= LAST_DAY - ANIMALS[herd]["first"] - 1
    ):
        orders.append(["BUY_ANIMAL", herd, 1])
        budget -= cost

    # 4. Seed, cheapest-and-fastest first, and never more than a working
    #    buffer. Ranking is by coins per tile-day, so wheat leads early and
    #    the slow premium crops only appear once there is ground and time
    #    to spare. The spend is capped at a share of what is left so a
    #    single turn can never drain the purse into the ground.
    seed_budget = budget * SEED_SPEND_SHARE
    for crop in ranking[:3]:
        if open_ground <= 0 or seed_budget <= 0:
            break
        have = seeds.get(crop, 0)
        cost = CROPS[crop]["seed"]
        want = min(SEED_BUFFER - have, open_ground)
        affordable = int(min(want, seed_budget // max(1, cost)))
        if affordable > 0:
            orders.append(["BUY_SEED", crop, affordable])
            budget -= cost * affordable
            seed_budget -= cost * affordable

    # 5. Feed. Wheat is grown, not bought. Every animal eats one wheat a
    #    day, so a seventeen-head herd needs some four hundred units over a
    #    season -- and because five of the eight town shops buy wheat, the
    #    market price of it runs at 40 to 48 against a base of 25 for the
    #    whole game. Buying that feed cost this agent more than the herd
    #    ever returned: it purchased 248 units at market while its animals
    #    produced 34 milk and 26 wool, and it sat at twenty coins from day
    #    two to day twenty-six as a result. So this buys only the emergency
    #    ration that keeps animals from bolting when the harvest is late.
    wheat_have = shed.get("WHEAT", 0)
    if starving > 0 and wheat_have <= 0 and budget > EMERGENCY_FEED_FLOOR:
        want = min(starving, 4)
        orders.append(["BUY_PRODUCT", "WHEAT", want])
        budget -= live_price(observation, "WHEAT") * want


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
    positions = _positions(farm)
    shed = _shed(observation)
    seeds = _seeds(observation)
    herd_counts, empty_pens = herd_census(tiles)
    herd, herd_worth = herd_plan(observation, day, herd_counts)
    ranking = crop_ranking(observation, day)

    # Feed comes before profit. One wheat per animal per day is the price
    # of keeping the herd alive, and a wheat tile returns roughly six units
    # every five days, so the standing wheat area has to track the herd or
    # the animals bolt and every coin sunk into them is lost. When the area
    # is short, wheat jumps the ranking -- both for what gets planted and
    # for what seed gets bought.
    wheat_tiles = sum(
        1
        for row in tiles
        for t in row
        if isinstance(t, dict) and t.get("crop") == "WHEAT"
    )
    animals_now = sum(
        1 for row in tiles for t in row if isinstance(t, dict) and "animal" in t
    )
    wheat_wanted = min(WHEAT_TILE_CAP, animals_now + 2)
    if wheat_tiles < wheat_wanted and "WHEAT" in ranking:
        ranking = ["WHEAT"] + [c for c in ranking if c != "WHEAT"]

    melons = sum(
        1
        for row in tiles
        for t in row
        if isinstance(t, dict) and t.get("crop") == "MELON"
    )
    pastures = sum(empty_pens.values()) + sum(herd_counts.values())
    # BUILD_PASTURE and BUILD_COOP cost nothing -- the simulator charges no
    # money for either -- so the only price of a pen is the tile it stands
    # on and the turn spent raising it. The old gate demanded twice an
    # animal's price in hand before laying a single pen, which is why this
    # agent capped out at six pens while a good route runs seventeen.
    #
    # What a pen must respect instead is feed. An animal eats a wheat a day
    # and bolts after two missed meals, so pens are built only as far as
    # the standing wheat can carry them; see the livestock note in
    # `_market_orders` for the game this rule was learned from.
    money = float(farm.get("money", 0.0))
    afford = int(money // ANIMALS[herd]["cost"])
    in_shed_animals = sum(int(shed.get(a, 0)) for a in LIVESTOCK)
    carrying = int(
        wheat_tiles * WHEAT_UNITS_PER_TILE_DAY + shed.get("WHEAT", 0) / 4.0
    )
    pen_kind = None
    if (
        herd_worth > 0
        and pastures < min(TARGET_PASTURES, carrying + 1)
        and pastures <= animals_now + in_shed_animals + afford + 1
        and day <= LAST_DAY - ANIMALS[herd]["first"] - 2
    ):
        pen_kind = str(ANIMALS[herd]["structure"])
    # An animal already paid for and sitting in the shed with nowhere to
    # stand is the worst thing on the farm: it cost 300 to 500 coins and it
    # earns nothing at all. This happened whenever the herd plan changed
    # its mind -- pens were raised as pastures, the plan later preferred
    # geese, and five geese sat in the shed from day 21 to the end of the
    # game. Whatever is in the shed gets a pen of its own kind first.
    for name in LIVESTOCK:
        if int(shed.get(name, 0)) <= 0:
            continue
        structure = str(ANIMALS[name]["structure"])
        if empty_pens.get(structure, 0) <= 0:
            pen_kind = structure
            break

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
    starving = sum(
        1
        for row in tiles
        for t in row
        if isinstance(t, dict)
        and "animal" in t
        and not t.get("fed_today")
        and int(t.get("consecutive_unfed", 0)) >= 1
    )

    budgeted_seeds = dict(seeds)
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

    # ---- the herd crew -------------------------------------------------
    # Animals are the densest work on the farm and the only work that
    # renews itself every single day without being asked: the simulator
    # sets `fertilizer_available` on every surviving animal at each daily
    # refresh, fed or not, so a seventeen-head herd is 374 free units a
    # season. E was collecting 51 a game against a good route's 453.
    #
    # It is not that the jobs are undervalued -- it is that they are far.
    # The square-of-distance discount that keeps waterers local also stops
    # anyone crossing the farm to a pasture. Relaxing that discount for
    # herd work was measured and cost 9,000 coins, because it pulled the
    # whole crew off the fields; a plant missed twice is a weed. So instead
    # a couple of hands are taken off the auction entirely and given the
    # pasture round as their job, which is how a person would run it.
    herd_jobs: list[tuple[int, int]] = []
    for y in range(len(tiles)):
        for x in range(len(tiles[y])):
            if (x, y) in claimed or not _owned(tiles, x, y):
                continue
            tile = tiles[y][x]
            if not (isinstance(tile, dict) and "animal" in tile):
                continue
            if (
                tile.get("fertilizer_available")
                or int(tile.get("yield_units", 0)) > 0
                or not tile.get("cared_today")
            ):
                herd_jobs.append((x, y))

    for _ in range(min(HERD_CREW, len(unassigned), len(herd_jobs))):
        best: tuple[float, int, tuple[int, int]] | None = None
        for worker in unassigned:
            for target in herd_jobs:
                gap = distance(positions[worker], target)
                if best is None or gap < best[0]:
                    best = (gap, worker, target)
        if best is None:
            break
        _, worker, target = best
        x, y = target
        tile = tiles[y][x]
        inventory = _inventory(observation, worker)
        if tile.get("fertilizer_available"):
            job = ["COLLECT_FERTILIZER"]
        elif int(tile.get("yield_units", 0)) > 0:
            job = ["HARVEST"]
        elif not tile.get("cared_today"):
            job = ["CARE"]
        elif not tile.get("fed_today") and int(inventory.get("WHEAT", 0)) > 0:
            job = ["FEED"]
        else:
            job = ["CARE"]
        position = positions[worker]
        actions[worker] = (
            list(job) if position == target
            else step_toward(position, target, list(job))
        )
        claimed.add(target)
        unassigned.discard(worker)
        herd_jobs.remove(target)

    for worker in sorted(unassigned):
        position = positions[worker]
        inventory = _inventory(observation, worker)
        best_score = 0.0
        best_action: list[Any] = list(PASS)
        best_job: list[Any] = list(PASS)
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
                    pen_kind=pen_kind,
                    herd=herd,
                    empty_pens=empty_pens,
                    fertilizable=fertilizable,
                    hungry=hungry,
                )
                if tile is None:
                    planted = _plant_jobs(
                        observation, day, ranking, budgeted_seeds, melons
                    )
                    if planted is not None:
                        options = options + [planted]
                for value, act in options:
                    score = _travel_score(value, travel)
                    if score > best_score:
                        best_score = score
                        best_target = (x, y)
                        best_job = list(act)
                        best_action = (
                            list(act)
                            if travel == 0
                            else step_toward(position, (x, y), list(act))
                        )

        if best_target is not None:
            claimed.add(best_target)
        # Reserve against the shared stores for the job this worker is
        # committed to, whether it is standing on the tile or still walking
        # to it. Without this the whole crew independently picks the same
        # single seed and eleven of the twelve PLANT actions are no-ops.
        if len(best_job) > 1 and best_job[0] == "PLANT":
            crop = str(best_job[1])
            budgeted_seeds[crop] = budgeted_seeds.get(crop, 0) - 1
            if crop == "MELON":
                melons += 1
        actions[worker] = best_action

    for worker, act in enumerate(actions):
        if act is None:
            actions[worker] = list(PASS)

    return {
        "farmer": actions[0],
        "hands": actions[1:],
        "market": _market_orders(
            observation, day, herd, ranking, starving, herd_worth,
            fertilizable,
        ),
    }


def agent(observation: dict[str, Any]) -> AgentAction:
    """Candidate E: demand-driven, value-scheduled, self-generated play."""
    return decide(observation)
