# Kaggriculture rules and economics: a verified reference

Written 2026-09-27 against the installed engine, `kaggle-environments` 1.32.7.
"L123" means a line of
`.conda/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`.

Every number here comes from code. The labels are:

- **Verified**: an engine experiment in `tools/analysis/l2_econ_rules.py`. All 67 checks pass.
- **Engine-measured**: one tile or one animal run through the stock engine with an exact schedule (`l2_econ_value.py`).
- **Measured**: from replays of our 148 real ladder games, 103 by A (submission 56571049) and 45 by L (56582917). Each game was replayed from both players' tapes, and every one reproduced the live final money of both players to the coin (148/148). The replay ledger also balances: start money plus logged flows equals final money in every group.
- **Derived**: arithmetic on the numbers above.
- **Estimate**: a projection that has not been tested. These are marked where they appear, and none of them is a measurement.

Unless a figure says otherwise, "real games" means the pooled A+L set (148 games: 117 won, median money 95,286 against 91,204, median opponent rating 1,801).

## 0. Reproduce

```bash
PY=./.conda/python.exe; export PYTHONIOENCODING=utf-8
$PY -m tools.analysis.l2_econ_rules            # 67 rule checks -> rl/data/l2/econ/rules.json
$PY -m tools.analysis.l2_econ_replay --workers 1   # 148 real games -> rl/data/l2/econ/games/ (13 s/game)
$PY -m tools.analysis.l2_econ_report           # price paths, flows, labour, leaks -> summary.json
$PY -m tools.analysis.l2_econ_value            # per tile-day / per action, hands, land, payback -> value.json
$PY -m tools.analysis.l2_econ_market           # curves, slopes, impact, slot order, demand -> market.json
$PY -m tools.analysis.l2_econ_cycles           # what each crop cycle earned, by planting day -> cycles.json
```

`tools/analysis/l2_econ_sim.py` is a small harness that drives `kaggriculture.interpreter` directly. With it you can set up any state, submit exact actions for both players, and read back what happened.

---

## 1. Rules that matter for decisions

### 1.1 Clock and turn order

- **A game has 719 agent turns: steps 0 to 718** (verified: the agent is called 719 times, and the last call is day 29, hour 22). Day 29 has only hours 0 to 22. **The day-29 night refresh never runs** (L945-946, L960-963). Consequences:
  - No production, plant death, animal escape or CARE payout happens after the day-28 night.
  - A CARE on day 28 banks a bonus that could only pay on a later night, so it can never pay. CARE or FEED on day 29 is also worthless. On days 28-29 our side still requests about 15 CARE on day 28, 3.5 CARE on day 29 and 21 WATER on day 29 per game (measured from tapes; some day-29 WATERs on one-time crops inside the window do add yield).
  - Goods must be in the shed and sold by step 718. Goods left in a unit's hands or on tiles are worth nothing.
- **Order within one step** (L894-946):
  1. The atomic PLANT check (L920-933).
  2. Player 0's units, then player 1's units. Within a player the farmer acts first, then the hands in list order. Actions are applied sequentially (L935-939).
  3. The market, slot by slot (L941).
  4. The town consumption tick (L942).
  5. Plant decay (L943-944).
  6. The night refresh, if hour 23 (L945-946).

  The observation for step t shows the state after all of step t-1.
- Consequences (all verified):
  - A shed-adjacent DROP and a SELL of those goods work in the same turn: 5 wheat were dropped and sold for +121.
  - Goods carried at hour 23 reach the shed only in the night drop, so they cannot be sold that turn.
  - **A hand hired this turn cannot act this turn**, so a hand hired at hour 0 acts on hours 1-23 (23 turns, 22 on day 29).
  - **Seeds bought this turn cannot be planted this turn.**
  - Three units on one tile can HARVEST, then PLANT, then WATER in one turn, and all three apply.
  - Unit order also matters for fertilizer. If the farmer WATERs and hand 1 FERTILIZEs the same tile in the same turn, that day's double bonus is lost; the yield came out 2, not 3.

### 1.2 Units, hiring, invalid actions

- Every unit (the farmer and each hand) does one action per turn. Invalid actions are silent no-ops. Moving off the board is ignored. Locked tiles can be walked over, but tile actions there are no-ops that consume nothing (L323-332, L414-415). PICKUP, DROP and PLACE-into-shed work from the four shed-access tiles (4,4), (5,4), (4,5), (5,5) even when those tiles are locked (L339-410).
- **Hire cost**: the n-th hire of a day costs fib(n) = 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987 (L690-709). Hiring resets every night (L879-882).
  - Ten hires in one turn cost 143. The 11th and 12th hires must wait for the next turn (see the 10-order cap below), and twelve hands cost 376 per day.
  - A HIRE without enough money silently fails (L704).
- **Spawn tile**: a new hand goes to the least-occupied shed-access tile, with ties broken in NWSE order (L533-541). Occupancy is counted after that turn's unit actions. With the farmer still on (4,4), the first ten hires land on (5,4), (4,5), (5,5), (4,4), (5,4), and so on. **So an hour-0 hire, made while the farmer stands on (4,4), lands on (5,4), which is locked until NE is bought.**
- Each night the farmer respawns at (4,4), every hand is dismissed, and everything carried drops into the shed (L873-882).

### 1.3 Crops

Survival rules:

- A new plant starts with `consecutive_unwatered = 1`, so **the planting day counts as unwatered**. A plant that is not watered on its planting day is a weed by morning (L222, L777-785; verified).
- After a watered day, one dry day can be survived. The second consecutive dry night kills the plant (verified). Surviving therefore needs a WATER on the planting day and then at least every other day.

One-time crops (wheat, carrot, melon):

