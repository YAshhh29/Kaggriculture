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

THE THREE LAYERS
----------------
* **Plan** (once a step, cheap). Prices every crop and every species at the
  *margin* -- what the next unit fetches once everything already growing has
  been sold and the town has eaten what it is going to eat -- and converts
  that into coins per worker-turn. Sets the crew, the herd, the crop mix and
  the land purchases. No fixed calendar decides what to grow.
* **Schedule** (the expensive part). Every job on the board is quoted in
  coins and in the turns it costs *including the walk*, and the best
  (worker, job) pairs are taken globally. A worker keeps the job it is
  walking to unless something clearly better appears.
* **Market** (free money, costs no worker turns). Meters the fragile books,
  ranks sales by the revenue a rival batch would take from them, keeps the
  order list inside the ten slots the engine reads, and liquidates at 718.

ENGINE RULES THIS AGENT IS BUILT ON
-----------------------------------
Each was read in `kaggriculture.py`, not assumed.

* `_new_plant` sets `consecutive_unwatered = 1`, and `_daily_refresh_plants`
  turns a plant to WEED at 2. **A tile sown and not watered the same day is
  dead by morning.** Planting therefore books its own watering turn.
* The same threshold means an *established* plant survives one dry day, so
  ongoing crops are watered every other day, not every day. That is half the
  watering labour on tomato and strawberry.
* For non-ongoing crops the yield bonus only lands for
  `age in [(max_yield_day+1)//2 .. max_yield_day]`, and FERTILIZE doubles it
  for three days. Wheat goes 4 units -> 6, carrot 3 -> 4.
* `_daily_refresh_animals` consumes `pending_care_bonus` only on a fed
  production day and accrues one per cared-and-fed day, so a tended animal
  yields `1 + interval` units per production event: 2 a day from a goose,
  3 every two days from a cow, 4 every three from a sheep.
* An animal escapes at `consecutive_unfed >= 2`, so it may be fed every
  other day, but it must be fed then.
* Glut curves differ per good. Units from equilibrium to the price floor:
  WOOL 59, STRAWBERRY 62, MILK 76, MELON 158, and WHEAT and EGG effectively
  never, because their curves are logarithmic. Fragile books are metered.
* `_town_consume` drains each unlocked shop's basket every four steps and
  the town centre takes one of every non-fertilizer good a day, so the price
  steps up at `step % 4 == 1` and is flat across the block. Selling at
  `step % 4 == 0` throws a tick of scarcity away.
* `_process_market` walks both players' orders by index at the same
  pre-commit inventory, a failed unit aborts its whole order, and orders past
  the tenth are dropped. Sales go first, inventory-priced buys next, and
  fixed-price orders (HIRE, BUY_LAND, BUY_SEED, BUY_ANIMAL) last -- but they
  must still *fit*, so the plan claims its slots before the sales do.
* Hiring is a daily rental on a fibonacci curve that resets each night: ten
  hands cost 143 coins for the day. Hands spawn at the shed, so the roster is
  built at hour 0 and left alone.
* FERTILIZER is in no shop basket and is excluded from the town centre's
  daily consumption, so nothing in the game consumes it and its price only
  decays, 100 -> 24. Spread on a watered wheat tile inside its window it is
  worth two extra wheat instead.
* Step 718 is the last action the interpreter processes and reward is
  `farm["money"]`, so anything unsold is worth zero.
