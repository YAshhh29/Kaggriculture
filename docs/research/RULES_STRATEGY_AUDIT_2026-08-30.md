# Kaggriculture Rules and Strategy Audit

**Date:** 2026-08-30
**Simulator audited:** installed `kaggle-environments==1.32.7`
**Purpose:** identify rule-implied macro policies that conservative tiered/gated agents may be leaving untested.

## Evidence standard

This report uses four labels:

- **PROVEN**: directly specified by the installed first-party simulator or official Kaggle competition documentation.
- **DERIVED**: arithmetic or timing implied deterministically by proven mechanics, before labor, travel, and opponent effects unless stated otherwise.
- **OBSERVED**: present in a captured public replay or its local strategy report; it is not causal evidence.
- **HYPOTHESIS**: a candidate policy that needs controlled paired evaluation.

The installed source is the controlling authority for local 1.32.7 behavior. Kaggle's official [competition overview](https://www.kaggle.com/competitions/kaggriculture/overview) independently documents the 30-day objective, objects, actions, market, town, and configuration. The official [competition rules](https://www.kaggle.com/competitions/kaggriculture/rules) confirm that episode actions may be publicly downloadable. Public episode evidence in this report can be checked at `https://www.kaggle.com/competitions/episodes/<episode-id>/replay.json`.

## Highest-impact findings

1. **DERIVED:** a universal day-24 planting stop is early. Under base timing, full-yield wheat remains possible from a day-25 planting; first-positive wheat and carrot remain possible on day 27; tomato on day 21; strawberry and melon on day 19. Quote, route, and liquidation feasibility still decide actual profitability.
2. **PROVEN:** ongoing tomato and strawberry do not require daily water for base scheduled production. They require enough water to survive; water on a production refresh is additionally required only for the fertilizer double. Daily watering can therefore spend actions without increasing unfertilized output.
3. **DERIVED:** spent ongoing crops should be evaluated for same-day harvest, `DIG`, replant, and water. A day-0 tomato can complete a second full four-yield lifecycle after replacement around day 11. A day-0 strawberry replaced around day 16 can still produce twice, around days 26 and 28.
4. **PROVEN/DERIVED:** the first 12 hands cost only 376 coins per day cumulatively. If ten are hired at hour 0 and two at hour 1, they can supply up to 274 hand-actions; the 12th hand's marginal break-even is about 6.55 coins per available action before travel and idling.
5. **OBSERVED:** elite schedules repeatedly use 12 hands, and some use 13. The day-level report for episode 99058164 reaches 298 worker actions with 12 hands, exactly consistent with one main farmer plus ten hour-0 and two hour-1 hires.
6. **DERIVED:** all extra land costs 7,000 coins for 75 tiles, but static crop payback is a weak gate. One all-land episode paid six figures, while other higher-scoring farms bought only two quadrants. Expansion needs incremental counterfactual profit, not a blanket prohibition or blanket target.
7. **PROVEN/DERIVED:** full CARE has the same incremental steady-state product rate for every species: approximately one extra product per animal-day versus sparse survival. Its dynamic pre-labor break-even is therefore `product quote > 0.5 * wheat quote`; product-specific labor, caps, and horizon then decide.
8. **DERIVED:** caring every day before first production can waste bonus, especially for cows. A fully cared new cow can have eight units notionally due at its first production but can hold only six. CARE should be cap-aware and harvest-aware from placement onward.
9. **PROVEN:** workers act before market orders, so a shed-adjacent `DROP` can fund a `SELL` in the same transition. End-of-day auto-drop occurs after the market and cannot be sold until a later transition; final-day plans must explicitly return, drop, and sell.
10. **PROVEN:** town demand occurs after player market orders at hours divisible by four. Buying just before a demand tick and selling just after it is mechanically advantaged relative to the reverse, subject to opponent orders and integer price steps.
11. **OBSERVED/HYPOTHESIS:** animal escapes and terminal weeds appear in multiple six-figure elite games. Because animals cannot be sold or dug while present and weeds have no terminal penalty, some losses can be rational at high utilization or near season end. This needs marginal-value counterfactuals, not a zero-loss axiom.
12. **PROVEN:** final value is banked coins only. At the one-coin floor a sale still adds one coin and does not increase market supply, so every reachable sellable terminal unit should be liquidated even when its production was unprofitable.

## 1. Clock, score, and terminal boundary

