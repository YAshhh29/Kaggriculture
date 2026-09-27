# Inspection of Candidate G -- 2026-09-15 00:13

- G source `706c350cea83` at commit `36957bf`, overrides `{'PICKUP_SHARES_SHED': True}`, label `v9 pickup shares shed`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T15:02 (4h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 86,982, opponent 114,351, margin -27,369, wins 15/96

27 games had an opponent replay refusing over 2% of its moves; on the other 69 G wins 3 with margin -36,072

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -45,790 | 1.4% |
| redblackbst | 8 | 0 | -42,849 | 0.7% |
| Unknown Mother-Goose | 8 | 0 | -41,687 | 0.0% |
| Mengfei Li | 8 | 0 | -36,014 | 1.1% |
| Otter Vibe | 8 | 1 | -35,261 | 0.1% |
| feel the agi | 8 | 0 | -32,834 | 0.8% |
| HowardLeeTW | 8 | 0 | -31,306 | 0.4% |
| ymg_aq | 8 | 1 | -24,674 | 1.4% |
| DSM | 8 | 2 | -17,247 | 2.7% |
| Majkel1337 | 8 | 2 | -17,237 | 2.8% |
| Orbital Terraformer | 8 | 4 | -6,889 | 4.3% |
| SpaTaro | 8 | 5 | +3,363 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 15,296 | G sells 159 at 39, opponent 546 at 39; town takes 588 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 9,540 | G sells 151 at 171, opponent 209 at 169; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,585 | opponent 5,028/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | TOMATO | 3,932 | G sells 0 at 0, opponent 50 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | WOOL | 3,746 | G sells 69 at 170, opponent 130 at 118; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | FERTILIZER | 3,402 | G sells 186 at 58, opponent 229 at 62; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | MELON | 2,372 | G sells 92 at 156, opponent 74 at 227; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | loss | stranded | 2,018 | opponent 37/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 9 | revenue gap | CARROT | 1,698 | G sells 71 at 38, opponent 123 at 36; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 10 | loss (estimate) | care_missed | 1,362 | opponent 2,002/game, hit in 95/96 games; e.g. tape live_108910285 seat 0 seed 11 step 263 at [7, 4] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 11 | sell timing | MILK | 1,244 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | sell timing | STRAWBERRY | 1,098 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 13 | loss | died_unwatered | 763 | opponent 175/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 431 at [1, 2] (STRAWBERRY age0 y0) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 14 | loss | overflow | 544 | opponent 920/game, hit in 44/96 games; e.g. tape live_108884658 seat 1 seed 12 step 503 | DROP timing and shed selling in market_orders() |
| 15 | sell timing | WOOL | 485 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | loss | escaped | 370 | opponent 2,574/game, hit in 43/96 games; e.g. tape live_108910285 seat 0 seed 11 step 239 at [7, 2] (COW y0) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 17 | loss | fertilizer_uncollected | 206 | opponent 500/game, hit in 83/96 games; e.g. tape live_108910285 seat 0 seed 11 step 551 at [2, 2] (SHEEP y0 fed cared manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 18 | sell timing | WHEAT | 84 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | loss | rotted | 52 | opponent 391/game, hit in 34/96 games; e.g. tape live_108610498 seat 1 seed 16 step 360 at [3, 9] (CARROT age4 y2) | harvest timing: HARVEST_HOLD and BAND_HARVEST |
| 20 | sell timing | CARROT | 50 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  40.7% |  50.9% |   8.3% |   0.0% |   0.0% |
| OPP |  46.3% |  43.2% |   8.8% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 7.9 | 763 | 2.2 | 175 | 96 |
| rotted | 1.2 | 52 | 6.2 | 391 | 34 |
| early_harvest | 170.6 | 6,585 | 131.0 | 5,028 | 96 |
| escaped | 0.8 | 370 | 5.0 | 2,574 | 43 |
| care_missed | 8.7 | 1,362 | 16.4 | 2,002 | 95 |
| fertilizer_uncollected | 6.3 | 206 | 14.6 | 500 | 83 |
| capped_yield | 0.0 | 0 | 1.5 | 180 | 0 |
| overflow | 6.0 | 544 | 12.2 | 920 | 44 |
| stranded | 26.0 | 2,018 | 0.8 | 37 | 96 |

Ground, tile-days per game (G / opp): crop 1177/1251, animal 301/361, empty 250/109, weed 6/12, empty_pen 91/19, unwatered 25/349, unfed 17/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 588 | 159 | 546 | 39 | 39 | 0.0 | 6,139 | 21,435 | 13.0 |
| STRAWBERRY | 408 | 151 | 209 | 171 | 169 | 9.1 | 25,834 | 35,374 | 7.1 |
| TOMATO | 228 | 0 | 50 | 0 | 78 | 0.0 | 0 | 3,932 | 8.1 |
| WOOL | 156 | 69 | 130 | 170 | 118 | 6.3 | 11,667 | 15,413 | 0.1 |
| FERTILIZER | 0 | 186 | 229 | 58 | 62 | 0.2 | 10,762 | 14,164 | 0.0 |
| MELON | 30 | 92 | 74 | 156 | 227 | 0.6 | 14,409 | 16,781 | 0.0 |
| CARROT | 246 | 71 | 123 | 38 | 36 | 0.0 | 2,698 | 4,395 | 1.9 |
| EGG | 242 | 110 | 97 | 52 | 48 | 0.0 | 5,712 | 4,621 | 0.0 |
| MILK | 404 | 177 | 177 | 189 | 172 | 6.0 | 33,461 | 30,461 | 4.4 |

Units sold on the same turn as the other farm sold the same good: G 205, opponent 252 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,921 | 2,975 |
| animal GOOSE | 1,100 | 856 |
| animal SHEEP | 2,708 | 3,193 |
| buy FERTILIZER | 0 | 1,614 |
| buy WHEAT | 3,547 | 11,079 |
| hire | 6,581 | 5,742 |
| land | 3,000 | 2,938 |
| seed CARROT | 846 | 918 |
| seed MELON | 1,341 | 1,015 |
| seed STRAWBERRY | 3,570 | 2,992 |
| seed TOMATO | 0 | 363 |
| seed WHEAT | 1,085 | 1,540 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 199 | 150 | -49 |
| 5 | 618 | 699 | +81 |
| 8 | 708 | 1,588 | +879 |
| 11 | 3,916 | 15,074 | +11,158 |
| 14 | 13,975 | 25,595 | +11,620 |
| 17 | 25,088 | 42,112 | +17,024 |
| 20 | 32,612 | 62,145 | +29,534 |
| 23 | 53,546 | 81,166 | +27,620 |
| 26 | 68,230 | 95,957 | +27,728 |

## Since the last inspection (2026-09-14 23:31, v9 baseline)

- margin -27,429 -> -27,369, wins 13/96 -> 15/96, G 86,928 -> 86,982
- paired on 69 games where the opponent replay stayed in step in both runs: margin +161 per game (median +1,179), better in 42, worse in 27
- paired on 96 identical games: margin +60 per game, better in 58, worse in 38; G's own score better in 52
- died_unwatered: 887 -> 763 coins/game
- early_harvest: 6,913 -> 6,585 coins/game
- escaped: 494 -> 370 coins/game
- care_missed: 1,634 -> 1,362 coins/game
- overflow: 410 -> 544 coins/game
- stranded: 2,234 -> 2,018 coins/game
- G idle share 9.2% -> 8.3%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
