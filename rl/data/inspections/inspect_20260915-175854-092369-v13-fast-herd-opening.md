# Inspection of Candidate G -- 2026-09-15 17:58

- G source `7cfdc7a6fdb1` at commit `cf4b692`, overrides `{'PEN_ORDER': ['PASTURE', 'COOP'], 'BIRDS_PER_TURN': 3, 'COOP_LEAD': 4, 'GOOSE_CASH_FLOOR': 150}`, label `v13 fast herd opening`
- 83 games against 12 opponents; match snapshot newest game 2026-09-15T11:39 (1h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 84,896, opponent 111,402, margin -26,506, wins 10/83

24 games had an opponent replay refusing over 2% of its moves; on the other 59 G wins 1 with margin -36,176

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 4 | 0 | -49,884 | 1.5% |
| Zhenghongshuang | 8 | 0 | -44,188 | 0.6% |
| Cow Boy | 8 | 1 | -41,708 | 0.6% |
| Artem The Farmer 🍅 | 3 | 0 | -40,017 | 1.3% |
| Otter Vibe | 8 | 0 | -34,531 | 0.0% |
| HowardLeeTW | 8 | 0 | -31,272 | 0.3% |
| Mengfei Li | 8 | 1 | -29,762 | 2.8% |
| ymg_aq | 8 | 0 | -25,603 | 0.1% |
| DSM | 4 | 1 | -22,849 | 3.1% |
| Majkel1337 | 8 | 2 | -15,342 | 3.2% |
| Orbital Terraformer | 8 | 2 | -6,131 | 5.1% |
| SpaTaro | 8 | 3 | +4,913 | 4.3% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 14,122 | G sells 162 at 39, opponent 518 at 39; town takes 585 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 10,622 | G sells 151 at 164, opponent 212 at 167; town takes 417 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,228 | opponent 4,718/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | WOOL | 5,154 | G sells 58 at 181, opponent 126 at 124; town takes 147 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | MELON | 3,533 | G sells 77 at 172, opponent 73 at 232; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | TOMATO | 3,384 | G sells 0 at 0, opponent 45 at 76; town takes 223 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | FERTILIZER | 3,314 | G sells 199 at 55, opponent 238 at 60; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | loss (estimate) | care_missed | 1,859 | opponent 1,513/game, hit in 83/83 games; e.g. tape live_108910285 seat 0 seed 11 step 119 at [3, 0] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 9 | revenue gap | CARROT | 1,513 | G sells 70 at 39, opponent 116 at 37; town takes 248 | crop and herd choice: CROP_TILES, herd_plan() |
| 10 | sell timing | MILK | 1,489 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | loss | escaped | 1,318 | opponent 2,240/game, hit in 70/83 games; e.g. tape live_108910285 seat 0 seed 11 step 527 at [4, 8] (GOOSE y0 manure) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 12 | sell timing | STRAWBERRY | 1,129 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 13 | loss | overflow | 602 | opponent 883/game, hit in 33/83 games; e.g. tape live_108884658 seat 1 seed 12 step 623 | DROP timing and shed selling in market_orders() |
| 14 | loss | died_unwatered | 601 | opponent 150/game, hit in 81/83 games; e.g. tape live_108910285 seat 0 seed 11 step 311 at [0, 0] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 15 | sell timing | WOOL | 309 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | loss | fertilizer_uncollected | 222 | opponent 412/game, hit in 62/83 games; e.g. tape live_108910285 seat 0 seed 11 step 527 at [4, 8] (GOOSE y0 manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 17 | sell timing | WHEAT | 76 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 18 | sell timing | CARROT | 53 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | sell timing | EGG | 40 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | loss | stranded | 31 | opponent 39/game, hit in 13/83 games; e.g. tape live_108500554 seat 1 seed 18 step 719 | closing sell and DROP_FROM_STEP |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  38.3% |  49.3% |  12.4% |   0.0% |   0.0% |
| OPP |  45.5% |  43.3% |   9.3% |   1.9% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 7.0 | 601 | 1.8 | 150 | 81 |
| rotted | 0.6 | 27 | 5.8 | 316 | 17 |
| early_harvest | 160.2 | 6,228 | 122.2 | 4,718 | 83 |
| escaped | 2.8 | 1,318 | 4.2 | 2,240 | 70 |
| care_missed | 11.3 | 1,859 | 10.8 | 1,513 | 83 |
| fertilizer_uncollected | 6.0 | 222 | 11.7 | 412 | 62 |
| capped_yield | 0.0 | 0 | 1.5 | 211 | 0 |
| overflow | 6.4 | 602 | 10.8 | 883 | 33 |
| stranded | 0.3 | 31 | 0.7 | 39 | 13 |

Ground, tile-days per game (G / opp): crop 1073/1243, animal 309/350, empty 176/115, weed 5/10, empty_pen 107/22, unwatered 18/334, unfed 22/59

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 585 | 162 | 518 | 39 | 39 | 0.0 | 6,276 | 20,398 | 15.4 |
| STRAWBERRY | 417 | 151 | 212 | 164 | 167 | 10.2 | 24,774 | 35,396 | 10.7 |
| WOOL | 147 | 58 | 126 | 181 | 124 | 4.9 | 10,537 | 15,691 | 0.2 |
| MELON | 30 | 77 | 73 | 172 | 232 | 0.1 | 13,282 | 16,815 | 0.0 |
| TOMATO | 223 | 0 | 45 | 0 | 76 | 0.0 | 0 | 3,384 | 7.9 |
| FERTILIZER | 0 | 199 | 238 | 55 | 60 | 1.8 | 11,007 | 14,322 | 0.0 |
| CARROT | 248 | 70 | 116 | 39 | 37 | 0.0 | 2,760 | 4,272 | 2.0 |
| EGG | 245 | 86 | 73 | 55 | 50 | 0.0 | 4,740 | 3,676 | 0.1 |
| MILK | 403 | 205 | 176 | 176 | 160 | 7.2 | 36,108 | 28,247 | 3.8 |

Units sold on the same turn as the other farm sold the same good: G 230, opponent 237 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 3,320 | 3,022 |
| animal GOOSE | 1,146 | 683 |
| animal SHEEP | 3,012 | 3,193 |
| buy FERTILIZER | 0 | 1,736 |
| buy WHEAT | 4,048 | 9,793 |
| hire | 6,922 | 5,743 |
| land | 2,783 | 2,831 |
| seed CARROT | 814 | 865 |
| seed MELON | 1,133 | 1,000 |
| seed STRAWBERRY | 3,396 | 3,035 |
| seed TOMATO | 0 | 331 |
| seed WHEAT | 1,013 | 1,566 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 110 | 209 | +99 |
| 5 | 149 | 785 | +636 |
| 8 | 1,957 | 1,789 | -168 |
| 11 | 4,932 | 13,082 | +8,150 |
| 14 | 12,116 | 24,593 | +12,477 |
| 17 | 21,076 | 42,790 | +21,714 |
| 20 | 31,417 | 63,210 | +31,793 |
| 23 | 46,495 | 80,888 | +34,393 |
| 26 | 62,454 | 93,929 | +31,475 |

## Since the last inspection (2026-09-15 17:24, v13 baseline)

- margin -24,356 -> -26,506, wins 12/83 -> 10/83, G 89,332 -> 84,896
- paired on 59 games where the opponent replay stayed in step in both runs: margin -3,358 per game (median -3,640), better in 16, worse in 43
- paired on 83 identical games: margin -2,150 per game, better in 23, worse in 60; G's own score better in 18
- died_unwatered: 862 -> 601 coins/game
- early_harvest: 6,838 -> 6,228 coins/game
- escaped: 453 -> 1,318 coins/game
- care_missed: 1,636 -> 1,859 coins/game
- overflow: 517 -> 602 coins/game
- G idle share 9.5% -> 12.4%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
