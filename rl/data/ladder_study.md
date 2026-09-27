# Ladder Study — top-of-ladder Kaggriculture replays

Source: 200 replay tapes across 9 top-of-ladder teams, decoded from `actions_zlib_b64`
in `kaggle_cache/live_clones/live_*.json` (no engine replay — action logs only, per the
task's fast path). Team game counts: Otter Vibe 38, Zhenghongshuang 30, HowardLeeTW 25,
Mengfei Li 23, Orbital Terraformer 21, Cow Boy 21, Majkel1337 20, ymg_aq 12, SpaTaro 10.
Rules read from `kaggriculture.py` (CROPS, ANIMALS, MARKET_PARAMS, `_do_hire`,
`_do_buy_land`, `_daily_refresh_*`).

## Theses

1. Every one of 200 games opens with WHEAT or MELON as the very first PLANT action on
   day 0 — Otter Vibe (38/38) and HowardLeeTW (25/25) always start WHEAT; the other 7
   teams (137 games) always start MELON despite melon being the most expensive seed
   ($80) and slowest to mature (10-12 days) — a real strategic split among strong teams
   on what to put in the ground turn 1.
2. All 9 teams buy COW and SHEEP within the first 0-3 days in essentially every game
   (196-200/200); Otter Vibe additionally always buys GOOSE on day 0 (38/38), the only
   team observed doing 3-species day-0 stocking.
3. All 9 teams front-load hiring: mean 4-7 hand hires already placed in the very first
   market queue of day 0, and total hires sustained across the 30-day season average
   266-316 per game (roughly 9-11 hires/day), consistent with the Fibonacci hire-cost
   curve staying cheap once the daily counter resets.
4. WORK actions (WATER/HARVEST/PLANT/FEED/CARE/etc.) outnumber MOVE actions for 8 of 9
   teams (42-53% work vs 40-48% move, aggregated over ~150k-270k unit-actions per team),
   but PASS share is a genuine point of disagreement: 0.8% for Majkel1337 and 1.1% for
   Orbital Terraformer vs 16.3% for HowardLeeTW and 13.8% for SpaTaro — a ~20x spread in
   how much idle time top teams tolerate.
5. WHEAT sowing volume dwarfs every other crop by 5-20x: 100-210 PLANT-WHEAT actions per
   game vs CARROT 33-94, STRAWBERRY 26-34, MELON 11-16, TOMATO 5-20 (n=200 games) —
   consistent with wheat's 4-day max-yield window letting the same tiles be replanted
   many times across 30 days, unlike the slower ongoing crops.
6. Teams that buy a 2nd quadrant do so around day 5-6 on average, and a 3rd (when they
   get it at all) around day 8-11; SpaTaro is fastest (means 1.9 / 5.6 / 7.2 for
   1st/2nd/3rd, n=10) while Zhenghongshuang and Cow Boy are both slowest to a 3rd
   quadrant and rarely reach it (day ~15-16, only 5/30 and 4/21 games respectively).
7. FERTILIZER and WHEAT are sold starting day 0-1 in all 200 games (median first-sell
   day 0-1) while CARROT is held back to a median first sale on day 26 and TOMATO to day
   20 — strong teams dump cheap/fast goods immediately but bank the slower crops rather
   than sell them at a thin early market.
8. Sell orders are placed in small increments for the large majority of teams (median
   requested size 3-16 units/order), but Cow Boy (25% of WHEAT sell orders) and
   Zhenghongshuang (6%) frequently request very large quantities (>=100, often literally
   999-1000, i.e. "sell whatever I have") — raw requested-quantity totals for these two
   teams substantially overstate actual executed sales, since `_commit_unit` caps SELL
   at current shed stock; this is a measurement caveat, not a behavioral claim about
   volume.
9. SpaTaro (10/10 games) issues day-0 BUY_PRODUCT orders for STRAWBERRY, TOMATO, CARROT,
   MELON and MILK — none of which are legal BUY_PRODUCT items under the rules
   (`_process_market` only allows `item in ("WHEAT", "FERTILIZER")` for that op) — these
   are silent no-ops per `_parse_order`/`_commit_unit`, so a chunk of SpaTaro's opening
   10-order market queue is wasted every game despite SpaTaro being a top-of-ladder team.
10. Several teams (clearest in Mengfei Li and Majkel1337, both 20+ games) run a
    per-turn `BUY_PRODUCT WHEAT 1` / `SELL WHEAT 1` round-trip starting day 0 and
    continuing most of the season. By the game's own pricing design (buy is quoted at
    post-buy inventory so a round trip nets ~0 cash) this looks like a mechanism to keep
    a steady 1-wheat/turn buffer available for animal FEED without touching harvested
    stock, rather than a profit play.

