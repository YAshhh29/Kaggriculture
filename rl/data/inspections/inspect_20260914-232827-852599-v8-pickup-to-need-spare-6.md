# Inspection of Candidate G -- 2026-09-14 23:28

- G source `05cc090afe31` at commit `3622fbd`, overrides `{'FEED_PICKUP_TO_NEED': True, 'FEED_PICKUP_SPARE': 6}`, label `v8 pickup to need spare 6`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T15:02 (3h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 85,519, opponent 116,004, margin -30,485, wins 12/96

28 games had an opponent replay refusing over 2% of its moves; on the other 68 G wins 2 with margin -37,825

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -49,098 | 1.4% |
| redblackbst | 8 | 0 | -45,885 | 0.7% |
| Unknown Mother-Goose | 8 | 0 | -44,177 | 0.3% |
| feel the agi | 8 | 0 | -38,872 | 0.8% |
| Mengfei Li | 8 | 0 | -38,656 | 1.1% |
| ymg_aq | 8 | 0 | -34,540 | 0.9% |
| Otter Vibe | 8 | 1 | -33,660 | 0.1% |
| HowardLeeTW | 8 | 0 | -32,292 | 0.5% |
| Majkel1337 | 8 | 2 | -19,180 | 2.8% |
| DSM | 8 | 2 | -18,724 | 2.7% |
| Orbital Terraformer | 8 | 3 | -11,749 | 4.3% |
| SpaTaro | 8 | 4 | +1,018 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 13,818 | G sells 202 at 39, opponent 549 at 39; town takes 588 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 10,643 | G sells 146 at 169, opponent 210 at 168; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,928 | opponent 5,070/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | WOOL | 3,992 | G sells 68 at 171, opponent 131 at 119; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | TOMATO | 3,954 | G sells 0 at 0, opponent 51 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | FERTILIZER | 3,809 | G sells 182 at 58, opponent 230 at 62; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | MELON | 2,556 | G sells 88 at 161, opponent 74 at 225; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | loss | stranded | 2,125 | opponent 37/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 9 | revenue gap | CARROT | 1,588 | G sells 74 at 38, opponent 124 at 36; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 10 | loss (estimate) | care_missed | 1,466 | opponent 2,047/game, hit in 93/96 games; e.g. tape live_108910285 seat 0 seed 11 step 215 at [7, 1] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 11 | sell timing | MILK | 1,187 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | sell timing | STRAWBERRY | 1,055 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 13 | loss | died_unwatered | 956 | opponent 177/game, hit in 95/96 games; e.g. tape live_108910285 seat 0 seed 11 step 311 at [4, 8] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 14 | loss | overflow | 767 | opponent 960/game, hit in 66/96 games; e.g. tape live_108910285 seat 0 seed 11 step 503 | DROP timing and shed selling in market_orders() |
| 15 | sell timing | WOOL | 447 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | loss | escaped | 377 | opponent 2,565/game, hit in 38/96 games; e.g. tape live_108884658 seat 1 seed 12 step 575 at [1, 2] (SHEEP y1 manure) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 17 | loss | fertilizer_uncollected | 167 | opponent 513/game, hit in 78/96 games; e.g. tape live_108884658 seat 1 seed 12 step 407 at [4, 6] (SHEEP y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 18 | sell timing | WHEAT | 139 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | loss | rotted | 75 | opponent 402/game, hit in 47/96 games; e.g. tape live_108910285 seat 0 seed 11 step 432 at [2, 9] (CARROT age4 y2) | harvest timing: HARVEST_HOLD and BAND_HARVEST |
| 20 | sell timing | CARROT | 51 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  40.6% |  49.9% |   9.5% |   0.0% |   0.0% |
| OPP |  46.5% |  43.2% |   8.6% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 9.3 | 956 | 2.3 | 177 | 95 |
| rotted | 1.9 | 75 | 6.4 | 402 | 47 |
| early_harvest | 179.0 | 6,928 | 131.9 | 5,070 | 96 |
| escaped | 0.8 | 377 | 5.0 | 2,565 | 38 |
| care_missed | 9.0 | 1,466 | 16.4 | 2,047 | 93 |
| fertilizer_uncollected | 4.4 | 167 | 14.6 | 513 | 78 |
| capped_yield | 0.0 | 0 | 1.5 | 185 | 0 |
| overflow | 9.0 | 767 | 12.7 | 960 | 66 |
| stranded | 25.4 | 2,125 | 0.8 | 37 | 96 |

Ground, tile-days per game (G / opp): crop 1151/1259, animal 301/363, empty 257/111, weed 8/12, empty_pen 98/18, unwatered 24/351, unfed 17/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 588 | 202 | 549 | 39 | 39 | 0.0 | 7,830 | 21,648 | 12.0 |
| STRAWBERRY | 408 | 146 | 210 | 169 | 168 | 8.6 | 24,796 | 35,439 | 9.8 |
| WOOL | 156 | 68 | 131 | 171 | 119 | 6.7 | 11,572 | 15,564 | 0.0 |
| TOMATO | 228 | 0 | 51 | 0 | 78 | 0.0 | 0 | 3,954 | 8.1 |
| FERTILIZER | 0 | 182 | 230 | 58 | 62 | 0.1 | 10,548 | 14,357 | 0.0 |
| MELON | 30 | 88 | 74 | 161 | 225 | 0.5 | 14,119 | 16,675 | 0.0 |
| CARROT | 246 | 74 | 124 | 38 | 36 | 0.0 | 2,822 | 4,410 | 2.0 |
| EGG | 242 | 116 | 96 | 52 | 48 | 0.0 | 6,035 | 4,577 | 0.0 |
| MILK | 404 | 173 | 179 | 193 | 177 | 6.5 | 33,492 | 31,640 | 4.0 |

Units sold on the same turn as the other farm sold the same good: G 218, opponent 263 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,950 | 2,975 |
| animal GOOSE | 1,134 | 850 |
| animal SHEEP | 2,651 | 3,193 |
| buy FERTILIZER | 0 | 1,632 |
| buy WHEAT | 5,528 | 11,059 |
| hire | 6,593 | 5,743 |
| land | 2,958 | 2,979 |
| seed CARROT | 868 | 918 |
| seed MELON | 1,341 | 1,015 |
| seed STRAWBERRY | 3,580 | 2,994 |
| seed TOMATO | 0 | 363 |
| seed WHEAT | 1,090 | 1,540 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 223 | 154 | -69 |
| 5 | 732 | 716 | -16 |
| 8 | 1,426 | 1,596 | +170 |
| 11 | 8,802 | 14,794 | +5,992 |
| 14 | 12,287 | 25,586 | +13,298 |
| 17 | 22,950 | 42,922 | +19,972 |
| 20 | 29,538 | 62,978 | +33,441 |
| 23 | 51,201 | 82,516 | +31,314 |
| 26 | 66,328 | 97,326 | +30,997 |

## Since the last inspection (2026-09-14 22:52, v8 baseline)

- margin -33,408 -> -30,485, wins 11/96 -> 12/96, G 81,842 -> 85,519
- paired on 68 games where the opponent replay stayed in step in both runs: margin +2,981 per game (median +2,824), better in 49, worse in 19
- paired on 96 identical games: margin +2,923 per game, better in 69, worse in 27; G's own score better in 71
- died_unwatered: 1,062 -> 956 coins/game
- early_harvest: 14,814 -> 6,928 coins/game
- escaped: 35 -> 377 coins/game
- care_missed: 878 -> 1,466 coins/game
- overflow: 3,849 -> 767 coins/game
- stranded: 1,605 -> 2,125 coins/game
- G idle share 9.1% -> 9.5%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
