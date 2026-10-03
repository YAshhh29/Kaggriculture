# Inspector report: what the top of the Kaggriculture ladder actually does

Primary evidence only. No repository agent was read (no `rl/candidate_*.py`, no
`submissions/`, no `rl/data/*.md`). Sources used:

1. `.conda/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py` (engine ground truth)
2. `kaggle_cache/top200_tapes/*.json` — 1,210 recorded ladder games, both sides' tapes
3. `kaggle_cache/notebooks/*.py` — 9 published competitor sources

All per-game numbers below are counted **inside the engine**, by wrapping
`_apply_unit_action`, `_commit_unit`, `_do_hire`, `_do_buy_land` and
`_end_of_day` during a faithful replay. Nothing is inferred from the board.
Harness: a throwaway local probe script.

## 0. Corpus note (important)

The brief asked to compare a 2800-rated side against a 2300-2500 one. **That
band does not exist in this corpus.** `top200_tapes` is a top-200 scrape:

| statistic | team_score | opponent_rating |
|---|---|---|
| min | 2779.8 | 2615.8 |
| median | 2845.7 | 2835.1 |
| max | 3200.4 | 3176.1 |

Bucket counts by team_score: 2700s=229, 2800s=670, 2900s=232, 3000s=57, 3100s=19, 3200s=3.

So the real contrast available is **~3100-3200 (ladder rank 1-3) vs ~2780-2800
(the bottom of the top-200)**. That is the comparison this report makes, and it
is the more useful one anyway: it is the gap between "good enough for the top
200" and "actually rank 1".

## 1. Engine facts that the measurements hang on

- 720 steps, `turnsPerDay=24`, so **30 days of 24 turns**. Reward = final `money`.
- Each turn a player submits `{"farmer":[...], "hands":[[...],...], "market":[...]}`.
  Every unit (farmer + each hand) gets **one action per turn**.
  **Correction to the brief: there are only 4 compass moves, not 8.**
  `FARMER_MOVES` (line 91) is exactly `{NORTH, SOUTH, EAST, WEST}` — no
  diagonals — so crossing a 10x10 board costs up to 18 worker-turns, and one
  step of walking is one whole turn of one worker's labour.
- `maxMarketOrdersPerTurn = 10`. Orders are executed **one unit at a time, in
  lockstep with the opponent's current order** (`_process_market`, line 538),
  re-quoting `market_price` after every single unit. HIRE and BUY_LAND are
  atomic and resolve first, in player order.
- Hiring costs `FARM_HAND_COST_MULT * fib(hires_today)` = 1,1,2,3,5,8,13,21,...
  (`_hire_cost`, line 690). Hands are **wiped every night** (`_end_of_day`
  resets `farm["hands"] = []`), so labour is rented daily. The cumulative cost
  per day, and what a whole season of that many hands costs:

  | hands that day | n-th hire costs | that day's total | x30 days | worker-turns/day bought |
  |---|---|---|---|---|
  | 5 | 5 | 12 | 360 | 120 |
  | 8 | 21 | 54 | 1,620 | 192 |
  | 10 | 55 | 143 | 4,290 | 240 |
  | **11** | **89** | **232** | **6,960** | **264** |
  | 12 | 144 | 376 | 11,280 | 288 |
  | 13 | 233 | 609 | 18,270 | 312 |
  | 14 | 377 | 986 | 29,580 | 336 |
  | 16 | 987 | 2,583 | 77,490 | 384 |

  Labour is almost free up to ~11 hands and then explodes. Both cohorts stop at
  exactly 11 (section B.3).
- **Real ladder games give the agent 1 second per turn.** All 1,210 tapes carry
  the identical configuration `actTimeout=1, runTimeout=1200, episodeSteps=720,
  startingMoney=3000, shedCapacity=100`. 720 turns inside a 1,200s total budget
  is ~1.67s/turn on average, with a 1s hard cap per call. This is the constraint
  that makes a precomputed tape attractive in the first place: it costs nothing
  to execute.
- Land: `LAND_PRICES = [1000, 2000, 4000]` for NE, SW, SE. NW (25 tiles) is free.
- Market price: `base ± amp * f(|inv - 10000|)`, floored at 1. Selling raises
  inventory and **drops the price**; the town consumes (lowers inventory, raises
  price) every 4 steps per shop and every 24 steps at the town centre.
- `shedCapacity = 100`. Bought goods land in the shed and **a full shed blocks
  BUY_PRODUCT / BUY_ANIMAL entirely** (`_commit_unit`, lines 653-676).
- Unwatered 2 days running -> the plant becomes a WEED. Unfed 2 days -> the
  animal escapes and leaves the bare structure.


## A. FIDELITY — do the tapes replay?

Method: for each tape, decode both `actions_zlib_b64` (the recorded team) and
`opponent_actions_zlib_b64`, wrap each in `rl/replay_agent.build_replay_agent`,
seat them per the recorded `seat`, and run
`make("kaggriculture", configuration={"episodeSteps":720,"seed":<seed>,"runTimeout":36000,"actTimeout":60})`.
Compare final rewards to `rewards{them,opponent}`.

| tape | team (rating) | opponent (rating) | seat | recorded them/opp | replayed them/opp | match |
|---|---|---|---|---|---|---|
| ep111743272 | DSM (3200.4) | Unknown Mother-Goose (3060) | 0 | 119842 / 120507 | 119842 / 120507 | exact |
| ep111876816 | DSM (3200.4) | Majkel1337 (3076) | 1 | 92807 / 86317 | 92807 / 86317 | exact |
| ep111883527 | DSM (3200.4) | Vadim Vasilenko (3099) | 0 | 117571 / 110607 | 117571 / 110607 | exact |
| ep109983899 | Majkel1337 (3192.2) | Unknown Mother-Goose (3114) | 1 | 101597 / 102389 | 101597 / 102389 | exact |
| ep110003132 | Majkel1337 (3192.2) | Unknown Mother-Goose (3107) | 0 | 145162 / 157574 | 145162 / 157574 | exact |
| ep110016042 | Majkel1337 (3192.2) | DSM (3105) | 1 | 89685 / 84087 | 89685 / 84087 | exact |
| ep110022430 | Majkel1337 (3192.2) | Unknown Mother-Goose (3124) | 1 | 128071 / 128233 | 128071 / 128233 | exact |
| ep110028793 | Majkel1337 (3192.2) | DSM (3101) | 0 | 72658 / 68215 | 72658 / 68215 | exact |
| ep110035119 | Majkel1337 (3192.2) | Unknown Mother-Goose (3118) | 0 | 120038 / 115622 | 120038 / 115622 | exact |
| ep110028792 | DSM (3119.7) | Sida Zuo (3038) | 1 | 103075 / 100312 | 103075 / 100312 | exact |
| ep110035124 | DSM (3119.7) | Excluding (3052) | 0 | 103754 / 92074 | 103754 / 92074 | exact |
| ep110040731 | DSM (3119.7) | Excluding (3045) | 1 | 118445 / 115660 | 118445 / 115660 | exact |

**12 of 12 reproduce to the coin, both sides.** Not a single drift. The tapes
are fully trustworthy evidence: the environment is deterministic given the seed,
the recorded action tapes are complete and correctly aligned (action index
`step+1` is the action chosen while observing `step`), and the opponent tapes
are recorded from the same episode rather than reconstructed.

Practical consequence: **anything measured from these replays is ground truth,
not a reconstruction.** Median replay cost is ~8s per game on this machine.

**Extended check.** Section B needed a larger sample, so the same replay was run
over **149 tapes** (all 79 with `team_score >= 3000`, plus a random 70 with
`team_score <= 2800`), this time with the counting instrumentation attached.
**149 of 149 reproduced both sides' rewards exactly**, with the hooks live — so
the instrumentation is provably non-invasive as well.

One harness note worth recording, because it silently corrupted a first pass:
`kaggle_environments` hands the interpreter freshly deserialized observation
objects on every step, so a hook that identifies the player by `id(farm)` maps
~98% of events to the wrong bucket. The identity maps have to be rebuilt inside
a wrapped `interpreter`, and the wrapper must be installed into
`kaggle_environments.environments["kaggriculture"]["interpreter"]` as well as on
the module, because `make()` copies the registry entry and caches the function
object.


