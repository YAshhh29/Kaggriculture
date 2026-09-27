# Inspection of Candidate G -- 2026-09-16 00:48

- G source `d77ff39bcc94` at commit `22f382c`, overrides `{'SETTINGS': {'hire_reserve': 15, 'hire_reserve_until_day': 1}}`, label `H hire reserve 15 days 0-1 v14 field`
- 83 games against 12 opponents; match snapshot newest game 2026-09-15T12:47 (6h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 116,268, opponent 83,722, margin +32,546, wins 78/83

29 games had an opponent replay refusing over 2% of its moves; on the other 54 G wins 49 with margin +17,501

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 4 | 1 | +1,096 | 1.5% |
| Zhenghongshuang | 8 | 6 | +11,243 | 0.6% |
| Cow Boy | 8 | 8 | +12,531 | 0.6% |
| Artem The Farmer 🍅 | 3 | 3 | +12,609 | 1.2% |
| ymg_aq | 8 | 8 | +15,130 | 0.4% |
| Otter Vibe | 8 | 8 | +23,843 | 0.4% |
| HowardLeeTW | 8 | 8 | +25,736 | 0.4% |
| Mengfei Li | 8 | 8 | +28,439 | 3.1% |
| SpaTaro | 8 | 8 | +38,786 | 2.6% |
| DSM | 4 | 4 | +41,782 | 8.4% |
| Orbital Terraformer | 8 | 8 | +54,389 | 6.7% |
| Majkel1337 | 8 | 8 | +101,405 | 10.7% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | loss (estimate) | early_harvest | 5,009 | opponent 4,373/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 60 at [0, 1] (WHEAT age2 y2 W) | harvest gate in job_value and HARVEST_HOLD |
| 2 | revenue gap | WHEAT | 3,707 | G sells 401 at 38, opponent 503 at 38; town takes 585 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | revenue gap | TOMATO | 1,957 | G sells 8 at 153, opponent 43 at 73; town takes 223 | crop and herd choice: CROP_TILES, herd_plan() |
| 4 | sell timing | STRAWBERRY | 1,550 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 5 | sell timing | MILK | 1,128 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 6 | sell timing | WOOL | 849 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 7 | revenue gap | CARROT | 533 | G sells 92 at 43, opponent 115 at 39; town takes 248 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | loss | fertilizer_uncollected | 324 | opponent 284/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 383 at [2, 3] (GOOSE y0 fed cared manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 9 | loss (estimate) | care_missed | 315 | opponent 1,135/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 359 at [4, 1] (GOOSE y0 fed) | CARE jobs (BAND_SERVICE) |
| 10 | loss | overflow | 313 | opponent 427/game, hit in 59/83 games; e.g. tape live_108910285 seat 0 seed 11 step 623 | DROP timing and shed selling in market_orders() |
| 11 | loss | capped_yield | 217 | opponent 157/game, hit in 74/83 games; e.g. tape live_108910285 seat 0 seed 11 step 479 at [2, 3] (GOOSE y4 fed cared) | animal HARVEST jobs (HARVEST_AT, BAND_HARVEST) |
| 12 | loss | died_unwatered | 157 | opponent 308/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 383 at [9, 0] (WHEAT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 13 | sell timing | WHEAT | 99 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 14 | sell timing | TOMATO | 61 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | sell timing | FERTILIZER | 53 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | sell timing | EGG | 25 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 17 | sell timing | CARROT | 7 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  49.9% |  42.3% |   7.1% |   0.7% |   0.0% |
| OPP |  43.3% |  43.3% |  10.5% |   3.0% |   0.0% |

G's moves the engine ignored:

- 12.2/game (0.18% of turns) **CARE: already cared for** -- e.g. tape live_108910285 seat 0 seed 11 step 91 worker 0 on COW y0 cared
- 10.5/game (0.15% of turns) **WATER: already watered today** -- e.g. tape live_108910285 seat 0 seed 11 step 132 worker 4 on MELON age5 y1 W
- 8.3/game (0.12% of turns) **COLLECT_FERTILIZER: none ready** -- e.g. tape live_108910285 seat 0 seed 11 step 107 worker 0 on SHEEP y0 fed cared
- 4.0/game (0.06% of turns) **HARVEST: nothing ready** -- e.g. tape live_108910285 seat 0 seed 11 step 367 worker 10 on COW y0 manure
- 3.6/game (0.05% of turns) **WATER: nothing to water** -- e.g. tape live_108931878 seat 0 seed 11 step 19 worker 1 on empty
- 2.7/game (0.04% of turns) **DIG: tile already empty** -- e.g. tape live_108910285 seat 0 seed 11 step 186 worker 1 on empty
- 1.8/game (0.03% of turns) **HARVEST: nothing here** -- e.g. tape live_108910285 seat 0 seed 11 step 708 worker 4 on empty
- 1.0/game (0.01% of turns) **PLACE: no MILK in hand or shed full** -- e.g. tape live_108910285 seat 0 seed 11 step 258 worker 0 on COW y0 fed cared
- 0.6/game (0.01% of turns) **FERTILIZE: no fertilizer in hand** -- e.g. tape live_108910285 seat 0 seed 11 step 517 worker 5 on STRAWBERRY age13 y0
- 0.3/game (0.00% of turns) **CARE: no animal here** -- e.g. tape live_108903709 seat 0 seed 17 step 70 worker 0 on empty
- 0.3/game (0.00% of turns) **COLLECT_FERTILIZER: no animal here** -- e.g. tape live_108903709 seat 0 seed 17 step 85 worker 0 on empty
- 0.3/game (0.00% of turns) **PLANT: more PLANT MELON this turn than seeds, all cancelled** -- e.g. tape live_108931878 seat 0 seed 11 step 18 worker 1 on empty
- 0.3/game (0.00% of turns) **PLANT: more PLANT WHEAT this turn than seeds, all cancelled** -- e.g. tape live_108944058 seat 0 seed 11 step 20 worker 4 on empty
- 0.3/game (0.00% of turns) **FEED: no animal here** -- e.g. tape live_108903709 seat 0 seed 17 step 83 worker 0 on empty
- 0.1/game (0.00% of turns) **PLACE: no MELON in hand or shed full** -- e.g. tape live_108931878 seat 0 seed 11 step 251 worker 1 on COW y3 fed cared

## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 2.1 | 157 | 2.4 | 308 | 83 |
| rotted | 0.0 | 0 | 5.9 | 320 | 0 |
| early_harvest | 134.3 | 5,009 | 113.8 | 4,373 | 83 |
| escaped | 0.0 | 0 | 3.9 | 1,998 | 0 |
| care_missed | 2.8 | 315 | 10.7 | 1,135 | 83 |
| fertilizer_uncollected | 15.3 | 324 | 11.6 | 284 | 83 |
| capped_yield | 4.0 | 217 | 1.4 | 157 | 74 |
| overflow | 4.9 | 313 | 6.1 | 427 | 59 |
| stranded | 0.0 | 0 | 0.7 | 28 | 0 |

Ground, tile-days per game (G / opp): crop 1281/1189, animal 396/329, empty 83/138, weed 1/10, empty_pen 19/29, unwatered 386/326, unfed 64/58

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 585 | 401 | 503 | 38 | 38 | 0.0 | 15,333 | 19,041 | 2.0 |
| TOMATO | 223 | 8 | 43 | 153 | 73 | 0.0 | 1,216 | 3,173 | 7.5 |
| CARROT | 248 | 92 | 115 | 43 | 39 | 0.0 | 3,969 | 4,501 | 5.7 |
| EGG | 245 | 74 | 69 | 55 | 51 | 0.0 | 4,096 | 3,522 | 0.1 |
| MELON | 30 | 70 | 71 | 220 | 181 | 0.0 | 15,475 | 12,797 | 0.0 |
| FERTILIZER | 0 | 343 | 229 | 49 | 52 | 3.6 | 16,934 | 11,884 | 0.0 |
| WOOL | 147 | 132 | 119 | 120 | 81 | 31.1 | 15,907 | 9,584 | 0.0 |
| STRAWBERRY | 417 | 249 | 197 | 129 | 125 | 27.9 | 32,086 | 24,619 | 9.8 |
| MILK | 403 | 235 | 163 | 164 | 149 | 11.5 | 38,404 | 24,321 | 4.0 |

Units sold on the same turn as the other farm sold the same good: G 485, opponent 478 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 3,272 | 2,940 |
| animal GOOSE | 802 | 669 |
| animal SHEEP | 3,066 | 3,048 |
| buy FERTILIZER | 2,950 | 1,319 |
| buy WHEAT | 5,387 | 9,684 |
| hire | 4,696 | 5,719 |
| land | 3,434 | 2,699 |
| seed CARROT | 620 | 865 |
| seed MELON | 945 | 990 |
| seed STRAWBERRY | 3,300 | 2,898 |
| seed TOMATO | 54 | 329 |
| seed WHEAT | 1,627 | 1,562 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 201 | 194 | -7 |
| 5 | 798 | 627 | -171 |
| 8 | 1,541 | 1,286 | -255 |
| 11 | 15,992 | 11,058 | -4,934 |
| 14 | 25,890 | 19,692 | -6,198 |
| 17 | 44,081 | 33,809 | -10,272 |
| 20 | 61,910 | 50,185 | -11,725 |
| 23 | 80,102 | 61,615 | -18,487 |
| 26 | 90,463 | 70,025 | -20,438 |

## Since the last inspection (2026-09-16 00:36, H package v14 field)

- margin +30,053 -> +32,546, wins 71/83 -> 78/83, G 115,545 -> 116,268
- paired on 54 games where the opponent replay stayed in step in both runs: margin +3,833 per game (median +0), better in 8, worse in 0
- paired on 83 identical games: margin +2,494 per game, better in 8, worse in 0; G's own score better in 6
- G idle share 7.1% -> 7.1%
- G noop share 1.3% -> 0.7%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
