# Inspection of Candidate G -- 2026-09-14 23:14

- G source `391ff4efdd29` at commit `094ba3b`, overrides `{'FEED_PICKUP_TO_NEED': True, 'FEED_PICKUP_SPARE': 12}`, label `v8 pickup to need spare 12`
- 96 games against 12 opponents; match snapshot newest game 2026-09-14T15:02 (3h old)
- engine-model agreement 100.00% of turns (below 99% means the verdicts cannot be trusted)

## Scoreboard

G 84,821, opponent 115,863, margin -31,042, wins 11/96

27 games had an opponent replay refusing over 2% of its moves; on the other 69 G wins 1 with margin -40,246

| opponent | games | wins | margin | opponent replay no-op |
|---|---:|---:|---:|---:|
| Catalyst | 8 | 0 | -48,432 | 1.4% |
| redblackbst | 8 | 0 | -47,990 | 0.7% |
| Unknown Mother-Goose | 8 | 0 | -44,493 | 0.3% |
| Mengfei Li | 8 | 0 | -40,314 | 1.1% |
| feel the agi | 8 | 0 | -38,153 | 0.8% |
| Otter Vibe | 8 | 1 | -37,200 | 0.0% |
| HowardLeeTW | 8 | 0 | -33,938 | 0.2% |
| ymg_aq | 8 | 1 | -30,309 | 0.9% |
| Majkel1337 | 8 | 1 | -20,365 | 2.8% |
| DSM | 8 | 1 | -19,515 | 2.7% |
| Orbital Terraformer | 8 | 4 | -9,944 | 4.3% |
| SpaTaro | 8 | 3 | -1,848 | 4.7% |

## Findings, ranked by coins per game

| # | kind | what | G coins/game | detail | where in G |
|---:|---|---|---:|---|---|
| 1 | revenue gap | WHEAT | 10,753 | G sells 277 at 38, opponent 546 at 39; town takes 588 | crop and herd choice: CROP_TILES, herd_plan() |
| 2 | revenue gap | STRAWBERRY | 10,659 | G sells 145 at 172, opponent 210 at 169; town takes 408 | crop and herd choice: CROP_TILES, herd_plan() |
| 3 | loss (estimate) | early_harvest | 8,381 | opponent 5,018/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 51 at [3, 4] (WHEAT age2 y1) | harvest gate in job_value and HARVEST_HOLD |
| 4 | revenue gap | FERTILIZER | 4,692 | G sells 167 at 59, opponent 229 at 64; town takes 0 | crop and herd choice: CROP_TILES, herd_plan() |
| 5 | revenue gap | WOOL | 4,388 | G sells 65 at 174, opponent 130 at 120; town takes 156 | crop and herd choice: CROP_TILES, herd_plan() |
| 6 | revenue gap | TOMATO | 3,937 | G sells 0 at 0, opponent 50 at 78; town takes 228 | crop and herd choice: CROP_TILES, herd_plan() |
| 7 | revenue gap | MELON | 2,668 | G sells 88 at 160, opponent 74 at 226; town takes 30 | crop and herd choice: CROP_TILES, herd_plan() |
| 8 | loss | stranded | 2,188 | opponent 38/game, hit in 96/96 games; e.g. tape live_108910285 seat 0 seed 11 step 719 | closing sell and DROP_FROM_STEP |
| 9 | revenue gap | CARROT | 1,761 | G sells 70 at 38, opponent 123 at 36; town takes 246 | crop and herd choice: CROP_TILES, herd_plan() |
| 10 | sell timing | MILK | 1,189 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 11 | sell timing | STRAWBERRY | 1,002 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 12 | loss (estimate) | care_missed | 904 | opponent 2,049/game, hit in 88/96 games; e.g. tape live_108884658 seat 1 seed 12 step 311 at [7, 0] (GOOSE y0 fed) | CARE jobs (BAND_SERVICE) |
| 13 | loss | died_unwatered | 715 | opponent 174/game, hit in 94/96 games; e.g. tape live_108910285 seat 0 seed 11 step 311 at [2, 9] (CARROT age0 y1) | WATER jobs in job_value (BAND_WATER) and crew size (hands_target) |
| 14 | loss | overflow | 689 | opponent 917/game, hit in 55/96 games; e.g. tape live_108884658 seat 1 seed 12 step 503 | DROP timing and shed selling in market_orders() |
| 15 | sell timing | WOOL | 352 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 16 | loss | escaped | 322 | opponent 2,592/game, hit in 37/96 games; e.g. tape live_108884658 seat 1 seed 12 step 503 at [0, 8] (SHEEP y1) | FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration |
| 17 | sell timing | WHEAT | 219 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 18 | loss | fertilizer_uncollected | 143 | opponent 553/game, hit in 72/96 games; e.g. tape live_108884658 seat 1 seed 12 step 527 at [7, 1] (GOOSE y0 fed manure) | COLLECT_FERTILIZER jobs (BAND_SERVICE) |
| 19 | sell timing | CARROT | 48 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |
| 20 | sell timing | EGG | 45 | hindsight: best price in the next day minus the price taken; an upper bound | SELL timing and quantities in market_orders() |

## Labour: where worker-turns go