- The plant starts with 1 unit (L223).
- A WATER at an age inside the window `[ceil(max_yield_day/2), max_yield_day]` adds 1 unit, or 2 while fertilized, up to `max_yield`. **The bonus is credited at the moment of the WATER** (L431-444). So a crop can be watered and then harvested on the same day, and **fertilizer applied after that day's water does not count for that day** (verified: wheat fertilized at age 4 after its water gave 4, before its water 5).
- One FERTILIZE covers the day it is applied and the next two days (L481).
- HARVEST before `first_yield_day` is a silent no-op (L453-463). A harvest removes the plant.

Yield of one tile given survival watering plus every window watering (engine-measured):

| Crop | Window ages | No fertilizer | One fertilizer applied at age 0 / 1 / 2 / 3 / 4 | Useful fertilizer gain |
| --- | --- | ---: | --- | --- |
| Wheat | 2-4 | 4 | 5 / 6 / 6 / 6 / 5 | **+2 if applied at age 1-3** (before that day's water) |
| Carrot | 2-3 | 3 | 4 / 4 / 4 / 4 | +1 at any age 0-3 |
| Melon | 6-12 | 6 (reached at age 10) | 6 at every age | **0**: it only saves 2 waterings, and it costs one FERTILIZE |

Ongoing crops (tomato, strawberry):

- Production is credited during the night refresh on fixed nights. Tomato produces on nights P+7 to P+10 (ages 8-11). Strawberry produces on nights P+9, P+11, P+13 and P+15 (ages 10, 12, 14, 16) (L786-802).
- **Base production needs only survival.** Water that day is not required.
- A production is doubled when the plant was watered that day and `fertilized_until_day` covers that day (L798-800).
- **One fertilizer can double up to 3 tomato productions or 2 strawberry productions.**
  - Tomato: survival watering alone gave 4 units. One fertilizer on day 7, with water on days 7-9, gave 7. Fertilizer on days 7 and 10 gave 8.
  - Strawberry: survival watering alone gave 4. Fertilizer on days 9 and 13, with water on 9, 11, 13 and 15, gave 8.
- A tile holds at most 4 units (L800). A doubled crop must be harvested at least every 2 productions, or units are lost. Verified: a doubled tomato harvested once at age 11 gave 4, not 8.
- **Harvesting does not extend the plant's life.** After the 4th production, decay starts at hour 0 of the day after it (L801-802). An empty plant then turns into a weed at once, and it needs a DIG before the tile can be reused.

Decay:

- A one-time crop has `max_lifespan_step = (planted_day + max_yield_day + 1) * 24` (L224).
- From that step on, the plant loses 1 unit at that step and at every second step after it, **after that turn's actions**. It becomes a weed at 0 units (L752-766).
- Verified on wheat planted on day 0: a harvest at step 120 (age 5, hour 0) still takes all 4 units. The units then run 3, 3, 2, 2, 1, 1, and the tile is a weed after step 126.

Latest useful planting day, from the first-harvest ages and the 719-turn clock (derived):

| Crop | Latest planting day |
| --- | ---: |
| Wheat, carrot | 27 |
| Tomato | 21 (first unit on day 29) |
| Melon, strawberry | 19 |

### 1.4 Animals

- FEED uses one wheat carried by the unit (L505-513). Two consecutive unfed nights make the animal escape, leaving an empty structure (L813-820). A newly placed animal starts with `consecutive_unfed = 0`, so it survives its first unfed day (verified: it escapes on the second night).
- **Production** happens on nights where `next_day - placed_day - first_yield_day` is at least 0 and divides by the interval:
  - Goose: from night P+3, daily.
  - Cow: from night P+7, every 2 nights.
  - Sheep: from night P+5, every 3 nights.

  Base production is 1 unit, **even when the animal was unfed that day** (L821-828).
- **CARE banking.** At the night refresh the production is computed first. On a fed day it pays out the whole bank; on an unfed production day the bank is forfeited (verified). *Then*, if the animal was fed and cared that day, the bank grows by 1 (L829-830). This has two consequences:
  - CARE on a production day pays on the *next* production.
  - Every fed-and-cared day adds exactly +1 unit of product, subject to the held cap (4 for a goose, 6 for a cow or sheep, L827).
- With full care from placement, the first productions come out as follows (verified):

  | Animal | Units credited on successive production nights |
  | --- | --- |
  | Goose | 4, 2, 2, 2, ... |
  | Cow | 6 (8 requested, 2 lost to the cap), 3, 3, ... |
  | Sheep | 6, 4, 4, ... |
- **Fertilizer**: every surviving animal gets `fertilizer_available` at every night refresh, fed or not (L831). It does not stack (verified: collecting twice after three nights gave 1). COLLECT puts the unit into the collecting unit's own inventory, so that unit can go straight to a plant and FERTILIZE without visiting the shed.
- DIG cannot remove an occupied structure (L484-491). Animals cannot be sold (L596-607).

### 1.5 Shed

The cap is 100 non-seed items. Animals waiting in the shed count toward the cap (verified). Seeds have their own uncapped slot.

| Action | Behaviour when the shed is nearly full | Lines |
| --- | --- | --- |
| DROP | Stores what fits and **discards the rest of the carried stack** (98 in the shed plus 5 carried leaves 2 stored, 3 destroyed) | L343-356 |
| PLACE item n (into the shed) | Stores what fits and **keeps the rest in hand** | L393-410 |
| End-of-night drop | Discards overflow | L843-857 |
| BUY_PRODUCT, BUY_ANIMAL | Refused when the shed is full | L662-686 |
| BUY_SEED | Never blocked by the shed | L673-678 |
| SELL | Draws from the shed only, never from a unit's hands | L653-656 |

### 1.6 Market mechanics

- **At most 10 market orders per player per turn** (L560). Extra orders are dropped silently. The quantity inside one order is not capped.
- **Slots.** Player 0's i-th order and player 1's i-th order are processed together as slot i (L563-626). HIRE and BUY_LAND are atomic and settle at the start of their slot (L571-581). Your own orders run in list order: with $0 in the bank, [SELL, HIRE] hires, while [HIRE, SELL] does not (verified).
- **Lockstep.** Within a slot, each round quotes both players' next unit from the same pre-commit inventory, then commits both (L590-623).
  - Two players selling the same item in the same slot get identical prices (verified: +234 each for 10 wheat), and each round adds 2 units of inventory.
  - Selling in an earlier slot than the opponent wins the undisturbed book (see section 3.4).
- **Quotes.**
  - A SELL is quoted at the inventory before the sale (L597).
  - A BUY_PRODUCT is quoted at the inventory after the purchase (L598-601), so buying one unit and selling it back on an unchanged market nets 0 (verified).
  - The first wheat bought at I0 costs 26. Buying 100 at I0 cost 2,995 (average 29.95) and left the price at 35 (verified).
- **The $1 floor.** A sale at $1 pays $1 and **does not add inventory** (L657-660; verified: 3 melons sold at the floor left the inventory unchanged). A book at the floor stays pinned at the inventory where it first rounds to $1, and it recovers only as the town consumes.
- **What can be traded.** Any of the 9 products, fertilizer included, can be SOLD. Only WHEAT and FERTILIZER can be bought (L596-607). Seeds and animals are sold to players at fixed prices (L602-605).
- **Running out of money.** An order stops mid-way when money runs out, and later orders still run (verified: 5 strawberry seeds ordered with $250 bought 2, and a later wheat seed still bought) (L618-623).
- **Land.** BUY_LAND unlocks NE, then SW, then SE, at $1,000, $2,000 and $4,000 (L95-97, L712-725).

### 1.7 Town

- Shops consume at every step with `step % 4 == 0` (hours 0, 4, 8, 12, 16, 20). The town centre consumes at hour 0. **Both run after that step's market** (L728-749).
  - Every shop instance eats 1 of each product it stocks per tick. A single-product shop (Pet Cafe, Yarn Store) eats 2 per tick.
  - So a shop uses 6 or 12 units per listed product per day. The town centre eats 1 per day of every product except fertilizer. Day 29 still has all 6 shop ticks.
- One shop unlocks on each night before days 3, 6, ..., 24, to a maximum of 8 instances (verified). Draws are made with replacement (L884-891).
- **The shop draw shares its RNG with the weed draws** (L870-891). `_spawn_weeds` draws one random number per *empty* unlocked tile on farm 0, then on farm 1. Only after that is the shop chosen. So the number of empty tiles on both farms that night changes which shop appears. Verified: on seed 12345, an empty farm drew YARN_STORE on day 3, while a full farm drew FARMERS_MARKET. The seed is hidden from agents, so this cannot be steered deliberately. It does mean two configs can see different towns on the same seed.
- Weeds spawn on each empty unlocked tile with 0.5% chance per night (measured 0.48% over 58,000 tile-nights, L836-840). Locked tiles never spawn weeds, but newly bought land does.

### 1.8 Price function

`price(inv) = base ± amp·f(|inv − I0|)`, with `amp = target·base/f(T)`. The result is rounded and floored at $1 (L41-74, L192-206). Carrot, tomato and egg use `hinge` below I0: the price stays calm down to I0−T, then runs away quadratically. See section 3.1 for the numbers.

---

## 2. Economics

### 2.1 Real prices by day

The table gives each item's morning price, as the median over 148 real games (measured). p10-p90 ranges are shown for three days.

| Item | d0 | d3 | d6 | d9 | d12 | d15 | d18 | d21 | d24 | d27 | d29 | p10-p90 on d10 / d20 / d29 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Wheat | 25 | 30 | 31 | 35 | 40 | 41 | 42 | 42 | 42 | 40 | 38 | 33-38 / 38-44 / 32-42 |
| Carrot | 35 | 35 | 35 | 36 | 39 | 42 | 45 | 48 | 52 | 56 | 55 | 36-42 / 37-57 / 36-67 |
| Tomato | 60 | 60 | 61 | 61 | 64 | 66 | 71 | 73 | 78 | 83 | 87 | 61-69 / 62-87 / 63-179 |
| Strawberry | 120 | 135 | 141 | 164 | 188 | 206 | 188 | 128 | **16** | **11** | **9** | 147-196 / 4-218 / 1-195 |
| Melon | 250 | 262 | 267 | 270 | **76** | 84 | 91 | 99 | 106 | 113 | 118 | 271 / 96 / 118 |
| Egg | 50 | 50 | 50 | 51 | 52 | 52 | 52 | 53 | 53 | 54 | 55 | 51-53 / 45-58 / 42-64 |
| Milk | 160 | 175 | 181 | 175 | 141 | 103 | **38** | **26** | 38 | 56 | 30 | 131-223 / 3-189 / 1-207 |
| Wool | 200 | 212 | 217 | 187 | 154 | **1** | 28 | 72 | 18 | 72 | 21 | 148-234 / 1-178 / 1-184 |
| Fertilizer | 100 | 97 | 91 | 81 | 71 | 52 | 40 | 31 | 19 | 14 | **6** | 76 / 31-34 / 1-12 |

The volume-weighted price we actually got is not the morning price. Our realised prices (VWAP) were:

| Item | Days 10-19 | Days 20-29 | Units sold per game | Revenue per game |
| --- | ---: | ---: | ---: | ---: |
| Wheat | 42 | 41 | 512 | 20,833 |
| Carrot | 56 | 53 | 140 | 7,398 |
| Tomato | – | 169 | 23 | 3,892 |
| Strawberry | 180 | 81 | 247 | 27,441 |
| Melon | 201 | – | 72 | 14,481 |
| Egg | 52 | 50 | 74 | 3,754 |
| Milk | 115 | 83 | 201 | 20,840 |
| Wool | 138 | 82 | 168 | 19,778 |
| Fertilizer | 55 (88 in days 0-9) | 17 | 334 | 15,050 |

Melon is the clearest case. We sell 72 melons at $201 on days 10-11, before the book crashes to $76.

The average game's money flow (measured) was:

- **Revenue**: 133.5k.
- **Costs**: 39.1k in total:
  - wheat bought: −12.2k (305 units at $40.1)
  - animals: −7.5k
  - seeds: −6.8k
  - wages: −5.8k
  - land: −4.4k
  - fertilizer bought: −2.4k (84 units at $28)
- **Mean final money**: 97.3k.

### 2.2 Crops per tile-day and per field action

Yields below are engine-measured. "Actions" counts field actions only: plant, water, fertilize, harvest, and dig for ongoing crops. Walking and delivery are excluded. In our games a useful action costs **2.03 unit-turns** once moves and PASSes are counted (section 2.6).

Net value is units × price − seed − fertilizer, with fertilizer charged at its sale price. Base uses base prices. Mid and late use our realised VWAP for days 10-19 and 20-29, or the median morning price where we did not sell that item then.

| Schedule (plant on day 0) | Units | Days held | Actions | Base $/tile-day | Base $/action | Mid $/tile-day | Mid $/action | Late $/tile-day | Late $/action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Wheat, harvest at age 2 | 2 | 2 | 4 | 20.0 | 10.0 | 37.3 | 18.6 | 35.7 | 17.9 |
| Wheat, harvest at age 3 | 3 | 3 | 5 | 21.7 | 13.0 | 38.9 | 23.4 | 37.4 | 22.4 |
| Wheat, harvest at age 4 | 4 | 4 | 6 | 22.5 | 15.0 | 39.8 | 26.5 | 38.2 | 25.5 |
| Wheat, age 3 + fertilizer | 5 | 3 | 6 | 5.0 | 2.5 | 48.7 | 24.4 | **58.8** | **29.4** |
| Wheat, age 4 + fertilizer | 6 | 4 | 7 | 10.0 | 5.7 | 47.1 | 26.9 | 54.3 | 31.0 |
| Carrot, harvest at age 3 | 3 | 3 | 5 | 28.3 | 17.0 | 49.1 | 29.5 | 46.2 | 27.7 |
| Carrot, age 2 + fertilizer | 3 | 2 | 5 | −7.5 | −3.0 | 46.0 | 18.4 | 60.7 | 24.3 |
| Carrot, age 3 + fertilizer | 4 | 3 | 6 | 6.7 | 3.3 | 49.3 | 24.6 | 58.1 | 29.0 |
| Melon, harvest at age 10 | 6 | 10 | 10 | 142.0 | 142.0 | 112.7 | 112.7 | 56.3 | 56.3 |
| Tomato, survival water only | 4 | 11 | 9 | 17.3 | 21.1 | 19.6 | 24.0 | 57.1 | 69.7 |
| Tomato + 1 fertilizer (day 7) | 7 | 11 | 12 | 24.5 | 22.5 | 32.7 | 30.0 | **101.7** | **93.2** |
| Tomato + 2 fertilizer | 8 | 11 | 14 | 20.9 | 16.4 | 33.7 | 26.5 | 115.5 | 90.8 |
| Strawberry, survival water only | 4 | 16 | 11 | 23.8 | 34.5 | 38.7 | 56.2 | 14.1 | 20.5 |
| Strawberry + 2 fertilizer | 8 | 16 | 15 | 41.2 | 44.0 | **76.7** | **81.8** | 32.3 | 34.4 |

The minimal watering schedules are:

| Crop | Water on days |
| --- | --- |
| Wheat | 0, 2, 3, 4 (day 1 can be skipped) |
| Carrot | 0, 2, 3 |
| Melon | 0, 2, 4, 6, 7, 8, 9, 10 |
| Tomato | every other day to day 10 |
| Strawberry | every other day to day 14 |

These schedules are shorter than the habit of watering daily. Our real cycles used 3.6 waterings per wheat cycle, 3.1 per carrot, 9.2 per strawberry and 9.2 per melon (measured).

At base prices, fertilizing wheat or carrot loses money, because a fertilizer sells for $100. At late prices it is the best wheat and carrot schedule, because fertilizer sells for $17.

### 2.3 What each crop cycle earned in our games, by planting day

This table is measured, from the tile ledger of our side. Each unit is valued at the same game's morning price on the day after its harvest, minus seed and fertilizer.

| Crop | Planted days | Cycles per game | Units per cycle | Net per cycle | $ per tile-day | $ per action |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Wheat | 0-4 | 18.0 | 2.28 | 58 | 25.5 | 11.2 |
| Wheat | 10-14 | 38.4 | 3.36 | 123 | 37.8 | 20.9 |
| Wheat | 15-19 | 33.4 | 4.19 | 158 | 41.4 | 25.6 |
| Wheat | 20-24 | 40.4 | 4.80 | 170 | 45.8 | 27.0 |
| Carrot | 20-24 | 11.6 | 3.31 | 183 | **60.9** | **34.3** |
| Carrot | 25-29 | 32.8 | 2.93 | 135 | 50.8 | 25.0 |
| Tomato | 15-19 | 2.9 | 7.91 | 1,157 | **105.2** | **72.5** |
| Strawberry | 5-9 | 20.0 | 7.32 | 783 | 49.6 | 46.5 |
| Strawberry | **10-14** | 13.0 | 7.84 | **408** | **25.5** | 23.8 |
| Melon | 0-4 | 12.0 | 6.00 | 735* | 73.5* | 65.9* |

\*Melon is undervalued by this method. We sell melons at $201 on the harvest day, before the next-morning crash. The realised figure is 6 × 201 − 80 = $1,126 per cycle, or $113 per tile-day.

The second strawberry wave (13 cycles per game planted on days 10-14) earned **less per tile-day than wheat planted the same days**, and about the same per action. It harvests into the day 21-29 strawberry crash.

Tomato and late carrot are the most valuable uses of a late tile. The tomato book is thin: nobody sells tomatoes, and its inventory drifts to −197 by day 29, right at the hinge knee.

### 2.4 Animals

The animal figures below are engine-measured over a 12-night steady state, per animal-day. Wheat is charged at the $40.1 we paid, fertilizer at its sale price, and actions are counted as FEED, CARE, COLLECT and HARVEST.

| Animal and service | Product per day | Fertilizer per day | Wheat per day | Actions per day | Base $/day | Base $/action | Mid $/day | Mid $/action | Late $/day | Late $/action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Goose, fed + cared | 2.00 | 1 | 1 | 3.50 | 175 | 50.0 | 120 | 34.1 | 77 | 22.1 |
| Goose, fed every other day, no care | 1.00 | 1 | 0.5 | 2.00 | 138 | 68.8 | 87 | 43.7 | 47 | 23.6 |
| Cow, fed + cared | 1.50 | 1 | 1 | 3.25 | 315 | 96.9 | 188 | 57.8 | 102 | 31.3 |
| Cow, fed every other day, no care | 0.50 | 1 | 0.5 | 1.75 | 168 | 95.7 | 93 | 53.0 | 39 | 22.1 |
| Sheep, fed + cared | 1.33 | 1 | 1 | 3.33 | 342 | 102.5 | 199 | 59.7 | 87 | 25.9 |
| Sheep, fed every other day, no care | 0.33 | 1 | 0.5 | 1.83 | 154 | 84.1 | 81 | 44.3 | 25 | 13.4 |

Four findings follow from this table.

- **CARE is worth exactly one unit of product per CARE action**, provided the animal is fed that day and the cap has room. That is $83 for milk at the late realised price, but $1 on the many days wool or milk sits at the floor (the median wool price on day 15 is $1). CARE should follow the product's book, not habit.
- **Daily feeding only pays when you also CARE.** For an animal that is not cared for, feeding every other day gives the same output for half the wheat. The escape rule allows exactly one dry night.
- **In the real games the herd was:**

  | Animal | Per game | Placed around day | Product per animal-day, placement to day 29 |
  | --- | ---: | ---: | ---: |
  | Cow | 7.3 | 3 | 1.09 |
  | Sheep | 7.8 | 8 | 0.98 |
  | Goose | 2.4 | 10 | 1.61 |

  These rates include the wait before first production (measured).
- **Latest placement day that still pays back** its purchase price, with full care, the fertilizer sold, bought wheat, and labour ignored (engine-measured):

  | Animal | At base prices | At mid-game prices | At late prices |
  | --- | ---: | ---: | ---: |
  | Goose | day 25 | 24 | 22 |
  | Cow | day 23 | 21 | 19 |
  | Sheep | day 23 | 23 | 20 |

**Feed.** A daily-fed animal eats one wheat per day, $40.1 at the price we paid. A wheat tile on an age-4 cycle yields 1 wheat per tile-day, so a self-fed animal effectively occupies two tiles. We bought 305 wheat per game and sold 512 (measured).

### 2.5 Fertilizer: where one unit is worth most

Derived from sections 1.3 and 2.1. The value of one fertilizer depends on where it goes:

| Use | Units gained per fertilizer | Mid-game value | Late value |
| --- | --- | ---: | ---: |
| Tomato | +3, if the three production days are watered | 3 × $66 | 3 × $169 |
| Strawberry | +2 | 2 × $180 | 2 × $81 |
| Wheat, applied at age 1-3 before the water | +2 (+1 on an age-2 harvest) | 2 × $42 | 2 × $41 |
| Carrot | +1 | $56 | $53 |
| Melon | 0 | 0 | 0 |
| **Selling it** | – | **$55** (and $88 in days 0-9) | **$17** |

Nothing in town consumes fertilizer, and both lineage farms sell about 330 each per game. The fertilizer book therefore falls from 100 to 6 in the median game (measured: inventory +470 by day 29).

So from about day 10, one fertilizer on wheat is worth more than one sold. Yet in days 20-29 our side sold 144 fertilizers per game at $17, bought 63 back, and harvested **33.6 wheat cycles per game planted on day 17 or later with no fertilizer** (measured). Only 23% of wheat cycles and 39% of carrot cycles were fertilized.

### 2.6 Labour: the unit-turn is the currency

Measured per game, on our side:

- **6,996 unit-turns** in total:
  - moves: 2,959 (42.3%)
  - PASS: 541 (7.7%)
  - silently ignored actions: 46 (0.7%)
  - **useful actions: 3,450 (49.3%)**
- Useful actions by verb:

  | Verb | Per game |
  | --- | ---: |
  | WATER | 1,121 |
  | HARVEST | 494 |
  | CARE | 410 |
  | COLLECT | 374 |
  | FEED | 334 |
  | PLANT | 242 |
  | PICKUP | 197 |
  | FERTILIZE | 116 |
  | PLACE | 106 |
  | DROP | 45 |
  | DIG | 37 |
  | BUILD | 19 |
- The ignored actions were mostly CARE (12.4 per game), WATER (10.6) and HARVEST (8.7).
- The median game nets 92,286 over 3,450 useful actions, which is **$26.8 per useful action, or $13.2 per unit-turn**.
- Hands (median by day):

  | Days | Hands |
  | --- | ---: |
  | 0-5 | 3-5 |
  | 6-9 | 7-8 |
  | 10-15 | 9-11 |
  | 16 onward | 11-12 |

  Wages were 5.8k per game.

The marginal hand compares with that value as follows. A hand hired at hour 0 gets 23 turns, and 49% of our unit-turns are useful:

| Hand number | Daily cost | Cumulative | $ per turn | $ per useful action |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 55 | 143 | 2.39 | 4.85 |
| 11 | 89 | 232 | 3.87 | 7.85 |
| 12 | 144 | 376 | 6.26 | 12.70 |
| 13 | 233 | 609 | 10.13 | **20.54** |
| 14 | 377 | 986 | 16.39 | 33.24 |
| 15 | 610 | 1,596 | 26.52 | 53.79 |

Hands 1 to 12 cost less per useful action than any crop earns at mid- or late-game prices ($17.9 or more per action). The 13th ($20.5) is at the level of average-quality work, and the 14th and later cost more than an average action earns.

**So extra work must come from the same ~12 hands.** That means fewer moves, fewer PASSes, and less low-value work such as CARE on a crashed book. This matches the established top-30 finding: the same ~11 hands, 23 more planted tiles, and fewer CARE actions.

### 2.7 Land

The net value per tile-day needed to repay a quadrant, with all 25 tiles worked from the purchase day to day 29, before labour and weeds (derived):

| Purchase day | NE ($1,000) | SW ($2,000) | SE ($4,000) |
| ---: | ---: | ---: | ---: |
| 6 | 1.7 | 3.5 | 7.0 |
| 10 | 2.1 | 4.2 | 8.4 |
| 14 | 2.7 | 5.3 | 10.7 |
| 18 | 3.6 | 7.3 | 14.5 |
| 22 | 5.7 | 11.4 | 22.9 |
| 26 | 13.3 | 26.7 | 53.3 |

Wheat earns $38-46 per tile-day and late carrot $51-61 before labour. So **land is never the constraint; labour is.**

Twenty-five wheat tiles need about 37.5 field actions per day, which is about 76 unit-turns, or 3.3 hand-days. If those hands were hires 13 to 15, they would cost $233 to $610 per day each.

On our side NE was bought on day 6 (100% of games) and SW on day 11 (100%). SE was bought in only 36% of games, with a median day of 18 (measured).

---

## 3. Market math

These tables use the engine's `market_price` and its $1 floor rule. "Typical inventories" means the median morning inventory in our real games.

### 3.1 Curves, floors and hinge knees

Price at inventory I0 + offset (I0 = 10,000):

| Item | T | −900 | −400 | −200 | −100 | 0 | +50 | +100 | +200 | +400 | $1 floor from |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Wheat | 400 | 55 | 45 | 39 | 35 | 25 | 22 | 21 | 21 | 20 | never |
| Carrot | 450 | 385 | 66 | 51 | 43 | 35 | 27 | 23 | 19 | 12 | I0+842 |
| Tomato | 200 | 2,520 | 300 | 84 | 72 | 60 | 42 | 35 | 24 | 9 | I0+529 |
| Strawberry | 100 | 372 | 288 | 239 | 204 | 120 | 24 | 1 | 1 | 1 | **I0+62** |
| Melon | 300 | 310 | 303 | 296 | 290 | 250 | 225 | 150 | 1 | 1 | I0+158 |
| Egg | 332 | 573 | 81 | 62 | 56 | 50 | 43 | 42 | 41 | 40 | never |
| Milk | 122 | 421 | 334 | 283 | 247 | 160 | 55 | 1 | 1 | 1 | **I0+76** |
| Wool | 105 | 258 | 251 | 245 | 240 | 200 | 55 | 1 | 1 | 1 | **I0+59** |
| Fertilizer | 200 | 280 | 180 | 140 | 120 | 100 | 90 | 80 | 60 | 20 | I0+493 |

Hinge knees:

| Item | I0 − 0.5T | I0 − T | I0 − 1.25T | I0 − 1.5T | I0 − 2T |
| --- | ---: | ---: | ---: | ---: | ---: |
| Carrot | $52 | $70 | $96 | $158 | $385 |
| Tomato | $72 | $84 | $102 | $144 | $300 |
| Egg | $60 | $70 | $85 | $120 | $250 |

Measured inventories reached −259 for carrot and −197 for tomato by day 29, near or approaching the knee. Egg reached only −95. **Only 59 to 76 units of net oversupply put wool, strawberry or milk at the floor**, and each unit sold above I0 costs $1.9 (strawberry), $2.1 (milk) or $2.4 (melon, at +120).

### 3.2 Where the books actually sat

Median inventory relative to I0 on the morning of each day (measured):

| Item | d9 | d12 | d15 | d18 | d21 | d24 | d27 | d29 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Wheat | −94 | −212 | −252 | −274 | −285 | −280 | −231 | −173 |
| Carrot | −9 | −48 | −87 | −126 | −183 | −240 | −287 | −259 |
| Tomato | −9 | −30 | −51 | −90 | −111 | −150 | −171 | −197 |
| Strawberry | −27 | −66 | −87 | −64 | −1 | +55 | +57 | +58 (floor at +62) |
| Melon | −9 | +132 | +129 | +126 | +123 | +120 | +117 | +115 |
| Egg | −9 | −30 | −37 | −36 | −54 | −57 | −79 | −95 |
| Milk | −3 | +12 | +27 | +60 | +66 | +60 | +49 | +57 (floor at +76) |
| Wool | +15 | +28 | **+59** | +54 | +47 | +55 | +46 | +55 (floor at +59) |
| Fertilizer | +94 | +147 | +238 | +302 | +346 | +403 | +429 | +470 |

Wheat is deep: the slope is about 0 to 0.1 dollars per unit at these inventories. Carrot, tomato and egg slide about 0.1 per unit. The premium items (strawberry, milk, melon) move $1.9 to $2.9 per unit, wool about $6.9 per unit just above its floor edge, and all of them sit near their floors from mid-game.

### 3.3 Impact of selling n units at once

Average price per unit, and in brackets the loss against n × the opening quote:

| Item | Day-15 book, 10 units | Day-15 book, 40 units | Day-15 book, 80 units | Day-25 book, 10 units | Day-25 book, 40 units | Day-25 book, 80 units |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Wheat | 41.0 (0) | 40.3 (28) | 39.5 (116) | 41.0 (0) | 40.7 (11) | 40.1 (72) |
| Carrot | 41.4 (6) | 40.3 (69) | 38.7 (264) | 54.9 (1) | 53.6 (55) | 52.1 (235) |
| Tomato | 65.6 (4) | 63.8 (88) | 58.8 (578) | 78.3 (7) | 76.5 (100) | 74.1 (392) |
| Strawberry | 196.3 (17) | 188.8 (369) | 175.9 (1,770) | 21.0 (90) | 6.8 (930) | 3.9 (2,090) |
| Melon | 71.7 (123) | 32.8 (2,047) | 16.9 (5,367) | 97.4 (106) | 56.9 (2,043) | 29.0 (6,323) |
| Egg | 52.0 (0) | 51.0 (41) | 47.9 (325) | 53.9 (1) | 52.9 (45) | 51.2 (221) |
| Milk | 93.9 (91) | 62.4 (1,623) | 32.8 (5,613) | 33.0 (90) | 11.8 (1,209) | 6.4 (2,849) |
| Fertilizer | 51.5 (5) | 48.5 (140) | 44.5 (600) | 19.5 (5) | 16.5 (140) | 12.5 (600) |

### 3.4 Selling first versus second

Our revenue when we and the opponent each sell n units of the same item. The three figures are for the opponent selling in an earlier slot, in the same slot (lockstep), or in a later slot than ours. All use the day-15 median book.

| Item | n = 10 | n = 20 | n = 40 | First-slot edge at n = 40 |
| --- | --- | --- | --- | ---: |
| Wheat | 410 / 406 / 402 | 812 / 806 / 800 | 1,612 / 1,582 / 1,552 | 60 |
| Carrot | 414 / 411 / 407 | 821 / 806 / 790 | 1,611 / 1,549 / 1,485 | 126 |
| Tomato | 656 / 650 / 644 | 1,300 / 1,277 / 1,252 | 2,552 / 2,355 / 2,150 | 402 |
| Strawberry | 1,963 / 1,943 / 1,915 | 3,878 / 3,783 / 3,673 | 7,551 / 7,051 / 6,519 | 1,032 |
| Egg | 520 / 517 / 513 | 1,033 / 1,021 / 1,006 | 2,039 / 1,920 / 1,796 | 243 |
| **Milk** | 939 / 845 / 729 | 1,668 / 1,270 / 829 | 2,497 / 1,340 / 130 | **2,367** |
| **Melon** | 717 / 593 / 441 | 1,158 / 678 / 155 | 1,313 / 698 / 40 | **1,273** |
| Fertilizer | 515 / 506 / 495 | 1,010 / 972 / 930 | 1,940 / 1,784 / 1,620 | 320 |

At I0 (verified in the engine), 40 milk each gave +4,764 to the player in slot 0 against +1,421 in slot 1, and 40 strawberries gave +3,302 against +525. The slot edge is decisive for premium goods and negligible for wheat. L's `stack/market_front.py` exploits this within a turn.

### 3.5 Town demand

| Product | Shops that eat it (units per day each) | Expected added demand per unlock (per day) | Expected season demand | T |
| --- | --- | ---: | ---: | ---: |
| Wheat | Bakery, Pizza, Brunch, Ice cream, Farmers market (6 each) | 3.75 | 525 | 400 |
| Carrot | Pet cafe (12), Farmers market (6) | 2.25 | 327 | 450 |
| Tomato | Pizza, Farmers market (6 each) | 1.50 | 228 | 200 |
| Strawberry | Brunch, Ice cream, Smoothie, Farmers market (6 each) | 3.00 | 426 | 100 |
| Melon | none (town centre only) | 0 | **30** | 300 |
| Egg | Bakery, Brunch (6 each) | 1.50 | 228 | 332 |
| Milk | Pizza, Ice cream, Smoothie (6 each) | 2.25 | 327 | 122 |
| Wool | Yarn store (12) | 1.50 | 228 | 105 |
| Fertilizer | none, and not the town centre | 0 | **0** | 200 |

Eight unlocks, live from days 3, 6, ..., 24, give 132 shop-days (derived). Set against what the two farms sold per game:

| Product | Sold by both farms per game | Expected season demand |
| --- | ---: | ---: |
| Strawberry | 489 | 426 |
| Milk | 399 | 327 |
| Wool | 333 | 228 |
| Melon | 146 | 30 |
| Fertilizer | 659 (less 158 bought back) | 0 |
| Tomato | 43 | 228 |
| Egg | 147 | 228 |
| Carrot | 259 | 327 |

**The premium books are over-supplied, and tomato, egg and carrot are under-supplied.**

**Demand timing.** A tick runs after the market, so a unit sold on the turn after a tick gets the post-tick price. At the day-15 books the gain per unit from waiting for the tick is:

| Item | 1 shop | 2 shops | 3 shops |
| --- | ---: | ---: | ---: |
| Wheat, carrot, tomato, egg | $0 | $0 | $0 |
| Strawberry | $1 | $1 | $2 |
| Milk | $2 | $5 | $7 |
| Wool (at its floor edge) | $10 | $23 | $36 |

Waiting for a glut to clear rarely pays. Our sales at $10 or less were:

| Item | Units per game at ≤ $10 | Median price 48 steps later | Share above $50 after 48 steps |
| --- | ---: | ---: | ---: |
| Strawberry | 53 | $9 | 5% |
| Fertilizer | 37 | $2 | 0% |
| Wool | 36 | $5 | 16% |
| Milk | 30 | $7 | 1% |

These books were still near the floor two days later, because both farms keep feeding them. The glut is structural, not a timing problem.

### 3.6 Buying wheat

Buying n wheat at once. The quote is taken at the inventory after the purchase:

| Book | Quote | 10 units | 30 units | 60 units | 100 units |
| --- | ---: | --- | --- | --- | --- |
| Day 5 (−32) | 31 | 31.0 | 31.9 | 32.8 | 33.9 |
| Day 15 (−252) | 41 | 41.0 | 41.3 | 41.8 | 42.4 |
| Day 25 (−269) | 41 | 41.7 | 41.9 | 42.3 | 42.9 |

Feed wheat costs about $40 per animal-day after day 10, whether it is bought or grown.

---

## 4. What the real games say about L and A's play

- **Execution leaks are small** (measured, per game, our side):
  - shed overflow: 8.6 units, mostly fertilizer 2.9 and wheat 2.3
  - terminal residue: 0.18 units
  - escapes: 0.46 animals, mostly geese
  - dead plants: 1.1
  - fertilizer left uncollected: 21 of 402
  - care lost to the cap: 2.0 units

  Valued at our whole-game prices, all of these together come to at most about **$2.0k per game**. Of that, $958 is the uncollected fertilizer, and it is valued at $45 although most of it would have sold for about $17. **The money is lost in allocation and in the market, not in execution.**
- **The same premium calendar as the opponent.** In A's games the opponent's farm matches ours almost exactly: 32.5 against 33.0 strawberry cycles, 7.0 against 7.1 cows, 7.8 against 7.9 sheep, 12.3 against 12.0 melons. Both farms harvest into the same books on the same days. The results:
  - strawberry's median price falls from $206 on day 15 to $16 on day 24
  - milk falls to $26 by day 21
  - wool reaches $1 on day 15
  - melon falls from $270 to $76 on day 12

  About 120 premium units per game (53 strawberries, 36 wool, 30 milk) go at $10 or less, plus 37 fertilizers (measured).
- **Fertilizer goes to the wrong place late.** See section 2.5.
- **Under-served books.** Tomato (2.9 cycles per game) earned $105 per tile-day, and late carrot $51-61, against $38-46 for wheat. Tomato's inventory drifts toward its knee because almost nobody sells it.
- **Half of all unit-turns are not useful work.** 42% are moves, 8% PASS.

---

## 5. Where an agent like L can still earn more (ranked)

The ranking is by expected dollars per game and by how solid the evidence is. Gains marked as estimates are untested. Items that overlap another active workflow say so.

1. **Plant and care according to the book (premium glut control).**
   - Evidence: section 2.3 shows the second-wave strawberries (13 cycles per game planted on days 10-14) earned $25.5 per tile-day, against $37.8-45.8 for wheat and $60.9 for carrot planted in the same fortnight. Section 4 shows about 150 premium units per game sold at $10 or less. Section 3.5 shows the premium books are over-supplied.
   - Rule: the opponent's farm is public, so their strawberry tiles and herd can be counted. An upcoming glut is visible about 10 days before it lands.
   - Levers: don't plant a strawberry wave that will harvest into a book the two farms already over-supply; move those tiles to carrot, wheat or tomato. Skip CARE when the product's book is within about 20 units of its floor, where CARE is worth $1-5 against $13-27 for the alternative action.
   - Estimate, untested: +$1-3k per game. The replaced tiles earn $12-35 more per tile-day. The strawberries you no longer sell also lift the price of the ones you still sell, by $1.9 per unit for every unit withheld, but the opponent shares that gain. Replacing strawberries with wheat costs about +0.56 field actions per tile-day.
2. **Put late fertilizer on wheat and carrot instead of selling it.**
   - Evidence (section 2.5): in days 20-29 we sold 144 fertilizers per game at $17, while 33.6 late wheat cycles per game went unfertilized. Each one gains +2 wheat, worth $82, when applied at age 1-3 before that day's water, at the cost of one FERTILIZE action. Collected fertilizer is already in the collecting unit's hands.
   - Estimate, untested: about 34 × ($70 − $17) − 34 actions × $13 ≈ **+$1.3k per game**.
   - This overlaps the wheat and fertilizer line of the other workflow. These numbers are for them: the earlier result that buying fertilizer and hiring a hand to apply it lost did not use fertilizer that was going to be sold at $17.
3. **Serve the thin books: tomato, late carrot, eggs.**
   - Evidence: tomato is the best late tile in the game ($105 per tile-day, section 2.3), and its book only reaches its knee because it is starved. At the day-25 book, 80 extra tomatoes still average $74.1 (section 3.3). That is about $500 per fertilized cycle, or $46 per tile-day, still above wheat.
   - Late carrot beats late wheat by $15 per tile-day. The carrot book is deep: 80 extra carrots sold at once at the day-25 book average $52.1 against a $55 quote (section 3.3).
   - The egg book is deep, stable at $50-55, and has no floor in reach. Geese are cheap ($300), start producing after 4 days, and pay back until day 22.
   - Tomato gating overlaps the other workflow's tomato line.
4. **Free labour, then use the land.**
   - Evidence: 49% of unit-turns are useful, and a useful action is worth about $27. Hires 13 and later cost $20-54 per useful action, so extra work has to come from the same ~12 hands (section 2.6).
   - SE is bought in 36% of games (median day 18), although it needs only $8.4 per tile-day on day 10 (section 2.7).
   - Converting moves, PASSes and crashed-book CARE into planting on SE is the top-30 pattern: SE on day 10, +23 tiles, fewer CARE actions.
   - Estimate, untested: the potential is up to the ~9.7k gap to the top-30 teams, but it needs a scheduler, not a layer.
5. **Win the slot and the day on premium sales.** A first-slot edge is worth $0.8-2.4k on 20-40 milk or melon (section 3.4). L already takes the within-turn edge. What remains is the across-turn race: sell before the opponent's visible harvest lands. That belongs to the opponent-shadow line of the other workflow.
6. **Small, certain fixes** (under $0.5k per game together):
   - CARE on days 28-29 and FEED on day 29 can never pay (about 18.5 actions per game).
   - Feed uncared animals every other day, not daily.
   - Water survival-only crops every other day. Tomato and strawberry need water only for survival and on fertilized production days.
   - Before a DROP near the cap, use PLACE item n, which keeps what doesn't fit.

What not to chase:

- **Holding floor-priced goods for a recovery.** Only 1-16% of those books were above $50 48 steps later (section 3.5).
- **Fertilizer on melons.** It adds no yield.
- **Early fertilizer on wheat.** Before about day 9 a fertilizer sells for $88, more than two wheat.
- **Fixing execution leaks as a project.** They total at most about $2k per game, spread over five separate mechanisms (section 4).