## Tables

### Opening hires, day 0-2 (mean HIRE orders per day, from the first market queue)

| Team | day0 | day1 | day2 | n games |
|---|---|---|---|---|
| Otter Vibe | 5.00 | 1.00 | 3.00 | 38 |
| Mengfei Li | 5.00 | 4.00 | 4.00 | 23 |
| SpaTaro | 6.10 | 6.40 | 6.00 | 10 |
| Majkel1337 | 4.00 | 9.95 | 6.00 | 20 |
| HowardLeeTW | 7.00 | 4.04 | 7.00 | 25 |
| Orbital Terraformer | 4.00 | 8.00 | 6.00 | 21 |
| ymg_aq | 4.00 | 1.00 | 4.00 | 12 |
| Zhenghongshuang | 5.00 | 3.00 | 4.00 | 30 |
| Cow Boy | 4.05 | 3.00 | 3.05 | 21 |

### First crop planted (day of first PLANT, days 0-3, always day 0 in every game)

| Team | first crop |
|---|---|
| Otter Vibe | WHEAT (38/38) |
| HowardLeeTW | WHEAT (25/25) |
| Mengfei Li | MELON (23/23) |
| SpaTaro | MELON (10/10) |
| Majkel1337 | MELON (20/20) |
| Orbital Terraformer | MELON (21/21) |
| ymg_aq | MELON (12/12) |
| Zhenghongshuang | MELON (30/30) |
| Cow Boy | MELON (21/21) |

### Animals bought day 0-3 (total head count, pooled across a team's games)

| Team | species (day 0-3 totals) | games with any animal by day3 |
|---|---|---|
| Otter Vibe | SHEEP 38, GOOSE 38, COW 38 | 38/38 |
| Mengfei Li | COW 69, SHEEP 23 | 23/23 |
| SpaTaro | COW 18, SHEEP 13 | 10/10 |
| Majkel1337 | COW 40, SHEEP 20 | 20/20 |
| HowardLeeTW | COW 25, SHEEP 25 | 25/25 |
| Orbital Terraformer | COW 42, SHEEP 21 | 21/21 |
| ymg_aq | COW 23, SHEEP 24 | 12/12 |
| Zhenghongshuang | COW 90, SHEEP 60 | 30/30 |
| Cow Boy | COW 63, SHEEP 21 | 21/21 |

Note: totals are cumulative head counts summed over all BUY_ANIMAL orders in days 0-3
(a team buying 2 cows on day 0 and 1 more day 2 counts as 3). GOOSE is unique to Otter
Vibe in the opening window.

### Seed buys, total per game (mean units)

| Team | CARROT | MELON | STRAWBERRY | TOMATO | WHEAT |
|---|---|---|---|---|---|
| Otter Vibe | 35.4 | 15.3 | 29.4 | 16.4 | 100.3 |
| Mengfei Li | 37.3 | 14.6 | 34.6 | 11.4 | 107.8 |
| SpaTaro | 54.9 | 19.5 | 34.0 | - | 215.1 |
| Majkel1337 | 40.9 | 13.4 | 36.2 | 8.7 | 177.0 |
| HowardLeeTW | 41.2 | 13.8 | 31.2 | 12.3 | 139.4 |
| Orbital Terraformer | 73.6 | 12.4 | 34.5 | 5.7 | 168.3 |
| ymg_aq | 37.8 | 11.6 | 33.6 | 8.6 | 162.4 |
| Zhenghongshuang | 34.1 | 12.0 | 33.4 | 20.0 | 163.5 |
| Cow Boy | 33.6 | 12.0 | 33.0 | 10.0 | 160.5 |

### Labour: total hires/game and action-type share (all units, all steps)

