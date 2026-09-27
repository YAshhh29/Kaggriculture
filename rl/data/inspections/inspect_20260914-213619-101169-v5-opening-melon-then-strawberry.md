# Inspection of Candidate G -- 2026-09-14 21:36

- G source `14cce7cc9842` at commit `8be59c2`, overrides `{'OPENING_CROP_TILES': [['MELON', 8], ['STRAWBERRY', 32]]}`, label `v5 opening melon then strawberry`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T15:02 (1h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 77,402, opponent 119,041, margin -41,639, wins 6/96

28 games had an opponent replay refusing over 2% of its moves; on the other 68 G wins 0 with margin -50,827

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -61,499 | 1.4% |
| redblackbst | 8 | 0 | -59,576 | 0.7% |
| Unknown Mother-Goose | 8 | 0 | -55,961 | 0.2% |
| feel the agi | 8 | 0 | -52,725 | 0.8% |
| Mengfei Li | 8 | 0 | -51,595 | 1.2% |
| Otter Vibe | 8 | 0 | -42,508 | 0.0% |
| ymg_aq | 8 | 1 | -40,563 | 1.4% |
| HowardLeeTW | 8 | 0 | -38,926 | 0.4% |
| Majkel1337 | 8 | 1 | -33,063 | 2.9% |
| DSM | 8 | 0 | -32,052 | 2.7% |
| Orbital Terraformer | 8 | 1 | -24,069 | 4.3% |
| SpaTaro | 8 | 3 | -7,131 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | STRAWBERRY | 15,645 | G sells 110 at 173, opponent 209 at 166; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | loss (estimate) | early_harvest | 13,947 | opponent 5,122/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 3 | revenue gap | WOOL | 6,706 | G sells 54 at 173, opponent 131 at 123; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 4 | revenue gap | FERTILIZER | 6,522 | G sells 154 at 58, opponent 230 at 67; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | MELON | 3,967 | G sells 64 at 191, opponent 74 at 219; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | TOMATO | 3,951 | G sells 0 at 0, opponent 51 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | loss | overflow | 3,732 | opponent 1,006/game, hit in 94/96 games; e.g. tape live_108910285 seat 0 seed 11 step 527 | DROP timing and shed selling in market_orders() |
| 8 | revenue gap | WHEAT | 3,721 | G sells 458 at 39, opponent 548 at 39; town takes 588 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | revenue gap | CARROT | 3,393 | G sells 32 at 43, opponent 123 at 39; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 10 | loss | stranded | 2,863 | opponent 39/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 11 | sell timing | MILK | 1,057 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | loss (estimate) | care_missed | 804 | opponent 2,126/game, hit in 94/96 games; e.g. tape live_108910285 seat 0 seed 11 step 311 at [2, 1] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 13 | sell timing | STRAWBERRY | 722 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 14 | sell timing | WHEAT | 514 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | loss | died_unwatered | 433 | opponent 176/game, hit in 90/96 games; e.g. tape live_108910285 seat 0 seed 11 step 311 at [9, 1] (STRAWBERRY age0 y0) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 16 | sell timing | WOOL | 264 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 17 | loss | fertilizer_uncollected | 61 | opponent 630/game, hit in 46/96 games; e.g. tape live_108694097 seat 1 seed 14 step 527 at [0, 4] (COW y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 18 | sell timing | EGG | 42 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | sell timing | CARROT | 22 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | loss | escaped | 17 | opponent 2,590/game, hit in 3/96 games; e.g. tape live_108848381 seat 1 seed 16 step 695 at [0, 3] (COW y0) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  39.9% |  46.1% |  14.0% |   0.0% |   0.0% |
| OPP |  46.4% |  43.2% |   8.7% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 4.5 | 433 | 2.3 | 176 | 90 |
| rotted | 0.0 | 2 | 6.3 | 383 | 2 |
| early_harvest | 364.1 | 13,947 | 131.9 | 5,122 | 96 |
| escaped | 0.0 | 17 | 5.1 | 2,590 | 3 |
| care_missed | 4.1 | 804 | 16.3 | 2,126 | 94 |
| fertilizer_uncollected | 1.3 | 61 | 14.6 | 630 | 46 |
| capped_yield | 0.0 | 0 | 1.5 | 185 | 0 |
| overflow | 37.4 | 3,732 | 13.4 | 1,006 | 94 |
| stranded | 29.6 | 2,863 | 0.8 | 39 | 96 |

Ground, tile-days per game (G / opp): crop 845/1254, animal 295/362, empty 128/110, weed 1/13, empty_pen 76/19, unwatered 6/350, unfed 10/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| STRAWBERRY | 408 | 110 | 209 | 173 | 166 | 5.1 | 18,985 | 34,631 | 8.9 |
| WOOL | 156 | 54 | 131 | 173 | 123 | 4.8 | 9,401 | 16,107 | 0.3 |
| FERTILIZER | 0 | 154 | 230 | 58 | 67 | 0.0 | 8,929 | 15,451 | 0.0 |
| MELON | 30 | 64 | 74 | 191 | 219 | 0.0 | 12,174 | 16,141 | 0.0 |
| TOMATO | 228 | 0 | 51 | 0 | 78 | 0.0 | 0 | 3,951 | 8.1 |
| WHEAT | 588 | 458 | 548 | 39 | 39 | 0.0 | 17,877 | 21,597 | 2.9 |
| CARROT | 246 | 32 | 123 | 43 | 39 | 0.0 | 1,404 | 4,797 | 4.2 |
| EGG | 242 | 97 | 96 | 52 | 49 | 0.0 | 5,069 | 4,674 | 0.0 |
| MILK | 404 | 184 | 178 | 201 | 192 | 9.5 | 36,997 | 34,004 | 10.5 |

Units sold on the same turn as the other farm sold the same good: G 252, opponent 270 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 4,050 | 2,975 |
| animal GOOSE | 862 | 856 |
| animal SHEEP | 1,786 | 3,208 |
| buy FERTILIZER | 0 | 1,838 |
| buy WHEAT | 16,655 | 10,901 |
| hire | 6,312 | 5,743 |
| land | 1,083 | 2,958 |
| seed CARROT | 397 | 918 |
| seed MELON | 1,307 | 1,016 |
| seed STRAWBERRY | 2,400 | 2,993 |
| seed TOMATO | 0 | 364 |
| seed WHEAT | 1,579 | 1,541 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 508 | 154 | -354 |
| 5 | 447 | 660 | +213 |
| 8 | 332 | 1,664 | +1,332 |
| 11 | 9,205 | 14,654 | +5,449 |
| 14 | 10,176 | 26,298 | +16,122 |
| 17 | 17,768 | 44,395 | +26,626 |
| 20 | 34,087 | 64,460 | +30,374 |
| 23 | 48,548 | 82,348 | +33,800 |
| 26 | 64,436 | 97,276 | +32,840 |

## Since the last inspection (2026-09-14 21:32, v5 night 95 + close 705)

- margin -35,466 -> -41,639, wins 8/96 -> 6/96, G 81,067 -> 77,402
- paired on 66 games where the opponent replay stayed in step in both runs: margin -7,592 per game (median -8,974), better in 7, worse in 59
- paired on 96 identical games: margin -6,173 per game, better in 14, worse in 82; G's own score better in 26
- died_unwatered: 1,858 -> 433 coins/game
- rotted: 54 -> 2 coins/game
- early_harvest: 15,005 -> 13,947 coins/game
- care_missed: 1,201 -> 804 coins/game
- fertilizer_uncollected: 246 -> 61 coins/game
- overflow: 4,072 -> 3,732 coins/game
- stranded: 1,616 -> 2,863 coins/game
- G idle share 6.3% -> 14.0%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
