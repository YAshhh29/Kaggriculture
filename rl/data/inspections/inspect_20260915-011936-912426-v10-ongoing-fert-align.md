# Inspection of Candidate G -- 2026-09-15 01:19

- G source `c3b25658b27a` at commit `4fa1a48`, overrides `{'ONGOING_FERT_ALIGN': True}`, label `v10 ongoing fert align`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T19:44 (0h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 88,672, opponent 114,574, margin -25,902, wins 13/96

27 games had an opponent replay refusing over 2% of its moves; on the other 69 G wins 1 with margin -34,473

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -43,338 | 1.4% |
| redblackbst | 8 | 0 | -42,278 | 0.7% |
| Unknown Mother-Goose | 8 | 0 | -40,606 | 0.0% |
| Mengfei Li | 8 | 0 | -33,925 | 1.1% |
| feel the agi | 8 | 0 | -32,813 | 0.8% |
| HowardLeeTW | 8 | 0 | -30,073 | 0.4% |
| Otter Vibe | 8 | 1 | -29,677 | 0.1% |
| ymg_aq | 8 | 1 | -24,107 | 1.4% |
| Majkel1337 | 8 | 2 | -17,243 | 2.8% |
| DSM | 8 | 2 | -15,080 | 2.7% |
| Orbital Terraformer | 8 | 4 | -4,783 | 4.3% |
| SpaTaro | 8 | 3 | +3,099 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 15,476 | G sells 155 at 39, opponent 545 at 39; town takes 588 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 9,280 | G sells 153 at 171, opponent 210 at 169; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,755 | opponent 5,044/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | TOMATO | 3,930 | G sells 0 at 0, opponent 50 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | WOOL | 3,864 | G sells 67 at 172, opponent 130 at 118; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | FERTILIZER | 3,449 | G sells 190 at 57, opponent 229 at 62; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | MELON | 2,630 | G sells 89 at 159, opponent 74 at 226; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | revenue gap | CARROT | 1,817 | G sells 68 at 38, opponent 123 at 36; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | loss (estimate) | care_missed | 1,500 | opponent 2,001/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 335 at [4, 0] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 10 | sell timing | MILK | 1,259 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | sell timing | STRAWBERRY | 986 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | loss | died_unwatered | 753 | opponent 176/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 311 at [1, 7] (MELON age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 13 | loss | stranded | 706 | opponent 37/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 14 | sell timing | WOOL | 426 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | loss | overflow | 285 | opponent 933/game, hit in 41/96 games; e.g. tape live_108884658 seat 1 seed 12 step 503 | DROP timing and shed selling in market_orders() |
| 16 | loss | escaped | 250 | opponent 2,577/game, hit in 32/96 games; e.g. tape live_108884658 seat 1 seed 12 step 575 at [8, 4] (GOOSE y1) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 17 | loss | fertilizer_uncollected | 165 | opponent 503/game, hit in 77/96 games; e.g. tape live_108910285 seat 0 seed 11 step 599 at [1, 3] (SHEEP y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 18 | sell timing | WHEAT | 78 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | sell timing | CARROT | 46 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | sell timing | EGG | 46 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  39.5% |  50.1% |  10.4% |   0.0% |   0.0% |
| OPP |  46.3% |  43.2% |   8.8% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 7.8 | 753 | 2.2 | 176 | 96 |
| rotted | 0.9 | 33 | 6.2 | 392 | 29 |
| early_harvest | 174.5 | 6,755 | 130.9 | 5,044 | 96 |
| escaped | 0.6 | 250 | 5.0 | 2,577 | 32 |
| care_missed | 9.4 | 1,500 | 16.3 | 2,001 | 96 |
| fertilizer_uncollected | 4.5 | 165 | 14.6 | 503 | 77 |
| capped_yield | 0.0 | 0 | 1.5 | 184 | 0 |
| overflow | 3.2 | 285 | 12.4 | 933 | 41 |
| stranded | 8.7 | 706 | 0.8 | 37 | 96 |

Ground, tile-days per game (G / opp): crop 1128/1252, animal 300/361, empty 251/109, weed 4/12, empty_pen 95/19, unwatered 23/349, unfed 15/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 588 | 155 | 545 | 39 | 39 | 0.0 | 6,041 | 21,518 | 14.4 |
| STRAWBERRY | 408 | 153 | 210 | 171 | 169 | 9.9 | 26,241 | 35,521 | 10.2 |
| TOMATO | 228 | 0 | 50 | 0 | 78 | 0.0 | 0 | 3,930 | 8.1 |
| WOOL | 156 | 67 | 130 | 172 | 118 | 6.1 | 11,550 | 15,414 | 0.1 |
| FERTILIZER | 0 | 190 | 229 | 57 | 62 | 0.2 | 10,776 | 14,225 | 0.0 |
| MELON | 30 | 89 | 74 | 159 | 226 | 0.7 | 14,095 | 16,725 | 0.0 |
| CARROT | 246 | 68 | 123 | 38 | 36 | 0.0 | 2,617 | 4,434 | 2.4 |
| EGG | 242 | 113 | 97 | 52 | 48 | 0.0 | 5,894 | 4,616 | 0.0 |
| MILK | 404 | 183 | 177 | 189 | 172 | 8.1 | 34,519 | 30,419 | 4.1 |

Units sold on the same turn as the other farm sold the same good: G 216, opponent 240 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,888 | 2,975 |
| animal GOOSE | 1,050 | 856 |
| animal SHEEP | 2,526 | 3,193 |
| buy FERTILIZER | 0 | 1,616 |
| buy WHEAT | 3,448 | 11,076 |
| hire | 6,696 | 5,743 |
| land | 2,812 | 2,938 |
| seed CARROT | 801 | 918 |
| seed MELON | 1,302 | 1,015 |
| seed STRAWBERRY | 3,456 | 2,995 |
| seed TOMATO | 0 | 363 |
| seed WHEAT | 1,081 | 1,540 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 223 | 154 | -69 |
| 5 | 486 | 693 | +207 |
| 8 | 1,376 | 1,590 | +214 |
| 11 | 8,814 | 14,796 | +5,982 |
| 14 | 13,393 | 25,634 | +12,242 |
| 17 | 24,581 | 42,522 | +17,940 |
| 20 | 31,418 | 62,218 | +30,799 |
| 23 | 52,423 | 80,576 | +28,154 |
| 26 | 67,954 | 95,691 | +27,736 |

## Since the last inspection (2026-09-15 00:40, v10 baseline)

- margin -25,882 -> -25,902, wins 15/96 -> 13/96, G 88,554 -> 88,672
- paired on 69 games where the opponent replay stayed in step in both runs: margin +435 per game (median +597), better in 41, worse in 28
- paired on 96 identical games: margin -20 per game, better in 51, worse in 45; G's own score better in 47
- died_unwatered: 867 -> 753 coins/game
- early_harvest: 6,914 -> 6,755 coins/game
- escaped: 501 -> 250 coins/game
- care_missed: 1,653 -> 1,500 coins/game
- overflow: 550 -> 285 coins/game
- G idle share 9.2% -> 10.4%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
