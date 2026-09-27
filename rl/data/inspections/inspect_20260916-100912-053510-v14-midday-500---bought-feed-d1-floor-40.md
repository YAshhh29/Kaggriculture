# Inspection of Candidate G -- 2026-09-16 10:09

- G source `5fa803543462` at commit `8d46c3a`, overrides `{'FEED_STOCK_DAYS': 1, 'FEED_BUY_UNTIL': 29, 'FEED_STOCK_FLOOR': 400}`, label `v14 midday 500 + bought feed d1 floor 400`
- 65 games against 12 opponents; match snapshot newest game 2026-09-15T12:47 (16h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 88,737, opponent 114,740, margin -26,003, wins 8/65

19 games had an opponent replay refusing over 2% of its moves; on the other 46 G wins 1 with margin -37,242

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 4 | 0 | -51,711 | 1.5% |
| Artem The Farmer 🍅 | 3 | 0 | -49,151 | 0.4% |
| Cow Boy | 6 | 0 | -45,736 | 0.7% |
| Zhenghongshuang | 6 | 0 | -42,422 | 0.6% |
| HowardLeeTW | 6 | 0 | -37,833 | 0.1% |
| DSM | 4 | 1 | -27,096 | 2.4% |
| Otter Vibe | 6 | 1 | -25,899 | 0.2% |
| Mengfei Li | 6 | 1 | -22,592 | 3.3% |
| ymg_aq | 6 | 0 | -20,877 | 0.2% |
| Majkel1337 | 6 | 1 | -9,256 | 3.0% |
| SpaTaro | 6 | 2 | -336 | 3.8% |
| Orbital Terraformer | 6 | 2 | +364 | 5.5% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | STRAWBERRY | 10,181 | G sells 157 at 191, opponent 214 at 187; town takes 467 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | loss | overflow | 6,101 | opponent 898/game, hit in 61/65 games; e.g. tape live_108910285 seat 0 seed 11 step 359 | DROP timing and shed selling in market_orders() |
| 3 | loss (estimate) | early_harvest | 5,750 | opponent 5,067/game, hit in 65/65 games; e.g. tape live_108910285 seat 0 seed 11 step 100 at [2, 4] (WHEAT age4 y3) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | WHEAT | 4,795 | G sells 409 at 40, opponent 525 at 40; town takes 600 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | MELON | 3,979 | G sells 74 at 172, opponent 73 at 228; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | TOMATO | 3,160 | G sells 0 at 0, opponent 45 at 70; town takes 199 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | FERTILIZER | 3,065 | G sells 193 at 57, opponent 235 at 60; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | revenue gap | CARROT | 2,171 | G sells 59 at 39, opponent 121 at 37; town takes 238 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | loss | died_unwatered | 1,397 | opponent 138/game, hit in 65/65 games; e.g. tape live_108910285 seat 0 seed 11 step 23 at [0, 1] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 10 | revenue gap | WOOL | 1,235 | G sells 70 at 148, opponent 122 at 95; town takes 125 | crop and herd choice: CROP_TILES, herd_plan() |
| 11 | sell timing | STRAWBERRY | 1,066 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | loss (estimate) | care_missed | 996 | opponent 1,283/game, hit in 56/65 games; e.g. tape live_108910285 seat 0 seed 11 step 623 at [4, 2] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 13 | sell timing | MILK | 983 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 14 | sell timing | WOOL | 522 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | sell timing | WHEAT | 313 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | loss | escaped | 296 | opponent 2,027/game, hit in 25/65 games; e.g. tape live_108610498 seat 1 seed 16 step 599 at [3, 7] (SHEEP y1) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 17 | loss | fertilizer_uncollected | 156 | opponent 370/game, hit in 46/65 games; e.g. tape live_108884658 seat 1 seed 12 step 503 at [3, 4] (SHEEP y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 18 | loss | rotted | 101 | opponent 334/game, hit in 38/65 games; e.g. tape live_108910285 seat 0 seed 11 step 312 at [9, 0] (CARROT age4 y2) | harvest timing: HARVEST_HOLD and BAND_HARVEST |
| 19 | sell timing | EGG | 61 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | sell timing | CARROT | 37 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  41.4% |  50.8% |   7.9% |   0.0% |   0.0% |
| OPP |  46.1% |  43.4% |   8.6% |   1.9% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 12.1 | 1,397 | 1.8 | 138 | 65 |
| rotted | 2.3 | 101 | 5.8 | 334 | 38 |
| early_harvest | 142.8 | 5,750 | 126.6 | 5,067 | 65 |
| escaped | 0.7 | 296 | 3.9 | 2,027 | 25 |
| care_missed | 7.2 | 996 | 10.4 | 1,283 | 56 |
| fertilizer_uncollected | 4.2 | 156 | 10.7 | 370 | 46 |
| capped_yield | 0.0 | 0 | 1.6 | 165 | 0 |
| overflow | 75.7 | 6,101 | 11.0 | 898 | 61 |
| stranded | 0.2 | 9 | 0.9 | 44 | 8 |

Ground, tile-days per game (G / opp): crop 1124/1260, animal 323/349, empty 284/112, weed 13/10, empty_pen 81/21, unwatered 31/337, unfed 8/58

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| STRAWBERRY | 467 | 157 | 214 | 191 | 187 | 1.8 | 29,850 | 40,031 | 9.6 |
| WHEAT | 600 | 409 | 525 | 40 | 40 | 0.0 | 16,469 | 21,263 | 6.8 |
| MELON | 30 | 74 | 73 | 172 | 228 | 0.4 | 12,763 | 16,742 | 0.0 |
| TOMATO | 199 | 0 | 45 | 0 | 70 | 0.0 | 0 | 3,160 | 7.1 |
| FERTILIZER | 0 | 193 | 235 | 57 | 60 | 2.2 | 10,934 | 13,999 | 0.0 |
| CARROT | 238 | 59 | 121 | 39 | 37 | 0.0 | 2,328 | 4,498 | 2.8 |
| WOOL | 125 | 70 | 122 | 148 | 95 | 10.5 | 10,394 | 11,629 | 0.1 |
| MILK | 392 | 179 | 183 | 187 | 166 | 6.5 | 33,406 | 30,347 | 5.0 |
| EGG | 268 | 154 | 72 | 51 | 48 | 0.0 | 7,881 | 3,495 | 0.0 |

Units sold on the same turn as the other farm sold the same good: G 279, opponent 278 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,880 | 3,083 |
| animal GOOSE | 1,311 | 669 |
| animal SHEEP | 2,385 | 2,938 |
| buy FERTILIZER | 0 | 1,639 |
| buy WHEAT | 15,195 | 9,936 |
| hire | 6,741 | 5,543 |
| land | 3,000 | 2,815 |
| seed CARROT | 760 | 903 |
| seed MELON | 1,394 | 1,002 |
| seed STRAWBERRY | 3,592 | 3,014 |
| seed TOMATO | 0 | 324 |
| seed WHEAT | 1,029 | 1,556 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 247 | 197 | -50 |
| 5 | 610 | 791 | +181 |
| 8 | 1,014 | 1,675 | +661 |
| 11 | 8,576 | 13,165 | +4,589 |
| 14 | 14,228 | 25,332 | +11,104 |
| 17 | 25,363 | 42,173 | +16,810 |
| 20 | 34,914 | 63,774 | +28,860 |
| 23 | 53,356 | 82,303 | +28,947 |
| 26 | 68,321 | 93,324 | +25,003 |

## Since the last inspection (2026-09-15 22:45, v14 midday drop 500)

- margin -21,181 -> -26,003, wins 14/83 -> 8/65, G 90,929 -> 88,737
- paired on 45 games where the opponent replay stayed in step in both runs: margin -5,985 per game (median -6,251), better in 7, worse in 38
- paired on 65 identical games: margin -5,360 per game, better in 14, worse in 51; G's own score better in 14
- rotted: 50 -> 101 coins/game
- early_harvest: 5,838 -> 5,750 coins/game
- overflow: 776 -> 6,101 coins/game
- G idle share 7.6% -> 7.9%
- G noop share 0.0% -> 0.0%
- the opponent field differs from last time, so these deltas mix a change in G with a change in opponents

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