## B0. The shape of the market (engine ground truth, computed from `market_price`)

Section B's numbers only mean something against this. Every price below comes
from calling the engine's own `market_price(good, inventory)`.

Market inventory starts at `I0 = 10000` for every good. **Selling raises
inventory and lowers the price; the town lowers inventory and raises it.** The
goods differ enormously in how much selling they can absorb:

| good | base | price at I0-100 | I0-25 | I0 | I0+25 | I0+50 | I0+100 | units above I0 before price hits the floor | coins for dumping 60 units from I0 | vs 60 x base |
|---|---|---|---|---|---|---|---|---|---|---|
| WHEAT | 25 | 35 | 30 | 25 | 22 | 22 | 21 | >20000 | 1,347 | 90% |
| CARROT | 35 | 43 | 37 | 35 | 29 | 27 | 23 | 842 | 1,747 | 83% |
| TOMATO | 60 | 72 | 63 | 60 | 47 | 42 | 35 | 529 | 2,823 | 78% |
| STRAWBERRY | 120 | 204 | 162 | 120 | 72 | 24 | 1 | **62** | 3,801 | **53%** |
| MELON | 250 | 290 | 279 | 250 | 244 | 225 | 150 | 158 | 14,301 | 95% |
| EGG | 50 | 56 | 52 | 50 | 44 | 43 | 42 | >20000 | 2,674 | 89% |
| MILK | 160 | 247 | 203 | 160 | 108 | 55 | 1 | **76** | 5,886 | **61%** |
| WOOL | 200 | 240 | 228 | 200 | 164 | 55 | 1 | **59** | 7,929 | **66%** |
| FERTILIZER | 100 | 120 | 105 | 100 | 95 | 90 | 80 | 493 | 5,646 | 94% |

The marginal price path for a burst sale starting at I0 (price of the k-th unit):

```
STRAWBERRY  k=0:120  10:101  20: 82  30: 62  40: 43  50: 24  60:  5  80:1
MILK        k=0:160  10:139  20:118  30: 97  40: 76  50: 55  60: 34  80:1
WOOL        k=0:200  10:194  20:177  30:148  40:107  50: 55  60:  1  80:1
MELON       k=0:250  10:249  20:246  30:241  40:234  50:225  60:214  80:186
WHEAT       k=0: 25  10: 23  20: 22  30: 22  40: 22  50: 22  60: 22  80:21
EGG         k=0: 50  10: 46  20: 45  30: 44  40: 44  50: 43  60: 43  80:42
CARROT      k=0: 35  10: 31  20: 30  30: 29  40: 28  50: 27  60: 26  80:25
```

Two families, and they want opposite treatment:

- **Bottomless (WHEAT, EGG, CARROT, MELON, FERTILIZER, TOMATO)** — log/sqrt/linear
  glut curves. Dumping is nearly free. WHEAT loses 10% on a 60-unit dump; MELON
  loses 5%.
- **Razor-thin (WOOL, STRAWBERRY, MILK)** — the goods with the *highest* base
  prices are also the ones with `above_func` in {`sq`, `linear`} and
  `above_target` of 3.20 / 1.60 / 1.60. **59 units of wool sold into an
  untouched market takes the price from 200 to 1.** They are also the goods with
  the biggest *upside* from scarcity: wool at I0-100 is 240, milk 247, strawberry
  **204 — 70% above base**.

So the premium goods are not "sell for more". They are **a demand quota you must
not exceed**, and the quota is refilled by the town on a fixed clock.

### The town's demand budget

Shops unlock at the end of day 2, 5, 8, ... (`townShopUnlockInterval = 3`),
capped at `MAX_SHOP_INSTANCES = 8`, so instances go live at steps 72, 144, 216,
288, 360, 432, 504, 576. Each instance consumes **every 4 steps**
(`townShopSellInterval = 4`), taking 1 unit of each of its products — or **2
units if the shop sells only one product** (YARN_STORE -> WOOL, PET_CAFE ->
CARROT). The instances therefore live for 162, 144, 126, 108, 90, 72, 54 and 36
four-step ticks respectively: **792 shop-ticks for the whole season.** The town
centre adds 30 units of each of the 8 non-fertilizer goods (every 24 steps).

Shops are drawn uniformly with replacement from the 8 kinds, so the *expected*
season demand per good is:

| good | shops that sell it | expected shop demand (units/season) | town centre | total demand |
|---|---|---|---|---|
| WHEAT | 5 (BAKERY, BRUNCH_SPOT, FARMERS_MARKET, ICE_CREAM_SHOP, PIZZA_SHOP) | 495 | 30 | **525** |
| STRAWBERRY | 4 (BRUNCH_SPOT, FARMERS_MARKET, ICE_CREAM_SHOP, SMOOTHIE_SHOP) | 396 | 30 | **426** |
| CARROT | 2 (FARMERS_MARKET, PET_CAFE) | 297 | 30 | 327 |
| MILK | 3 (ICE_CREAM_SHOP, PIZZA_SHOP, SMOOTHIE_SHOP) | 297 | 30 | 327 |
| TOMATO | 2 (FARMERS_MARKET, PIZZA_SHOP) | 198 | 30 | 228 |
| EGG | 2 (BAKERY, BRUNCH_SPOT) | 198 | 30 | 228 |
| WOOL | 1 (YARN_STORE, but double rate) | 198 | 30 | 228 |
| **MELON** | **0 — no shop sells melon** | **0** | 30 | **30** |
| **FERTILIZER** | **0** | **0** | **0** | **0** |

**MELON and FERTILIZER are structurally different from every other good: they
have no renewable demand.** Their market inventory only ever rises, so their
total lifetime revenue is a **fixed pot shared between the two farms**, and the
only question is who gets there first:

| | total combined extractable | first 36 units | first 72 | first 144 | marginal unit #144 |
|---|---|---|---|---|---|
| MELON | 26,487 coins (over ~160 units) | 8,852 (mean 245.9) | 16,785 (mean 233.1) | 26,156 (mean 181.6) | **43** |
| FERTILIZER | 25,052 coins (over ~500 units) | 3,474 (mean 96.5) | 6,689 (mean 92.9) | 12,341 (mean 85.7) | 71 |

A single YARN_STORE drawn first is worth `162 x 2 + 30 = 354 units` of wool
demand over the season — which, at base 200, is ~70,800 coins of near-base
revenue, **if it is drip-fed**. Dumped in six bursts of 59 it is worth ~47,000.
That single arithmetic is why `_router` (section C.2) reads the shop draw at step
144 and why the whole strategy branches on `YARN_STORE` count.

It is also exactly why `_sell_lead` (section C.4a) refuses to act when
`step % 4 == 0`: that is the tick on which the town is about to restock demand,
and selling across it would spend the quota before it exists.


## B. WHAT THE STRONG FARMS DO

Every number below is counted inside the engine during a faithful replay.
`_apply_unit_action` is wrapped to record the op and whether it actually
changed anything (position, carried inventory or the tile under the unit);
`_commit_unit` records every single unit sold or bought and the exact price
the engine quoted for it; `_do_hire` / `_do_buy_land` record successful hires
and land unlocks; `_end_of_day` snapshots the tile census before the nightly
reset. Rewards still reproduced exactly with instrumentation attached.

- **ELITE** = the recorded side of every tape with `team_score >= 3000`: **79 games across 15 teams** (DSM 9 games, Majkel1337 9, THIRD FARM CLUB 6, Orbital Terraformer 6, Sida Zuo 6, Unknown Mother-Goose 6, Ebi 5, ymg_aq 5, Arda Ceylan 5, SpaTaro 5, Excluding 4, Planned Economy 4, KawattaTaido 3, Vadim Vasilenko 3, M & M & P & Q 3).
- **FIELD** = the recorded side of a random sample of tapes with `team_score <= 2800`: **70 games** (a random sample of the bottom of the top-200).

