# Inspection of Candidate G -- 2026-09-15 11:53

- G source `1868f151334f` at commit `88544be`, overrides `{'PLANT_CLAIM_WALKING': True}`, label `v11 plant claim walking`
- 92 games against 12 opponents; match snapshot newest game 2026-09-14T19:44 (11h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 88,762, opponent 112,742, margin -23,981, wins 15/92

26 games had an opponent replay refusing over 2% of its moves; on the other 66 G wins 2 with margin -34,462

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -44,237 | 1.4% |
| redblackbst | 8 | 0 | -41,637 | 0.7% |
| Artem The Farmer 🍅 | 4 | 0 | -38,848 | 0.1% |
| Mengfei Li | 8 | 0 | -34,566 | 1.1% |
| feel the agi | 8 | 0 | -32,798 | 0.8% |
| Otter Vibe | 8 | 1 | -31,472 | 0.1% |
| HowardLeeTW | 8 | 0 | -29,588 | 0.1% |
| ymg_aq | 8 | 1 | -20,736 | 1.4% |
| Majkel1337 | 8 | 2 | -17,163 | 2.8% |
| Orbital Terraformer | 8 | 4 | -4,761 | 4.8% |
| DSM | 8 | 3 | -2,802 | 4.4% |
| SpaTaro | 8 | 4 | +3,408 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 15,124 | G sells 164 at 39, opponent 548 at 39; town takes 587 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 8,131 | G sells 163 at 166, opponent 210 at 167; town takes 411 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,643 | opponent 4,872/game, hit in 92/92 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | TOMATO | 3,647 | G sells 0 at 0, opponent 48 at 76; town takes 226 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | FERTILIZER | 3,502 | G sells 184 at 58, opponent 229 at 62; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | WOOL | 3,438 | G sells 68 at 173, opponent 130 at 117; town takes 153 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | MELON | 2,005 | G sells 91 at 160, opponent 73 at 226; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | revenue gap | CARROT | 1,707 | G sells 67 at 39, opponent 116 at 37; town takes 247 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | loss (estimate) | care_missed | 1,326 | opponent 1,830/game, hit in 91/92 games; e.g. tape live_108910285 seat 0 seed 11 step 239 at [6, 1] (GOOSE y0 fed) | CARE jobs (BAND_SERVICE) |
| 10 | sell timing | MILK | 1,202 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | sell timing | STRAWBERRY | 1,152 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | loss | died_unwatered | 905 | opponent 158/game, hit in 92/92 games; e.g. tape live_108910285 seat 0 seed 11 step 23 at [0, 4] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 13 | loss | stranded | 814 | opponent 42/game, hit in 92/92 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 14 | loss | overflow | 525 | opponent 866/game, hit in 41/92 games; e.g. tape live_108884658 seat 1 seed 12 step 503 | DROP timing and shed selling in market_orders() |
| 15 | sell timing | WOOL | 436 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | loss | escaped | 428 | opponent 2,635/game, hit in 45/92 games; e.g. tape live_108884658 seat 1 seed 12 step 455 at [4, 8] (SHEEP y1) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 17 | loss | fertilizer_uncollected | 165 | opponent 523/game, hit in 70/92 games; e.g. tape live_108910285 seat 0 seed 11 step 623 at [4, 0] (COW y0 fed cared manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 18 | sell timing | WHEAT | 81 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | loss | rotted | 51 | opponent 376/game, hit in 31/92 games; e.g. tape live_108884658 seat 1 seed 12 step 552 at [1, 9] (CARROT age4 y2) | harvest timing: HARVEST_HOLD and BAND_HARVEST |
| 20 | sell timing | EGG | 45 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  40.4% |  49.3% |  10.3% |   0.0% |   0.0% |
| OPP |  45.7% |  43.4% |   9.0% |   1.9% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 9.9 | 905 | 2.0 | 158 | 92 |
| rotted | 1.1 | 51 | 6.0 | 376 | 31 |
| early_harvest | 172.2 | 6,643 | 126.7 | 4,872 | 92 |
| escaped | 0.9 | 428 | 5.0 | 2,635 | 45 |
| care_missed | 8.5 | 1,326 | 14.8 | 1,830 | 91 |
| fertilizer_uncollected | 4.7 | 165 | 15.0 | 523 | 70 |
| capped_yield | 0.0 | 0 | 1.5 | 179 | 0 |
| overflow | 5.9 | 525 | 11.2 | 866 | 41 |
| stranded | 8.6 | 814 | 1.0 | 42 | 92 |

Ground, tile-days per game (G / opp): crop 1170/1238, animal 302/355, empty 260/113, weed 6/13, empty_pen 86/20, unwatered 25/333, unfed 20/51

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 587 | 164 | 548 | 39 | 39 | 0.0 | 6,382 | 21,506 | 14.6 |
| STRAWBERRY | 411 | 163 | 210 | 166 | 167 | 10.3 | 27,021 | 35,152 | 10.1 |
| TOMATO | 226 | 0 | 48 | 0 | 76 | 0.0 | 0 | 3,647 | 8.1 |
| FERTILIZER | 0 | 184 | 229 | 58 | 62 | 0.4 | 10,660 | 14,162 | 0.0 |
| WOOL | 153 | 68 | 130 | 173 | 117 | 5.9 | 11,791 | 15,229 | 0.1 |
| MELON | 30 | 91 | 73 | 160 | 226 | 0.5 | 14,478 | 16,483 | 0.0 |
| CARROT | 247 | 67 | 116 | 39 | 37 | 0.0 | 2,603 | 4,310 | 2.3 |
| EGG | 243 | 115 | 87 | 52 | 48 | 0.0 | 6,013 | 4,178 | 0.0 |
| MILK | 403 | 177 | 179 | 187 | 172 | 7.6 | 33,073 | 30,760 | 4.2 |

Units sold on the same turn as the other farm sold the same good: G 222, opponent 245 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,865 | 3,017 |
| animal GOOSE | 1,109 | 783 |
| animal SHEEP | 2,429 | 3,201 |
| buy FERTILIZER | 0 | 1,618 |
| buy WHEAT | 3,365 | 11,558 |
| hire | 6,633 | 5,836 |
| land | 3,000 | 2,870 |
| seed CARROT | 809 | 885 |
| seed MELON | 1,334 | 1,003 |
| seed STRAWBERRY | 3,623 | 3,012 |
| seed TOMATO | 0 | 351 |
| seed WHEAT | 1,093 | 1,552 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 223 | 154 | -69 |
| 5 | 552 | 697 | +144 |
| 8 | 1,200 | 1,568 | +368 |
| 11 | 8,483 | 13,732 | +5,248 |
| 14 | 12,479 | 24,844 | +12,366 |
| 17 | 23,134 | 42,770 | +19,636 |
| 20 | 34,349 | 63,222 | +28,874 |
| 23 | 52,715 | 81,844 | +29,128 |
| 26 | 68,542 | 95,184 | +26,643 |

## Since the last inspection (2026-09-15 11:23, v11 baseline)

- margin -26,186 -> -23,981, wins 15/92 -> 15/92, G 85,661 -> 88,762
- paired on 66 games where the opponent replay stayed in step in both runs: margin +847 per game (median +736), better in 35, worse in 31
- paired on 92 identical games: margin +2,205 per game, better in 50, worse in 42; G's own score better in 49
- died_unwatered: 1,404 -> 905 coins/game
- rotted: 126 -> 51 coins/game
- early_harvest: 6,761 -> 6,643 coins/game
- escaped: 1,033 -> 428 coins/game
- care_missed: 1,646 -> 1,326 coins/game
- fertilizer_uncollected: 267 -> 165 coins/game
- stranded: 892 -> 814 coins/game
- G idle share 9.4% -> 10.3%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
