# Inspection of Candidate G -- 2026-09-15 01:03

- G source `2100b677b8c2` at commit `1a1d7e6`, overrides `{'SEED_FIRST_UNTIL_DAY': 10, 'SEED_FIRST_ORDER': ['MELON', 'STRAWBERRY', 'CARROT']}`, label `v10 seed after herd d1-10 melon first`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T15:02 (4h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 85,498, opponent 115,819, margin -30,321, wins 14/96

27 games had an opponent replay refusing over 2% of its moves; on the other 69 G wins 2 with margin -38,889

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -50,435 | 1.4% |
| redblackbst | 8 | 0 | -48,199 | 0.7% |
| Unknown Mother-Goose | 8 | 0 | -45,610 | 0.0% |
| feel the agi | 8 | 0 | -39,682 | 0.8% |
| Mengfei Li | 8 | 0 | -38,816 | 1.1% |
| Otter Vibe | 8 | 1 | -34,408 | 0.0% |
| HowardLeeTW | 8 | 0 | -31,363 | 0.4% |
| ymg_aq | 8 | 1 | -25,407 | 1.4% |
| Majkel1337 | 8 | 2 | -19,305 | 2.8% |
| DSM | 8 | 2 | -18,903 | 2.7% |
| Orbital Terraformer | 8 | 4 | -10,431 | 4.3% |
| SpaTaro | 8 | 4 | -1,289 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 14,327 | G sells 179 at 38, opponent 546 at 39; town takes 588 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 10,032 | G sells 152 at 169, opponent 210 at 170; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,687 | opponent 4,976/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | WOOL | 5,217 | G sells 62 at 172, opponent 130 at 122; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | FERTILIZER | 3,972 | G sells 179 at 58, opponent 229 at 63; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | TOMATO | 3,937 | G sells 0 at 0, opponent 50 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | CARROT | 2,135 | G sells 61 at 38, opponent 123 at 36; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | loss (estimate) | care_missed | 1,818 | opponent 2,110/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 215 at [9, 2] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 9 | sell timing | MILK | 1,100 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 10 | sell timing | STRAWBERRY | 982 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | revenue gap | MELON | 751 | G sells 106 at 144, opponent 74 at 215; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 12 | loss | stranded | 749 | opponent 37/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 13 | loss | escaped | 660 | opponent 2,594/game, hit in 59/96 games; e.g. tape live_108884658 seat 1 seed 12 step 479 at [1, 3] (SHEEP y0) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 14 | loss | died_unwatered | 622 | opponent 174/game, hit in 91/96 games; e.g. tape live_108910285 seat 0 seed 11 step 407 at [2, 9] (STRAWBERRY age0 y0) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 15 | loss | overflow | 478 | opponent 946/game, hit in 41/96 games; e.g. tape live_108910285 seat 0 seed 11 step 695 | DROP timing and shed selling in market_orders() |
| 16 | sell timing | WOOL | 372 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 17 | revenue gap | MILK | 243 | G sells 161 at 196, opponent 177 at 180; town takes 404 | crop and herd choice: CROP_TILES, herd_plan() |
| 18 | loss | fertilizer_uncollected | 162 | opponent 527/game, hit in 70/96 games; e.g. tape live_108910285 seat 0 seed 11 step 551 at [1, 3] (SHEEP y1 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 19 | sell timing | WHEAT | 98 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | sell timing | EGG | 45 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  39.3% |  49.7% |  11.0% |   0.0% |   0.0% |
| OPP |  46.3% |  43.2% |   8.8% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 6.5 | 622 | 2.2 | 174 | 91 |
| rotted | 0.6 | 27 | 6.2 | 393 | 20 |
| early_harvest | 175.0 | 6,687 | 130.9 | 4,976 | 96 |
| escaped | 1.5 | 660 | 5.0 | 2,594 | 59 |
| care_missed | 10.4 | 1,818 | 16.4 | 2,110 | 96 |
| fertilizer_uncollected | 4.4 | 162 | 14.6 | 527 | 70 |
| capped_yield | 0.0 | 0 | 1.5 | 186 | 0 |
| overflow | 4.8 | 478 | 12.5 | 946 | 41 |
| stranded | 9.0 | 749 | 0.8 | 37 | 96 |

Ground, tile-days per game (G / opp): crop 1155/1251, animal 291/361, empty 170/109, weed 4/12, empty_pen 90/19, unwatered 14/349, unfed 25/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 588 | 179 | 546 | 38 | 39 | 0.0 | 6,881 | 21,208 | 13.9 |
| STRAWBERRY | 408 | 152 | 210 | 169 | 170 | 10.5 | 25,623 | 35,655 | 10.4 |
| WOOL | 156 | 62 | 130 | 172 | 122 | 5.7 | 10,659 | 15,876 | 0.2 |
| FERTILIZER | 0 | 179 | 229 | 58 | 63 | 0.0 | 10,409 | 14,381 | 0.0 |
| TOMATO | 228 | 0 | 50 | 0 | 78 | 0.0 | 0 | 3,937 | 8.1 |
| CARROT | 246 | 61 | 123 | 38 | 36 | 0.0 | 2,324 | 4,459 | 2.1 |
| MELON | 30 | 106 | 74 | 144 | 215 | 5.6 | 15,165 | 15,916 | 0.0 |
| MILK | 404 | 161 | 177 | 196 | 180 | 5.2 | 31,698 | 31,941 | 4.2 |
| EGG | 242 | 112 | 97 | 52 | 48 | 0.0 | 5,819 | 4,634 | 0.0 |

Units sold on the same turn as the other farm sold the same good: G 211, opponent 246 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 3,058 | 2,975 |
| animal GOOSE | 1,084 | 856 |
| animal SHEEP | 2,375 | 3,193 |
| buy FERTILIZER | 0 | 1,658 |
| buy WHEAT | 3,389 | 10,996 |
| hire | 6,640 | 5,743 |
| land | 2,542 | 2,938 |
| seed CARROT | 736 | 918 |
| seed MELON | 1,779 | 1,015 |
| seed STRAWBERRY | 3,384 | 2,994 |
| seed TOMATO | 0 | 364 |
| seed WHEAT | 1,093 | 1,541 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 223 | 154 | -69 |
| 5 | 161 | 693 | +532 |
| 8 | 1,029 | 1,592 | +563 |
| 11 | 8,956 | 14,804 | +5,848 |
| 14 | 13,128 | 25,708 | +12,580 |
| 17 | 28,476 | 42,554 | +14,078 |
| 20 | 36,432 | 61,875 | +25,444 |
| 23 | 50,995 | 81,962 | +30,968 |
| 26 | 64,897 | 97,547 | +32,650 |

## Since the last inspection (2026-09-15 00:40, v10 baseline)

- margin -25,882 -> -30,321, wins 15/96 -> 14/96, G 88,554 -> 85,498
- paired on 69 games where the opponent replay stayed in step in both runs: margin -3,980 per game (median -3,458), better in 17, worse in 52
- paired on 96 identical games: margin -4,439 per game, better in 23, worse in 73; G's own score better in 34
- died_unwatered: 867 -> 622 coins/game
- early_harvest: 6,914 -> 6,687 coins/game
- escaped: 501 -> 660 coins/game
- care_missed: 1,653 -> 1,818 coins/game
- overflow: 550 -> 478 coins/game
- stranded: 693 -> 749 coins/game
- G idle share 9.2% -> 11.0%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