All figures are **medians over games**, per game, for the rated side only.

### B.1 Headline

| | ELITE (3000+) | FIELD (<=2800) | gap |
|---|---|---|---|
| final money (coins) | 106254 | 101824 | +4,430 |
| total sale revenue (coins) | 133131 | 130118 | +3,013 |
| total spend on market buys (coins) | 21285 | 21472 | -186 |
| units sold (all goods) | 1457 | 1565 | -108 |
| units harvested (all goods) | 1769 | 1768 | +1 |
| hands hired (whole game) | 285 | 268 | +17 |
| land quadrants bought | 2.0 | 2.0 | +0.0 |
| worker-turns taken (whole game) | 7219 | 6808 | +411 |

### B.2 Where the labour goes

A worker-turn is one unit (main farmer or one hand) acting for one turn.
`turnsPerDay=24`, and every hand costs a turn of walking to get anywhere, so
this is the real budget being competed over.

| | ELITE | FIELD |
|---|---|---|
| worker-turns per game | 7219 | 6808 |
| **walking** (N/S/E/W) share | **44.3%** | **42.2%** |
| **PASS** share | **3.6%** | **7.1%** |
| real jobs share | 50.4% | 50.7% |
| of which had no effect (wasted) | 0.75pp | 0.69pp |
| walk turns blocked by board edge | 0.00% | 0.00% |

Full op mix, as a share of all worker-turns, with the per-game count and how
many of those calls actually changed engine state:

| op | ELITE share | ELITE /game | ELITE effective | FIELD share | FIELD /game | FIELD effective |
|---|---|---|---|---|---|---|
| WATER | 16.87% | 1212 | 1178 | 16.24% | 1122 | 1110 |
| NORTH | 13.54% | 973 | 973 | 13.40% | 926 | 926 |
| WEST | 12.69% | 912 | 912 | 12.76% | 882 | 882 |
| EAST | 8.99% | 646 | 646 | 8.77% | 606 | 606 |
| SOUTH | 8.46% | 608 | 608 | 7.39% | 511 | 511 |
| HARVEST | 6.87% | 493 | 485 | 7.01% | 485 | 479 |
| PASS | 5.82% | 418 | 0 | 7.29% | 504 | 0 |
| COLLECT_FERTILIZER | 5.37% | 386 | 382 | 5.45% | 377 | 368 |
| FEED | 4.59% | 330 | 327 | 4.69% | 324 | 323 |
| CARE | 4.52% | 325 | 321 | 5.91% | 409 | 392 |
| PLANT | 3.51% | 252 | 249 | 3.47% | 240 | 240 |
| PICKUP | 3.24% | 233 | 226 | 2.94% | 203 | 203 |
| FERTILIZE | 2.40% | 173 | 173 | 1.69% | 117 | 116 |
| PLACE | 1.32% | 95 | 93 | 1.47% | 102 | 100 |
| DROP | 1.00% | 72 | 71 | 0.69% | 48 | 48 |
| DIG | 0.52% | 37 | 36 | 0.54% | 37 | 34 |
| BUILD_PASTURE | 0.22% | 16 | 15 | 0.20% | 14 | 14 |
| BUILD_COOP | 0.07% | 5 | 4 | 0.07% | 5 | 5 |

### B.3 Hands hired per day

Hands are wiped every night and re-hired every morning, at `fib(n)` coins for
the n-th hire of that day. The profile is the labour curve of the season:

| day | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 20 | 22 | 24 | 26 | 28 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ELITE hands | 4 | 6 | 6 | 8 | 9 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 10 |
| FIELD hands | 5 | 4 | 4 | 7 | 8 | 11 | 9 | 9 | 11 | 11 | 11 | 11 | 11 | 11 | 11 |

Peak hands: ELITE 11, FIELD 11. 
Whole-game hires: ELITE 285, FIELD 268. 

### B.4 Land: owned vs occupied vs bare, by day

`owned` = tiles not LOCKED (25 = NW only, 50 / 75 / 100 after each BUY_LAND).
`plant` + `animal` + `empty structure` + `weed` + `bare` = owned.

| day | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 20 | 22 | 24 | 26 | 28 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ELITE owned | 25 | 25 | 25 | 50 | 50 | 75 | 75 | 75 | 75 | 75 | 75 | 75 | 75 | 75 | 75 |
| FIELD owned | 25 | 25 | 25 | 50 | 50 | 50 | 75 | 75 | 75 | 75 | 75 | 75 | 75 | 75 | 75 |
| ELITE planted | 16 | 19 | 19 | 34 | 38 | 56 | 57 | 58 | 57 | 57 | 57 | 56 | 56 | 54 | 34 |
| FIELD planted | 19 | 19 | 19 | 29 | 37 | 32 | 57 | 57 | 58 | 58 | 58 | 58 | 58 | 58 | 21 |
| ELITE animals | 5 | 5 | 6 | 10 | 12 | 15 | 17 | 17 | 17 | 17 | 17 | 16 | 16 | 16 | 14 |
| FIELD animals | 4 | 5 | 6 | 8 | 12 | 16 | 17 | 17 | 17 | 17 | 17 | 17 | 17 | 17 | 17 |
| ELITE bare | 4 | 0 | 0 | 6 | 0 | 3 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 3 | 22 |
| FIELD bare | 2 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 |
| ELITE weeds | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| FIELD weeds | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Money on hand at the end of each day:

| day | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 20 | 22 | 24 | 26 | 28 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ELITE coins | 10 | 25 | 369 | 160 | 1270 | 7604 | 15044 | 23367 | 34821 | 49860 | 60196 | 69112 | 77879 | 85861 | 96970 |
| FIELD coins | 22 | 211 | 684 | 1116 | 1429 | 15830 | 18072 | 23812 | 34572 | 42521 | 51528 | 63045 | 72056 | 78604 | 92535 |

### B.5 Harvest, sales, and the price actually realised

`ppu` is total coins received divided by units sold, measured unit by unit at
the price `_commit_unit` was handed. `base` is `MARKET_PARAMS[good]["base"]`.
A ratio above 1.0 means they sold into scarcity the town created; below 1.0
means they sold into their own glut.

| good | base | ELITE harv | ELITE sold | ELITE revenue | ELITE ppu | ppu/base | FIELD harv | FIELD sold | FIELD revenue | FIELD ppu | ppu/base |
|---|---|---|---|---|---|---|---|---|---|---|---|
| WHEAT | 25 | 542 | 390 | 15,122 | 37.9 | 1.52 | 590 | 416 | 15,463 | 37.4 | 1.50 |
| CARROT | 35 | 123 | 120 | 5,791 | 45.8 | 1.31 | 94 | 94 | 4,919 | 51.1 | 1.46 |
| TOMATO | 60 | 59 | 58 | 4,293 | 72.8 | 1.21 | 0 | 0 | 0 | 128.9 | 2.15 |
| STRAWBERRY | 120 | 228 | 228 | 32,826 | 144.7 | 1.21 | 249 | 249 | 32,776 | 131.2 | 1.09 |
| MELON | 250 | 72 | 72 | 14,354 | 189.5 | 0.76 | 72 | 72 | 14,267 | 198.2 | 0.79 |
| EGG | 50 | 82 | 82 | 4,320 | 47.7 | 0.95 | 83 | 82 | 4,464 | 52.2 | 1.04 |
| MILK | 160 | 203 | 203 | 21,802 | 101.5 | 0.63 | 201 | 201 | 17,254 | 81.1 | 0.51 |
| WOOL | 200 | 87 | 87 | 10,144 | 109.0 | 0.54 | 110 | 110 | 10,130 | 78.0 | 0.39 |
| FERTILIZER | 100 | 373 | 217 | 12,371 | 58.1 | 0.58 | 368 | 341 | 15,304 | 45.1 | 0.45 |

Revenue mix (median coins per game from each good, share of total):