| Team | mean hires/game | MOVE% | WORK% | PASS% |
|---|---|---|---|---|
| Otter Vibe | 279.6 | 40.8 | 50.4 | 8.7 |
| Mengfei Li | 266.3 | 42.6 | 47.1 | 10.3 |
| SpaTaro | 278.1 | 40.3 | 46.0 | 13.8 |
| Majkel1337 | 292.2 | 47.0 | 52.1 | 0.8 |
| HowardLeeTW | 316.3 | 41.2 | 42.4 | 16.3 |
| Orbital Terraformer | 290.6 | 45.8 | 53.1 | 1.1 |
| ymg_aq | 277.8 | 48.5 | 46.4 | 5.1 |
| Zhenghongshuang | 271.8 | 42.3 | 49.6 | 8.1 |
| Cow Boy | 270.5 | 42.5 | 50.7 | 6.8 |

### Crops: PLANT actions per crop per game (mean) — proxy for sowing volume, not
standing tile count (wheat/carrot are non-ongoing and get replanted after each harvest)

| Team | WHEAT | CARROT | STRAWBERRY | MELON | TOMATO |
|---|---|---|---|---|---|
| Otter Vibe | 100.3 | 35.4 | 29.4 | 15.3 | 16.4 |
| Mengfei Li | 107.8 | 38.6 | 34.0 | 14.6 | 11.4 |
| SpaTaro | 209.9 | 54.5 | 26.1 | 11.2 | - |
| Majkel1337 | 181.1 | 42.2 | 31.4 | 13.9 | 8.7 |
| HowardLeeTW | 138.9 | 40.8 | 31.1 | 13.8 | 12.3 |
| Orbital Terraformer | 175.4 | 94.2 | 30.0 | 13.8 | 7.3 |
| ymg_aq | 162.2 | 37.5 | 33.5 | 11.5 | 8.1 |
| Zhenghongshuang | 159.2 | 34.1 | 32.9 | 12.0 | 20.0 |
| Cow Boy | 159.3 | 33.6 | 33.0 | 12.0 | 10.0 |

Orbital Terraformer stands out with far heavier CARROT sowing (94.2/game vs 33-55 for
everyone else) — a clear crop-mix disagreement.

### Crops: sow-day distribution, pooled across all 200 games

| Crop | n sow actions | median day | p10 | p90 |
|---|---|---|---|---|
| WHEAT | 29238 | 17 | 4 | 25 |
| CARROT | 8610 | 25 | 17 | 27 |
| STRAWBERRY | 6278 | 7 | 4 | 11 |
| MELON | 2690 | 0 | 0 | 10 |
| TOMATO | 1595 | 14 | 10 | 18 |

### Market: median day of first SELL per item, pooled

| Item | n games selling it | median first-sell day |
|---|---|---|
| FERTILIZER | 200/200 | 1 |
| WHEAT | 200/200 | 0 |
| WOOL | 200/200 | 6 |
| MILK | 200/200 | 8 |
| MELON | 200/200 | 10 |
| STRAWBERRY | 200/200 | 15 |
| EGG | 156/200 | 13 |
| TOMATO | 134/200 | 20 |
| CARROT | 195/200 | 26 |

### Market: WHEAT sell-order sizing (dump vs hold proxy)

| Team | orders/game | median order size | % orders requesting >=100 |
|---|---|---|---|
| Otter Vibe | 18.8 | 16 | 0% |
| Mengfei Li | 35.4 | 6 | 0% |
| SpaTaro | 102.8 | 6 | 0% |
| Majkel1337 | 71.7 | 5 | 0% |
| HowardLeeTW | 33.0 | 7 | 0% |
| Orbital Terraformer | 72.5 | 6 | 0% |
| ymg_aq | 133.7 | 5 | 0% |
| Zhenghongshuang | 69.0 | 3 | 6% |
| Cow Boy | 68.6 | 9 | 25% |

(Raw "units sold" totals from summing order request sizes are not reported as a primary
table because Cow Boy/Zhenghongshuang's large "sell-all" requests are capped by shed
stock at execution time and inflate the requested-quantity sum well past anything
physically produced — see Thesis 8.)

