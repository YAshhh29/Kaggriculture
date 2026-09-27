# Inspection of Candidate G -- 2026-09-15 00:23

- G source `c58503bf3054` at commit `36957bf`, overrides `{'DROP_SHARES_SHED': True, 'CLOSE_ONLY_GOODS_FROM_STEP': 696}`, label `v9 drop shares + goods only`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T15:02 (4h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 88,554, opponent 114,436, margin -25,882, wins 15/96

27 games had an opponent replay refusing over 2% of its moves; on the other 69 G wins 2 with margin -34,908

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -44,378 | 1.4% |
| redblackbst | 8 | 0 | -41,968 | 0.7% |
| Unknown Mother-Goose | 8 | 0 | -41,091 | 0.0% |
| Mengfei Li | 8 | 0 | -33,344 | 1.1% |
| Otter Vibe | 8 | 1 | -32,550 | 0.1% |
| HowardLeeTW | 8 | 0 | -32,366 | 0.4% |
| feel the agi | 8 | 0 | -31,405 | 0.8% |
| ymg_aq | 8 | 1 | -24,120 | 1.4% |
| Majkel1337 | 8 | 3 | -15,730 | 2.8% |
| DSM | 8 | 2 | -14,850 | 2.7% |
| Orbital Terraformer | 8 | 4 | -1,901 | 4.3% |
| SpaTaro | 8 | 4 | +3,121 | 4.6% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 15,504 | G sells 154 at 39, opponent 545 at 39; town takes 588 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 8,732 | G sells 157 at 168, opponent 210 at 168; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 6,914 | opponent 5,062/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | WOOL | 4,708 | G sells 62 at 176, opponent 130 at 121; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | TOMATO | 3,932 | G sells 0 at 0, opponent 50 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | FERTILIZER | 3,325 | G sells 191 at 57, opponent 229 at 62; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | MELON | 2,315 | G sells 91 at 158, opponent 74 at 225; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | revenue gap | CARROT | 1,890 | G sells 67 at 39, opponent 123 at 36; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 9 | loss (estimate) | care_missed | 1,653 | opponent 2,010/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 239 at [6, 1] (COW y0 fed) | CARE jobs (BAND_SERVICE) |
| 10 | sell timing | MILK | 1,298 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | sell timing | STRAWBERRY | 1,066 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | loss | died_unwatered | 867 | opponent 176/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 335 at [3, 5] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 13 | loss | stranded | 693 | opponent 37/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 14 | loss | overflow | 550 | opponent 930/game, hit in 51/96 games; e.g. tape live_108884658 seat 1 seed 12 step 503 | DROP timing and shed selling in market_orders() |
| 15 | loss | escaped | 501 | opponent 2,572/game, hit in 43/96 games; e.g. tape live_108884658 seat 1 seed 12 step 335 at [3, 7] (SHEEP y0) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 16 | sell timing | WOOL | 344 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 17 | loss | fertilizer_uncollected | 197 | opponent 504/game, hit in 87/96 games; e.g. tape live_108910285 seat 0 seed 11 step 671 at [1, 3] (SHEEP y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 18 | sell timing | WHEAT | 76 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 19 | sell timing | EGG | 46 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | loss | rotted | 45 | opponent 395/game, hit in 38/96 games; e.g. tape live_108931876 seat 1 seed 12 step 624 at [8, 3] (CARROT age4 y2) | harvest timing: HARVEST_HOLD and BAND_HARVEST |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  40.3% |  50.5% |   9.2% |   0.0% |   0.0% |
| OPP |  46.3% |  43.2% |   8.8% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 9.0 | 867 | 2.2 | 176 | 96 |
| rotted | 1.1 | 45 | 6.2 | 395 | 38 |
| early_harvest | 178.2 | 6,914 | 130.9 | 5,062 | 96 |
| escaped | 1.0 | 501 | 5.0 | 2,572 | 43 |
| care_missed | 10.4 | 1,653 | 16.4 | 2,010 | 96 |
| fertilizer_uncollected | 5.7 | 197 | 14.6 | 504 | 87 |
| capped_yield | 0.0 | 0 | 1.5 | 180 | 0 |
| overflow | 6.1 | 550 | 12.3 | 930 | 51 |
| stranded | 8.1 | 693 | 0.8 | 37 | 96 |

Ground, tile-days per game (G / opp): crop 1158/1252, animal 306/361, empty 255/109, weed 6/12, empty_pen 94/19, unwatered 25/349, unfed 18/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 588 | 154 | 545 | 39 | 39 | 0.0 | 6,030 | 21,534 | 14.6 |
| STRAWBERRY | 408 | 157 | 210 | 168 | 168 | 8.7 | 26,412 | 35,143 | 10.1 |
| WOOL | 156 | 62 | 130 | 176 | 121 | 4.7 | 11,006 | 15,714 | 0.1 |
| TOMATO | 228 | 0 | 50 | 0 | 78 | 0.0 | 0 | 3,932 | 8.1 |
| FERTILIZER | 0 | 191 | 229 | 57 | 62 | 0.1 | 10,874 | 14,199 | 0.0 |
| MELON | 30 | 91 | 74 | 158 | 225 | 0.5 | 14,345 | 16,660 | 0.0 |
| CARROT | 246 | 67 | 123 | 39 | 36 | 0.0 | 2,567 | 4,457 | 2.3 |
| EGG | 242 | 116 | 97 | 52 | 48 | 0.0 | 6,045 | 4,638 | 0.0 |
| MILK | 404 | 188 | 177 | 186 | 172 | 8.8 | 35,006 | 30,395 | 4.1 |

Units sold on the same turn as the other farm sold the same good: G 220, opponent 247 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 3,125 | 2,975 |
| animal GOOSE | 1,122 | 856 |
| animal SHEEP | 2,443 | 3,193 |
| buy FERTILIZER | 0 | 1,629 |
| buy WHEAT | 3,541 | 11,071 |
| hire | 6,698 | 5,743 |
| land | 2,979 | 2,938 |
| seed CARROT | 808 | 918 |
| seed MELON | 1,340 | 1,015 |
| seed STRAWBERRY | 3,581 | 2,995 |
| seed TOMATO | 0 | 363 |
| seed WHEAT | 1,094 | 1,540 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 223 | 154 | -69 |
| 5 | 486 | 693 | +207 |
| 8 | 979 | 1,585 | +606 |
| 11 | 8,777 | 14,788 | +6,012 |
| 14 | 12,924 | 25,630 | +12,706 |
| 17 | 24,750 | 42,568 | +17,818 |
| 20 | 33,480 | 62,321 | +28,841 |
| 23 | 52,552 | 80,544 | +27,992 |
| 26 | 67,146 | 95,140 | +27,994 |

## Since the last inspection (2026-09-14 23:31, v9 baseline)

- margin -27,429 -> -25,882, wins 13/96 -> 15/96, G 86,928 -> 88,554
- paired on 69 games where the opponent replay stayed in step in both runs: margin +1,324 per game (median +1,396), better in 60, worse in 9
- paired on 96 identical games: margin +1,547 per game, better in 83, worse in 13; G's own score better in 87
- overflow: 410 -> 550 coins/game
- stranded: 2,234 -> 693 coins/game
- G idle share 9.2% -> 9.2%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