| good | ELITE coins | ELITE share | FIELD coins | FIELD share |
|---|---|---|---|---|
| STRAWBERRY | 32,826 | 27.1% | 32,776 | 28.6% |
| MILK | 21,802 | 18.0% | 17,254 | 15.1% |
| WHEAT | 15,122 | 12.5% | 15,463 | 13.5% |
| MELON | 14,354 | 11.9% | 14,267 | 12.5% |
| FERTILIZER | 12,371 | 10.2% | 15,304 | 13.4% |
| WOOL | 10,144 | 8.4% | 10,130 | 8.8% |
| CARROT | 5,791 | 4.8% | 4,919 | 4.3% |
| EGG | 4,320 | 3.6% | 4,464 | 3.9% |
| TOMATO | 4,293 | 3.5% | 0 | 0.0% |

### B.6 What they buy

| order | ELITE units/game | ELITE coins/game | FIELD units/game | FIELD coins/game |
|---|---|---|---|---|
| BUY_PRODUCT WHEAT | 183.3 | 6,668 | 312.8 | 12,291 |
| BUY_ANIMAL COW | 8.6 | 3,433 | 7.6 | 3,029 |
| BUY_SEED STRAWBERRY | 31.7 | 3,172 | 33.0 | 3,300 |
| BUY_ANIMAL SHEEP | 6.1 | 3,057 | 6.4 | 3,200 |
| BUY_SEED WHEAT | 145.8 | 1,458 | 163.0 | 1,630 |
| BUY_SEED MELON | 13.2 | 1,056 | 12.0 | 959 |
| BUY_ANIMAL GOOSE | 3.5 | 1,037 | 3.1 | 921 |
| BUY_SEED CARROT | 50.7 | 1,014 | 31.8 | 637 |
| BUY_PRODUCT FERTILIZER | 14.4 | 499 | 91.2 | 2,702 |
| BUY_SEED TOMATO | 9.3 | 467 | 1.9 | 93 |

### B.7 Herd

| | ELITE | FIELD |
|---|---|---|
| peak animals placed | 17 | 17 |
| final GOOSE | 3.3 | 3.1 |
| final COW | 7.2 | 7.6 |
| final SHEEP | 4.0 | 6.3 |

Crop planting, as tile-days standing (a tile planted with X, counted once per
night it survived) — the real measure of how the field is allocated:

| crop | ELITE tile-days | FIELD tile-days |
|---|---|---|
| WHEAT | 454 | 519 |
| CARROT | 132 | 89 |
| TOMATO | 102 | 20 |
| STRAWBERRY | 499 | 544 |
| MELON | 131 | 120 |

### B.8 Sell pacing (every decoded tape in the corpus, not only the replayed ones)

ELITE 79 tapes (team_score >= 3000), FIELD 235 tapes (<= 2800).
Measured on the submitted SELL orders themselves, so this is what the agent
*intended*, independent of what the shed could actually fill.

| | ELITE | FIELD |
|---|---|---|
| SELL orders issued per game (median) | 349 | 449 |
| lot size, all goods: median | 3 | 4 |
| lot size, all goods: mean | 4.1 | 6.9 |
| lot size, all goods: p90 | 8 | 12 |
| **premium lot (WOOL/STRAWBERRY/MILK/MELON): mean** | **3.7** | **7.8** |
| premium lot: p90 | 6 | 12 |
| share of all sells falling in the single busiest hour | 7.3% (hour 2) | 13.0% (hour 2) |

The ELITE break their selling into **more, smaller orders** than the FIELD.
On exactly the goods where price impact bites -- wool, strawberry, milk, melon
-- the ELITE mean lot is **3.7 units against the FIELD's 7.8, and the p90 is
6 against 12**. Read that against the marginal price paths in B0: a
12-unit wool lot starting from I0 realises 200+199+...+189, but the same
12-unit lot dropped on top of an existing 40-unit glut realises prices in the
55-107 band -- roughly half. The ELITE also spread selling across the day
(7.3% in the busiest hour) where the FIELD concentrates it (13.0%).

### B.9 Derived efficiency, and the day-0 opening

| ratio | ELITE | FIELD |
|---|---|---|
| sale revenue per worker-turn | 18.4 coins | 19.0 coins |
| sale revenue per *job* turn (excl. walking and PASS) | 37.3 coins | 37.5 coins |
| walking turns per job turn | 0.86 | 0.83 |
| units harvested per worker-turn | 0.260 | 0.265 |
| units sold as a share of units harvested | 82.6% | 88.6% |
| final money | 106,254 | 101,824 |

Day 0 only (steps 0-23), **mean** units *ordered* per game, from the tapes
(ELITE 79 tapes, FIELD 235 tapes):

| day-0 order | ELITE units | FIELD units |
|---|---|---|
| SELL WHEAT | 68.8 | 37.7 |
| BUY_ANIMAL GOOSE | 17.6 | 0.0 |
| BUY_PRODUCT WHEAT | 13.8 | 32.0 |
| BUY_SEED WHEAT | 10.5 | 6.8 |
| BUY_SEED MELON | 6.8 | 12.0 |
| SELL MELON | 5.2 | 0.0 |
| SELL MILK | 5.2 | 0.0 |
| SELL STRAWBERRY | 5.2 | 0.0 |
| SELL TOMATO | 5.0 | 0.0 |
| SELL EGG | 5.0 | 0.0 |
| SELL CARROT | 5.0 | 0.0 |
| SELL WOOL | 5.0 | 0.0 |
| BUY_ANIMAL COW | 3.0 | 2.0 |
| BUY_ANIMAL SHEEP | 2.7 | 2.0 |
| BUY_PRODUCT STRAWBERRY | 2.6 | 0.0 |
| BUY_PRODUCT TOMATO | 1.7 | 0.0 |
| BUY_PRODUCT CARROT | 1.2 | 0.0 |
| BUY_PRODUCT MILK | 0.5 | 0.0 |
| BUY_PRODUCT MELON | 0.5 | 0.0 |
| BUY_SEED STRAWBERRY | 0.5 | 0.0 |
| BUY_PRODUCT WOOL | 0.4 | 0.0 |
| BUY_PRODUCT EGG | 0.2 | 0.0 |
| HIRE orders | 4.6 | 4.9 |

First `BUY_ANIMAL` order: ELITE median **step 1** (79/79 games), FIELD median **step 2** (235/235 games).


Two caveats on that table, both verified by tracing the orders back to teams:

- The block of `SELL <everything> ~5` on day 0 is **one team only** (DSM 3120,
  132 orders across its tapes). The shed is empty on day 0, so `_commit_unit`
  returns False immediately and these are pure no-ops — an unconditional
  "liquidate whatever I hold" idiom that happens to be free on day 0.
- Every `BUY_PRODUCT` of something other than WHEAT or FERTILIZER is also a
  no-op: `_process_market` only quotes `BUY_PRODUCT` for those two items and
  otherwise sets `order_states[player_id] = None`. **One ELITE team (SpaTaro,
  3080) burns 1,364 market-order slots per game on these.** It is a bug, not a
  trick, and it still rates 3080 — which says how little the 10-slot order
  budget binds (mean orders per turn: ELITE 1.50, FIELD 1.38; only 3% of turns
  reach the cap, and zero orders per game are discarded past it).

Stripping those artifacts, the real day-0 difference is: **ELITE buys 13.8 wheat
and sells 68.8; FIELD buys 32.0 and sells 37.7.** The FIELD is doing the
oversized round trip that `nathanjacob`'s notebook measured as a net loss
(section C.5), and it shows up over the whole game in B.6: FIELD pays 12,291
coins for 313 units of market wheat, ELITE pays 6,668 for 183.

### B.10 What the B tables say, in one place

**The money gap is small and it is almost entirely a price gap, not a production gap.**

- Final money: ELITE 106,254 vs FIELD 101,824 — a **4.3%** gap across a ~300-point
  rating difference. This is a game of thin margins.
- Units harvested: ELITE 1,769 vs FIELD 1,768. **Identical.** They grow the same
  amount of food.
- Units sold: ELITE 1,457 vs FIELD 1,565. The ELITE sell **7% fewer units** and
  still take **more money**.
- Revenue per worker-turn: 18.4 vs 19.0 coins — the FIELD is very slightly
  *better* per turn. The ELITE simply take 411 more turns (7,219 vs 6,808) by
  hiring earlier.