**PROVEN.** The default game has 720 configured episode steps, 24 turns per day, a 3,000-coin start, and a reward equal to terminal money. Unsold crops, products, animals, seeds, and fertilizer have no salvage value. See the installed specification at `.conda/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.json` and its reward definition at lines 89-94 (`kaggriculture.json`, a local file).

**PROVEN, local implementation detail.** The interpreter executes unit actions, market, town, decay, and optional day refresh in that order, then marks agents done when the incoming step is at least `episodeSteps - 2`. In the installed replay convention, record 0 is initialization and the 720-record episode contains 719 executed transitions; the final executable source step is 718, corresponding to day 29 hour 22 under the source's zero-based clock. See `interpreter` (`kaggriculture.py`, a local file). This is one transition less than a naive reading of “720 turns,” so terminal tests should assert the actual callback sequence rather than infer it from prose.

**Consequence.** A day-29 plan should reserve at least one transition of slack. The final executable transition may combine `DROP` and `SELL`, but it cannot combine movement, harvest, and drop by one worker.

## 2. Exact crop lifecycle economics

Crop constants are first-party facts: seeds, first-yield ages, final/interval timing, held caps, and ongoing status are defined together in `CROPS` (`kaggriculture.py`, a local file). New one-time crops start with one unit; ongoing crops start with zero; planting day starts at one missed-water count (`_new_plant` (`kaggriculture.py`, a local file)).

For one-time crops, productive watering begins at `(max_yield_day + 1) // 2`, adds one unit or two while fertilized, and is capped at `max_yield`; harvesting removes the crop (`WATER` and `HARVEST` (`kaggriculture.py`, a local file)). For ongoing crops, the daily refresh creates fixed scheduled yields, whether or not that production day was watered; water is required for the fertilizer double and for survival (`_daily_refresh_plants` (`kaggriculture.py`, a local file)).

### Latest cashable planting days

The table assumes base quotes, adequate workers, planting-day water, survival service, a harvest, a shed return/drop, and sale by the final executable transition. “Any” means the first positive pre-labor crop margin available at the base quote. “Full” means the complete unfertilized maximum schedule, not necessarily the best marginal use of labor.

| Crop | Base path | Base net before labor | Latest full planting | Latest any-positive planting | Any-positive output and base net | Minimum integer quote for that late path |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Wheat | 10 seed; productive water ages 2-4 | `4*25-10 = 90` | day 25 | day 27 | 2 units; 40 | 6 |
| Carrot | 20 seed; productive water ages 2-3 | `3*35-20 = 85` | day 26 | day 27 | 2 units; 50 | 11 |
| Tomato | 50 seed; yields at observed ages 8-11 | `4*60-50 = 190` | day 18 | day 21 | 1 unit; 10 | 51 |
| Strawberry | 100 seed; yields at observed ages 10, 12, 14, 16 | `4*120-100 = 380` | day 13 | day 19 | 1 unit; 20 | 101 |
| Melon | 80 seed; productive water ages 6-12, cap reached at 10 | `6*250-80 = 1,420` | day 19 | day 19 | up to 6 units; 1,420 | 14 for six units |

Days are simulator-zero-based; add one for the visualizer's displayed day. These are **DERIVED feasibility bounds, not admission recommendations**. A current quote below the last column makes even seed recovery impossible before labor. Route congestion, missing same-day water, insufficient harvest/drop time, market impact, or a final callback mismatch moves the operational cutoff earlier.

### Survival and service subtleties

- **PROVEN:** planting day counts as unwatered. A new crop must be watered before that night's refresh or it immediately becomes a weed (plant initialization (`kaggriculture.py`, a local file), daily refresh (`kaggriculture.py`, a local file)).
- **PROVEN:** after a watered day, one missed day is survivable. A second consecutive missed refresh makes a weed. Therefore daily water is not intrinsically required for survival.
- **PROVEN:** one-time crops gain units only from productive-window water. Non-window water is survival service, not yield service.
- **PROVEN:** ongoing crops produce their base unit on schedule as long as they survive. Fertilizer doubles only when that production refresh was watered.
- **PROVEN:** held ongoing yield is capped at four. Failure to harvest between doubled production events can discard potential output.
- **PROVEN:** lifetime is based on scheduled production count, not harvest count. Harvesting does not extend tomato or strawberry life.

### Ongoing crop replacement

