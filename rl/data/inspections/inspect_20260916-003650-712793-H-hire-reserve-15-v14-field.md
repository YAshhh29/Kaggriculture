# Inspection of Candidate G -- 2026-09-16 00:36

- G source `d77ff39bcc94` at commit `22f382c`, overrides `{'SETTINGS': {'hire_reserve': 15}}`, label `H hire reserve 15 v14 field`
- 83 games against 12 opponents; match snapshot newest game 2026-09-15T12:47 (6h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 116,261, opponent 83,788, margin +32,474, wins 78/83

29 games had an opponent replay refusing over 2% of its moves; on the other 54 G wins 49 with margin +17,430

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 4 | 1 | +1,052 | 1.5% |
| Zhenghongshuang | 8 | 6 | +11,190 | 0.6% |
| Cow Boy | 8 | 8 | +12,365 | 0.6% |
| Artem The Farmer 🍅 | 3 | 3 | +12,548 | 1.2% |
| ymg_aq | 8 | 8 | +15,063 | 0.4% |
| Otter Vibe | 8 | 8 | +23,795 | 0.4% |
| HowardLeeTW | 8 | 8 | +25,660 | 0.4% |
| Mengfei Li | 8 | 8 | +28,414 | 3.1% |
| SpaTaro | 8 | 8 | +38,722 | 2.6% |
| DSM | 4 | 4 | +41,720 | 8.4% |
| Orbital Terraformer | 8 | 8 | +54,352 | 6.7% |
| Majkel1337 | 8 | 8 | +101,260 | 10.7% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | loss (estimate) | early_harvest | 4,956 | opponent 4,380/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 60 at [0, 1] (WHEAT age2 y2 W) | harvest gate in job_value and HARVEST_HOLD |
| 2 | revenue gap | WHEAT | 3,705 | G sells 401 at 38, opponent 504 at 38; town takes 585 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | revenue gap | TOMATO | 1,957 | G sells 8 at 153, opponent 43 at 73; town takes 223 | crop and herd choice: CROP_TILES, herd_plan() |
| 4 | sell timing | STRAWBERRY | 1,549 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 5 | sell timing | MILK | 1,128 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 6 | sell timing | WOOL | 843 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 7 | revenue gap | CARROT | 533 | G sells 92 at 43, opponent 115 at 39; town takes 248 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | loss | fertilizer_uncollected | 325 | opponent 285/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 383 at [2, 3] (GOOSE y0 fed cared manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 9 | loss | overflow | 315 | opponent 428/game, hit in 59/83 games; e.g. tape live_108910285 seat 0 seed 11 step 623 | DROP timing and shed selling in market_orders() |
| 10 | loss (estimate) | care_missed | 314 | opponent 1,135/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 359 at [4, 1] (GOOSE y0 fed) | CARE jobs (BAND_SERVICE) |
| 11 | loss | capped_yield | 217 | opponent 157/game, hit in 74/83 games; e.g. tape live_108910285 seat 0 seed 11 step 479 at [2, 3] (GOOSE y4 fed cared) | animal HARVEST jobs (HARVEST_AT, BAND_HARVEST) |
| 12 | loss | died_unwatered | 157 | opponent 309/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 383 at [9, 0] (WHEAT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 13 | sell timing | WHEAT | 99 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 14 | sell timing | TOMATO | 61 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | sell timing | FERTILIZER | 54 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | sell timing | EGG | 25 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 17 | sell timing | CARROT | 7 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  49.9% |  42.3% |   7.1% |   0.8% |   0.0% |
| OPP |  43.3% |  43.3% |  10.5% |   3.0% |   0.0% |

G's moves the engine ignored:

- 12.2/game (0.18% of turns) **CARE: already cared for** -- e.g. tape live_108910285 seat 0 seed 11 step 91 worker 0 on COW y0 cared
- 10.5/game (0.15% of turns) **WATER: already watered today** -- e.g. tape live_108910285 seat 0 seed 11 step 132 worker 4 on MELON age5 y1 W
- 8.3/game (0.12% of turns) **COLLECT_FERTILIZER: none ready** -- e.g. tape live_108910285 seat 0 seed 11 step 107 worker 0 on SHEEP y0 fed cared
- 6.6/game (0.10% of turns) **WATER: nothing to water** -- e.g. tape live_108910285 seat 0 seed 11 step 67 worker 4 on empty
- 4.1/game (0.06% of turns) **HARVEST: nothing ready** -- e.g. tape live_108910285 seat 0 seed 11 step 367 worker 10 on COW y0 manure
- 2.8/game (0.04% of turns) **HARVEST: nothing here** -- e.g. tape live_108910285 seat 0 seed 11 step 110 worker 4 on empty
- 2.7/game (0.04% of turns) **DIG: tile already empty** -- e.g. tape live_108910285 seat 0 seed 11 step 186 worker 1 on empty
- 1.3/game (0.02% of turns) **PLANT: more PLANT WHEAT this turn than seeds, all cancelled** -- e.g. tape live_108910285 seat 0 seed 11 step 66 worker 4 on empty
- 1.0/game (0.01% of turns) **PLACE: no MILK in hand or shed full** -- e.g. tape live_108910285 seat 0 seed 11 step 258 worker 0 on COW y0 fed cared
- 0.6/game (0.01% of turns) **FERTILIZE: no fertilizer in hand** -- e.g. tape live_108910285 seat 0 seed 11 step 517 worker 5 on STRAWBERRY age13 y0
- 0.6/game (0.01% of turns) **CARE: no animal here** -- e.g. tape live_108903709 seat 0 seed 17 step 70 worker 0 on empty
- 0.6/game (0.01% of turns) **COLLECT_FERTILIZER: no animal here** -- e.g. tape live_108903709 seat 0 seed 17 step 85 worker 0 on empty
- 0.5/game (0.01% of turns) **FEED: no animal here** -- e.g. tape live_108903709 seat 0 seed 17 step 83 worker 0 on empty
- 0.3/game (0.00% of turns) **PLANT: more PLANT MELON this turn than seeds, all cancelled** -- e.g. tape live_108931878 seat 0 seed 11 step 18 worker 1 on empty
- 0.1/game (0.00% of turns) **PLACE: no MELON in hand or shed full** -- e.g. tape live_108931878 seat 0 seed 11 step 251 worker 1 on COW y3 fed cared

## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 2.1 | 157 | 2.4 | 309 | 83 |
| rotted | 0.0 | 0 | 5.9 | 320 | 0 |
| early_harvest | 132.3 | 4,956 | 113.9 | 4,380 | 83 |
| escaped | 0.0 | 0 | 3.9 | 1,998 | 0 |
| care_missed | 2.7 | 314 | 10.7 | 1,135 | 83 |
| fertilizer_uncollected | 15.3 | 325 | 11.6 | 285 | 83 |
| capped_yield | 4.0 | 217 | 1.4 | 157 | 74 |
| overflow | 4.9 | 315 | 6.1 | 428 | 59 |
| stranded | 0.0 | 0 | 0.7 | 28 | 0 |

Ground, tile-days per game (G / opp): crop 1279/1189, animal 395/329, empty 85/138, weed 1/10, empty_pen 19/29, unwatered 386/326, unfed 64/58

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 585 | 401 | 504 | 38 | 38 | 0.0 | 15,373 | 19,078 | 2.0 |
| TOMATO | 223 | 8 | 43 | 153 | 73 | 0.0 | 1,216 | 3,173 | 7.5 |
| CARROT | 248 | 92 | 115 | 43 | 39 | 0.0 | 3,968 | 4,501 | 5.7 |
| EGG | 245 | 74 | 69 | 55 | 51 | 0.0 | 4,096 | 3,522 | 0.1 |
| MELON | 30 | 70 | 71 | 220 | 181 | 0.0 | 15,475 | 12,797 | 0.0 |
| FERTILIZER | 0 | 343 | 229 | 49 | 52 | 3.5 | 16,932 | 11,890 | 0.0 |
| WOOL | 147 | 132 | 119 | 121 | 81 | 30.8 | 15,935 | 9,624 | 0.0 |
| STRAWBERRY | 417 | 249 | 197 | 129 | 125 | 27.9 | 32,081 | 24,618 | 9.8 |
| MILK | 403 | 235 | 163 | 164 | 149 | 11.4 | 38,404 | 24,323 | 4.0 |

Units sold on the same turn as the other farm sold the same good: G 485, opponent 478 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 3,277 | 2,935 |
| animal GOOSE | 802 | 669 |
| animal SHEEP | 3,060 | 3,048 |
| buy FERTILIZER | 2,955 | 1,321 |
| buy WHEAT | 5,459 | 9,705 |
| hire | 4,696 | 5,719 |
| land | 3,434 | 2,699 |
| seed CARROT | 620 | 865 |
| seed MELON | 945 | 990 |
| seed STRAWBERRY | 3,300 | 2,898 |
| seed TOMATO | 54 | 329 |
| seed WHEAT | 1,617 | 1,562 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 211 | 194 | -17 |
| 5 | 807 | 627 | -180 |
| 8 | 1,479 | 1,283 | -196 |
| 11 | 15,928 | 11,059 | -4,869 |
| 14 | 25,830 | 19,695 | -6,135 |
| 17 | 44,026 | 33,801 | -10,225 |
| 20 | 61,849 | 50,176 | -11,673 |
| 23 | 80,041 | 61,610 | -18,431 |
| 26 | 90,415 | 70,071 | -20,344 |

## Since the last inspection (2026-09-16 00:36, H package v14 field)

- margin +30,053 -> +32,474, wins 71/83 -> 78/83, G 115,545 -> 116,261
- paired on 54 games where the opponent replay stayed in step in both runs: margin +3,762 per game (median -49), better in 9, worse in 45
- paired on 83 identical games: margin +2,421 per game, better in 10, worse in 73; G's own score better in 9
- G idle share 7.1% -> 7.1%
- G noop share 1.3% -> 0.8%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