So production, labour efficiency and land are all near-parity. The gap is in
`ppu` — the price each unit actually fetched:

| good | ELITE ppu | FIELD ppu | ELITE edge per unit | ELITE units | edge x units |
|---|---|---|---|---|---|
| WOOL | 109.0 | 78.0 | +31.0 | 87 | **+2,700** |
| MILK | 101.5 | 81.1 | +20.4 | 203 | **+4,140** |
| STRAWBERRY | 144.7 | 131.2 | +13.5 | 228 | **+3,080** |
| FERTILIZER | 58.1 | 45.1 | +13.0 | 217 | +2,820 |
| WHEAT | 37.9 | 37.4 | +0.5 | 390 | +200 |
| CARROT | 45.8 | 51.1 | -5.3 | 120 | -640 |
| MELON | 189.5 | 198.2 | -8.7 | 72 | -630 |
| EGG | 47.7 | 52.2 | -4.5 | 82 | -370 |

Every good where the ELITE win is one of the three razor-thin markets from B0
(wool `sq`/3.20, milk `linear`/1.60, strawberry `linear`/1.60) plus fertilizer,
which has **no town demand at all**. Every good where they lose is a deep market
where price discipline does not pay. That is not a coincidence: it is the whole
skill.

The mechanism is visible in B.8: on exactly those goods the ELITE mean sell lot
is **3.7 units against the FIELD's 7.8**, p90 **6 against 12**.

**Four more concrete, separable differences:**

1. **Market wheat.** ELITE buy 183 units for 6,668 coins; FIELD buy 313 for
   12,291. A **5,623-coin** swing, and the FIELD gets *worse* unit pricing
   (39.3 vs 36.4/unit) because it is the one moving the price.
2. **Market fertilizer.** ELITE buy 14 units (499 coins); FIELD buy 91 (2,702).
   The FIELD buys fertilizer to fertilize while simultaneously dumping 341 of
   its own (at 45.1/unit). The ELITE keep 173 of their 373 for their own crops
   and sell only 217 — staying higher on a curve that never recovers. A
   **2,200-coin** swing, plus the 13.0/unit price edge.
