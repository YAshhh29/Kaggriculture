# Inspection of Candidate G -- 2026-09-16 10:03

- G source `48a3c9d30a9f` at commit `815344d`, overrides `{'FEED_STOCK_DAYS': 2, 'FEED_BUY_UNTIL': 29, 'FEED_STOCK_FLOOR': 150}`, label `v14 midday 500 + bought feed d2 all season`
- 65 games against 12 opponents; match snapshot newest game 2026-09-15T12:47 (16h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 88,620, opponent 116,640, margin -28,020, wins 8/65

19 games had an opponent replay refusing over 2% of its moves; on the other 46 G wins 1 with margin -38,688

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 4 | 0 | -53,758 | 1.5% |
| Cow Boy | 6 | 0 | -49,563 | 0.7% |
| Zhenghongshuang | 6 | 0 | -45,501 | 0.6% |
| Artem The Farmer 🍅 | 3 | 0 | -43,136 | 1.9% |
| HowardLeeTW | 6 | 0 | -36,511 | 0.1% |
| Mengfei Li | 6 | 1 | -32,016 | 3.0% |
| Otter Vibe | 6 | 1 | -28,907 | 0.2% |
| DSM | 4 | 1 | -27,042 | 3.2% |
| ymg_aq | 6 | 0 | -18,890 | 0.9% |
| Majkel1337 | 6 | 1 | -13,244 | 3.0% |
| SpaTaro | 6 | 1 | -7,142 | 2.6% |
| Orbital Terraformer | 6 | 3 | +3,661 | 6.1% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | STRAWBERRY | 11,772 | G sells 150 at 196, opponent 213 at 192; town takes 467 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | loss | overflow | 6,732 | opponent 893/game, hit in 57/65 games; e.g. tape live_108884658 seat 1 seed 12 step 311 | DROP timing and shed selling in market_orders() |
| 3 | loss (estimate) | early_harvest | 5,865 | opponent 4,873/game, hit in 65/65 games; e.g. tape live_108910285 seat 0 seed 11 step 86 at [0, 1] (CARROT age3 y2) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | FERTILIZER | 3,875 | G sells 174 at 60, opponent 233 at 61; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | MELON | 3,315 | G sells 80 at 167, opponent 73 at 229; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | TOMATO | 3,080 | G sells 0 at 0, opponent 44 at 70; town takes 199 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | CARROT | 2,171 | G sells 61 at 38, opponent 121 at 37; town takes 238 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | revenue gap | WOOL | 1,454 | G sells 66 at 157, opponent 122 at 96; town takes 125 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | loss | died_unwatered | 961 | opponent 123/game, hit in 65/65 games; e.g. tape live_108910285 seat 0 seed 11 step 311 at [2, 7] (MELON age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 10 | sell timing | STRAWBERRY | 950 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | sell timing | MILK | 902 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | loss (estimate) | care_missed | 781 | opponent 1,340/game, hit in 60/65 games; e.g. tape live_108884658 seat 1 seed 12 step 551 at [6, 4] (GOOSE y0 fed manure) | CARE jobs (BAND_SERVICE) |
| 13 | sell timing | WHEAT | 692 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 14 | sell timing | WOOL | 358 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 15 | loss | escaped | 148 | opponent 2,050/game, hit in 16/65 games; e.g. tape live_108884658 seat 1 seed 12 step 191 at [6, 4] (GOOSE y0) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 16 | loss | fertilizer_uncollected | 129 | opponent 402/game, hit in 42/65 games; e.g. tape live_108884658 seat 1 seed 12 step 503 at [2, 4] (SHEEP y0 fed cared manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 17 | loss | rotted | 119 | opponent 343/game, hit in 45/65 games; e.g. tape live_108910285 seat 0 seed 11 step 696 at [1, 9] (CARROT age4 y2) | harvest timing: HARVEST_HOLD and BAND_HARVEST |
| 18 | sell timing | EGG | 61 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | sell timing | CARROT | 37 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | loss | stranded | 34 | opponent 41/game, hit in 12/65 games; e.g. tape live_108694097 seat 1 seed 14 step 719 | closing sell and DROP_FROM_STEP |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  40.5% |  49.7% |   9.8% |   0.0% |   0.0% |
| OPP |  45.6% |  43.4% |   9.0% |   2.0% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 9.8 | 961 | 1.6 | 123 | 65 |
| rotted | 2.9 | 119 | 5.7 | 343 | 45 |
| early_harvest | 146.8 | 5,865 | 124.0 | 4,873 | 65 |
| escaped | 0.3 | 148 | 4.0 | 2,050 | 16 |
| care_missed | 4.6 | 781 | 10.3 | 1,340 | 60 |
| fertilizer_uncollected | 3.4 | 129 | 10.7 | 402 | 42 |
| capped_yield | 0.0 | 0 | 1.6 | 169 | 0 |
| overflow | 78.6 | 6,732 | 10.7 | 893 | 57 |
| stranded | 0.3 | 34 | 0.8 | 41 | 12 |

Ground, tile-days per game (G / opp): crop 1140/1248, animal 298/345, empty 300/112, weed 10/10, empty_pen 76/21, unwatered 31/334, unfed 7/58

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| STRAWBERRY | 467 | 150 | 213 | 196 | 192 | 1.1 | 29,281 | 41,053 | 11.1 |
| FERTILIZER | 0 | 174 | 233 | 60 | 61 | 0.2 | 10,424 | 14,299 | 0.0 |
| MELON | 30 | 80 | 73 | 167 | 229 | 0.2 | 13,382 | 16,697 | 0.0 |
| TOMATO | 199 | 0 | 44 | 0 | 70 | 0.0 | 0 | 3,080 | 7.1 |
| CARROT | 238 | 61 | 121 | 38 | 37 | 0.0 | 2,310 | 4,481 | 2.9 |
| WOOL | 125 | 66 | 122 | 157 | 96 | 8.8 | 10,311 | 11,765 | 0.2 |
| MILK | 392 | 167 | 178 | 194 | 176 | 5.0 | 32,514 | 31,381 | 6.5 |
| EGG | 268 | 143 | 71 | 51 | 49 | 0.0 | 7,320 | 3,473 | 0.0 |
| WHEAT | 600 | 741 | 520 | 38 | 40 | 0.0 | 28,507 | 20,857 | 0.0 |

Units sold on the same turn as the other farm sold the same good: G 303, opponent 306 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,775 | 3,071 |
| animal GOOSE | 1,135 | 674 |
| animal SHEEP | 2,200 | 2,946 |
| buy FERTILIZER | 0 | 1,721 |
| buy WHEAT | 26,108 | 9,948 |
| hire | 6,521 | 5,544 |
| land | 3,000 | 2,754 |
| seed CARROT | 815 | 902 |
| seed MELON | 1,332 | 996 |
| seed STRAWBERRY | 3,489 | 3,011 |
| seed TOMATO | 0 | 324 |
| seed WHEAT | 1,053 | 1,556 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 616 | 196 | -420 |
| 5 | 552 | 796 | +244 |
| 8 | 869 | 1,702 | +833 |
| 11 | 8,060 | 13,163 | +5,103 |
| 14 | 13,341 | 25,229 | +11,888 |
| 17 | 24,947 | 42,394 | +17,447 |
| 20 | 31,374 | 64,067 | +32,693 |
| 23 | 49,793 | 83,618 | +33,825 |
| 26 | 66,125 | 95,036 | +28,911 |

## Since the last inspection (2026-09-15 22:45, v14 midday drop 500)

- margin -21,181 -> -28,020, wins 14/83 -> 8/65, G 90,929 -> 88,620
- paired on 44 games where the opponent replay stayed in step in both runs: margin -8,637 per game (median -7,806), better in 3, worse in 41
- paired on 65 identical games: margin -7,376 per game, better in 11, worse in 54; G's own score better in 21
- died_unwatered: 1,419 -> 961 coins/game
- rotted: 50 -> 119 coins/game
- escaped: 329 -> 148 coins/game
- care_missed: 1,003 -> 781 coins/game
- overflow: 776 -> 6,732 coins/game
- G idle share 7.6% -> 9.8%
- G noop share 0.0% -> 0.0%
- the opponent field differs from last time, so these deltas mix a change in G with a change in opponents

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
