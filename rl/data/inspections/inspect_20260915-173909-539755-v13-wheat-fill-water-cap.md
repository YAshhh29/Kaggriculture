# Inspection of Candidate G -- 2026-09-15 17:39

- G source `7290710fdaf2` at commit `0d86b30`, overrides `{'WHEAT_FILL': True, 'WHEAT_FILL_WATER_CAP': True}`, label `v13 wheat fill water cap`
- 83 games against 12 opponents; match snapshot newest game 2026-09-15T11:39 (0h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 87,844, opponent 113,517, margin -25,674, wins 12/83

22 games had an opponent replay refusing over 2% of its moves; on the other 61 G wins 3 with margin -33,456

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 4 | 0 | -46,689 | 1.5% |
| Zhenghongshuang | 8 | 0 | -42,047 | 0.6% |
| Cow Boy | 8 | 1 | -39,877 | 0.6% |
| Artem The Farmer 🍅 | 3 | 0 | -36,810 | 1.6% |
| Otter Vibe | 8 | 1 | -33,663 | 0.1% |
| Mengfei Li | 8 | 1 | -28,199 | 2.7% |
| HowardLeeTW | 8 | 0 | -26,386 | 0.1% |
| DSM | 4 | 0 | -26,308 | 2.3% |
| ymg_aq | 8 | 1 | -23,528 | 0.1% |
| Majkel1337 | 8 | 2 | -17,235 | 2.8% |
| Orbital Terraformer | 8 | 4 | -4,332 | 5.1% |
| SpaTaro | 8 | 2 | -795 | 3.0% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 12,731 | G sells 186 at 37, opponent 525 at 38; town takes 585 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 9,798 | G sells 157 at 164, opponent 214 at 166; town takes 417 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,212 | opponent 4,701/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | WOOL | 3,976 | G sells 64 at 169, opponent 129 at 115; town takes 147 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | FERTILIZER | 3,972 | G sells 185 at 57, opponent 240 at 61; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | TOMATO | 3,454 | G sells 0 at 0, opponent 46 at 75; town takes 223 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | MELON | 2,360 | G sells 89 at 159, opponent 73 at 227; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | revenue gap | CARROT | 2,071 | G sells 61 at 39, opponent 119 at 38; town takes 248 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | loss (estimate) | care_missed | 1,317 | opponent 1,553/game, hit in 81/83 games; e.g. tape live_108910285 seat 0 seed 11 step 647 at [4, 0] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 10 | sell timing | STRAWBERRY | 1,196 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | sell timing | MILK | 1,156 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | loss | died_unwatered | 886 | opponent 131/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 287 at [0, 6] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 13 | loss | escaped | 582 | opponent 2,143/game, hit in 53/83 games; e.g. tape live_108884658 seat 1 seed 12 step 335 at [2, 7] (SHEEP y0) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 14 | sell timing | WOOL | 391 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | loss | overflow | 343 | opponent 931/game, hit in 27/83 games; e.g. tape live_108884658 seat 1 seed 12 step 575 | DROP timing and shed selling in market_orders() |
| 16 | loss | fertilizer_uncollected | 154 | opponent 426/game, hit in 63/83 games; e.g. tape live_108884658 seat 1 seed 12 step 551 at [0, 6] (SHEEP y0 manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 17 | sell timing | WHEAT | 100 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 18 | sell timing | EGG | 50 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | loss | rotted | 45 | opponent 315/game, hit in 24/83 games; e.g. tape live_108884658 seat 1 seed 12 step 432 at [9, 3] (WHEAT age5 y5) | harvest timing: HARVEST_HOLD and BAND_HARVEST |
| 20 | sell timing | CARROT | 43 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  39.9% |  51.5% |   8.6% |   0.0% |   0.0% |
| OPP |  46.1% |  43.3% |   8.9% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 8.7 | 886 | 1.8 | 131 | 83 |
| rotted | 1.1 | 45 | 5.9 | 315 | 24 |
| early_harvest | 164.1 | 6,212 | 125.9 | 4,701 | 83 |
| escaped | 1.3 | 582 | 4.0 | 2,143 | 53 |
| care_missed | 8.3 | 1,317 | 10.8 | 1,553 | 81 |
| fertilizer_uncollected | 4.4 | 154 | 11.8 | 426 | 63 |
| capped_yield | 0.0 | 0 | 1.6 | 219 | 0 |
| overflow | 4.2 | 343 | 11.5 | 931 | 27 |
| stranded | 0.7 | 25 | 0.7 | 37 | 41 |

Ground, tile-days per game (G / opp): crop 1176/1260, animal 289/354, empty 197/115, weed 4/10, empty_pen 111/19, unwatered 22/338, unfed 15/60

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 585 | 186 | 525 | 37 | 38 | 0.0 | 6,959 | 19,690 | 11.2 |
| STRAWBERRY | 417 | 157 | 214 | 164 | 166 | 9.7 | 25,797 | 35,595 | 10.5 |
| WOOL | 147 | 64 | 129 | 169 | 115 | 7.0 | 10,866 | 14,842 | 0.1 |
| FERTILIZER | 0 | 185 | 240 | 57 | 61 | 1.0 | 10,568 | 14,540 | 0.0 |
| TOMATO | 223 | 0 | 46 | 0 | 75 | 0.0 | 0 | 3,454 | 7.9 |
| MELON | 30 | 89 | 73 | 159 | 227 | 0.6 | 14,233 | 16,592 | 0.0 |
| CARROT | 248 | 61 | 119 | 39 | 38 | 0.0 | 2,389 | 4,459 | 2.4 |
| MILK | 403 | 172 | 180 | 190 | 175 | 5.9 | 32,635 | 31,388 | 4.4 |
| EGG | 245 | 118 | 73 | 53 | 49 | 0.0 | 6,254 | 3,572 | 0.0 |

Units sold on the same turn as the other farm sold the same good: G 233, opponent 254 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,742 | 3,022 |
| animal GOOSE | 1,113 | 683 |
| animal SHEEP | 2,398 | 3,175 |
| buy FERTILIZER | 0 | 1,797 |
| buy WHEAT | 2,437 | 9,489 |
| hire | 6,589 | 5,742 |
| land | 2,807 | 2,904 |
| seed CARROT | 753 | 865 |
| seed MELON | 1,337 | 1,000 |
| seed STRAWBERRY | 3,500 | 3,039 |
| seed TOMATO | 0 | 331 |
| seed WHEAT | 1,181 | 1,567 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 222 | 205 | -17 |
| 5 | 486 | 777 | +291 |
| 8 | 743 | 1,807 | +1,064 |
| 11 | 9,706 | 13,071 | +3,365 |
| 14 | 15,560 | 25,167 | +9,607 |
| 17 | 25,197 | 42,900 | +17,703 |
| 20 | 33,326 | 63,854 | +30,528 |
| 23 | 51,294 | 81,906 | +30,612 |
| 26 | 66,696 | 94,589 | +27,893 |

## Since the last inspection (2026-09-15 17:24, v13 baseline)

- margin -24,356 -> -25,674, wins 12/83 -> 12/83, G 89,332 -> 87,844
- paired on 61 games where the opponent replay stayed in step in both runs: margin -931 per game (median +442), better in 31, worse in 30
- paired on 83 identical games: margin -1,318 per game, better in 41, worse in 42; G's own score better in 39
- early_harvest: 6,838 -> 6,212 coins/game
- escaped: 453 -> 582 coins/game
- care_missed: 1,636 -> 1,317 coins/game
- overflow: 517 -> 343 coins/game
- G idle share 9.5% -> 8.6%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