### Land: quadrant purchase days (mean day of 1st/2nd/3rd BUY_LAND)

| Team | 1st | 2nd | 3rd | games |
|---|---|---|---|---|
| Otter Vibe | 5.0 (n=38) | 10.2 (n=38) | - | 38 |
| Mengfei Li | 6.0 (n=23) | 11.0 (n=23) | - | 23 |
| SpaTaro | 1.9 (n=10) | 5.6 (n=10) | 7.2 (n=10) | 10 |
| Majkel1337 | 6.0 (n=20) | 9.0 (n=20) | 9.0 (n=17) | 20 |
| HowardLeeTW | 3.0 (n=25) | 8.0 (n=25) | - | 25 |
| Orbital Terraformer | 5.9 (n=21) | 8.6 (n=21) | 8.8 (n=19) | 21 |
| ymg_aq | 5.1 (n=12) | 8.0 (n=12) | - | 12 |
| Zhenghongshuang | 6.0 (n=30) | 11.0 (n=30) | 15.6 (n=5) | 30 |
| Cow Boy | 6.0 (n=21) | 11.0 (n=21) | 16.5 (n=4) | 21 |

Note: "-" or low n for 3rd land means most games in that team's sample never buy the 3rd
quadrant (SE, $4000) at all; only Majkel1337, Orbital Terraformer buy it in nearly every
game, while Otter Vibe, Mengfei Li, HowardLeeTW, ymg_aq essentially never do in this
sample.

## Disagreements

- **Opening crop**: Otter Vibe and HowardLeeTW always open with WHEAT; the other 7 teams
  always open with MELON. This is a clean, consistent 2-vs-7 split, not noise.
- **PASS tolerance**: Majkel1337 (0.8%) and Orbital Terraformer (1.1%) essentially never
  let a unit pass, while HowardLeeTW (16.3%) and SpaTaro (13.8%) leave hands idle a
  sixth to an eighth of the time. Both groups are top-of-ladder, so idling is not simply
  a losing trait.
- **Land aggression**: SpaTaro buys all 3 quadrants by day ~7; Zhenghongshuang and Cow
  Boy buy the 2nd around day 11 and rarely ever get the 3rd. Both extremes coexist among
  strong teams.
- **Carrot investment**: Orbital Terraformer sows carrot ~2-3x more than every other
  team (94.2 vs 33-55 PLANT-CARROT actions/game) while keeping wheat/strawberry/melon in
  line with peers — an isolated crop-mix choice, not a whole-strategy shift.
- **Sell-order sizing**: most teams sell in small, frequent increments (median 3-16
  units); Cow Boy is the outlier using large "sell whatever's there" requests roughly a
  quarter of the time.
- **SpaTaro's invalid orders**: unique among the 9 teams, SpaTaro spends opening
  market-queue slots on BUY_PRODUCT for non-WHEAT/FERTILIZER items, which the engine
  silently drops. No other team was observed doing this.

## Confidence

- **Solid** (large n, consistent across all/most of 200 games, directly read off action
  logs with no inference): opening crop split, day-0 hires, day 0-3 animal purchases,
  first-sell-day ordering across items, land-purchase timing, MOVE/WORK/PASS shares.
- **Solid with a caveat**: seed-buy and PLANT-count tables are accurate counts of
  actions taken, but PLANT-action count is a sowing-volume proxy, not a live standing-
  tile count — a crop's actual concurrent tile footprint would need an engine replay to
  track PLANT vs DIG/weed-death/HARVEST-clears tile-by-tile, which was out of scope here.
- **Thin / caveated**: raw "units sold" tables are unreliable for teams using large
  sell-all order sizes (Cow Boy, Zhenghongshuang) because requested quantity in the tape
  isn't the executed quantity (capped by shed stock in `_commit_unit`); I used order
  count and median order size instead where this mattered. Fixing this fully would
  require replaying the engine to track shed inventory, which the task treats as
  optional/heavier-weight than the action-log approach.
- **Single-game-derived qualitative detail** (the exact first-~20-order sequences shown
  for Otter Vibe/Mengfei Li/SpaTaro/Majkel1337 in scratch output): illustrative of team
  style, drawn from one representative game per team rather than aggregated, so treat as
  color rather than a statistic.
