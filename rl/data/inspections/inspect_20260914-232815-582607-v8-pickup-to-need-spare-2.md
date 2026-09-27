# Inspection of Candidate G -- 2026-09-14 23:28

- G source `05cc090afe31` at commit `3622fbd`, overrides `{'FEED_PICKUP_TO_NEED': True, 'FEED_PICKUP_SPARE': 2}`, label `v8 pickup to need spare 2`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T15:02 (3h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 84,788, opponent 115,152, margin -30,364, wins 12/96

27 games had an opponent replay refusing over 2% of its moves; on the other 69 G wins 1 with margin -38,599

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| redblackbst | 8 | 0 | -46,918 | 0.7% |
| Catalyst | 8 | 0 | -46,311 | 1.4% |
| Unknown Mother-Goose | 8 | 0 | -42,993 | 0.0% |
| HowardLeeTW | 8 | 0 | -37,950 | 0.4% |
| Mengfei Li | 8 | 0 | -37,379 | 1.1% |
| Otter Vibe | 8 | 0 | -36,753 | 0.1% |
| feel the agi | 8 | 0 | -35,669 | 0.8% |
| ymg_aq | 8 | 2 | -22,314 | 1.9% |
| Majkel1337 | 8 | 2 | -21,409 | 2.8% |
| DSM | 8 | 1 | -19,820 | 2.7% |
| Orbital Terraformer | 8 | 3 | -14,831 | 4.3% |
| SpaTaro | 8 | 4 | -2,026 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 15,267 | G sells 159 at 38, opponent 548 at 39; town takes 588 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 9,334 | G sells 152 at 169, opponent 209 at 168; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,608 | opponent 5,028/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | WOOL | 4,318 | G sells 67 at 167, opponent 131 at 119; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | TOMATO | 3,949 | G sells 0 at 0, opponent 50 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | FERTILIZER | 3,379 | G sells 187 at 58, opponent 229 at 62; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | loss | stranded | 2,471 | opponent 37/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 8 | revenue gap | MELON | 2,416 | G sells 89 at 160, opponent 74 at 225; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | loss (estimate) | care_missed | 1,794 | opponent 2,056/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 287 at [4, 0] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 10 | revenue gap | CARROT | 1,724 | G sells 71 at 38, opponent 123 at 36; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 11 | sell timing | STRAWBERRY | 1,101 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | sell timing | MILK | 1,053 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 13 | loss | died_unwatered | 617 | opponent 178/game, hit in 95/96 games; e.g. tape live_108910285 seat 0 seed 11 step 335 at [3, 7] (STRAWBERRY age0 y0) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 14 | revenue gap | MILK | 501 | G sells 160 at 194, opponent 177 at 179; town takes 404 | crop and herd choice: CROP_TILES, herd_plan() |
| 15 | sell timing | WOOL | 456 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | loss | escaped | 444 | opponent 2,595/game, hit in 49/96 games; e.g. tape live_108884658 seat 1 seed 12 step 431 at [0, 4] (SHEEP y0) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 17 | loss | overflow | 394 | opponent 1,009/game, hit in 44/96 games; e.g. tape live_108884658 seat 1 seed 12 step 527 | DROP timing and shed selling in market_orders() |
| 18 | loss | fertilizer_uncollected | 148 | opponent 510/game, hit in 71/96 games; e.g. tape live_108884658 seat 1 seed 12 step 455 at [2, 7] (SHEEP y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 19 | sell timing | WHEAT | 85 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | sell timing | CARROT | 49 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  40.2% |  49.9% |   9.9% |   0.0% |   0.0% |
| OPP |  46.3% |  43.2% |   8.7% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 6.4 | 617 | 2.3 | 178 | 95 |
| rotted | 1.2 | 46 | 6.3 | 385 | 35 |
| early_harvest | 173.8 | 6,608 | 131.8 | 5,028 | 96 |
| escaped | 1.0 | 444 | 5.0 | 2,595 | 49 |
| care_missed | 10.2 | 1,794 | 16.3 | 2,056 | 96 |
| fertilizer_uncollected | 4.3 | 148 | 14.6 | 510 | 71 |
| capped_yield | 0.0 | 0 | 1.5 | 183 | 0 |
| overflow | 4.0 | 394 | 13.2 | 1,009 | 44 |
| stranded | 27.2 | 2,471 | 0.8 | 37 | 96 |

Ground, tile-days per game (G / opp): crop 1163/1255, animal 305/361, empty 243/110, weed 4/12, empty_pen 95/19, unwatered 21/350, unfed 33/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 588 | 159 | 548 | 38 | 39 | 0.0 | 6,092 | 21,359 | 15.4 |
| STRAWBERRY | 408 | 152 | 209 | 169 | 168 | 8.9 | 25,697 | 35,031 | 10.1 |
| WOOL | 156 | 67 | 131 | 167 | 119 | 7.4 | 11,193 | 15,511 | 0.1 |
| TOMATO | 228 | 0 | 50 | 0 | 78 | 0.0 | 0 | 3,949 | 8.1 |
| FERTILIZER | 0 | 187 | 229 | 58 | 62 | 0.2 | 10,791 | 14,170 | 0.0 |
| MELON | 30 | 89 | 74 | 160 | 225 | 0.2 | 14,265 | 16,681 | 0.0 |
| CARROT | 246 | 71 | 123 | 38 | 36 | 0.0 | 2,693 | 4,417 | 2.0 |
| MILK | 404 | 160 | 177 | 194 | 179 | 5.5 | 31,096 | 31,597 | 4.2 |
| EGG | 242 | 114 | 97 | 52 | 48 | 0.0 | 5,916 | 4,628 | 0.0 |

Units sold on the same turn as the other farm sold the same good: G 211, opponent 251 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,946 | 2,975 |
| animal GOOSE | 1,050 | 856 |
| animal SHEEP | 2,677 | 3,193 |
| buy FERTILIZER | 0 | 1,616 |
| buy WHEAT | 2,921 | 11,020 |
| hire | 6,657 | 5,742 |
| land | 2,938 | 2,958 |
| seed CARROT | 825 | 918 |
| seed MELON | 1,308 | 1,015 |
| seed STRAWBERRY | 3,548 | 2,993 |
| seed TOMATO | 0 | 363 |
| seed WHEAT | 1,084 | 1,540 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 223 | 154 | -69 |
| 5 | 553 | 693 | +140 |
| 8 | 1,144 | 1,586 | +443 |
| 11 | 9,006 | 14,786 | +5,779 |
| 14 | 12,918 | 25,621 | +12,703 |
| 17 | 22,512 | 42,735 | +20,222 |
| 20 | 30,763 | 62,251 | +31,488 |
| 23 | 48,678 | 81,025 | +32,347 |
| 26 | 64,568 | 95,132 | +30,564 |

## Since the last inspection (2026-09-14 22:52, v8 baseline)

- margin -33,408 -> -30,364, wins 11/96 -> 12/96, G 81,842 -> 84,788
- paired on 68 games where the opponent replay stayed in step in both runs: margin +2,418 per game (median +2,494), better in 43, worse in 25
- paired on 96 identical games: margin +3,043 per game, better in 60, worse in 36; G's own score better in 63
- died_unwatered: 1,062 -> 617 coins/game
- early_harvest: 14,814 -> 6,608 coins/game
- escaped: 35 -> 444 coins/game
- care_missed: 878 -> 1,794 coins/game
- overflow: 3,849 -> 394 coins/game
- stranded: 1,605 -> 2,471 coins/game
- G idle share 9.1% -> 9.9%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