After the fourth scheduled yield, ongoing crops begin decay one day later. `DIG` can clear a plant but cannot clear an occupied animal (`DIG` (`kaggriculture.py`, a local file)); final-production timing and decay are in plant refresh and decay (`kaggriculture.py`, a local file).

**DERIVED replacement opportunities:**

- A day-0 tomato yields on observed days 8-11. Harvesting the last yield, digging, replanting, and watering around day 11 permits another complete set on days 19-22. At base quote, the second seed has 190 coins of crop margin before service.
- A day-0 strawberry yields on days 10, 12, 14, and 16. Replacement around day 16 can still yield around days 26 and 28. At base quote, two unfertilized units return 240 against a 100 seed, or 140 before labor.
- Same-day replacement requires separate `HARVEST`, `DIG`, `PLANT`, and `WATER` actions, but these can be parallelized across co-located workers because unit actions execute main farmer then hand order.

**HYPOTHESIS:** a replacement controller should compare remaining scheduled output at current projected quotes against seed, water, harvest, dig, travel, shed, and sale costs. It should not keep spent plants merely because they are ongoing, and it should not replace at a market floor merely because calendar time exists.

## 3. Fibonacci labor and break-even work

The source defines the nth daily hire as `fib(n_already_today)`, resets hires at day end, and removes all hands (hire implementation (`kaggriculture.py`, a local file), day-end reset (`kaggriculture.py`, a local file)). A newly hired hand is created during market processing, after that transition's worker actions, so an hour-0 hire first acts at hour 1.

| Hand | Marginal daily cost | Cumulative cost | Earliest actions available* | Marginal cost / action |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 1 | 23 | 0.04 |
| 2 | 1 | 2 | 23 | 0.04 |
| 3 | 2 | 4 | 23 | 0.09 |
| 4 | 3 | 7 | 23 | 0.13 |
| 5 | 5 | 12 | 23 | 0.22 |
| 6 | 8 | 20 | 23 | 0.35 |
| 7 | 13 | 33 | 23 | 0.57 |
| 8 | 21 | 54 | 23 | 0.91 |
| 9 | 34 | 88 | 23 | 1.48 |
| 10 | 55 | 143 | 23 | 2.39 |
| 11 | 89 | 232 | 22 | 4.05 |
| 12 | 144 | 376 | 22 | 6.55 |
| 13 | 233 | 609 | 22 | 10.59 |
| 14 | 377 | 986 | 22 | 17.14 |
| 15 | 610 | 1,596 | 22 | 27.73 |
| 16 | 987 | 2,583 | 22 | 44.86 |

`*` Ten market entries per turn allow hands 1-10 to be hired at hour 0. Hands 11+ can be hired at hour 1 if the first list is all hires. Other required market entries reduce availability.

The correct admission equation for marginal hand `k` is:

```text
expected incremental sale value
- incremental seed/feed/fertilizer purchases
- market-impact loss
- overflow/discard risk
> marginal hire cost(k)
```

Cost per raw action is only a lower bound. If half of a hand's actions are movement, pass, duplicate service, or unliquidated production, the required value per useful action doubles. Conversely, one hand can unlock many high-value tasks in a route, so comparing a 144-coin 12th hand to a single CARE action is too conservative.