| | work | move | idle | no-op | phantom |
|---|---:|---:|---:|---:|---:|
| G |  40.7% |  49.2% |  10.1% |   0.0% |   0.0% |
| OPP |  46.3% |  43.2% |   8.8% |   1.7% |   0.0% |

G's moves the engine ignored:


## Losses per game

| loss | G units | G coins | opp units | opp coins | G games hit |
|---|---:|---:|---:|---:|---:|
| died_unwatered | 7.7 | 715 | 2.3 | 174 | 94 |
| rotted | 0.8 | 33 | 6.2 | 390 | 28 |
| early_harvest | 221.0 | 8,381 | 131.0 | 5,018 | 96 |
| escaped | 0.7 | 322 | 5.0 | 2,592 | 37 |
| care_missed | 5.6 | 904 | 16.4 | 2,049 | 88 |
| fertilizer_uncollected | 3.8 | 143 | 14.6 | 553 | 72 |
| capped_yield | 0.0 | 0 | 1.5 | 182 | 0 |
| overflow | 7.7 | 689 | 12.1 | 917 | 55 |
| stranded | 25.8 | 2,188 | 0.8 | 38 | 96 |

Ground, tile-days per game (G / opp): crop 1144/1253, animal 283/361, empty 249/108, weed 5/12, empty_pen 97/19, unwatered 23/349, unfed 10/54

## Market and the town's demand, per game

| good | town takes | G sold | opp sold | G price | opp price | G floor | G revenue | opp revenue | G open-book days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WHEAT | 588 | 277 | 546 | 38 | 39 | 0.0 | 10,608 | 21,361 | 4.6 |
| STRAWBERRY | 408 | 145 | 210 | 172 | 169 | 8.6 | 24,816 | 35,475 | 10.5 |
| FERTILIZER | 0 | 167 | 229 | 59 | 64 | 0.3 | 9,899 | 14,592 | 0.0 |
| WOOL | 156 | 65 | 130 | 174 | 120 | 5.9 | 11,241 | 15,629 | 0.1 |
| TOMATO | 228 | 0 | 50 | 0 | 78 | 0.0 | 0 | 3,937 | 8.1 |
| MELON | 30 | 88 | 74 | 160 | 226 | 0.4 | 14,032 | 16,700 | 0.0 |
| CARROT | 246 | 70 | 123 | 38 | 36 | 0.0 | 2,661 | 4,422 | 2.2 |
| MILK | 404 | 170 | 178 | 191 | 177 | 6.8 | 32,434 | 31,422 | 4.6 |
| EGG | 242 | 116 | 96 | 52 | 48 | 0.0 | 5,984 | 4,606 | 0.0 |

Units sold on the same turn as the other farm sold the same good: G 221, opponent 276 per game.

## Spending per game

| item | G | opponent |
|---|---:|---:|
| animal COW | 2,721 | 2,983 |
| animal GOOSE | 1,109 | 850 |
| animal SHEEP | 2,354 | 3,193 |
| buy FERTILIZER | 0 | 1,696 |
| buy WHEAT | 7,593 | 11,040 |
| hire | 6,428 | 5,743 |
| land | 2,812 | 2,938 |
| seed CARROT | 836 | 918 |
| seed MELON | 1,308 | 1,016 |
| seed STRAWBERRY | 3,482 | 2,999 |
| seed TOMATO | 0 | 364 |
| seed WHEAT | 1,211 | 1,541 |

## Money by day (median)

| day | G | opponent | gap |
|---:|---:|---:|---:|
| 2 | 133 | 154 | +21 |
| 5 | 543 | 724 | +180 |
| 8 | 524 | 1,598 | +1,075 |
| 11 | 9,071 | 14,816 | +5,744 |
| 14 | 12,755 | 25,686 | +12,931 |
| 17 | 24,024 | 43,165 | +19,141 |
| 20 | 30,576 | 62,669 | +32,092 |
| 23 | 50,794 | 81,700 | +30,906 |
| 26 | 65,840 | 96,561 | +30,722 |

## Since the last inspection (2026-09-14 22:52, v8 baseline)

- margin -33,408 -> -31,042, wins 11/96 -> 11/96, G 81,842 -> 84,821
- paired on 69 games where the opponent replay stayed in step in both runs: margin +1,756 per game (median +1,275), better in 41, worse in 28
- paired on 96 identical games: margin +2,366 per game, better in 60, worse in 36; G's own score better in 63
- died_unwatered: 1,062 -> 715 coins/game
- early_harvest: 14,814 -> 8,381 coins/game
- escaped: 35 -> 322 coins/game
- overflow: 3,849 -> 689 coins/game
- stranded: 1,605 -> 2,188 coins/game
- G idle share 9.1% -> 10.1%
- G noop share 0.0% -> 0.0%

## Caveats

- Opponents are replayed tapes: they cannot react to G, so anything G does to the market is felt by a farm that cannot adapt.
- A tape replayed on a seed it was not recorded on drifts; the opponent no-op column above says how far.
- Early-harvest, care and open-book coins are estimates of what was available, not of what a different decision would certainly have earned. Rot, escapes, deaths, overflow and stranded goods are exact.
- Drill into any example with `python -m tools.eval.inspect_g --drill EPISODE --seat S --seed SEED --from STEP --to STEP`.