3. **Tomato.** ELITE harvest 59 tomatoes for 4,293 coins at 1.21x base; **the
   FIELD grows none at all** (0 harvested, 20 tile-days vs ELITE's 102). An
   entire 4,300-coin revenue line the FIELD has not discovered.
4. **Idle turns.** ELITE PASS on 3.6% of worker-turns, FIELD on 7.1% — 418 vs
   504 wasted turns, and the ELITE have more turns in total. At 37.3 coins per
   job-turn, closing that gap alone is worth ~3,200 coins.

**Where both are leaving money on the table:**

- **Melon is sold below base by both** (ppu 189.5 and 198.2 against base 250).
  Each side sells 72 melons; 144 combined sits against a market with 30 units of
  season-long demand (no shop sells melon at all) and ~158 units of depth. The
  pair is saturating it. Melon is nonetheless by far the best crop per
  worker-turn (94.7 coins/turn at base vs wheat's 12.9), so the lever is not
  "plant more" but "sell earlier than the opponent" — see D.1 item 7.
- **Both stop hiring at exactly 11 hands.** The 12th hand costs 144/day
  (4,320 for the season) and buys 24 more worker-turns per day — 720 turns over
  the season, i.e. **6.0 coins per extra worker-turn against a measured job-turn
  value of 37.3**. Nobody buys it. The 13th is 11,310 for the season over the
  11-hand baseline for 1,440 extra turns, ~7.9 coins/turn: still far under.
- **Nobody uses the market order budget.** Mean 1.5 orders/turn out of 10
  allowed; 3% of turns hit the cap; zero orders discarded.

## C. ARCHITECTURE — how the published strong agents are actually built

Sources read: `kaggle_cache/notebooks/*.py`. The decisive one is
`ahmedberatozer__kaggriculture-v55-one-turn-market-race-edge.py`, which embeds
its **entire real submission** as a zlib+base85 blob (`SOURCE_BLOB`, line 34;
`SOURCE_BYTES = zlib.decompress(base64.b85decode(SOURCE_BLOB))`, line 232,
SHA256-checked at line 233). Decoded it is **1,014,183 bytes / 6,658 lines**.
`aurax7__kaggriculture-shop-router-reactive-v7.py` (4,004 lines) is the same
codebase in plain source. Line numbers below refer to the decoded v55 `main.py`
unless marked `aurax7`.

### C.1 They do NOT decide per turn. They replay a precomputed tape.

This is the single most important architectural fact.

`Chassis` (v55 line 406 / aurax7 line 398) documents itself as:

```python
class Chassis:
    """Replays ``routes[router(...)]`` with reactive safety/market layers.

    routes         : {route_id: list of >= 719 Kaggle action dicts}
    router         : callable(observation, step, state_dict) -> route_id, called every
                     step; ``state_dict`` is per-player and persists across the game.
```

and the per-turn action is a **dict lookup by step index**, not a decision
(aurax7 line 428):

```python
    def _route_action(self, route, step):
        tape = self.routes[route]
        if 0 <= step < len(tape) and isinstance(tape[step], dict):
            return copy.deepcopy(tape[step])
        return copy.deepcopy(PASS_ACTION)
```

Measured by loading the decoded v55 module: **41 routes, each a list of 719
fully-specified action dicts** (`{"farmer": [...], "hands": [[...],...],
"market": [[...],...]}`). Worker routing, the watering schedule, the feeding
schedule, shed drops and market orders are all baked in offline.
`anhadmahajan06`'s notebook names this "**The Stored Programme Paradigm (Action
Tapes)**" and gives the reason:

> "Rather than making myopic, greedy turn-by-turn decisions that lead to spatial
> deadlocks and worker collisions, our agent employs precomputed, multi-agent
> coordinating action tapes."

### C.2 How the work order is chosen: essentially one observation, at step 144

`_router` (v55 line 961) is the *entire* strategic decision surface. It reads
the board on exactly three occasions in 720 turns:

```python
def _router(observation,step,state):
    if step==2:
        _rv=observation['farms'][1-int(observation['player'])]
        state['rkey']=(round(float(_rv['money']),3), int(observation['market']['inventory']['WHEAT']))
    if step>=144 and not state.get('day6'):
        shops=tuple((_get(_get(observation,'town',{}),'unlocked_shops',[]) or [])[:2])
        use_new=shops.count('YARN_STORE')<=0
        state['expert']='EXP240' if use_new else 'V39'
        state['route']=_R108_SHOP_ROUTES.get(shops,100) if use_new else _R110_OLD_SHOPS.get(shops,0)
        state['route']=_V92_TABLE.get(shops,state['route'])
        if 'YARN_STORE' in shops and state.get('rkey') in _V93_ROUTE_BY_RIVAL:
            state['route']=_V93_ROUTE_BY_RIVAL[state['rkey']]
        state['day6']=True
    if step>=648 and not state.get('day27'):
        state['route']=2
        state['day27']=True
    return state.get('route',0)
```

- **step 2** — fingerprint the rival (their money + market wheat inventory). An
  opponent-identification key, used only to pick a counter-route against one
  specific rival: `_V93_ROUTE_BY_RIVAL = {(229.0, 9989): 128}` (line 960).
- **step 144 (day 6, hour 0)** — read `town.unlocked_shops[:2]`; the first two
  shop draws are now public. **Commit to one of 41 routes for the rest of the
  season** by table lookup on the shop pair. No search. The comment at line 953
  says the policy split was "learned with five whole-team held-out folds" and
  "uses only first-two-shop YARN_STORE count".
- **step 648 (day 27)** — switch unconditionally to route 2, the liquidation tape.

Three observations decide the season. Everything the workers do is the tape.

### C.3 The reactive layers are a thin safety/market jacket in fixed order

`Chassis.act` (aurax7 line 452) mutates the tape action through a fixed
pipeline, each stage switchable via `DEFAULT_SETTINGS` (v55 line 263):

```python
action = self._route_action(route, step)
raw = copy.deepcopy(action)
try:
    if cfg["hand_align"]:  self._hand_align(action, view)   # pad/truncate hands list to real hand count
    if cfg["weed_repair"]: self._weed_repair(action, view, st, route, step)
    if cfg["sell_lead"] or cfg["front_run"]: self._apply_suppression(action, st["sell_state"], step)
    projected = self._projected_shed(action, view)
    if cfg["sell_lead"]:   self._sell_lead(action, view, lead_available, route, step, next_sup)
    if cfg["front_run"]:   self._front_run(action, view, lead_available, route, step, next_sup)
    if cfg["budget_guard"]: self._budget_guard(action, view, route, step)
    if cfg["room_guard"]:   self._room_guard(action, view, route, step)
    if cfg["clamp_sells"]:  self._clamp_sells(action, projected)
    if cfg["dead_stock"]:   self._dead_stock(action, view, projected, route, step)
    if cfg["terminal_liquidation"]: self._terminal_liquidation(action, projected, step)
    action["market"] = action["market"][: cfg["max_orders"]]
    return action
except Exception:
    self.diagnostics["layer_fallbacks"] += 1
    return raw
```

The shipped v55 config turns **most of them off** (line 951):

```python
_SETTINGS={'hand_align': True, 'weed_repair': True, 'sell_lead': True,
           'budget_guard': False, 'room_guard': False, 'clamp_sells': False,
           'dead_stock': False, 'terminal_liquidation': False, 'front_run': False}
```

Three live layers: keep the hands list the right length, repair a tile the weed
RNG ruined, and lead sales by one step. `nathanjacob__kaggriculture-pipe-7`
reports the others *lose* when enabled: `clamp_sells` 2W-48L, `dead_stock`
19W-27L, expanded terminal planner 2W-3L-45T. Their conclusion:

> "V45 has 30 reactive wrapper layers calibrated together like a Swiss watch.
> Change one gear and the whole thing breaks."

### C.4 How market orders are built, and in what order they are emitted

Order **within the 10-slot market list matters**, because `_process_market`
(engine line 538) walks both players' lists index by index in lockstep and
re-quotes `market_price` after every single unit. All four mechanisms below are
about *ordering and timing*, not quantity.

**(a) `_sell_lead` — sell one step early (v55 line 631).** If the tape plans to
SELL item X at step+1, and `step % 4 != 0` (so no town consumption lands in
between), sell it now and suppress it next step:

```python
nxt = step + 1
unlock_period = 3 * cfg["turns_per_day"]
if nxt > LAST_ACT_STEP or nxt % unlock_period == 0 or step % 4 == 0:
    return
...
for item in PRODUCTS:
    if item in ("WHEAT", "FERTILIZER") or planned.get(item, 0) <= 0 or item in already:
        continue
    qty = min(projected.get(item, 0), planned[item])
```

Identical revenue against a static market, strictly better if the rival sells
the same good next step. WHEAT and FERTILIZER are excluded because those are the
goods they *buy*.

**(b) `_front_run` (v55 line 662)** — the same trick against a known opponent
tape, restricted to `FRONT_RUN_ITEMS = ("MILK","WOOL","STRAWBERRY","MELON")` —
exactly the four goods with the steepest glut curves (`above_target` 1.60 /
3.20 / 1.60 / 3.60). Bounded by their own planned quantity "so it never dumps".
Off in shipped v55.

**(c) `_v224_sales_first` (v55 line 1496)** — after step 144, bubble every SELL
toward the front of the list, past HIRE / BUY_LAND / BUY_SEED, stopping only at
another SELL or at a BUY of the same item:

```python
for index in range(len(orders)):
    order=orders[index]
    if order[0]!='SELL':continue
    cursor=index
    while cursor>0:
        previous=orders[cursor-1]
        if previous[0]=='SELL':break
        if previous[0] in ('BUY_PRODUCT','BUY_ANIMAL') and previous[1]==order[1]:break
        orders[cursor-1],orders[cursor]=orders[cursor],orders[cursor-1]
        cursor-=1
```

Get cash into the till before the rival's order at the same list index does.

**(d) `_r37_reorder_sales` / `_r37_quote_priority` (v55 lines 1801-1850)** — rank
a contiguous block of SELLs by *revenue at risk*, not headline revenue. They
re-implement the engine's `market_price` (`_r37_market_price`, line 1768) and
price the same sale now vs after a plausible rival batch, sizing the batch from
the rival's **visible ripe yield**:

```python
standing = sum(max(0, int(t.get('yield_units', 0))) for row in rival['tiles'] for t in row
               if isinstance(t, dict) and
               ((crop_item is not None and t.get('crop') == crop_item) or
                (animal is not None and t.get('animal') == animal)))
# Public fields do not reveal the rival shed. Eight units are a scenario,
# not a recovered hidden quantity; visible ripe yield increases the stress.
batch = min(24, max(8, standing))
now   = sum(_r37_market_price(item, inventory+j, params) for j in range(quantity))
later = sum(_r37_market_price(item, inventory+batch+j, params) for j in range(quantity))
return now-later
```

Sell first whatever the rival can most damage. This is the only place in any
published source where the opponent's *production* is modelled.

### C.5 The opening is a hard-coded market-microstructure trick

v55 line 987 overwrites step 0 of every one of the 41 routes:

```python
_R42_OPENING=[['BUY_PRODUCT', 'WHEAT', 13], ['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]
for _r42_tape in _ROUTES.values():
    _r42_tape[0]=dict(_r42_tape[0],market=[list(o) for o in _R42_OPENING])
```

and step 1 of route 0 reads:

```python
[['SELL','WHEAT',13], ['BUY_PRODUCT','WHEAT',5], ['HIRE'],['HIRE'],['HIRE'],['HIRE'],['HIRE'],
 ['BUY_ANIMAL','COW',2], ['BUY_ANIMAL','SHEEP',2]]
```

A wheat round-trip against the opponent's lockstep order, then **5 hands and 4
animals bought inside the first two turns of day 0.** `nathanjacob`'s entire
notebook is about tuning the round-trip quantity: 70 (V45's shipped default)
loses to every quantity from 5 to 65 because "market impact exceeds the profit";
75 gives 2W-48L and 80 gives 0W-50L. They price the fix at "~$250 per game" —
about 0.25% of a 100k score, but it flipped a 10-agent tournament to 179-1.

### C.6 Terminal behaviour

Step 718 of every tape is a blanket liquidation with absurd quantities, relying
on `_commit_unit` simply stopping at an empty shed:

```python
718 farmer ['PASS'] hands 11 market [['SELL','CARROT',1000], ['SELL','WOOL',1000], ['SELL','WHEAT',1000]]
```

Unsold inventory scores zero, so they dump regardless of price — and the engine
makes that nearly free: `PRICE_FLOOR = 1`, and "sales at $1 do not increase
market supply" (`_commit_unit`, engine line 657), so the tail of a dump cannot
even damage the book. `anhadmahajan06` describes a "64-rollout shadow tree
search" over turns 712-719 to walk every ripe unit into the shed first; v55
ships that as `_shadow_terminal` (line 1043), gated behind a shadow comparison
that must beat the parent's plan before it is accepted.

### C.7 The published architecture is the FIELD's, not the leaders'

Everything in C.1-C.6 is what the *notebooks* do. The notebooks' authors
(ahmedberatozer, aurax7, nathanjacob) are not at the top of this corpus. So the
architecture claim has to be tested against the leaders' own tapes, and it
fails for them.

**The test.** A precomputed tape is open-loop by construction: the same agent,
on a different seed, against a different opponent, must emit the *same main
farmer action at the same step* until a reactive layer intervenes. So for every
team with >= 3 tapes in the corpus, compare `actions[step]["farmer"]` pairwise
across that team's games and measure (a) the share of the 719 steps on which the
action is identical, and (b) the first step at which any pair disagrees.

| cohort | teams | farmer action identical across games | first divergence | hand-count identical |
|---|---|---|---|---|
| **ELITE** (team_score >= 3000) | 17 | **40.5%** | **step 40** | 93.5% |
| **FIELD** (team_score <= 2800) | 44 | **95.7%** | **step 258** | 67.5% |

The bottom of the top-200 is running a literal stored programme: 95.7% of its
main farmer's actions are byte-identical across games it has never seen, and the
first deviation does not arrive until step 258 (day 10). That is exactly the
`Chassis._route_action` architecture of section C.1, with `weed_repair` being
essentially the only thing that ever perturbs it.

The leaders are not. Per team, the top of the table:

| team | rating | games | farmer identical | first divergence |
|---|---|---|---|---|
| DSM | 3200.4 | 3 | 40.5% | step 12 |
| Majkel1337 | 3192.2 | 6 | 50.6% | step 15 |
| DSM | 3119.7 | 6 | 72.3% | step 27 |
| Unknown Mother-Goose | 3117.8 | 4 | 65.6% | step 130 |
| Vadim Vasilenko | 3100.0 | 3 | 37.1% | step 13 |
| SpaTaro | 3080.3 | 5 | 26.0% | step 5 |
| Sida Zuo | 3056.2 | 6 | 27.0% | step 43 |
| M & M & P & Q | 3031.4 | 3 | 24.8% | step 10 |

**What the rank-1 agent actually looks like.** DSM's three highest-rated tapes,
main farmer, steps 0-33 (`<-- DIFF` marks a step where the three games disagree):

```
  0 hands=[0,0,0] mkt=[0,0,0]  PASS / PASS / PASS
  1 hands=[0,0,0] mkt=[2,2,2]  PASS / PASS / PASS
  2 hands=[0,0,0] mkt=[7,7,7]  PICKUP COW 1  (x3)
  3 hands=[4,4,4] mkt=[1,1,1]  BUILD_PASTURE (x3)
  4 hands=[4,4,4] mkt=[2,2,2]  PLACE COW 1   (x3)
  5 hands=[4,4,4] mkt=[2,2,2]  PICKUP WHEAT 3(x3)
  6 hands=[4,4,4]              FEED          (x3)
  ...
 11 hands=[4,4,4]              CARE          (x3)
 12 hands=[4,4,4]              WEST / PASS / WEST        <-- DIFF
 13 hands=[4,4,4]              PASS / WEST / PASS        <-- DIFF
 14 hands=[4,4,4]              PLANT MELON   (x3)
 ...
 25 hands=[0,0,0] mkt=[8,8,8]  COLLECT_FERTILIZER (x3)
 26 hands=[3,4,3] mkt=[10,2,10] DROP         (x3)
 27 hands=[3,4,3]              NORTH / CARE / NORTH      <-- DIFF
 28 hands=[4,4,4] mkt=[0,1,0]  COLLECT_FERTILIZER / WEST / COLLECT_FERTILIZER  <-- DIFF
 29 hands=[4,4,4]              SOUTH / CARE / SOUTH      <-- DIFF
 30 hands=[4,4,4]              DROP / COLLECT_FERTILIZER / DROP                <-- DIFF
 31 hands=[4,4,4] mkt=[2,3,2]  PICKUP WHEAT 2 / EAST / PICKUP WHEAT 2          <-- DIFF
 32 hands=[4,4,4] mkt=[1,2,1]  NORTH / PLACE FERTILIZER 1 / NORTH              <-- DIFF
 33 hands=[4,4,4] mkt=[1,3,1]  FEED / PASS / FEED                              <-- DIFF
```

Read that carefully. Steps 0-11 are a **scripted opening**, identical to the
turn. Steps 12-13 are a one-turn reordering — a tie-break, not a plan change.
Steps 14-25 are scripted again. **From step 26 (day 1, hour 2) it is a different
agent in each game**: different jobs, a different number of hands hired
(3 vs 4 vs 3), and a wildly different number of market orders (10 vs 2 vs 10).

So the top of the ladder is:

- **scripted for the opening** (roughly day 0, where the state is known exactly
  and the moves are a solved sequence — note COW bought, pasture built, cow
  placed and fed all inside the first 6 turns), then
- **reactive from day 1 on**, with a *fixed labour schedule* (hand count agrees
  93.5% of the time across games, i.e. "hire N hands on day D" is still planned)
  but a **re-solved work assignment each turn**.

The FIELD has the opposite profile: the work assignment is frozen (95.7%
identical) and the hand count is what drifts (67.5% identical) — because a tape
that assumes 11 hands gets `hand_align`-truncated whenever a hire silently fails.

**This is the architectural gap.** The published notebooks describe a solved
problem: precompute the best route offline, pick it at step 144, defend it with
wrapper layers. It is worth ~2800. The teams above 3000 kept the precomputed
opening — where a tape is genuinely optimal — and replaced the other 29 days
with something that re-decides per turn against the actual board.

## D. THESIS — what separates a 3200 farm from a 2800 one

### D.0 The number that reframes everything

Across all 1,210 recorded ladder games:

| | |
|---|---|
| median final score | **98,494 coins** |
| median absolute winning margin | **1,356 coins (1.4% of the score)** |
| games decided by < 500 coins | 24.5% |
| games decided by < 1,000 coins | 40.7% |
| games decided by < 2,000 coins | **60.9%** |
| games decided by < 5,000 coins | 81.0% |

Median margin for the ELITE cohort's own games: **930 coins**. For the FIELD:
**48.5 coins**.

Nothing about this competition is won by out-farming the opponent. Both cohorts
harvest an identical 1,769 vs 1,768 units and convert them at an identical 18.4
vs 19.0 coins per worker-turn. **The whole ladder is a price-execution contest
decided by ~1.4% of the score.** Any single item below is, on its own, worth
more than a typical game's margin.

Caveat, stated plainly: the levers are measured independently against matched
cohorts, so they do **not** sum to the observed 4,430-coin cohort gap — the
FIELD wins some lines back (carrot, egg and melon `ppu`, and 7% more units
sold). Treat each row as "what this lever is worth where it is measured", not as
a decomposition.

### D.1 Ranked by apparent money value

**1. Sell premium goods in lots of ~4, not ~8. (+9,900 coins)**

The three high-base goods have the steepest glut curves in the game
(`above_target` WOOL 3.20 `sq`, MILK 1.60 `linear`, STRAWBERRY 1.60 `linear`).
**59 units of wool sold into an untouched market takes the price from 200 to 1.**
Measured lot sizes: ELITE mean **3.7** units per premium SELL order, p90 **6**;
FIELD mean **7.8**, p90 **12**. Realised price per unit:

| | ELITE ppu | FIELD ppu | edge | ELITE units | value |
|---|---|---|---|---|---|
| WOOL | 109.0 | 78.0 | +31.0 | 87 | +2,700 |
| MILK | 101.5 | 81.1 | +20.4 | 203 | +4,140 |
| STRAWBERRY | 144.7 | 131.2 | +13.5 | 228 | +3,080 |

The ELITE sell **7% fewer units in total and take more money for them.** Wool is
the cleanest case: same revenue (10,144 vs 10,130) from 87 units instead of 110.
The town restores this demand on a fixed 4-step clock (792 shop-ticks per
season, section B0), so the quota is a *rate*, not a stock — which is exactly why
the published `_sell_lead` layer refuses to fire when `step % 4 == 0`.

**2. Stop overbuying market wheat. (+5,600 coins)**

ELITE buy 183 units of market WHEAT for 6,668 coins (36.4/unit). FIELD buy 313
for 12,291 (39.3/unit) — more units *and* a worse price, because they are the
ones moving it. `nathanjacob__kaggriculture-pipe-7` independently found the same
cliff by brute force: the V45 opening's 70-unit wheat round-trip loses to every
quantity from 5 to 65, and quantity 80 scores 0 wins in 50 games. Day-0 orders
confirm it: ELITE buy 13.8 wheat and sell 68.8; FIELD buy 32.0 and sell 37.7.

**3. Fertilizer is a fixed, non-renewing, shared pot — and it is the only such good. (+5,000 coins)**

`FERTILIZER` appears in **no shop** and is excluded from `TOWN_CENTER_PRODUCTS`
(engine line 112: `[p for p in PRODUCTS if p != "FERTILIZER"]`). Its inventory
therefore only ever rises. Total extractable value **for both players combined**:

| units sold from a fresh market | cumulative coins | mean/unit | marginal unit |
|---|---|---|---|
| 100 | 9,010 | 90.1 | 80 |
| 200 | 16,020 | 80.1 | 60 |
| 300 | 21,030 | 70.1 | 40 |
| 400 | 24,040 | 60.1 | 20 |
| 500 | 25,052 | 50.1 | **1** |

**~25,000 coins, once, split between the two farms — whoever sells first.**
A 17-animal herd generates ~27 fertilizer per animal per season, so each side
alone can produce ~400 units: the pot is guaranteed to be exhausted.

ELITE behaviour: collect 373, **keep 173 for their own crops**, sell 217 at
58.1/unit, buy 14 from the market. FIELD behaviour: collect 368, sell **341** at
45.1/unit, fertilize only 117, and then **buy 91 back for 2,702 coins**. The
FIELD is selling into a floor and repurchasing.

The correct policy falls straight out of the arithmetic: sell fertilizer **early
and hard** while the price is near 100, and once the marginal price drops under
~70, stop selling and spend it on crops instead. Engine-verified per-tile
returns for fertilizing (charging fertilizer at 95/unit):

| crop | plain units | fertilized units | coins gained per fertilizer used |
|---|---|---|---|
| STRAWBERRY (in production window only) | 4 | 8 | **69** |
| CARROT (in window) | 21 | 28 | 35 |
| TOMATO (in window) | 4 | 8 | 30 |
| WHEAT | 24 | 36 | 25 |
| MELON | 12 | 12 | **0 — melon already caps without it** |

Two things fall out. (a) **Fertilizing melon is strictly wasted** — its 7-day
watering window already reaches `max_yield` unaided. (b) Fertilizer applied
*outside* a crop's scoring window does nothing at all, and a naive
"fertilize whenever it lapses" policy spends ~40% of its fertilizer during the
10 pre-yield growth days of a strawberry.

**4. Grow tomatoes. (+4,300 coins)**

ELITE harvest 59 tomatoes and sell them for 4,293 coins at **1.21x base**.
**The FIELD harvests zero** (102 tile-days of tomato vs 20). Tomato's glut curve
is `sqrt`/0.60 with 529 units of depth — a completely unexploited, deep market
that pays above base because the town drains it (PIZZA_SHOP and FARMERS_MARKET
both consume it). This is a whole revenue line the FIELD has not discovered.

**5. Stop passing. (+3,200 coins)**

PASS share of worker-turns: ELITE **3.6%** (418 turns), FIELD **7.1%** (504
turns). At the measured 37.3 coins per job-turn, the 86-turn difference plus the
ELITE's 411 extra turns is worth several thousand coins. Note also that
**44.3% of every worker-turn is spent walking** — and there are only 4 compass
moves, no diagonals, so crossing the board costs up to 18 turns. Walking is the
single largest line item in the game's labour budget and neither cohort has
attacked it.

**6. Buy the land earlier, and buy the fourth quadrant. (~2,000-4,000 coins)**

First BUY_LAND: both cohorts at step ~150 (day 6). Second: ELITE median
**step 218 (day 9)**, FIELD **step 266 (day 11)**. Third (the 4,000-coin SE
quadrant): ELITE buy it in **48% of games at day 9**; FIELD in **17% of games at
day 18**. The tile census shows the consequence — ELITE are at 75 owned tiles by
day 10, FIELD not until day 12, and ELITE hold 56 planted tiles on day 10
against the FIELD's 32.

**7. Melon and fertilizer are races, not crops — and melon is the best crop per worker-turn.**

Engine-verified, one tile worked for a whole season with replanting:

| crop | units/season | worker-turns | coins/turn at base | coins/turn at the ELITE's realised price |
|---|---|---|---|---|
| **MELON** | 12 | 30 | **94.7** | **75.8** |
| CARROT | 21 | 42 | 14.2 | 18.6 |
| WHEAT | 24 | 42 | 12.9 | 19.6 |
| STRAWBERRY | 4 | 35 | 10.9 | 13.1 |
| TOMATO | 4 | 35 | 5.4 | 6.6 |

Melon is 4-6x the next best crop per worker-turn. But **no shop sells melon**
(check `SHOPS` — it appears in none of the eight), so its only demand is the
town centre's 30 units for the whole season. Both cohorts realise a melon `ppu`
of **189.5 / 198.2 against a base of 250**, because the two of them together
push ~144 units into a market with 30 units of demand and ~158 units of depth.

That makes melon — like fertilizer — a **fixed pot worth ~26,500 coins split
between the two farms**, where the marginal 144th unit is worth 43 coins and the
first 36 are worth 246 each. The implication is not "plant more melon"; the pair
is already near saturation and the marginal melon is only breaking even on
labour. The implication is **sell melon (and fertilizer) earlier than the
opponent does**, because on these two goods every coin the opponent takes is a
coin that no longer exists. This is the only place in the game where a
front-running layer has a real, quantified prize — which is presumably why the
published `_front_run` restricts itself to `("MILK","WOOL","STRAWBERRY","MELON")`.

**8. The architecture itself: be reactive after day 0. (the 2800 -> 3000 step)**

Measured over every team with >= 3 tapes (section C.7): the FIELD's main farmer
emits the **identical action at the identical step in 95.7%** of steps across
different seeds and opponents, first diverging at **step 258**. That is a
literal stored programme — the `Chassis._route_action(route, step)` architecture
of the published notebooks, whose only strategic decision is a table lookup on
`town.unlocked_shops[:2]` at step 144.

The ELITE are at **40.5% identical, first diverging at step 40**. The rank-1
agent (DSM, 3200.4) is byte-identical for steps 0-11, identical again for 14-25,
and **completely different in every game from step 26 onward** — different jobs,
different hire counts (3 vs 4), different market volumes (10 orders vs 2).

The pattern is: **keep the solved opening (day 0 is a known-state puzzle worth
scripting — cow bought, pasture built, animal placed and fed inside 6 turns),
and re-decide everything after it.** Note what stays planned even at the top:
hand count agrees 93.5% across ELITE games. The *labour schedule* is still a
plan; the *work assignment* is not.

**9. Nobody hires the 12th hand, and the maths says they should.**

Both cohorts cap at exactly 11 hands from day 10 onward, while sitting on 7,600+
coins. The 12th hand costs 144/day = **4,320 for the season** and buys **24 more
worker-turns per day = 720 for the season — 6.0 coins per extra worker-turn**,
against a measured **37.3 coins per job-turn** and 18.4 per raw worker-turn. The
13th hand works out at 7.9 coins/turn. Land is not the limit either: the ELITE
median game leaves 1-3 tiles bare mid-season and **22 bare on day 28**. This is
the clearest unexploited lever in the whole dataset, and the reason it is
unexploited is architectural — a precomputed tape cannot add a worker it did not
plan for.

**10. Order slots are free; stop treating them as scarce.**

`maxMarketOrdersPerTurn = 10`, but the measured mean is **1.50 orders/turn for
ELITE and 1.38 for FIELD**; only 3% of turns reach the cap and **zero** orders
per game are discarded past it. One ELITE team (SpaTaro, 3080) burns **1,364
slots per game** on `BUY_PRODUCT` orders for items the engine refuses to quote
(only WHEAT and FERTILIZER are buyable) and still rates 3080 — which is the
proof that the order budget does not bind. There is ample room to split every
premium sale into more, smaller orders (lever 1) at zero cost.

### D.2 The one-sentence version

Both cohorts grow the same food with the same efficiency; the ELITE take ~4,400
more coins almost entirely by **selling the thin-market goods (wool, milk,
strawberry) in half-size lots, not overpaying for market wheat, and not dumping
a fertilizer stock that has no buyer** — and they can do it because from day 1
they re-decide each turn instead of replaying a tape, while the largest lever
either side is still ignoring is simply **hiring a 12th hand at 6 coins per
worker-turn in a game where a worker-turn earns 37**.