**OBSERVED.** Both players in episode [99058164](https://www.kaggle.com/competitions/episodes/99058164/replay.json) reached 12 hands; the local report records 293 and 289 hires (player 0 (`episode-99058164-rank1-vs-rank2-strategy.json`, a local file), player 1 (`episode-99058164-rank1-vs-rank2-strategy.json`, a local file)). The augmented day report records 298 worker actions on many days and 285 on day 29, including 19 harvests and 21 drops (day-level endgame (`episode-99058164-rank1-vs-rank2-strategy-harvest-ages.json`, a local file)). This proves high utilization is feasible, not that 12 is universally optimal.

## 4. Land payback and all-land policy

**PROVEN.** Extra quadrants unlock in NE, SW, SE order for 1,000, 2,000, and 4,000 coins (land constants (`kaggriculture.py`, a local file), purchase implementation (`kaggriculture.py`, a local file)). Each adds 25 tiles. Capital per added tile is 40, 80, and 160 coins respectively; all 75 blend to 93.33 coins per tile.

Static base-price tile-cycles needed merely to recover land capital are:

| Purchase | Cost | Wheat net 90 | Carrot net 85 | Tomato net 190 | Strawberry net 380 | Melon net 1,420 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NE | 1,000 | 12 | 12 | 6 | 3 | 1 |
| SW | 2,000 | 23 | 24 | 11 | 6 | 2 |
| SE | 4,000 | 45 | 48 | 22 | 11 | 3 |
| All extra land | 7,000 | 78 | 83 | 37 | 19 | 5 |

This **DERIVED** table excludes labor, movement, weeds, delayed cash, fertilizer opportunity cost, shed throughput, and nonlinear shared-market impact. It is therefore an optimistic lower bound, especially for melon, strawberry, milk, and wool gluts.

**OBSERVED.** Both players in episode [94173913](https://www.kaggle.com/competitions/episodes/94173913/replay.json) bought all three quadrants; player 0 bought on days 6, 11, and 12 (purchase schedule (`episode-94173913-strategy.json`, a local file)) and finished at 109,547 with an empty sellable terminal inventory (terminal state (`episode-94173913-strategy.json`, a local file)). Player 1 finished at 111,082, also with all land and no sellable terminal stock (terminal state (`episode-94173913-strategy.json`, a local file)). By contrast, Crop Dusta scored 167,126 in episode 97710447 after buying only two extra quadrants (purchases (`episode-97710447-rank1-crop-dusta-strategy.json`, a local file), terminal (`episode-97710447-rank1-crop-dusta-strategy.json`, a local file)).

**Conclusion:** all-land is feasible but not necessary. The missing test is the same schedule with each purchase removed while preserving the resulting cash and rerouting workload. Payback should be measured as paired terminal bank delta, not gross production on bought tiles.

## 5. Animal CARE, feed, caps, and dynamic prices

Animal costs, first production ages, intervals, held caps, and products are defined in `ANIMALS` (`kaggriculture.py`, a local file). `FEED` consumes one carried wheat; `CARE` only marks the day (unit actions (`kaggriculture.py`, a local file)). At refresh, two consecutive unfed days cause escape. Scheduled production always creates base one; a fed production consumes all banked CARE; fed-plus-cared then banks one for a later production. Every surviving animal exposes one fertilizer, even if unfed or uncared (animal refresh (`kaggriculture.py`, a local file)).

### Service modes

Let `P` be the animal-product quote, `W` the wheat buy/opportunity quote, and `F` the fertilizer quote.

| Mode | Average product/day after startup | Wheat/day | Fertilizer/day | Pre-labor operating value/day |
| --- | ---: | ---: | ---: | ---: |
| Goose, full feed + CARE | 2 | 1 | 1 | `2P + F - W` |
| Cow, full feed + CARE | 1.5 | 1 | 1 | `1.5P + F - W` |
| Sheep, full feed + CARE | 1.333 | 1 | 1 | `(4/3)P + F - W` |
| Any species, sparse survival/no CARE | `1 / interval` | about 0.5 | 1 | `P/interval + F - 0.5W` |

**DERIVED.** The full-CARE upgrade adds approximately one product per animal-day for goose, cow, and sheep, while requiring about another half wheat per day versus alternate-day survival. Before labor, upgrading is attractive when:

```text
P - 0.5W > 0
```

At product quote 1 and wheat quote 40, the upgrade loses about 19 coins per animal-day before CARE, FEED, harvest, and travel actions. At milk 160 and wheat 40, it has about 140 coins/day of pre-labor headroom.

### First-yield and held-cap waste

CARE accumulated before first production is paid in one batch. With daily feed and CARE from placement:

- goose first production can request `1 + 3 = 4`, exactly its cap;
- cow first production can request `1 + 7 = 8`, but its cap is 6, wasting two units;
- sheep first production can request `1 + 5 = 6`, exactly its cap.

**DERIVED:** a new cow should generally receive no more than five effective pre-first-yield CARE days unless the exact refresh sequence or an intervening mechanic changes. More broadly, CARE should stop whenever projected base plus banked bonus would exceed free held capacity before the next harvest.

At base quotes, mature full-service operating margins before labor are 175/day for goose, 315/day for cow, and about 341.67/day for sheep. These figures do not mean immediate payback: first production is delayed by 4, 8, and 6 days, respectively, and early fertilizer, feed, CARE, harvest, and market timing must be modeled as cash flows.

## 6. Shed capacity, same-turn drop/sell, and overflow

**PROVEN.** The shed holds 100 non-seed items. `DROP` transfers the worker's entire inventory up to remaining capacity and deletes all carried entries, so overflow is discarded. Shed-directed `PLACE` transfers only the requested amount that fits and leaves excess carried. See shed actions (`kaggriculture.py`, a local file).

**PROVEN.** Worker actions occur before market processing, so a shed-adjacent worker can `DROP` while the same agent action includes a `SELL` that consumes the newly deposited stock (turn order (`kaggriculture.py`, a local file)). End-of-day auto-drop occurs after market and discards overflow (auto-drop (`kaggriculture.py`, a local file)).

Strategic consequences:

- Reserve capacity for automatic hand returns or explicitly sell/drop during the day.
- Prefer `PLACE item n` over `DROP` when near capacity and other carried items are more valuable.
- Treat projected carried inventory, not only current shed stock, as sellable in the current market action.
- A full shed blocks product and animal purchases, even when money is available (market commit (`kaggriculture.py`, a local file)).
- On day 29, every return route must terminate in an explicit drop/sell wave; there is no useful next-day auto-drop.

## 7. Shared market timing, manipulation, and concurrency

The market curves share an inventory anchor of 10,000 and a one-coin floor. Premium goods have severe oversupply curves: strawberry, melon, milk, and wool can reach the floor rapidly, while wheat, egg, and fertilizer are more glut-tolerant. Constants and curve shapes are in `MARKET_PARAMS` (`kaggriculture.py`, a local file); price calculation is in `market_price` (`kaggriculture.py`, a local file).

**PROVEN concurrency rules:**

- Each player contributes at most ten market-list entries; later entries are sliced off silently (queue construction (`kaggriculture.py`, a local file)). Quantity inside one valid entry is not capped at ten.
- Entry `i` from each player is processed together. For each unit, both players receive quotes from the same pre-commit inventory, then both commits occur (lockstep loop (`kaggriculture.py`, a local file)).
- A sell quotes at pre-sell inventory. A wheat/fertilizer buy quotes at post-buy inventory, making an isolated buy/sell round trip net zero.
- A sale at the one-coin floor still pays one coin but does not add market inventory (sell commit (`kaggriculture.py`, a local file)).

**DERIVED timing opportunities:**

- Town consumption happens after market processing. Buy wheat/fertilizer before a known demand tick; sell demanded products after the tick, not immediately before it, when cash constraints permit.
- Break large premium sales into demand-paced batches when expected town depletion exceeds the lost benefit of earlier cash.
- If both players sell the same resource in the same order slot, neither can obtain the other's pre-sale price advantage for that unit; they receive equal pre-commit quotes. Order-index alignment therefore matters.
- Buying wheat for real feed demand also removes shared inventory and can raise both future wheat purchase costs and wheat sale quotes. A speculative manipulation policy must value its own remaining feed liability and the opponent's inferred liability.
- Since order cap counts entries, consolidate quantity by resource and prioritize hires, land, urgent seed/animal purchases, and liquidation ahead of optional orders.

**OBSERVED.** In episode [99058164](https://www.kaggle.com/competitions/episodes/99058164/replay.json), player 0 bought 1,859 wheat at a weighted mean quote of 39.17 and sold 2,011 at 40.60. The report shows 46 wheat sold on day 28 and 117 on day 29 (wheat trade summary (`episode-99058164-rank1-vs-rank2-wheat-trades.json`, a local file)). This is evidence of large-scale feed/market throughput and final liquidation, not proof that bounded wheat trading independently adds profit.

## 8. Town demand cadence

Shops and product baskets are defined in `SHOPS` (`kaggriculture.py`, a local file). Town processing is exact in `_town_consume` (`kaggriculture.py`, a local file):

- shop ticks occur when `step % 4 == 0`, at default hours 0, 4, 8, 12, 16, and 20;
- every active shop instance consumes each listed item; Pet Cafe and Yarn Store consume two units because they are single-product shops;
- town center consumes one of every non-fertilizer product when `step % 24 == 0`, at hour 0 daily;
- prices refresh immediately after consumption.

Shop unlocks occur after day-end refresh every three days, are sampled with replacement, persist, and stop after eight instances (unlock implementation (`kaggriculture.py`, a local file)). Default observed unlock days are 3, 6, 9, 12, 15, 18, 21, and 24.

**DERIVED daily demand per active instance:** multi-product shops consume six units/day of each listed good; Pet Cafe consumes 12 carrots/day; Yarn Store consumes 12 wool/day; town center adds one unit/day to every non-fertilizer product. Demand is monotone in shop instances but not in variety because duplicates are allowed.

**HYPOTHESIS:** crop and species slots should be re-optimized after each draw using exact duplicate counts, current inventory displacement from 10,000, opponent public production capacity, and time-to-first-cash. “Milk demand exists” is too coarse; three smoothie/ice-cream instances imply a different saturation regime from one pizza shop.

## 9. Final-day liquidation

**PROVEN:** only terminal bank is rewarded. Seeds, crops on tiles, animal products on tiles, fertilizer on animals, shed goods, carried goods, animals, and structures have no direct terminal value.

A robust final policy should:

1. Stop purchases whose output cannot be sold before source step 718.
2. Stop CARE when its next paid production cannot be harvested and sold.
3. Harvest all positive-value tile output, including at a one-coin quote when the marginal route/action cost is already sunk or lower than the proceeds.
4. Collect fertilizer only when its marginal sale exceeds route/action opportunity cost.
5. Route carriers to a shed-access tile with enough time for `DROP`.
6. Issue projected same-turn sells after `DROP`, ordered before any optional market entry.
7. Sell floor-priced stock: each unit adds one banked coin and does not deepen market inventory.

**OBSERVED.** The episode-99058164 player-0 schedule used 19 harvests and 21 drops on day 29, but still finished with 17 carried wheat (terminal state (`episode-99058164-rank1-vs-rank2-strategy.json`, a local file)). That wheat was economically worthless at terminal despite a 139,632 score. Even elite endgames leave measurable liquidation slack.

## 10. Can crop or animal loss be rational?

### Animals

**PROVEN:** an occupied animal cannot be sold and cannot be removed with `DIG`. Two unfed refreshes cause escape, leaving an empty structure that can then be dug. On the first missed-feed refresh the animal survives, can produce base output, and exposes fertilizer; on the second it escapes before those later refresh operations.

**DERIVED:** deliberate abandonment can be rational when:

```text
future product + fertilizer sale value
< feed purchases + CARE/FEED/harvest/collect travel and action value
```

It can also be rational when freeing the tile after the two-day escape delay plus one `DIG` enables a more valuable crop cycle. The animal purchase is sunk and should not enter the keep/abandon decision.

**OBSERVED:** the local public reports record four sheep losses for player 0 in episode 94173913 (loss count (`episode-94173913-strategy.json`, a local file)), four sheep losses for the 167,126-coin winner in episode 97710447 (loss count (`episode-97710447-rank1-crop-dusta-strategy.json`, a local file)), and cow losses for both players in episode 99058164 (player 0 (`episode-99058164-rank1-vs-rank2-strategy.json`, a local file), player 1 (`episode-99058164-rank1-vs-rank2-strategy.json`, a local file)). These may be intentional abandonment, scheduling failure, or harmless endgame neglect; replay occurrence alone cannot distinguish them.

### Crops and weeds

**PROVEN:** weeds have no direct bank penalty. A dead crop and an intentionally ignored spent crop both cost a future `DIG` only if the tile will be reused.

**DERIVED:** letting a crop die or leaving a spent plant/weed can be rational when no profitable reuse remains and water/dig actions have higher marginal value elsewhere. Before that point, crop death is costly if it destroys harvestable value or blocks a profitable replacement.

The policy distinction should be explicit:

- `avoidable_loss`: expected cashable value destroyed;
- `rational_abandonment`: service stopped after expected marginal value became negative;
- `terminal_residue`: zero-salvage object left because no profitable reuse exists.

## Replay observations relevant to conservative agents

| Episode | Observation | What it supports | What it does not prove |
| --- | --- | --- | --- |
| [94173913](https://www.kaggle.com/competitions/episodes/94173913/replay.json) | Both players bought all land and finished above 109k; both had animal losses and many terminal weeds. | All-land, high labor, and nonzero-loss play are feasible together. | Any one choice caused the high score. |
| [97710447](https://www.kaggle.com/competitions/episodes/97710447/replay.json) | Crop Dusta scored 167,126 with two extra quadrants, 12 hands, 11 cows, and four sheep losses. | Full land is unnecessary; high utilization can coexist with sacrifice. | Sheep abandonment was intentional or profitable. |
| [99003467](https://www.kaggle.com/competitions/episodes/99003467/replay.json) | A player reached 13 hands and recorded three cow losses (workforce/loss (`episode-99003467-rank3-recent-win-strategy.json`, a local file), loss count (`episode-99003467-rank3-recent-win-strategy.json`, a local file)). | The useful labor frontier can extend past 12. | A fixed 13-hand target generalizes. |
| [99058164](https://www.kaggle.com/competitions/episodes/99058164/replay.json) | Both players scored above 139k with 12-hand schedules, large wheat turnover, exact age-10/12/14/16 strawberry harvesting, and day-29 liquidation. | Precise lifecycle service and high throughput are executable. | Copying the macro schedule beats unseen opponents. |

The harvest-age report for episode 99058164 records 33, 33, 32, and 32 player-0 strawberry harvests at ages 10, 12, 14, and 16, plus a few intervening-age harvests (harvest ages (`episode-99058164-rank1-vs-rank2-strategy-harvest-ages.json`, a local file)). This is strong evidence that elite scheduling tracks the complete ongoing lifecycle rather than treating a strawberry as one harvest.

## Candidate macro policies and required measurements

| Candidate policy | Rule implication | Minimum measurement to validate | Primary failure mode |
| --- | --- | --- | --- |
| Quote-aware late planting | Calendar permits profitable crops after day 24. | Per crop/day/quote paired admission rollouts; terminal sold units; seed, labor, and route cost; no unfinished positive-value output. | Plant is theoretically profitable but cannot be serviced or liquidated. |
| Sparse ongoing-crop water | Base ongoing production does not require daily water. | Same schedules with daily versus survival-minimum water; yields, weeds, freed actions, terminal margin. | Alternation bug causes two missed refreshes or misses fertilizer production days. |
| Ongoing crop replacement | Harvest does not extend lifetime; early replacements can still pay. | Tile-level lifecycle traces; replacement-day sweep; incremental sold output and congestion. | Four-action replacement chain crowds out higher-value work. |
| Marginal-value workforce 12-16 | Fibonacci labor stays cheap through 12 and remains testable beyond it. | Per-day hand marginal ablation; useful-action rate; contribution by task class; paired bank delta. | Added hands mostly move/pass or create unsold/overflowing output. |
| Conditional third/fourth quadrant | Land cost is fixed but payback depends on demand and labor. | Remove each purchase from cloned state; preserve cash; reroute; compare terminal bank and utilization. | Static base-price model ignores shared-market collapse. |
| Animal service-state controller | Full CARE, sparse survival, and abandonment have distinct dynamic economics. | Animal-day ledger of quotes, feed, CARE bank, cap loss, fertilizer, products, labor, escape, and terminal sales. | State switching forfeits banked CARE or accidentally escapes valuable animals. |
| Cap-aware pre-first CARE | Cow first-yield CARE can exceed held cap. | CARE-day sweep from placement by species; first-harvest units; wheat/actions spent; downstream bonus. | Reduced early service changes survival or later production phase unexpectedly. |
| Demand-instance species/crop mix | Shops persist, duplicate, and produce exact rates. | Condition arms on complete shop multiset; demand/production ratio; quote path; opponent capacity. | Sparse contexts overfit individual shop draws. |
| Demand-clock market timing | Market precedes town consumption every tick. | Clone state around hours 0/4/8/12/16/20; sell-before versus sell-after; buy-before versus buy-after. | Integer rounding or urgent cash dominates timing gain. |
| Opponent-aware sale pacing | Both farms share inventory and lockstep quotes. | Direct-opponent cloned replays; simultaneous order-index variants; own/opponent price and bank effects. | Manipulation benefits opponent equally or delays cash too long. |
| Capacity-aware drop/sell | Same-turn projected deposits are sellable; overflow is destroyed. | Peak shed + carried projection; discarded units by value; order-cap use; terminal residue. | `DROP` destroys a higher-value carried mix when capacity is low. |
| Explicit terminal liquidation | Unsold stock has zero salvage and floor sales remain bank-positive. | Last 72-turn audit; each tile/shed/carrier unit reconciled to sale or justified abandonment. | Return routes start too late or sale entry is beyond the ten-entry cap. |
| Utilization-aware sacrifice | Service can be negative-value while sunk assets have no salvage. | Counterfactual continue/sparse/abandon arms from identical state; tile reuse value; action shadow price. | Apparent “rational” loss is actually a scheduler defect. |

## Recommended validation design

1. Use exact cloned replay states for narrow mechanic hypotheses, especially market timing, CARE caps, and abandonment. Restore the resolved simulator seed in every clone.
2. Evaluate macro policies on paired seeds, both player positions, and direct shared-market opponents. Starter profit is insufficient.
3. Record decomposition, not only wins: terminal bank, realized revenue by product, purchases, wages, land spend, sold/overflowed/terminal units, useful versus movement/pass actions, CARE cap loss, escapes, weeds, and market inventory path.
4. Separate feasibility gates from optimality gates. Same-day water and terminal liquidation are correctness; zero weeds and zero escapes are not universally optimality conditions once rational abandonment is modeled.
5. Promote only when untouched seeds preserve wins and no opponent class regresses, but use mean own-bank and margin deltas to detect promising neutral policies for further targeting.

## Applied result: public-calendar distillation

The first hand-tuned high-utilization implementation confirmed that copying only visible macro parameters is insufficient. With 12 hands, two extra quadrants, five opening melons, wheat replacement through day 27, seed buffers, and final crop liquidation, it scored 81,163 against tiered fertilizer's 91,002 on seed 224. It remains a rejected research probe, not a promoted agent.

The successful candidate instead distills the complete public action calendar of Crop Dusta player 0 from episode [99058164](https://www.kaggle.com/competitions/episodes/99058164/replay.json). The source is public downloadable Competition Data under the rules' Apache 2.0 Data Access and Use term and Sections 2.4 and 2.11; no competitor source code or private data is used. The rules also prohibit redistribution to non-participants, so the model and package must remain in the private participant repository or on Kaggle during the competition. The model records the replay SHA-256, canonical action SHA-256, source team, player, seed, episode, simulator version, and all 720 replay records. The package builder now rejects inconsistent type, simulator, record count, payload, action hash, package hash, or validation-ledger metadata.

The runtime maps source step `s` to replay action record `s + 1` and preserves simulator-native no-op and atomic market/planting semantics. It matches all 719 source decisions. The standalone package, source runtime, and simulator actions match over 1,438 decisions at seed 230, both player positions, with zero mismatches.

| Gate | Runtime | Seeds and opponents | Control | Candidate | Mean margin change | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Broad unseen-seed gate | Standalone package | Seeds 225-229, both positions, eight policy families | 55-25 | 72-8 | -4,401.48 to +48,431.57 | 0 |
| Hard elite holdout | Action-equivalent source | Seeds 230-234, both positions, four elite calendars plus two deployed controls | 10-50-0 | 41-15-4 | -31,668.10 to +24,347.30 | 0 |

The architectural change is measurable: broad-gate mean planting rose from 77.46 to 160.86 cycles per game, and hard-holdout planting rose from 77.73 to 154.30. On the broad gate the candidate went 60-0 against six non-elite policy families, 5-5 against the current top replay calendar, and 7-3 against the current rank-two replay calendar. On the harder holdout it went 4-6 against the current rank-one win calendar, 9-1 against its loss calendar, 3-3-4 against the source-like top calendar, 5-5 against rank two, and 20-0 against the two deployed 600-level agents.

This is promotion evidence for a live challenger, not proof of a 1000-1500 leaderboard rating. The policy is open-loop: it reproduces a robust elite schedule but does not adapt its task calendar when opponent market actions make a planned purchase fail. Its rank-one losses are therefore expected residual risk and the next technical target is state-conditioned repair without destroying atomic calendar behavior.

The compact tracked ledger at [`research/evaluation/distilled_calendar_validation_2026-08-31.json`](../../research/evaluation/distilled_calendar_validation_2026-08-31.json) records every matchup summary plus SHA-256 digests for the ignored detailed reports and the three public replay controls. This preserves an auditable evidence chain without redistributing the raw Competition Data.

## Bottom line

The conservative agents' strongest guarantees remain valuable: same-day planting water, deterministic routing, bounded fertilizer use, and explicit package equivalence. The audit does not justify removing those guarantees. It does justify replacing several blanket gates with marginal-value decisions:

- planting cutoff by crop, quote, route, and cashable horizon;
- water by survival and production event, not habit;
- CARE by wheat/product spread, banked bonus, held capacity, and next harvest;
- labor by marginal contribution rather than a fixed hand count;
- expansion by paired incremental payback;
- loss by destroyed future value rather than object survival alone;
- market actions by demand clock, opponent concurrency, capacity, and final liquidation.

Those policies are hypotheses until they beat the frozen controls on cloned mechanic checks, untouched paired seeds, both positions, and the captured replay league.