"""

from __future__ import annotations

import sys
from typing import Any

from core.routing import distance, step_toward
from rl.demand import remaining_demand
from rl.economics import ANIMALS, CROPS
from rl.market import MARKET_PARAMS, inventory_of, price_at
from rl.runtime import AgentAction

# Set once if `decide` ever raises, so the traceback is printed a
# single time rather than 720 times.
_FAILED = False
PASS: list[str] = ["PASS"]
BOARD = 10
TURNS = 24
LAST_DAY = 29
LAST_ACT_STEP = 718
MAX_ORDERS = 10
SHED_CAP = 100

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
ANIMAL_HOME = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
STRUCTURE_ACTION = {"COOP": "BUILD_COOP", "PASTURE": "BUILD_PASTURE"}

# --- the plan ----------------------------------------------------------

# Share of the town's remaining appetite this farm counts on capturing when
# it prices a unit it has not grown yet. The town refills the scarcity side
# of every book it eats from, so a good with two shops behind it can absorb
# far more than its static glut depth -- which is the whole reason the herd
# mix has to be read from `town.unlocked_shops` rather than fixed.
# How much of the town's remaining appetite to credit against the book when
# pricing something that does not exist yet.
#
# At 0.5 this agent was myopic in the one way that matters. Playing a strong
# opponent, its milk sales collapsed from 317 units at 203 coins to 27 units
# at 118, and it filled the pasture with geese instead -- 248 eggs at 55 --
# because the rival's dumping had flooded the milk book and the forward price
# said milk was finished. It was not: the same game saw that rival earn
# 23,972 from milk, because three of the eight shop types eat it and the town
# drains the book all season. Crediting the whole appetite is worth about
# 7,400 a game; crediting twice it is worse than crediting half.
# The largest share of the flock that may be geese. The ladder's median herd
# is three geese to eight cows and six sheep.
# Measured on 12 games against our 2265-rated agent: at 0.3 the own score is
# 47,556, at 0.12 it is 54,770. The rule floors at two geese either way, so
# what this really says is that a handful of geese is right and a farm full
# of them is not -- an egg is 50 coins where milk is 160 and wool 200, and
# each animal costs the same three worker-turns a day to keep.
# Long-lead crops must go in early or their last cycles fall off the end of
# the season. See the rate calculation in make_plan.
# Measured and OFF (-1 disables both the eased wheat floor and the long-lead
# urgency below). Easing the wheat floor in the opening looked right -- a
# top-200 agent has twelve strawberry standing on day 6 where J had none --
# and against that one agent it did help. Against the other three it was a
# disaster: the own score fell from 59,190 to 27,248 against our 2265-rated
# agent and from 60,003 to 27,640 against another published one.
#
# The lesson is about method, not wheat: this was tuned against a single
# opponent, and a single opponent is not a ladder. Every change is now judged
# on the whole strong panel.
LONG_LEAD_DAYS = -1
LONG_LEAD_URGENCY = 3.0
# What a meal and a grooming are worth, as multipliers on their own returns.
#
# A fed animal that is also cared for accrues a bonus that lands as an extra
# unit on its next production day, so the pair roughly doubles what the
# animal makes. Over a full game this agent fed 147 times where a top-200
# agent fed 297 and cared 405, and sold 37 units of milk to that agent's 147.
FEED_WORTH = 1.0
CARE_WORTH = 0.9
# Turns charged against a new tile for every future visit it will need,
# per tile of distance from the shed. Keeps the farm compact.
# Measured and OFF: charging a new tile for the travel its whole life will
# cost drops the own score from 55,473 to 42,156 and shrinks the herd from
# 16-22 head to 8-14. It makes the farm compact by making it small.
SHED_PULL = 0.0
# How far a worker will travel for a job. The board is ten tiles across, so
# anything above nine is no limit at all.
JOB_RADIUS = 99
# Whether a crop's revenue is scaled by the book it will meet on the day it
# ripens rather than today's book.
ARRIVAL_PRICING = True
# Whether manure is spread on ongoing crops as well as the once-harvested
# ones. See the FERTILIZE branch in job_offers.
FERTILISE_ONGOING = True
# A meal is priced at the units it actually cashes -- on a production night,
# one plus every care day banked since the last event; on any other night,
# the single care day it lets us bank -- and then discounted by this share,
# which stands for the harvest turn behind each unit and the grain itself.
#
# Measured: pricing the production night at the full `(1 + pending) * price`
# with no discount made a sheep's meal worth 848 coins for one turn, which
# beat every crop in the auction. The flock's own numbers improved -- care
# days wasted fell 214 to 42, production rose 36% -- and the score fell
# 70,593 to 63,378 over sixty games, because the labour came out of the
# fields. The units were real; they were not worth what they displaced.
FEED_PRODUCTION_SHARE = 0.5
# What a watering is worth on an ongoing crop's production day, as a share of
# one unit. The engine only pays the manure bonus on a day the tile was also
# watered, so this and FERTILISE_ONGOING are a pair: fertilising without
# watering buys nothing at all. Setting it to zero restores the behaviour
# that priced an established strawberry's watering as pure upkeep.
WATER_ONGOING = 1.0
# Wheat's rate is multiplied while standing wheat is below this share of the
# floor, so grain is secured without starving every other crop of ground.
# Measured, and the blanket boost wins. Narrowing it so wheat is only urgent
# below 60% of the floor gives 54,686 against our 2265-rated agent where the
# blanket boost gives 68,722; at 85% it gives 61,450. The reasoning that led
# me to narrow it was sound -- strawberry returns about 49 coins a worker-turn
# against wheat's 23, and wheat was taking 145 sowings to strawberry's 13 --
# and the measurement disagreed. Grain underpins the flock, and the flock is
# where this farm's money is.
# Whether a crop past its book depth is dropped from the plan or merely
# discounted. See the cap in make_plan.
# Inventory the crop cap measures depth from. 10000 is the market's
# equilibrium; 0 means use the live book instead.
# Measured and reverted to the live book (0). Anchoring the cap at the
# market's equilibrium, so a rival's dumping cannot shrink our planting,
# costs 9,500 a game against our 2265-rated agent and 9,600 against the
# published one. Letting a saturated crop plant anyway at a quarter of its
# rate is worse still (58,136 against 68,722). The bare ground this agent
# leaves is not the disease: planting into a flooded book is worse than
# planting nothing, and the real problem is upstream of both.
# What a sowing is charged in the per-turn auction. The future waterings are
# already reserved in the labour budget, so weighting them here charges them
# twice.
# Passes of pairwise swaps over the turn's assignments, trading crossed
# journeys for shorter ones. 0 disables.
# Jobs that any worker can do, whatever it happens to be carrying.
# How much a tile beside existing work is preferred over one standing alone,
# and how far "beside" reaches.
# Measured and OFF: preferring tiles beside existing work costs 24,600 a game
# against our 2265-rated agent. Clustering the farm shrinks it, the same way
# every other repair aimed at walking has.
CLUSTER_BONUS = 0.0
CLUSTER_RADIUS = 2
# The most head this farm will keep. Each one costs about three worker-turns
# a day, and this farm delivers about 84 work turns a day in practice: at
# twenty head the flock eats three quarters of everything the crew does.
# Measured across two strong opponents, 12 games each (own scores summed):
# 13 head gives 127,488, twenty gives 120,486 and sixteen 119,457. Each
# animal costs about three worker-turns a day and this farm delivers about 84
# a day, so twenty head eat three quarters of everything the crew does and
# the crops get what is left.
# How strongly a pen prefers ground near the shed, per tile of distance.
PEN_SHED_PULL = 0.0
# The grid says the top of the ladder keeps seventeen head where we kept
# thirteen, and seventeen measures better across the field even though
# thirteen measured better against one opponent.
HERD_MAX = 17
PORTABLE_JOBS = ("PLANT", "WATER", "HARVEST", "DIG", "BUILD_COOP",
                 "BUILD_PASTURE", "COLLECT_FERTILIZER", "CARE")
# Measured and OFF. Swapping crossed journeys between workers looks free --
# the same jobs get done, by nearer hands -- and costs 28,000 a game against
# our 2265-rated agent while gaining 9,500 against the published one. Two
# reasons, both real: a swapped job may need what the other worker is
# carrying (fixed by PORTABLE_JOBS above, and it still loses), and a worker
# already walking toward a tile loses the commitment that is worth 5,142 a
# game. Shorter journeys are not the same thing as better ones.
SWAP_PASSES = 0
PLANT_TURN_COST = 2.0
PLANT_FUTURE_WEIGHT = 0.25
CAP_ANCHOR = 0.0
CAP_IS_SOFT = False
OVER_CAP_RATE = 0.25
WHEAT_URGENT = 1.0
WHEAT_BOOST = 4.0
GOOSE_SHARE = 0.12
TOWN_SHARE = 1.0
# Which goods each shop type consumes, from the engine's SHOPS table.
SHOP_BASKET = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
# Share of base price that a good the town consumes is worth over a long
# horizon, however flooded its book looks right now. Fertilizer is excluded:
# it is in no shop basket and the town centre does not take it, so nothing
# ever drains it and its price only decays.
# Measured and OFF. Flooring a long-horizon price at 0.8 of base costs
# 10,248 a game against our 2265-rated agent and 11,462 against the
# published top-200 one: it stops the rival's dump misleading this agent,
# and in exchange makes it pour goods into books that really are saturated.
# The town's appetite belongs in the inventory (see TOWN_SHARE), not as a
# floor under the price.
LONG_RUN_FLOOR = 0.0
TOWN_EATS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
             "EGG", "MILK", "WOOL")
# Fraction of the care bonus the crew actually manages to collect. An animal
# cared and fed every day yields `1 + interval` per event; one that misses
# care yields 1. The crew misses some.
CARE_RATE = 0.7
# Worker-turns one animal costs a day: feed on alternate days, care, collect
# the manure, and a harvest every second or third day.
ANIMAL_TURNS = 3.0
# The opening, as a plan rather than an emergent property. Sized from the
# top-200 corpus: cows and sheep inside the first three days in every strong
# team's game, four head by day 3.
OPENING_DAYS = 3
OPENING_HERD = (2, 3, 4, 4)
OPENING_MIX = {"COW": 2, "SHEEP": 2, "GOOSE": 1}
# Share of a crew's turns that is work rather than walking. H2, the best
# agent we have measured, runs 51.1%; G runs 41.6%.
WORK_SHARE = 0.5
# Crew size by day. Ten hands cost 143 coins for the day and are wiped every
# night, so this is a rental, not an investment; the limit is daylight.
# Hands are hired daily on a fibonacci curve that resets each night: the
# first five cost 1+1+2+3+5 = 12 coins for the day, the ninth alone costs 34
# and the eleventh 89. Measured over the first ten days of a live game, this
# agent paid 1,194 coins in wages where a top-200 agent paid 223 -- it was
# buying a full crew before it had ground for them to work, while the same
# coins would have bought the twenty strawberry seeds that agent planted.
#
# So the crew grows with the farm rather than ahead of it.
# Measured on the panel: a crew capped at nine is worth 67,177 against our
# 2265-rated agent where twelve gives 59,190 and seven gives 46,462. The
# fibonacci wage is only half the story -- the tenth and eleventh hands spend
# most of their turns walking to work somebody nearer would have done, and
# this farm already loses 1,444 turns a game to travel.
# The failure grid against ten top-200 teams says they run nine hands on day
# 12 and twelve by day 18; we ran nine all the way. Capping at nine was tuned
# against a single opponent and it cost breadth: with twelve late and a herd
# of seventeen, wins against fourteen different top teams go from 3% to 14%
# and the median score from 66,291 to 70,666.
HAND_RAMP = ((0, 4), (3, 6), (6, 8), (10, 9), (13, 12))
# Days on which the next quadrant is bought, and the cash each must leave
# behind. Two quadrants is 75 tiles, which is what a crew of twelve can work.
LAND_DAYS = (5, 9, 24)
LAND_PRICES = (1000.0, 2000.0, 4000.0)
LAND_RESERVE = 400.0
# The opening basket, in the shape the top-ten family runs: the field's own
# median day-0 spend is 7 wheat seed, 8 melon, 2 cow, 2 sheep and 9 wheat of
# feed, and the seven teams at ranks 1-10 differ from the 52-team fork only
# by holding back cash on day 0.
OPEN_FEED = 9
OPEN_MELON = 8
OPEN_WHEAT = 9
OPEN_COW = 2
OPEN_SHEEP = 2
OPEN_HIRES = 5

# --- the scheduler -----------------------------------------------------

# What a worker-turn is worth when the farm has nothing better to do. A job
# whose coins per turn fall below this is not worth the walk.
# The floor a job must clear to be worth a worker's turn. At 8 coins a turn
# this farm passed 401 times in its first ten days -- 26% of every turn it
# had -- while a top-200 agent passed 232 and watered 236 times to our 139.
# An idle turn is worth nothing at all, so the floor belongs near zero.
IDLE_TURN_VALUE = 0.5
# Turns charged per tile of travel. Measured against two strong opponents,
# 12 games each: at 1.0 the margin against the published top-200 agent is
# -78,619; at 2.0 it is -60,422; at 3.5 it slips back to -63,683 and the
# score against our own 2265-rated agent falls hard. Walking is not merely
# time lost, it is a watering not done, and pricing it at two turns a tile
# keeps the crew on the work in front of it.
WALK_COST = 2.0
# How much a worker prefers the job it is already walking to. Measured on our
# other agent: without it, 17.1% of travelling turns ended in a change of
# destination, and committing was worth +5,142 coins a game.
COMMIT_BONUS = 2.5
# How much a worker prefers a job on the tile it is already standing on,
# over and above the travel it saves. One is no preference at all.
STAY_BONUS = 1.0
# How much an in-window watering is worth over its face value. One is the
# honest price.
#
# Measured and left alone: the watering is not being outbid, it is not being
# offered. At two and a half times face the waterings per wheat went 1.11 to
# 1.22, at five times to 1.36, against a top-200 team's 2.10 -- and the score
# fell 67,551 to 64,924 to 59,208. The plant is gone before its second window
# day comes round, so paying more for a job that no longer exists only robs
# the richer work that does.
WINDOW_WATER = 1.0
# Whether a hungry flock may pull unfinished wheat when the shed is empty.
EARLY_WHEAT = True
# Whether two workers may work the same tile in one turn, each on a
# different job. The engine allows it -- and it loses. Measured: passes
# barely moved, 8.4% to 8.2%, so tile contention was never what idled the
# crew, and the score fell from 95,434 to 64,451 over the same three games
# because the pairs conflict. One hand harvests a plant while the other is
# still walking over to water it, and the watering lands on bare ground.
SHARE_TILES = False
# A plant dies the night it is sown unless it is watered, and an established
# one dies after two dry days. Rescue watering is priced at this share of the
# tile's whole remaining crop. Pricing it at the full value once collapsed an
# earlier agent to zero -- the crew watered all game and banked nothing -- so
# it stays a discount rather than a cliff.
WATER_RESCUE = 0.7
# Hours before dusk at which the crew stops starting new work and walks its
# harvest home. Goods in hand at the close are worth nothing.
CLOSING_STEPS = 10

# --- the market --------------------------------------------------------

# Books that collapse if sold in bulk, and the price, as a share of base,
# below which this agent will not push them on a normal turn.
FRAGILE = ("WOOL", "STRAWBERRY", "MILK", "MELON")
FRAGILE_FLOOR = 0.55
FRAGILE_PER_TURN = 6
MIN_SELL_PRICE = 2.0
# Slots. The engine reads ten orders; the plan claims first, because a farm
# that cannot hire or buy land is finished whatever it is selling.
PLAN_SLOTS = 6
# Feed bought from the market, capped per turn and confined to two hours a
# day. The skeleton bought eight units every turn it had the cash, which at
# thirty head is 5,700 coins a day and was the whole reason it never banked
# anything.
# Feed. An animal eats one wheat a day and escapes after two missed meals,
# and a wheat tile takes days to yield, so the opening flock lives on bought
# grain. Measured over the first ten days of a live game: this agent bought
# nine units and starved its five animals, while the agent beating it bought
# a hundred and eleven. Grain is the cheapest thing on the board at about
# thirty coins, against three hundred for the animal it keeps alive.
FEED_BUY_HOURS = (1, 7, 13, 19)
FEED_BUY_MAX = 14
# Days of eating to keep ahead of the flock, in grain standing plus stored.
# Days of eating to keep ahead of the flock. Four days of grain for every
# animal cost 3,183 coins over the opening where a top-200 agent spent 2,542,
# and the difference is seed that never got bought. An animal escapes only on
# its second missed meal, so two days of cover is the honest margin.
FEED_DAYS_AHEAD = 2

_EN_ROUTE: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}


# --- reading the world -------------------------------------------------

def _farm(observation: dict[str, Any]) -> dict[str, Any]:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    return farms[player] if player < len(farms) and isinstance(
        farms[player], dict) else {}


def _rival(observation: dict[str, Any]) -> dict[str, Any]:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    other = 1 - player
    return farms[other] if other < len(farms) and isinstance(
        farms[other], dict) else {}


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


_SHED_SET = set(shed_tiles())


def shed_distance(x: int, y: int) -> int:
    """Steps from this tile to the nearest shed-access tile."""
    return min(abs(x - sx) + abs(y - sy) for sx, sy in shed_tiles())


def _on_shed(x: int, y: int) -> bool:
    return (x, y) in _SHED_SET


def _owned(tiles: list[list[Any]], x: int, y: int) -> bool:
    return (0 <= y < len(tiles) and 0 <= x < len(tiles[y])
            and tiles[y][x] != "LOCKED")


# --- how much a tile or a beast is still going to produce ---------------

def crop_units(crop: str, plant_day: int) -> int:
    """Units a tile sown on `plant_day` still yields before the close.

    Non-ongoing crops start at one unit and gain one for every watering
    inside `[(max_day+1)//2 .. max_day]`, capped at `max_yield`; ongoing
    crops accrue one per interval from their first yield day.
    """
    spec = CROPS.get(crop)
    if spec is None:
        return 0
    first = int(spec["first"])
    if plant_day + first > LAST_DAY:
        return 0
    if spec["ongoing"]:
        interval = max(1, int(spec["interval"]))
        n = 0
        for k in range(int(spec["max_yield"])):
            if plant_day + first + k * interval <= LAST_DAY:
                n += 1
        return n
    start = (int(spec["max_day"]) + 1) // 2
    waters = sum(1 for age in range(start, int(spec["max_day"]) + 1)
                 if plant_day + age <= LAST_DAY)
    return min(int(spec["max_yield"]), 1 + waters)


def crop_span(crop: str, plant_day: int) -> int:
    """Days the tile is occupied, which is what its ground costs."""
    spec = CROPS[crop]
    if spec["ongoing"]:
        last = (plant_day + int(spec["first"])
                + (int(spec["max_yield"]) - 1) * max(1, int(spec["interval"])))
    else:
        last = plant_day + int(spec["max_day"])
    return max(1, min(LAST_DAY, last) - plant_day + 1)


def crop_turns(crop: str, plant_day: int) -> float:
    """Worker-turns the tile demands over its life, walking excluded.

    Sowing, the mandatory same-day watering, a rescue watering every other
    day outside the yield window, one watering a day inside it, and a
    harvest per pick-up.
    """
    spec = CROPS[crop]
    span = crop_span(crop, plant_day)
    units = crop_units(crop, plant_day)
    if spec["ongoing"]:
        waters = 1.0 + (span - 1) / 2.0
        return 1.0 + waters + units
    start = (int(spec["max_day"]) + 1) // 2
    window = sum(1 for age in range(start, int(spec["max_day"]) + 1)
                 if plant_day + age <= LAST_DAY)
    dry = max(0, start - 1)
    return 1.0 + 1.0 + dry / 2.0 + window + 1.0


def animal_units(animal: str, place_day: int) -> float:
    """Product units a beast placed on `place_day` still yields.

    `_daily_refresh_animals` accrues one care bonus per cared-and-fed day
    and consumes the lot on the next fed production day, so a tended animal
    returns `1 + interval` per event rather than one.
    """
    spec = ANIMALS.get(animal)
    if spec is None:
        return 0.0
    first, interval = int(spec["first"]), max(1, int(spec["interval"]))
    per_event = 1.0 + interval * CARE_RATE
    n = 0.0
    day = place_day + first
    while day <= LAST_DAY:
        n += per_event
        day += interval
    return n


# --- what a unit of a good is worth ------------------------------------

def _context(observation: dict[str, Any], day: int, step: int) -> dict[str, Any]:
    """Prices, town appetite and the supply this farm has already committed.

    `spot` is the engine's own quote for a unit sold right now. `forward`
    prices a unit that does not exist yet: it is quoted at the inventory the
    market will hold once everything already growing has been sold and the
    town has eaten its share, which is the only honest way to decide whether
    another cow is worth its pasture.
    """
    inv = {item: inventory_of(observation, item) for item in PRODUCTS}
    demand = remaining_demand(observation)
    credit = {item: float(demand.get(item, 0.0)) * TOWN_SHARE
              for item in PRODUCTS}
    town = observation.get("town") or {}
    shops = tuple(town.get("unlocked_shops") or ())
    return {"inv": inv, "credit": credit, "shops": shops,
            "spot": {item: max(1.0, price_at(item, inv[item]))
                     for item in PRODUCTS},
            "pipeline": {item: 0.0 for item in PRODUCTS}}


def town_rate(ctx: dict[str, Any], item: str) -> float:
    """Units a day the town takes off this book, from the shops it has drawn.

    `_town_consume` runs every four steps: each unlocked shop removes one of
    every product in its basket, or two when the shop sells a single product,
    and every twenty four steps the town centre removes one of every product
    except fertilizer. So a good in three shop baskets is drained eighteen
    units a day while one in none is drained a single unit, and that rate is
    the floor under its price for the rest of the season.
    """
    rate = 0.0
    for shop in ctx.get("shops", ()):  # shop instances, with repeats
        basket = SHOP_BASKET.get(shop, ())
        if item in basket:
            rate += (2.0 if len(basket) == 1 else 1.0) * (TURNS / 4.0)
    if item != "FERTILIZER":
        rate += 1.0
    return rate


def arrival_price(ctx: dict[str, Any], item: str, already: float,
                  days_ahead: float) -> float:
    """What a unit will fetch on the day it actually reaches the market.

    Pricing tomorrow's harvest at today's book is what let a rival's dumping
    talk this agent out of milk while that rival went on earning 24,000 from
    it. Between now and delivery the town keeps eating, so the book this
    produce will meet is today's less what the town will have taken.
    """
    drained = town_rate(ctx, item) * max(0.0, days_ahead)
    inv = ctx["inv"][item] + already - drained
    return max(1.0, price_at(item, inv))


def forward(ctx: dict[str, Any], item: str, already: float) -> float:
    inv = ctx["inv"][item] + already - ctx["credit"][item]
    price = max(1.0, price_at(item, inv))
    # A rival's dump is a dent in today's book; the town's appetite is the
    # shape of the whole season. Simulating 200 seasons of pure town drain
    # with nobody selling ends with milk at 311, strawberry at 293, melon at
    # 280 and wool at 246 -- every consumed good well above its base. So a
    # price used to judge something that will produce for days on end is
    # floored at a share of base, or a flooded book talks this agent out of
    # the very goods the town is about to pay most for.
    if LONG_RUN_FLOOR > 0 and item in TOWN_EATS:
        base = float(MARKET_PARAMS.get(item, {}).get("base", 1))
        price = max(price, base * LONG_RUN_FLOOR)
    return price


def forward_batch(ctx: dict[str, Any], item: str, already: float,
                  units: float) -> float:
    """Coins a batch of `units` fetches, walking the curve down as it goes."""
    n = int(units)
    total = sum(forward(ctx, item, already + k) for k in range(n))
    frac = units - n
    if frac > 0:
        total += frac * forward(ctx, item, already + n)
    return total


# --- one pass over the board -------------------------------------------

def census(ctx: dict[str, Any], tiles: list[list[Any]], day: int,
           shed: dict[str, int]) -> dict[str, Any]:
    """What exists, what is in danger, and what is still going to be sold."""
    out: dict[str, Any] = {
        "free": 0, "owned": 0, "animals": 0, "at_risk": 0, "unfed": 0,
        "empty_coops": 0, "empty_pastures": 0, "wheat": 0, "weeds": 0,
        "plants": 0,
    }
    for animal in ANIMAL_HOME:
        out["have_" + animal] = 0
    for crop in CROPS:
        out["crop_" + crop] = 0
    pipeline = ctx["pipeline"]
    for item, qty in shed.items():
        if item in pipeline:
            pipeline[item] += float(qty)
    labour = 0.0
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
                animal = str(tile.get("animal", ""))
                out["animals"] += 1
                out["have_" + animal] = out.get("have_" + animal, 0) + 1
                labour += ANIMAL_TURNS
                if not tile.get("fed_today"):
                    out["unfed"] += 1
                    if int(tile.get("consecutive_unfed", 0) or 0) >= 1:
                        out["at_risk"] += 1
                product = ANIMAL_PRODUCT.get(animal)
                if product:
                    pipeline[product] += (
                        float(tile.get("yield_units", 0) or 0)
                        + animal_units(animal, int(tile.get("placed_day", day)))
                        * max(0.0, (LAST_DAY - day)) / max(1.0, LAST_DAY))
            elif tile.get("kind") == "COOP":
                out["empty_coops"] += 1
            elif tile.get("kind") == "PASTURE":
                out["empty_pastures"] += 1
            elif tile.get("kind") == "WEED":
                out["weeds"] += 1
            elif tile.get("kind") == "PLANT":
                crop = str(tile.get("crop", ""))
                out["plants"] += 1
                out["crop_" + crop] = out.get("crop_" + crop, 0) + 1
                if crop == "WHEAT":
                    out["wheat"] += 1
                planted = int(tile.get("planted_day", day))
                span = max(1, crop_span(crop, planted))
                labour += crop_turns(crop, planted) / span
                if crop in pipeline:
                    pipeline[crop] += max(
                        float(tile.get("yield_units", 0) or 0),
                        float(crop_units(crop, planted)))
    out["labour_used"] = labour
    return out


# --- the plan ----------------------------------------------------------

def hands_wanted(day: int) -> int:
    target = HAND_RAMP[0][1]
    for when, n in HAND_RAMP:
        if day >= when:
            target = n
    return target


def sellable_tiles(ctx: dict[str, Any], crop: str, day: int) -> int:
    """How many tiles of this crop the book can actually absorb.

    Pricing a tile at today's quote is how this agent came to plant twenty
    four melons by day ten: with an empty pipeline the curve still quotes
    near base, so each melon looks like the best tile on the board, and by
    the time the forward price notices, a hundred and forty four units are
    on their way into a book that reaches the floor at a hundred and fifty
    eight. Melon is in no shop's basket at all -- only the town centre's one
    unit a day supports it.

    So the cap comes from the curve itself: units that can be sold before
    the price falls below half of base, divided by what a tile yields, and
    halved again because the opponent sells into the same book.
    """
    spec = CROPS.get(crop)
    if spec is None:
        return 0
    base = float(MARKET_PARAMS.get(crop, {}).get("base", 1))
    # Measure the book's depth from equilibrium, not from where a rival has
    # pushed it today. Reading the live inventory made this agent cede the
    # market: the opponent floods a book, our cap shrinks, we plant less, and
    # that opponent goes on selling 1,723 units to our 826 at the same prices
    # because the town keeps draining what it dumped.
    inv = CAP_ANCHOR if CAP_ANCHOR > 0 else ctx["inv"][crop]
    room = 0
    for n in range(0, 400, 4):
        if price_at(crop, inv + n) < base * 0.5:
            break
        room = n
    # The curve alone is only half the story: the town keeps eating, so a
    # good its shops consume has its book drained all season and can absorb
    # far more than one snapshot of the price suggests. Strawberry sits in
    # three of the eight shop baskets, and the agent beating us keeps 33
    # tiles of it and sells 48,209 where this cap allowed 7 tiles and left
    # twenty tiles of ground bare.
    room += max(0.0, float(ctx["credit"].get(crop, 0.0)))
    per_tile = max(1.0, float(crop_units(crop, day) or spec["max_yield"]))
    # Halved for the rival, who sells into the same book. Loosening this to a
    # third of base and dropping the halving was measured and is worse: own
    # score fell from 36,020 to 30,104 against one strong opponent and from
    # 41,465 to 26,589 against another. Filling ground with a crop whose
    # price has already collapsed is worse than leaving the tile bare.
    return max(1, int(room / per_tile / 2))


def make_plan(ctx: dict[str, Any], observation: dict[str, Any], day: int,
              step: int, counts: dict[str, Any], shed: dict[str, int],
              money: float) -> dict[str, Any]:
    """Crew, herd, crop mix and ground, all priced in coins per worker-turn.

    Nothing here is a calendar. The crop order and the species order come out
    of the marginal price of what they produce, which is a function of the
    shops this particular town drew, so a game with two yarn stores grows a
    flock and a game without one does not.
    """
    hands_target = hands_wanted(day)
    budget = (hands_target + 1) * TURNS * WORK_SHARE
    left = budget - counts["labour_used"]

    # Crops, best coins per worker-turn first. A crop that cannot reach its
    # first yield before the close is worth nothing, and `crop_units` already
    # returns zero for it.
    # Wheat gets a floor, and it is the one crop that does.
    #
    # Priced as a single tile, wheat looks poor: 130 coins against a
    # strawberry's 694. That comparison is wrong twice over. A wheat tile is
    # harvested and resown every five days while a strawberry holds its
    # ground for twenty, so per tile-day they are close; wheat's glut curve
    # is logarithmic, so its book absorbs thousands of units where
    # strawberry's floors after sixty two; and wheat is the only crop that
    # is also an input, since every animal eats one a day and starves in two.
    #
    # Measured against a live opponent: it keeps 18 to 30 wheat tiles and
    # waters 1,099 times a game, earning 19,962 from grain; this agent kept
    # 4 to 11 tiles, watered 545 times, and earned 9,500.
    # In the opening the flock is small and its grain can simply be bought,
    # while strawberry's ten-day clock cannot be bought back: a top-200 agent
    # has twelve strawberry standing on day 6 and twenty on day 9, where this
    # one had none until day 7 because the wheat floor took every slot.
    if day <= LONG_LEAD_DAYS:
        wheat_floor = max(4, counts["animals"])
    else:
        wheat_floor = max(10, int(counts["animals"] * 1.5))

    crops: list[tuple[float, str, float, float]] = []
    for crop in CROPS:
        # Ground already committed to this crop counts against its book.
        cap = sellable_tiles(ctx, crop, day)
        if crop == "WHEAT":
            cap = max(cap, wheat_floor)
        over_cap = counts.get("crop_" + crop, 0) >= cap
        if over_cap and not CAP_IS_SOFT:
            continue
        units = crop_units(crop, day)
        if units <= 0:
            continue
        # A crop is sold on the day it ripens, not today, and the town eats
        # the book in between. Pricing the batch at its arrival is what lets
        # a ten-day crop compete honestly with a five-day one.
        lead = max(0.0, float(CROPS[crop]["first"]))
        arrival = arrival_price(ctx, crop, ctx["pipeline"][crop], lead)
        spot_now = forward(ctx, crop, ctx["pipeline"][crop])
        revenue = forward_batch(ctx, crop, ctx["pipeline"][crop], units)
        if ARRIVAL_PRICING and spot_now > 0:
            revenue *= max(0.5, min(2.5, arrival / spot_now))
        revenue -= float(CROPS[crop]["seed"])
        turns = crop_turns(crop, day)
        span = max(1, crop_span(crop, day))
        if revenue <= 0:
            continue
        rate = revenue / turns
        # A crop past its book's depth is not worthless, it is merely cheap,
        # and an empty tile earns nothing at all. This agent stood at 27
        # crops with 13 bare tiles and 10 weeds on day 20, holding nine
        # strawberry seeds, because the cap struck the crop out of the plan
        # entirely instead of letting its own low price decide.
        if CAP_IS_SOFT and over_cap:
            rate *= OVER_CAP_RATE
        # Wheat is boosted only while the flock is genuinely short of grain,
        # not merely below its target. Harvesting a wheat tile destroys it,
        # so standing wheat is below the floor on almost every turn, and a
        # blanket boost let wheat take every sowing slot in the game: 145
        # sowings against 13 of strawberry, while the agent beating us sowed
        # 163 wheat AND 33 strawberry. Per worker-turn a strawberry tile
        # returns about 49 coins and a wheat tile 23.
        if (crop == "WHEAT"
                and counts.get("crop_WHEAT", 0) < wheat_floor * WHEAT_URGENT):
            rate *= WHEAT_BOOST
        # A crop's clock starts when it is sown, and strawberry and melon
        # both wait ten days for their first yield. Measured against a
        # top-200 agent on identical worlds, it holds 18,474 coins on day 12
        # where this agent holds 2,628 -- while owning MORE animals and a
        # similar number of plants. The assets were there; the revenue was
        # six days late, because the long-lead crops went into the ground
        # late. Every day of delay costs a whole cycle at the end.
        first = int(CROPS[crop]["first"])
        if day <= LONG_LEAD_DAYS and first >= 8:
            rate *= LONG_LEAD_URGENCY
        crops.append((rate, crop, revenue, turns / span))
    crops.sort(reverse=True)

    # Species, the same way. A beast is its product plus a unit of manure a
    # day, less the wheat it eats and the coins it costs.
    beasts: list[tuple[float, str, float]] = []
    tended = max(0, LAST_DAY - day)
    for animal in ANIMAL_HOME:
        product = ANIMAL_PRODUCT[animal]
        units = animal_units(animal, day)
        if units <= 0:
            continue
        revenue = forward_batch(ctx, product, ctx["pipeline"][product], units)
        revenue += tended * forward(ctx, "FERTILIZER",
                                    ctx["pipeline"]["FERTILIZER"]) * 0.5
        revenue -= tended * 0.5 * ctx["spot"]["WHEAT"]
        revenue -= float(ANIMALS[animal]["cost"])
        if revenue <= 0:
            continue
        beasts.append((revenue / max(1.0, ANIMAL_TURNS * tended), animal,
                       revenue))
    beasts.sort(reverse=True)

    # Ground. Two quadrants is seventy-five tiles, which is what a crew of
    # twelve can actually work; the third is only worth 4,000 coins when the
    # farm is already rich and the season still has room to use it.
    owned_quadrants = max(1, (counts["owned"] + 24) // 25)
    want_land = False
    idx = owned_quadrants - 1
    if idx < len(LAND_DAYS) and day >= LAND_DAYS[idx]:
        if money >= LAND_PRICES[idx] + LAND_RESERVE and counts["free"] <= 12:
            want_land = True

    # A hard ceiling on the flock, because `labour_left` is a per-turn view
    # and the purchase runs every turn: against a live opponent this bought
    # 104 animals in one game and stood at 34 head on day 20 with 18 plants,
    # while the agent it was losing to kept about 17 head and 57 plants. Two
    # things bound the herd -- the turns to tend it (feed, care, collect,
    # about three a day each) and the grain to feed it (one wheat a day,
    # against four units from a wheat tile over its window).
    tend_cap = int(budget // ANIMAL_TURNS)
    # Feed can be bought as well as grown, and in the opening it must be:
    # a wheat tile takes days to yield while an animal starts paying at once.
    # Counting only standing grain left the farm on one animal at day 10
    # against an opponent's ten, a hole it never climbed out of.
    # Grain can be bought again tomorrow out of what the farm earns, so the
    # purse is a flow, not a stock. Treating it as a stock stalled the herd
    # between days 5 and 10 -- five animals where the agent beating us had
    # eleven -- and an animal bought on day 5 banks twice the production
    # cycles of one bought on day 12.
    purchasable = money / 45.0 if day <= 12 else money / 240.0
    grain_cap = (counts.get("wheat", 0) * 4 + int(counts.get("shed_wheat", 0))
                 + int(purchasable))
    herd_cap = max(4, min(tend_cap, grain_cap, HERD_MAX))

    return {
        "hands_target": hands_target,
        "labour_budget": budget,
        "herd_cap": herd_cap,
        "labour_left": left,
        "crops": crops,
        "beasts": beasts,
        "best_beast": beasts[0][1] if beasts else None,
        "want_land": want_land,
        "tile_value": {crop: rev for _rate, crop, rev, _daily in crops},
        "crop_daily": {crop: daily for _rate, crop, _rev, daily in crops},
        "beast_value": {animal: rev for _rate, animal, rev in beasts},
    }


# --- jobs, priced in coins and turns -----------------------------------

def job_offers(ctx: dict[str, Any], plan: dict[str, Any], tile: Any,
               x: int, y: int, inventory: dict[str, int], day: int, step: int,
               shed: dict[str, int], seeds: dict[str, int],
               counts: dict[str, Any]) -> list[tuple[float, float, list[Any]]]:
    """Every job this tile offers, as (coins, turns, action).

    Coins are what the job puts on the books before the season ends; turns
    are what it costs to do, excluding the walk, which the caller adds.
    """
    jobs: list[tuple[float, float, list[Any]]] = []
    spot = ctx["spot"]
    closing = step >= LAST_ACT_STEP - CLOSING_STEPS
    hour = step % TURNS

    if _on_shed(x, y):
        # Goods being carried as inputs are not cargo: wheat while the flock
        # is unfed, manure while there is a tile worth spreading it on.
        # Counting them sent workers into a loop -- 130 pickups and 49 drops
        # in one day, the same grain travelling back and forth.
        holding_back = set()
        # Grain in a worker's hands is tomorrow's breakfast, not cargo. The
        # old test only held it back while an animal was hungry right now, so
        # once the round was done the leftovers were carried to the shed and
        # fetched again in the morning: 215 pickups for 147 feeds, against a
        # top-200 agent's 207 pickups for 297 feeds.
        # Measured: holding grain back all season (rather than only while an
        # animal is hungry) is 126,200 against 127,488 summed over two strong
        # opponents -- inside the noise, so the narrower test stays.
        if counts["unfed"] > 0 or counts["at_risk"] > 0:
            holding_back.add("WHEAT")
        if counts.get("fertilizable", 0) > 0:
            holding_back.add("FERTILIZER")
        carried = sum(int(qty) * spot.get(item, 0.0)
                      for item, qty in inventory.items()
                      if int(qty) > 0 and item in MARKET_PARAMS
                      and item not in holding_back)
        if carried > 0:
            # Only the shed feeds the market, and the nightly tip discards
            # whatever a worker is still holding over the cap.
            jobs.append((carried * (3.0 if closing else 1.0), 1.0, ["DROP"]))

        need_feed = counts["unfed"] + counts["at_risk"]
        carrying_beast = any(int(inventory.get(a, 0)) > 0 for a in ANIMAL_HOME)
        if (need_feed > 0 and int(inventory.get("WHEAT", 0)) <= 0
                and int(shed.get("WHEAT", 0)) > 0 and not closing
                and not carrying_beast):
            carry = min(10, int(shed.get("WHEAT", 0)), max(2, need_feed))
            # A pickup is worth the meals it enables, and a meal is worth the
            # stream it keeps alive when the animal has already missed one.
            worth = 0.0
            for animal in ANIMAL_HOME:
                head = counts.get("have_" + animal, 0)
                if head:
                    worth += (plan["beast_value"].get(animal, 0.0)
                              / max(1.0, LAST_DAY - day)) * min(head, carry)
            jobs.append((max(60.0, worth * 0.4), 1.0,
                         ["PICKUP", "WHEAT", carry]))
        if not closing and not carrying_beast:
            for animal, house in ANIMAL_HOME.items():
                waiting = int(shed.get(animal, 0))
                room = (counts["empty_coops"] if house == "COOP"
                        else counts["empty_pastures"])
                if waiting > 0 and room > 0:
                    jobs.append((plan["beast_value"].get(animal, 400.0), 1.0,
                                 ["PICKUP", animal, min(3, waiting, room)]))
                    break

    if tile is None:
        if closing or hour >= TURNS - 2:
            # A tile sown without a watering turn behind it is a weed by
            # morning, so the last hours of the day are not for sowing.
            return jobs
        for animal in ANIMAL_HOME:
            if int(inventory.get(animal, 0)) > 0:
                # A beast in hand with nowhere to stand: build for it here.
                jobs.append((plan["beast_value"].get(animal, 400.0), 1.0,
                             [STRUCTURE_ACTION[ANIMAL_HOME[animal]]]))
                return jobs
        best = plan.get("best_beast")
        if best is not None and plan["labour_left"] >= ANIMAL_TURNS:
            house = ANIMAL_HOME[best]
            waiting = int(shed.get(best, 0))
            room = (counts["empty_coops"] if house == "COOP"
                    else counts["empty_pastures"])
            # A pen is free but for the turn, and an animal cannot be bought
            # without one standing empty. Keep one ahead of the queue and no
            # more: an empty pen is a tile that grows nothing.
            herd = (counts["animals"]
                    + sum(int(shed.get(a, 0)) for a in ANIMAL_HOME))
            pens_total = (counts["empty_coops"] + counts["empty_pastures"]
                          + counts["animals"])
            if (room <= waiting
                    and herd < plan.get("herd_cap", 20)
                    and pens_total < plan.get("herd_cap", 20) + 1):
                # A pen is permanent and its occupant is visited three
                # times a day for the rest of the season -- fed, cared for,
                # and relieved of its manure. Measured at day 20, this farm's
                # pens sit 2.8 tiles from the shed where a top-200 agent's
                # sit 1.8, and with a dozen animals that extra step each way
                # is dozens of turns a day, every day. So a pen near the shed
                # is worth far more than the same pen in a corner.
                walk = shed_distance(x, y)
                jobs.append((plan["beast_value"][best] * 0.7
                             / (1.0 + PEN_SHED_PULL * walk), 1.0,
                             [STRUCTURE_ACTION[house]]))
        for _rate, crop, revenue, daily in plan["crops"]:
            if int(seeds.get(crop, 0)) <= 0:
                continue
            if plan["labour_left"] < daily:
                continue
            # Sowing books its own watering turn: the tile dies tonight
            # without it.
            # Where a tile is matters as much as what is on it. A crop is
            # visited again every day it is watered and once more when it is
            # harvested, and each of those visits is a walk from the shed and
            # back. This farm walks 4,298 turns a game where a top-200 agent
            # walks 2,854, and the difference is roughly the whole gap
            # between them. So a distant tile carries the travel its whole
            # life will cost, not just the step needed to sow it.
            visits = 1.0 + crop_turns(crop, day)
            lifetime_walk = SHED_PULL * visits * min(shed_distance(x, y), 6)
            # A sowing costs one turn now, plus the watering it books for
            # today. The waterings and the harvest it will want later are
            # already held back in the labour budget (`labour_used`), so
            # charging them here as well priced expansion out of the auction
            # entirely: on day 14 this farm had seven strawberry standing
            # against a cap of fifty eight, free ground, and seed in hand.
            near = counts.get("density", {}).get((x, y), 0)
            clustered = 1.0 + CLUSTER_BONUS * min(near, 8) / 8.0
            jobs.append((revenue * clustered, PLANT_TURN_COST
                         + crop_turns(crop, day) * PLANT_FUTURE_WEIGHT
                         + lifetime_walk, ["PLANT", crop]))
            break
        return jobs

    if not isinstance(tile, dict):
        return jobs

    kind = tile.get("kind")
    if "animal" in tile:
        animal = str(tile.get("animal", ""))
        product = ANIMAL_PRODUCT.get(animal, "EGG")
        held = int(tile.get("yield_units", 0) or 0)
        price = spot.get(product, 1.0)
        interval = max(1, int(ANIMALS[animal]["interval"]))
        stream = plan["beast_value"].get(animal, 0.0)
        # What the engine will settle on this animal tonight. `placed_day`,
        # `pending_care_bonus` and `yield_units` are all in the public tile,
        # so none of this has to be guessed.
        placed = int(tile.get("placed_day", 0) or 0)
        first = int(ANIMALS[animal]["first"])
        max_held = int(ANIMALS[animal]["max_held"])
        pending = int(tile.get("pending_care_bonus", 0) or 0)
        since = (day + 1) - placed - first
        yields_tonight = since >= 0 and since % interval == 0
        room = max(0, max_held - held)
        if not tile.get("fed_today") and int(inventory.get("WHEAT", 0)) > 0:
            if int(tile.get("consecutive_unfed", 0) or 0) >= 1:
                # It escapes tonight if this is missed: the whole stream.
                jobs.append((max(stream, price * 4.0), 1.0, ["FEED"]))
            elif yields_tonight and FEED_PRODUCTION_SHARE > 0.0:
                # Tonight the engine cashes every care day banked since the
                # last event -- and only if the animal was fed:
                #
                #     bonus = tile.pop("pending_care_bonus", 0)
                #             if tile["fed_today"] else 0
                #     ...
                #     tile["pending_care_bonus"] = 0
                #
                # so an unfed production night pays nothing and wipes the
                # lot anyway. For a sheep with three care days banked that
                # is four fleeces, not the 0.5-of-a-unit the flat estimate
                # below charged for it. This agent threw away 214 care days
                # in three games where a top-200 team threw away 42.
                gain = min(room, 1 + pending) * price
                jobs.append(((gain * FEED_PRODUCTION_SHARE
                              - spot.get("WHEAT", 25.0)) * FEED_WORTH,
                             1.0, ["FEED"]))
            elif not closing:
                # Any other night the meal yields nothing by itself. All it
                # buys is the right to bank one care day, worth a unit at
                # the next event, plus another day away from escaping. The
                # flat estimate this replaced charged a sheep 1.55 units for
                # that, which is why the flock was eating turns the crops
                # needed.
                jobs.append(((price * FEED_PRODUCTION_SHARE
                              - spot.get("WHEAT", 25.0)) * FEED_WORTH,
                             1.0, ["FEED"]))
        if held > 0:
            jobs.append((price * held, 1.0, ["HARVEST"]))
        if tile.get("fertilizer_available") and not closing:
            jobs.append((max(spot.get("FERTILIZER", 1.0),
                             counts.get("fert_worth", 0.0)), 1.0,
                         ["COLLECT_FERTILIZER"]))
        if (not tile.get("cared_today") and tile.get("fed_today")
                and not closing):
            # A cared, fed day accrues one extra unit on the next production
            # day, which is worth a unit of the product.
            jobs.append((price * CARE_WORTH, 1.0, ["CARE"]))
    elif kind in ("COOP", "PASTURE"):
        for animal, house in ANIMAL_HOME.items():
            if house == kind and int(inventory.get(animal, 0)) > 0:
                jobs.append((plan["beast_value"].get(animal, 400.0), 1.0,
                             ["PLACE", animal]))
                break
    elif kind == "PLANT":
        crop = str(tile.get("crop", ""))
        spec = CROPS.get(crop)
        if spec is None:
            return jobs
        price = spot.get(crop, 1.0)
        planted = int(tile.get("planted_day", day))
        age = day - planted
        units = int(tile.get("yield_units", 0) or 0)
        dry = int(tile.get("consecutive_unwatered", 0) or 0)
        remaining = max(0, crop_units(crop, planted) - units)
        tile_worth = remaining * price
        if not tile.get("watered_today"):
            gain = 0.0
            if not spec["ongoing"]:
                start = (int(spec["max_day"]) + 1) // 2
                if start <= age <= int(spec["max_day"]):
                    step_up = (2 if int(tile.get("fertilized_until_day", -1))
                               >= day else 1)
                    room = max(0, int(spec["max_yield"]) - units)
                    # The engine adds the unit here and nowhere else:
                    #     if window_start <= age_days <= max_yield_day:
                    #         tile["yield_units"] += 2 if manured else 1
                    # One turn, one unit, so the honest price is the unit.
                    # But a wheat unit is 37 coins against a melon's 262, so
                    # the auction leaves grain unwatered while hands stand
                    # idle: this farm waters a wheat 1.11 times inside its
                    # window against a top-200 team's 2.10, and pulls 2.24
                    # units a plant against their 3.72. Its melons, worth
                    # servicing, get 5.00 waterings and beat them outright.
                    gain = price * min(step_up, room) * WINDOW_WATER
            else:
                # `_daily_refresh_plants` settles the day at dusk, and the
                # manure bonus is conditional on the water:
                #
                #     fertilized = was_watered and fertilized_until_day >= day
                #     yield_units += 2 if fertilized else 1
                #
                # so on a production day, watering an established strawberry
                # is not upkeep -- it is the second unit, about 170 coins for
                # one turn. Pricing it at zero is why this agent sowed 66
                # strawberries to a top-200 team's 116 and harvested 219 to
                # their 858: it was paying for the manure and then letting
                # the bonus lapse for want of a watering can.
                since = (day + 1) - planted - int(spec["first"])
                interval = max(1, int(spec["interval"]))
                count = since // interval + 1
                room = max(0, int(spec["max_yield"]) - units)
                if (since >= 0 and since % interval == 0 and room > 0
                        and count <= int(spec["max_yield"])
                        and int(tile.get("fertilized_until_day", -1)) >= day):
                    gain = price * WATER_ONGOING
            # An unwatered plant dies tonight if it is already one day dry.
            # An established one survives a day, so ongoing crops are watered
            # every other day and the labour halves.
            rescue = tile_worth * WATER_RESCUE if dry >= 1 else 0.0
            value = max(gain, rescue)
            if value > 0:
                jobs.append((value, 1.0, ["WATER"]))
        if (FERTILISE_ONGOING and int(inventory.get("FERTILIZER", 0)) > 0
                and spec["ongoing"] and not closing
                and int(tile.get("fertilized_until_day", -1)) < day):
            # `_daily_refresh_plants` gives an ongoing crop two units instead
            # of one on a production day when the tile was fertilized AND
            # watered. Manure lasts three days, so one turn can cover a
            # strawberry's next production and sometimes the one after -- and
            # a strawberry unit is worth about 170 coins against the 58 the
            # manure would fetch sold. This agent fertilised only the crops
            # that are harvested once, and sold 134 strawberry units where a
            # top-200 agent sold 247.
            interval = max(1, int(spec["interval"]))
            first = int(spec["first"])
            since = day - planted - first
            covered = sum(1 for ahead in (0, 1, 2)
                          if since + ahead >= 0
                          and (since + ahead) % interval == 0
                          and day + ahead <= LAST_DAY - 1)
            room = max(0, int(spec["max_yield"]) - units)
            gain = min(covered, room)
            worth = gain * price - spot.get("FERTILIZER", 1.0)
            if worth > 0:
                jobs.append((worth, 1.0, ["FERTILIZE"]))
        if (int(inventory.get("FERTILIZER", 0)) > 0 and not spec["ongoing"]
                and int(tile.get("fertilized_until_day", -1)) < day
                and not closing):
            start = (int(spec["max_day"]) + 1) // 2
            window = [a for a in range(max(age, start), int(spec["max_day"]) + 1)
                      if planted + a <= LAST_DAY]
            plain = min(int(spec["max_yield"]) - units, len(window))
            doubled = min(int(spec["max_yield"]) - units,
                          sum(2 if k < 3 else 1 for k in range(len(window))))
            gain = max(0, doubled - plain)
            worth = gain * price - spot.get("FERTILIZER", 1.0)
            if worth > 0:
                jobs.append((worth, 1.0, ["FERTILIZE"]))
        if units > 0 and age >= int(spec["first"]):
            done = units >= int(spec["max_yield"])
            ripe = age >= int(spec["max_day"]) or done or closing
            if spec["ongoing"] or ripe:
                jobs.append((price * units, 1.0, ["HARVEST"]))
            elif (EARLY_WHEAT and counts["at_risk"] > 0 and crop == "WHEAT"
                  and not shed.get("WHEAT")):
                # Grain for a starving animal, taken from a plant that is
                # not finished. It costs everything the plant had left: a
                # wheat pulled at two carries two units where four days and
                # two waterings would have made six.
                jobs.append((price * units, 1.0, ["HARVEST"]))
    elif kind == "WEED":
        if not closing and plan["crops"]:
            # A weed is a tile that could be growing the best crop we have.
            jobs.append((plan["crops"][0][2] * 0.5, 1.0, ["DIG"]))
    return jobs


# --- the market ---------------------------------------------------------

def _rival_standing(observation: dict[str, Any]) -> dict[str, float]:
    """Ripe units on the other farm, which is public and is a real threat."""
    out = {item: 0.0 for item in PRODUCTS}
    farm = _rival(observation)
    for row in farm.get("tiles") or []:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            units = float(tile.get("yield_units", 0) or 0)
            if units <= 0:
                continue
            if "animal" in tile:
                item = ANIMAL_PRODUCT.get(str(tile.get("animal", "")))
            elif tile.get("kind") == "PLANT":
                item = str(tile.get("crop", ""))
            else:
                item = None
            if item in out:
                out[item] += units
    return out


def sale_lots(ctx: dict[str, Any], shed: dict[str, int], counts: dict[str, Any],
              closing: bool, cramped: bool) -> list[tuple[float, str, int]]:
    """How many units of each good to offer now, and how urgent each lot is.

    Fragile books are metered: sixty units of wool takes it from 200 coins to
    1 and leaves it there for the rest of the game, for us and for the rival.
    The ranking is the revenue the lot loses if a plausible rival batch lands
    at a lower index than ours, which sorts the collapsing goods to the front
    without a hand-written priority list.
    """
    lots: list[tuple[float, str, int]] = []
    feed_reserve = 0 if closing else min(14, counts["animals"] * 2)
    for item in PRODUCTS:
        held = int(shed.get(item, 0))
        if item == "WHEAT":
            held = max(0, held - feed_reserve)
        if held <= 0:
            continue
        inv = ctx["inv"][item]
        price = ctx["spot"][item]
        if closing:
            lots.append((1e9 + price * held, item, held))
            continue
        if price < MIN_SELL_PRICE:
            continue
        if item in FRAGILE and not cramped:
            base = float(MARKET_PARAMS[item]["base"])
            room = 0
            while room < held and room < FRAGILE_PER_TURN:
                if price_at(item, inv + room) < base * FRAGILE_FLOOR:
                    break
                room += 1
            held = room
            if held <= 0:
                continue
        batch = ctx["rival_batch"].get(item, 8.0)
        loss = (sum(price_at(item, inv + j) for j in range(held))
                - sum(price_at(item, inv + batch + j) for j in range(held)))
        lots.append((loss + price * held * 0.001, item, held))
    lots.sort(reverse=True)
    return lots


def market_orders(ctx: dict[str, Any], observation: dict[str, Any],
                  plan: dict[str, Any], day: int, step: int,
                  counts: dict[str, Any], shed: dict[str, int],
                  seeds: dict[str, int], money: float,
                  hands: int) -> list[list[Any]]:
    """Ten slots, and the plan claims its share before the sales do.

    `_process_market` walks both players' orders by index and quotes each
    side at the same pre-commit inventory, so a sale at a low index brings in
    cash and frees shed room before anything that needs either. A unit that
    fails aborts its whole order, and the tenth order is the last one read --
    which is why the skeleton, emitting nine sell orders first, could not
    hire or buy land once its shed held five goods.
    """
    hour = step % TURNS
    if step == 0:
        # Buy only the feed actually needed, at index 0 of turn 0, while the
        # market is untouched and the shed is empty. The tape families' large
        # wheat round trip is cash-neutral in isolation and loses badly once
        # a rival trades inside the same lockstep window.
        return [["BUY_PRODUCT", "WHEAT", OPEN_FEED],
                ["BUY_ANIMAL", "COW", OPEN_COW],
                ["BUY_ANIMAL", "SHEEP", OPEN_SHEEP],
                ["BUY_SEED", "MELON", OPEN_MELON],
                ["BUY_SEED", "WHEAT", OPEN_WHEAT],
                *[["HIRE"] for _ in range(OPEN_HIRES)]]

    total_shed = sum(int(v) for v in shed.values())
    closing = step >= LAST_ACT_STEP - 1
    cramped = total_shed >= SHED_CAP - 12 or hour == TURNS - 1

    if closing:
        lots = sale_lots(ctx, shed, counts, True, True)
        return [["SELL", item, qty] for _r, item, qty in lots][:MAX_ORDERS]

    # The crew, at dawn, before anything else. Hands spawn at the shed and a
    # hand hired after hour two cannot finish a watering tour, so the whole
    # roster is bought in one order block and then left alone.
    if hour == 0 and hands < plan["hands_target"]:
        return [["HIRE"] for _ in range(
            min(MAX_ORDERS, plan["hands_target"] - hands))]

    fixed: list[list[Any]] = []
    buys: list[list[Any]] = []
    budget = money

    if hour <= 2 and hands < plan["hands_target"]:
        for _ in range(min(3, plan["hands_target"] - hands)):
            fixed.append(["HIRE"])

    if plan["want_land"]:
        fixed.append(["BUY_LAND"])
        owned_quadrants = max(1, (counts["owned"] + 24) // 25)
        budget -= LAND_PRICES[min(2, owned_quadrants - 1)]

    # Feed, confined to two hours a day and capped. Wheat carries an
    # obligation no other good has, but buying it every turn the purse allows
    # is how the skeleton spent five thousand coins a day on grain.
    if hour in FEED_BUY_HOURS and counts["animals"] > 0:
        standing = counts["wheat"] * 4 + int(shed.get("WHEAT", 0))
        short = counts["animals"] * FEED_DAYS_AHEAD - standing
        if short > 0 and budget > 90 and total_shed < SHED_CAP - 10:
            want = min(short, FEED_BUY_MAX,
                       int((budget - 60) // max(1.0, ctx["spot"]["WHEAT"])))
            if want > 0:
                buys.append(["BUY_PRODUCT", "WHEAT", want])
                budget -= ctx["spot"]["WHEAT"] * want

    # The opening, days 0 to 3. Left to the value model, J spends these days
    # planting melon -- a good in no shop's basket -- and owns one animal on
    # day 10 where a strong opponent owns thirteen and is already earning
    # from them. Across 1,006 replays of the current top 200, every one of
    # the nine strongest teams buys cows and sheep inside the first three
    # days; a cow returns milk from day 8 every second day and a sheep wool
    # from day 6, so a day lost at the start is a day lost at the end.
    #
    # This is our own schedule, sized from the measured field: four head in
    # the first three days, cattle first because milk starts earlier and
    # feeds the deeper book, and enough grain bought to keep them alive
    # until the wheat comes in.
    if day <= OPENING_DAYS and hour <= 3:
        herd = counts["animals"] + sum(int(shed.get(a, 0)) for a in ANIMAL_HOME)
        want = OPENING_HERD[min(day, len(OPENING_HERD) - 1)]
        if herd < want:
            for animal in ("COW", "SHEEP", "GOOSE"):
                cost = float(ANIMALS[animal]["cost"])
                have = counts.get("have_" + animal, 0) + int(shed.get(animal, 0))
                if have >= OPENING_MIX.get(animal, 0):
                    continue
                if budget >= cost + 80:
                    fixed.append(["BUY_ANIMAL", animal, 1])
                    budget -= cost
                    break

    # A beast, once there is a pen standing empty for it and the crew has the
    # turns to tend it.
    best = plan.get("best_beast")
    herd_now = counts["animals"] + sum(int(shed.get(a, 0)) for a in ANIMAL_HOME)
    if (best is not None and plan["labour_left"] >= ANIMAL_TURNS
            and herd_now < plan.get("herd_cap", 20)
            and total_shed < SHED_CAP - 4):
        house = ANIMAL_HOME[best]
        room = (counts["empty_coops"] if house == "COOP"
                else counts["empty_pastures"])
        cost = float(ANIMALS[best]["cost"])
        # A goose costs 300 where a sheep costs 500, so on a thin purse the
        # cheap animal is the only one affordable at the moment of asking --
        # and this farm filled itself with nineteen geese while its own
        # ranking said sheep, then cow, then goose. Per animal-day a goose
        # returns about 50 coins, a cow 80 and a sheep 66, and the top of the
        # ladder keeps a median of three geese to eight cows and six sheep.
        # So the flock is capped by kind: save the coins instead.
        herd_kind = counts.get("have_" + best, 0) + int(shed.get(best, 0))
        share_cap = int(plan.get("herd_cap", 20) * GOOSE_SHARE)
        if best == "GOOSE" and herd_kind >= max(2, share_cap):
            pass
        elif room > int(shed.get(best, 0)) and budget >= cost + 120:
            fixed.append(["BUY_ANIMAL", best, 1])
            budget -= cost

    # Seed for ground the crew can actually sow and water.
    sown = sum(int(v) for v in seeds.values())
    room = max(0, counts["free"] + counts["weeds"] - sown)
    # Seed is the cheapest thing that turns an idle tile into a crop: ten
    # coins for wheat, twenty for carrot. Buying four at a time from the top
    # two crops only, and only while fewer than three sit unsown, held this
    # farm to 33 planted tiles where the agent beating it had 58 -- it
    # commits 63 seed purchases in the first ten days against our 23.
    for _rate, crop, _revenue, daily in plan["crops"][:3]:
        if len(fixed) >= PLAN_SLOTS - 1 or room <= 0:
            break
        if plan["labour_left"] < daily:
            break
        price = float(CROPS[crop]["seed"])
        # In the opening, seed competes with livestock for the same purse and
        # loses: a sheep bought on day 2 sells wool from day 6 and a cow milk
        # from day 8, while the agent beating us reaches eleven head and
        # 10,774 coins by day 10 where we sit on five head and 69 coins.
        # So the early purse keeps enough back for the next animal.
        # Seed is the investment, not the luxury: a top-200 agent spends 2,000
        # coins on strawberry seed inside the first six days and still holds
        # 1,388 on day 6, while this one bought a single seed and sat on its
        # purse. Long-lead seed is worth going thin for, because its clock
        # cannot be bought back later.
        long_lead = int(CROPS[crop]["first"]) >= 8
        floor = 120.0 if (long_lead and day <= LONG_LEAD_DAYS) else (
            420.0 if day <= OPENING_DAYS + 3 else 100.0)
        want = min(8, room, int(max(0.0, budget - floor) // price))
        if int(seeds.get(crop, 0)) < 6 and want > 0:
            fixed.append(["BUY_SEED", crop, want])
            budget -= price * want
            room -= want

    plan_orders = (buys + fixed)[:PLAN_SLOTS]
    # A sale at `step % 4 == 0` is quoted before that step's town tick and
    # throws a tick of scarcity away, so on a quiet turn the sale waits.
    quiet = step % 4 == 0 and not cramped
    slots = MAX_ORDERS - len(plan_orders)
    sells: list[list[Any]] = []
    if slots > 0 and not quiet:
        lots = sale_lots(ctx, shed, counts, False, cramped)
        sells = [["SELL", item, qty] for _r, item, qty in lots[:slots]]
    # Sales first: they add cash and free shed room before anything that
    # needs either. Inventory-priced buys next. Fixed-price orders last,
    # because their index does not move their price.
    # Only ten orders are read, and the engine drops the rest in silence.
    # Sales belong first -- they bring the cash and the shed room everything
    # else needs -- but nine of them will bury a HIRE that costs one coin and
    # buys a whole day of labour, or the land the farm is saving for. So the
    # cheap, decisive orders keep their slots and sales take what is left,
    # richest first.
    room_for_sales = max(1, MAX_ORDERS - len(buys) - len(fixed))
    if len(sells) > room_for_sales:
        sells.sort(key=lambda o: -ctx["spot"].get(o[1], 1.0) * int(o[2]))
        sells = sells[:room_for_sales]
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
    money = float(farm.get("money", 0.0) or 0.0)

    ctx = _context(observation, day, step)
    ctx["rival_batch"] = {
        item: min(24.0, max(8.0, units))
        for item, units in _rival_standing(observation).items()}
    counts = census(ctx, tiles, day, shed)
    # Where the farm's work already is. A tile sown beside four others will
    # be watered by a worker who is already standing there; one sown alone in
    # a far corner books a journey every day of its life. This farm spends
    # 57% of its turns walking where a top-200 agent spends 42%, and the
    # difference is roughly the production it is missing.
    density: dict[tuple[int, int], int] = {}
    if CLUSTER_BONUS > 0:
        active = [(x, y)
                  for y, row in enumerate(tiles)
                  for x, t in enumerate(row)
                  if isinstance(t, dict)
                  and (t.get("kind") == "PLANT" or "animal" in t)]
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                near = sum(1 for ax, ay in active
                           if abs(ax - x) + abs(ay - y) <= CLUSTER_RADIUS)
                density[(x, y)] = near
    counts["density"] = density
    counts["money"] = money
    plan = make_plan(ctx, observation, day, step, counts, shed, money)
    # Manure is worth the greater of what it fetches and what it adds to a
    # tile. It is in no shop basket and the town centre skips it, so nothing
    # in the game consumes it and its price only decays, 100 -> 24; spread on
    # a watered wheat tile inside its window it is two extra wheat.
    counts["fert_worth"] = max(ctx["spot"]["FERTILIZER"],
                               ctx["spot"]["WHEAT"] * 2.0)
    counts["fertilizable"] = counts.get("crop_WHEAT", 0) + counts.get(
        "crop_CARROT", 0)

    # Every (worker, job) pair, priced in coins per turn including the walk.
    candidates: list[tuple[float, int, tuple[int, int], list[Any]]] = []
    for worker, position in enumerate(positions):
        inventory = _inventory(observation, worker)
        held = _EN_ROUTE.get((player, worker))
        for y in range(len(tiles)):
            row = tiles[y]
            for x in range(len(row)):
                if row[x] == "LOCKED" and not _on_shed(x, y):
                    continue
                travel = distance(position, (x, y))
                for coins, turns, action in job_offers(
                        ctx, plan, row[x], x, y, inventory, day, step,
                        shed, seeds, counts):
                    rate = coins / max(0.5, turns + travel * WALK_COST)
                    if (held is not None and held[0] == (x, y)
                            and held[1] == action[0]):
                        # Still applies on arrival: `_EN_ROUTE` keeps the
                        # target until the booking loop clears it, so the
                        # turn a worker reaches its tile is the turn the
                        # commitment matters most.
                        rate *= COMMIT_BONUS
                    if travel == 0:
                        # Finish what is under your feet. A top-200 team
                        # does 51% of its jobs without taking a step and
                        # this farm manages 37.9%, on a board where the work
                        # sits at the same distance from the shed for both
                        # -- mean ring 2.53 against 2.66. The geography is
                        # not the difference; re-auctioning every hand
                        # against the whole board every turn is, because a
                        # hand that has just fed an animal gets pulled away
                        # before it cares for it.
                        rate *= STAY_BONUS
                    # A worker that will not cross the farm for a job leaves
                    # that job to whoever is already near it. Walking is 4,298
                    # turns a game here against a top-200 agent's 2,854, and
                    # every one of those turns is a watering not done.
                    if travel > JOB_RADIUS and action[0] not in ("DROP",):
                        continue
                    if rate > IDLE_TURN_VALUE:
                        candidates.append((rate, worker, (x, y), list(action)))

    candidates.sort(key=lambda c: -c[0])
    chosen: dict[int, list[Any]] = {}
    claimed: set[tuple[tuple[int, int], str]] = set()
    booked: list[tuple[int, tuple[int, int], list[Any], int]] = []
    planted_now: dict[str, int] = {}
    for _rate, worker, cell, action in candidates:
        # One worker per tile per turn. The engine would allow two, each on
        # a different job, and SHARE_TILES tries exactly that -- see the
        # constant for why it loses. The crew is not idle for want of ground
        # to stand on: passes barely moved when the tile was freed.
        key = (cell, action[0]) if SHARE_TILES else (cell, "")
        if worker in chosen or key in claimed:
            continue
        if action[0] == "PLANT":
            # Atomic PLANT validation: if the turn's requests for a crop
            # exceed the seeds held, the interpreter drops every one of them.
            crop = action[1]
            if planted_now.get(crop, 0) + 1 > int(seeds.get(crop, 0)):
                continue
            planted_now[crop] = planted_now.get(crop, 0) + 1
        if action[0] == "PICKUP" and int(shed.get(action[1], 0)) <= 0:
            continue
        travel = distance(positions[worker], cell)
        chosen[worker] = (action if travel == 0
                          else step_toward(positions[worker], cell, action))
        booked.append((worker, cell, action, travel))
        if action[0] not in ("DROP", "PICKUP"):
            claimed.add(key)
        # Claim the consumable this job will spend, so two workers do not
        # both plan to place the last animal or spend the last grain.
        if action[0] == "PICKUP" and len(action) > 2:
            shed[action[1]] = max(0, int(shed.get(action[1], 0)) - int(action[2]))
        elif action[0] == "FEED":
            counts["unfed"] = max(0, counts["unfed"] - 1)
        elif action[0] in ("BUILD_COOP", "BUILD_PASTURE"):
            key = ("empty_coops" if action[0] == "BUILD_COOP"
                   else "empty_pastures")
            counts[key] += 1
            plan["labour_left"] -= ANIMAL_TURNS
        elif action[0] == "PLACE":
            key = ("empty_coops" if ANIMAL_HOME[action[1]] == "COOP"
                   else "empty_pastures")
            counts[key] = max(0, counts[key] - 1)
            counts["animals"] += 1

    # Greedy by rate crosses the farm: the best job goes to whoever values it
    # most, not to whoever stands nearest, so two workers can walk past each
    # other to reach each other's tiles. This farm spends 4,298 turns a game
    # walking where a top-200 agent spends 2,854. One pass of pairwise swaps
    # fixes the crossings without changing which jobs get done.
    if SWAP_PASSES > 0 and len(booked) > 1:
        for _ in range(SWAP_PASSES):
            improved = False
            for a in range(len(booked)):
                for b in range(a + 1, len(booked)):
                    wa, ca, aa, ta = booked[a]
                    wb, cb, ab, tb = booked[b]
                    # Only jobs that need nothing in hand may change owner.
                    # FEED needs the worker to be carrying wheat, PLACE an
                    # animal, FERTILIZE manure, DROP its own load -- handing
                    # those to another worker makes them silent no-ops.
                    if (aa[0] not in PORTABLE_JOBS
                            or ab[0] not in PORTABLE_JOBS):
                        continue
                    now = ta + tb
                    swapped = (distance(positions[wa], cb)
                               + distance(positions[wb], ca))
                    if swapped < now:
                        booked[a] = (wa, cb, ab, distance(positions[wa], cb))
                        booked[b] = (wb, ca, aa, distance(positions[wb], ca))
                        improved = True
            if not improved:
                break
        for worker, cell, action, travel in booked:
            chosen[worker] = (action if travel == 0
                              else step_toward(positions[worker], cell, action))

    for worker, cell, action, travel in booked:
        if travel > 0:
            _EN_ROUTE[(player, worker)] = (cell, action[0])
        else:
            _EN_ROUTE.pop((player, worker), None)
    for worker in range(len(positions)):
        if worker not in chosen:
            _EN_ROUTE.pop((player, worker), None)

    for crop, n in planted_now.items():
        seeds[crop] = max(0, int(seeds.get(crop, 0)) - n)

    actions = [chosen.get(w, list(PASS)) for w in range(len(positions))]
    return {
        "farmer": actions[0] if actions else list(PASS),
        "hands": actions[1:],
        "market": market_orders(ctx, observation, plan, day, step, counts,
                                shed, seeds, money,
                                len(farm.get("hands") or [])),
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
        # On the ladder a raised exception forfeits the game, so the farm
        # stands still instead. Locally that is worse than a crash: a single
        # mistyped key turns this into an agent that passes for thirty days
        # and quietly scores 1,278, which is exactly how one packaged
        # submission went out dead. So the first failure is printed once, to
        # stderr, where every local run will show it, and the ladder never
        # sees a raise either way.
        global _FAILED
        if not _FAILED:
            _FAILED = True
            import traceback
            traceback.print_exc(file=sys.stderr)
        farm = _farm(observation)
        hands = len(farm.get("hands") or [])
        return {"farmer": list(PASS),
                "hands": [list(PASS) for _ in range(hands)], "market": []}
