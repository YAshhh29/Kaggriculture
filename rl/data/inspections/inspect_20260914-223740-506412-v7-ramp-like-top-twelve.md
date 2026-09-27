# Inspection of Candidate G -- 2026-09-14 22:37

- G source `38ce35a429d8` at commit `35d6487`, overrides `{'HAND_RAMP': [[0, 5], [6, 7], [8, 9], [10, 11], [14, 12]]}`, label `v7 ramp like top twelve`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T15:02 (2h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 81,842, opponent 115,249, margin -33,408, wins 11/96

26 games had an opponent replay refusing over 2% of its moves; on the other 70 G wins 1 with margin -41,412

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -51,066 | 1.4% |
| redblackbst | 8 | 0 | -46,672 | 0.7% |
| Unknown Mother-Goose | 8 | 0 | -46,537 | 0.3% |
| feel the agi | 8 | 0 | -41,473 | 0.8% |
| Mengfei Li | 8 | 0 | -41,038 | 1.1% |
| HowardLeeTW | 8 | 0 | -39,017 | 0.3% |
| Otter Vibe | 8 | 1 | -36,974 | 0.1% |
| ymg_aq | 8 | 1 | -33,275 | 0.9% |
| Majkel1337 | 8 | 1 | -25,260 | 2.8% |
| DSM | 8 | 1 | -24,522 | 2.7% |
| Orbital Terraformer | 8 | 4 | -12,586 | 4.3% |
| SpaTaro | 8 | 3 | -2,469 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | loss (estimate) | early_harvest | 14,814 | opponent 5,072/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 2 | revenue gap | STRAWBERRY | 11,908 | G sells 134 at 172, opponent 210 at 167; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | revenue gap | FERTILIZER | 5,178 | G sells 157 at 61, opponent 229 at 64; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 4 | revenue gap | MELON | 4,129 | G sells 74 at 170, opponent 74 at 226; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | TOMATO | 3,932 | G sells 0 at 0, opponent 50 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | loss | overflow | 3,849 | opponent 920/game, hit in 90/96 games; e.g. tape live_108910285 seat 0 seed 11 step 455 | DROP timing and shed selling in market_orders() |
| 7 | revenue gap | WOOL | 3,474 | G sells 70 at 172, opponent 130 at 119; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | revenue gap | CARROT | 2,465 | G sells 54 at 39, opponent 123 at 37; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | loss | stranded | 1,605 | opponent 38/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 10 | sell timing | MILK | 1,259 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | loss | died_unwatered | 1,062 | opponent 175/game, hit in 94/96 games; e.g. tape live_108910285 seat 0 seed 11 step 215 at [8, 1] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 12 | sell timing | STRAWBERRY | 934 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 13 | loss (estimate) | care_missed | 878 | opponent 2,023/game, hit in 92/96 games; e.g. tape live_108910285 seat 0 seed 11 step 503 at [6, 0] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 14 | sell timing | WHEAT | 721 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | sell timing | WOOL | 425 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | loss | fertilizer_uncollected | 158 | opponent 574/game, hit in 68/96 games; e.g. tape live_108884658 seat 1 seed 12 step 599 at [4, 0] (COW y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 17 | sell timing | EGG | 43 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 18 | loss | escaped | 35 | opponent 2,578/game, hit in 5/96 games; e.g. tape live_108848381 seat 1 seed 16 step 623 at [0, 2] (SHEEP y0 manure) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 19 | loss | rotted | 33 | opponent 388/game, hit in 22/96 games; e.g. tape live_108884658 seat 1 seed 12 step 624 at [9, 0] (CARROT age4 y2) | harvest timing: HARVEST_HOLD and BAND_HARVEST |
| 20 | sell timing | CARROT | 32 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  42.3% |  48.7% |   9.1% |   0.0% |   0.0% |
| OPP |  46.3% |  43.2% |   8.8% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 10.1 | 1,062 | 2.3 | 175 | 94 |
| rotted | 0.7 | 33 | 6.2 | 388 | 22 |
| early_harvest | 386.8 | 14,814 | 131.0 | 5,072 | 96 |
| escaped | 0.1 | 35 | 5.0 | 2,578 | 5 |
| care_missed | 5.4 | 878 | 16.4 | 2,023 | 92 |
| fertilizer_uncollected | 3.8 | 158 | 14.6 | 574 | 68 |
| capped_yield | 0.0 | 0 | 1.5 | 181 | 0 |
| overflow | 47.6 | 3,849 | 12.2 | 920 | 90 |
| stranded | 19.3 | 1,605 | 0.8 | 38 | 96 |

Ground, tile-days per game (G / opp): crop 1048/1252, animal 289/361, empty 227/108, weed 11/12, empty_pen 93/19, unwatered 30/349, unfed 9/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| STRAWBERRY | 408 | 134 | 210 | 172 | 167 | 7.8 | 23,164 | 35,072 | 9.9 |
| FERTILIZER | 0 | 157 | 229 | 61 | 64 | 0.0 | 9,590 | 14,768 | 0.0 |
| MELON | 30 | 74 | 74 | 170 | 226 | 0.2 | 12,583 | 16,712 | 0.0 |
| TOMATO | 228 | 0 | 50 | 0 | 78 | 0.0 | 0 | 3,932 | 8.1 |
| WOOL | 156 | 70 | 130 | 172 | 119 | 7.0 | 12,046 | 15,520 | 0.1 |
| CARROT | 246 | 54 | 123 | 39 | 37 | 0.0 | 2,095 | 4,560 | 2.7 |
| EGG | 242 | 106 | 96 | 52 | 48 | 0.0 | 5,528 | 4,615 | 0.0 |
| WHEAT | 588 | 613 | 545 | 39 | 39 | 0.0 | 23,888 | 21,487 | 1.6 |
| MILK | 404 | 176 | 178 | 193 | 174 | 6.1 | 33,980 | 30,913 | 4.1 |

Units sold on the same turn as the other farm sold the same good: G 268, opponent 275 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,817 | 2,983 |
| animal GOOSE | 1,019 | 850 |
| animal SHEEP | 2,536 | 3,193 |
| buy FERTILIZER | 0 | 1,748 |
| buy WHEAT | 21,861 | 11,040 |
| hire | 6,446 | 5,743 |
| land | 2,417 | 2,938 |
| seed CARROT | 683 | 918 |
| seed MELON | 1,314 | 1,017 |
| seed STRAWBERRY | 3,284 | 2,997 |
| seed TOMATO | 0 | 363 |
| seed WHEAT | 1,655 | 1,541 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 133 | 154 | +21 |
| 5 | 42 | 693 | +650 |
| 8 | 912 | 1,609 | +697 |
| 11 | 8,152 | 14,849 | +6,697 |
| 14 | 13,266 | 25,536 | +12,270 |
| 17 | 23,392 | 42,576 | +19,184 |
| 20 | 34,026 | 62,222 | +28,196 |
| 23 | 51,532 | 80,202 | +28,670 |
| 26 | 65,268 | 94,306 | +29,037 |

## Since the last inspection (2026-09-14 22:06, v7 baseline)

- margin -34,891 -> -33,408, wins 8/96 -> 11/96, G 81,534 -> 81,842
- paired on 68 games where the opponent replay stayed in step in both runs: margin +1,083 per game (median +1,355), better in 42, worse in 26
- paired on 96 identical games: margin +1,484 per game, better in 60, worse in 36; G's own score better in 53
- died_unwatered: 1,805 -> 1,062 coins/game
- early_harvest: 14,987 -> 14,814 coins/game
- care_missed: 1,152 -> 878 coins/game
- fertilizer_uncollected: 233 -> 158 coins/game
- overflow: 4,015 -> 3,849 coins/game
- G idle share 6.4% -> 9.1%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
