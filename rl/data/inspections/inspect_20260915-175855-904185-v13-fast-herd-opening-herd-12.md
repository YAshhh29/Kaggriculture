# Inspection of Candidate G -- 2026-09-15 17:58

- G source `7cfdc7a6fdb1` at commit `cf4b692`, overrides `{'PEN_ORDER': ['PASTURE', 'COOP'], 'BIRDS_PER_TURN': 3, 'COOP_LEAD': 4, 'GOOSE_CASH_FLOOR': 150, 'HERD_TARGET': 12}`, label `v13 fast herd opening herd 12`
- 83 games against 12 opponents; match snapshot newest game 2026-09-15T11:39 (1h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 83,501, opponent 111,944, margin -28,443, wins 14/83

22 games had an opponent replay refusing over 2% of its moves; on the other 61 G wins 3 with margin -38,118

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 4 | 0 | -49,833 | 1.5% |
| Zhenghongshuang | 8 | 0 | -48,033 | 0.6% |
| Cow Boy | 8 | 1 | -45,604 | 0.6% |
| Mengfei Li | 8 | 0 | -39,644 | 1.5% |
| Artem The Farmer 🍅 | 3 | 0 | -37,399 | 0.6% |
| Otter Vibe | 8 | 0 | -36,559 | 0.2% |
| ymg_aq | 8 | 0 | -32,005 | 0.3% |
| DSM | 4 | 0 | -30,284 | 2.7% |
| HowardLeeTW | 8 | 1 | -27,139 | 0.1% |
| Majkel1337 | 8 | 3 | -16,694 | 3.1% |
| Orbital Terraformer | 8 | 5 | -3,138 | 5.3% |
| SpaTaro | 8 | 4 | +7,800 | 4.4% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 17,231 | G sells 96 at 40, opponent 519 at 41; town takes 585 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 13,534 | G sells 134 at 167, opponent 215 at 167; town takes 417 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 7,265 | opponent 4,837/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | MELON | 5,073 | G sells 67 at 177, opponent 73 at 233; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | TOMATO | 3,397 | G sells 0 at 0, opponent 45 at 75; town takes 223 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | CARROT | 2,417 | G sells 49 at 41, opponent 114 at 39; town takes 248 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | loss (estimate) | care_missed | 1,977 | opponent 1,374/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 287 at [7, 1] (GOOSE y0 fed) | CARE jobs (BAND_SERVICE) |
| 8 | revenue gap | FERTILIZER | 1,494 | G sells 245 at 50, opponent 239 at 57; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | sell timing | MILK | 1,313 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 10 | sell timing | STRAWBERRY | 996 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | loss | escaped | 964 | opponent 2,098/game, hit in 59/83 games; e.g. tape live_108884658 seat 1 seed 12 step 311 at [0, 7] (GOOSE y0) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 12 | loss | died_unwatered | 851 | opponent 141/game, hit in 75/83 games; e.g. tape live_108910285 seat 0 seed 11 step 287 at [9, 0] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 13 | loss | overflow | 800 | opponent 757/game, hit in 54/83 games; e.g. tape live_108910285 seat 0 seed 11 step 527 | DROP timing and shed selling in market_orders() |
| 14 | sell timing | WOOL | 591 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | loss | fertilizer_uncollected | 287 | opponent 335/game, hit in 74/83 games; e.g. tape live_108910285 seat 0 seed 11 step 359 at [6, 1] (COW y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 16 | revenue gap | WOOL | 68 | G sells 95 at 125, opponent 127 at 94; town takes 147 | crop and herd choice: CROP_TILES, herd_plan() |
| 17 | sell timing | WHEAT | 51 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 18 | sell timing | EGG | 46 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | sell timing | CARROT | 39 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | loss | rotted | 35 | opponent 334/game, hit in 20/83 games; e.g. tape live_109133305 seat 0 seed 11 step 672 at [9, 2] (CARROT age4 y2) | harvest timing: HARVEST_HOLD and BAND_HARVEST |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  39.1% |  48.2% |  12.8% |   0.0% |   0.0% |
| OPP |  45.8% |  43.3% |   9.2% |   1.8% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 8.2 | 851 | 1.7 | 141 | 75 |
| rotted | 0.7 | 35 | 5.9 | 334 | 20 |
| early_harvest | 185.4 | 7,265 | 122.2 | 4,837 | 83 |
| escaped | 2.2 | 964 | 4.0 | 2,098 | 59 |
| care_missed | 14.5 | 1,977 | 10.9 | 1,374 | 83 |
| fertilizer_uncollected | 9.0 | 287 | 11.7 | 335 | 74 |
| capped_yield | 0.0 | 0 | 1.5 | 180 | 0 |
| overflow | 9.0 | 800 | 9.6 | 757 | 54 |
| stranded | 0.7 | 27 | 0.7 | 33 | 35 |

Ground, tile-days per game (G / opp): crop 955/1250, animal 362/352, empty 147/114, weed 5/10, empty_pen 148/21, unwatered 22/336, unfed 24/59

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 585 | 96 | 519 | 40 | 41 | 0.0 | 3,817 | 21,048 | 16.1 |
| STRAWBERRY | 417 | 134 | 215 | 167 | 167 | 7.0 | 22,393 | 35,927 | 11.9 |
| MELON | 30 | 67 | 73 | 177 | 233 | 0.1 | 11,920 | 16,993 | 0.0 |
| TOMATO | 223 | 0 | 45 | 0 | 75 | 0.0 | 0 | 3,397 | 7.9 |
| CARROT | 248 | 49 | 114 | 41 | 39 | 0.0 | 2,032 | 4,449 | 2.5 |
| FERTILIZER | 0 | 245 | 239 | 50 | 57 | 5.3 | 12,206 | 13,700 | 0.0 |
| WOOL | 147 | 95 | 127 | 125 | 94 | 23.5 | 11,882 | 11,950 | 0.1 |
| EGG | 245 | 109 | 75 | 54 | 50 | 0.0 | 5,879 | 3,728 | 0.0 |
| MILK | 403 | 212 | 180 | 180 | 175 | 14.0 | 38,078 | 31,388 | 6.7 |

Units sold on the same turn as the other farm sold the same good: G 237, opponent 237 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 4,299 | 3,027 |
| animal GOOSE | 1,388 | 680 |
| animal SHEEP | 2,548 | 3,120 |
| buy FERTILIZER | 0 | 1,521 |
| buy WHEAT | 4,090 | 9,899 |
| hire | 6,820 | 5,742 |
| land | 2,687 | 2,855 |
| seed CARROT | 595 | 865 |
| seed MELON | 1,144 | 1,001 |
| seed STRAWBERRY | 3,049 | 3,029 |
| seed TOMATO | 0 | 330 |
| seed WHEAT | 1,086 | 1,566 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 35 | 208 | +173 |
| 5 | 252 | 740 | +488 |
| 8 | 1,851 | 1,765 | -86 |
| 11 | 3,135 | 12,961 | +9,826 |
| 14 | 6,606 | 23,827 | +17,221 |
| 17 | 15,125 | 41,931 | +26,806 |
| 20 | 30,110 | 63,294 | +33,184 |
| 23 | 45,039 | 82,441 | +37,402 |
| 26 | 58,874 | 94,287 | +35,413 |

## Since the last inspection (2026-09-15 17:24, v13 baseline)

- margin -24,356 -> -28,443, wins 12/83 -> 14/83, G 89,332 -> 83,501
- paired on 60 games where the opponent replay stayed in step in both runs: margin -5,373 per game (median -660), better in 26, worse in 34
- paired on 83 identical games: margin -4,087 per game, better in 35, worse in 48; G's own score better in 27
- early_harvest: 6,838 -> 7,265 coins/game
- escaped: 453 -> 964 coins/game
- care_missed: 1,636 -> 1,977 coins/game
- fertilizer_uncollected: 190 -> 287 coins/game
- overflow: 517 -> 800 coins/game
- G idle share 9.5% -> 12.8%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
