# Mechanisms study: five strong published Kaggriculture agents

What makes these agents strong, stated as decision rules a from-scratch scheduler could execute.
No code was copied and no recorded action tape was extracted.

## Sources and how they relate

| Short name | File (`kaggle_cache/notebooks/`) | Where the logic lives |
|---|---|---|
| **V46** | `ahmedberatozer__kaggriculture-v46-first-turn-microstructure-and-s.py` | agent embedded as `b''.join(...)` chunks |
| **Pipe-7** | `nathanjacob__kaggriculture-pipe-7-wheat-microstructure.py` | agent gzip+b64 in `AGENT_GZ_B64` |
| **ReadyStock** | `alperen5252525__kaggriculture-ready-stock-earlier-sales.py` | agent gzip+b85 in `SOURCE_B85` |
| **ShopRouter-V7** | `aurax7__kaggriculture-shop-router-reactive-v7.py` | plain text; tape in `_R108_DATA` |
| **V34** | `ahmedberatozer__kaggriculture-v34-observed-market-timing.py` | plain text; tape in `_PAYLOAD` |

**All five are one codebase.** Every one of them is a `Chassis` that replays a recorded tape of
~719 action dicts and then rewrites that action through a stack of ~30 reactive layers. The three
decoded agent sources are byte-identical for their first ~3,370 lines. They differ only in (a) which
tape is embedded, and (b) the last two or three layers on the stack:

* Pipe-7 = the common base with `_OPEN_UNITS = 5` (one constant).
* ReadyStock = V46 with `_ADV_LOOK = 6` (one constant, was 3).
* V46 = the base plus a re-engineered turn-0/turn-1 opening and a clone-gated race detector.
* ShopRouter-V7 / V34 = earlier points on the same line with different route tables and top layers.

That makes the split this study wants unusually clean: **the layers are portable policy, the tape is not.**
Tellingly, Pipe-7's own notebook reports that switching on three of the generic chassis guards
(`clamp_sells`, `dead_stock`, expanded terminal planner) *lost* 96%/58%/51% of games — because those
guards are calibrated against a specific tape. The layers below are the ones that are about the game,
not about the tape.

---

# Portable mechanisms

Ranked by (expected value x ease of implementing in a from-scratch scheduler). Nothing in this
section needs a recorded route: each one is a function of the public observation, the engine
constants, and your own plan.

### 1. Sell into the town's demand curve, not into the base price — pick crops by unlocked shops
**Mechanism.** Market inventory starts at `I0 = 10000` for every product and is drained only by the
town. `_town_consume` runs every `townShopSellInterval = 4` steps: each unlocked shop instance removes
1 of each product it sells (2x if the shop sells only one product), and every `townCenterSellInterval
= 24` steps the town centre removes 1 of every non-fertilizer product. Shops unlock on days 3, 6, 9 …
24 (`townShopUnlockInterval = 3`), **drawn with replacement**, capped at `MAX_SHOP_INSTANCES = 8`.
Price rises as inventory falls (`market_price`, scarcity side).

I simulated 200 seasons of pure town drain with no player sales. Median end-of-season price if
*nobody* sells (base price in brackets):

| | WHEAT | CARROT | TOMATO | STRAWBERRY | MELON | EGG | MILK | WOOL |
|---|---|---|---|---|---|---|---|---|
| median deficit vs I0 | 516 | 300 | 192 | 426 | **30** | 210 | 300 | 210 |
| price at that deficit | 48 (25) | 58 (35) | 83 (60) | 293 (120) | 280 (250) | 63 (50) | **311** (160) | 246 (200) |

**MELON appears in no shop at all** — its only demand is the town centre's 1/day, so its price barely
moves up while its glut curve is `sq` (see #2). Melon is a lure.

**Rule.** At day 6 (step 144), read `observation["town"]["unlocked_shops"]` and commit the mid-game
production mix to whatever those shops consume. ShopRouter-V7 does exactly this: its `_router` reads
`unlocked_shops[:2]` once at step >= 144 and never revisits it (except a terminal switch at step 648).
The concrete gates the lineage ships:

* **Tomato expansion** (`_v219_qualifies`): requires `>= 3` instances of PIZZA_SHOP/FARMERS_MARKET,
  `money >= 12000`, `prices["TOMATO"] >= 70`, and the SE quadrant still `LOCKED`. Then it buys land
  + 10 TOMATO seeds + hires.
* **Sheep/wool expansion** (`_v233_eligible`): requires `>= 2` YARN_STORE instances,
  `prices["WOOL"] >= 220`, `prices["WHEAT"] <= 45`, quadrants exactly `{NW,NE,SW}`, a clear SE block,
  and no sheep already in flight. Then it buys land + 6 SHEEP + 6 wheat + 2 hires on **day 12, hour <= 1**.
* **Cow-for-sheep substitution** (day 9, steps 216-227): if `>= 3` shops, **no** YARN_STORE,
  `>= 2` milk shops (PIZZA_SHOP/ICE_CREAM_SHOP/SMOOTHIE_SHOP), `prices["MILK"] >= prices["WOOL"]`,
  and you already hold `>= 4` cows and `>= 2` sheep, rewrite the pending `BUY_ANIMAL SHEEP` into
  `BUY_ANIMAL COW`.

**Engine rules exploited.** `_town_consume`, `SHOPS`, `MAX_SHOP_INSTANCES`, `_end_of_day`'s
`rng.choice(sorted(SHOPS))` shop draw, `market_price` scarcity side.
**Tape needed?** No. Pure function of `town.unlocked_shops` + `market.prices` + your own board.
**How to measure.** Fix the seed set, force the crop/animal mix to the shop-matched choice vs a fixed
mix, and compare mean own cash across the same worlds.

### 2. Never dump a `sq`/`linear` product; dump `log` products freely
**Mechanism.** The glut side of `market_price` uses a different shape per product. Units you can sell
from `I0` before the price halves / hits the $1 floor, and revenue from the first 50 units:

| | WHEAT | EGG | CARROT | TOMATO | MELON | STRAWBERRY | MILK | WOOL |
|---|---|---|---|---|---|---|---|---|
| glut shape | log | log | sqrt | sqrt | **sq** | linear | linear | **sq** |
| units to half price | >4000 | >4000 | 230 | 135 | 112 | **31** | 38 | **42** |
| units to $1 floor | >4000 | >4000 | 842 | 529 | 158 | **62** | 76 | **59** |
| revenue, first 50 units | 1,127 | 2,244 | 1,482 | 2,411 | **12,098** | 3,648 | 5,430 | **7,655** |

So WHEAT and EGG are effectively infinitely dumpable; WOOL, STRAWBERRY, MILK and MELON must be
metered out in lots of tens, spread across the season, because the town refills their scarcity only
at ~10-20 units/day. This is the quantitative core of the "wool trap" — 59 wool sold in one burst
takes wool from $200 to $1, and it stays there, for you *and* for the opponent.

**Engine rules exploited.** `MARKET_PARAMS` `above_func`/`above_target`, `_shape`, `PRICE_FLOOR`.
Also: `_commit_unit` does **not** add to market inventory when the sale price is 1, so floor sales
do not deepen the glut — dumping at the floor is not self-reinforcing, it is just worthless.
**Tape needed?** No.
**How to measure.** Cap per-turn sales of each premium product at N and sweep N in {4, 8, 16, 1e9};
plot mean own cash.

### 3. Order the market list: inventory-priced orders first, fixed-price orders last
**Mechanism.** `_process_market` walks order **index** `i = 0, 1, 2 …`, and at each index it quotes
both players' current unit at the *same* pre-commit inventory, commits, and repeats until that index
is exhausted — then moves to `i+1`. SELL and BUY_PRODUCT prices depend on inventory; BUY_SEED,
BUY_ANIMAL, HIRE and BUY_LAND are fixed-price and index-insensitive. Therefore:

1. **SELLs first** — they add cash and free shed room before anything that needs either
   (`_commit_unit` fails a BUY_PRODUCT if `money < price` **or** `sum(shed) >= shedCapacity`, and a
   failed unit **aborts the whole order**, `order_states[player_id] = None`).
2. **BUY_PRODUCT next** — a purchase at a lower index meets the rival's same-item purchase at the
   same index or earlier, i.e. at unlifted quotes.
3. **Everything fixed-price last.**

Exception both implementations carve out: the SELL leg of a same-turn `BUY_PRODUCT X … SELL X` wash
stays *behind* its buy leg. ShopRouter-V7's `frontload` additionally simulates the old and new order
under 0 and 1 units of rival pressure and declines the reorder if either would become unaffordable.
`maxMarketOrdersPerTurn = 10`; orders past index 9 are silently dropped, so ordering also decides
what survives.

**Engine rules exploited.** `_process_market` index loop, `_commit_unit` cash/capacity checks and
abort-on-failure, `maxMarketOrdersPerTurn`.
**Tape needed?** No — this is a pure sort of the order list you were going to emit anyway.
**How to measure.** Emit the identical order multiset in plan order vs sorted order over a fixed
seed set; the difference is pure microstructure.

### 4. Sell on the first step after a town tick, never on the step before one
**Mechanism.** In `interpreter`, one step runs: unit actions -> `_process_market` -> `_town_consume`.
So the market at step `t` is quoted on inventory that includes every town tick at steps
`0, 4, 8 … <= t-1` but **not** the tick at `t` itself. Price is therefore flat across each block
`[4k+1 … 4k+4]` and steps up at `t == 1 (mod 4)`.

* Selling at `t = 4k` instead of `t = 4k+1` throws away one tick's worth of scarcity for free.
* Within a block, selling *early* is strictly better, because the opponent's supply may land first.

The lineage encodes exactly this: `Chassis._sell_lead` pulls next step's planned sales forward to now
**only when `step % 4 != 0`** ("no town consumption between the two steps"), and skips the pull at
shop-unlock boundaries (`step % 72 == 0`).

**Engine rules exploited.** Statement order inside `interpreter`; `townShopSellInterval = 4`;
`townCenterSellInterval = 24`.
**Tape needed?** No. Any scheduler can phase its sale steps to `t % 4 == 1`.
**How to measure.** Take a fixed sale schedule and shift every sale step by +1/-1/+2; compare revenue.

### 5. Sell ready stock as soon as it is in the shed — the shed deposit and the sale happen in the same turn
**Mechanism.** Unit actions resolve *before* `_process_market` in the same step, so a hand standing
on a shed-access tile can `DROP`/`PLACE` its harvest and the market order in that same turn can sell
it. There is no one-turn lag. The lineage's "sale advance" layer therefore does: *if the plan sells
product X within the next `LOOK` turns and the units are already in the projected shed, sell them
now.* Parameters actually shipped:

* `LOOK`: 2 (ShopRouter-V7), 3 (V46), **6 (ReadyStock, the headline change — 56W/8L vs 48W/16L on
  their 64-game panel)**.
* Items: `("STRAWBERRY","WOOL","EGG","MILK","MELON","CARROT","TOMATO")` — never WHEAT (animal feed),
  never FERTILIZER (field input), never seeds/animals.
* Never on the dawn turn `step % 24 == 23`; never when this turn already has a `BUY_PRODUCT`;
  never for an item a unit is `PICKUP`-ing this turn; only when `price >= 2`; highest price first.
* The **first-listed** sale of the target turn is left alone (it funds the same-turn feed purchase).
* Active window `144 <= step < 718`.

The "projected shed" is worth building as a primitive: shed contents after this turn's unit actions
but before the market, accounting for PICKUP (removes), DROP and non-animal PLACE (adds, capped at
`shedCapacity`).

**Engine rules exploited.** `interpreter` applies unit actions before `_process_market`; SELL
quantities are caps, not commitments (`_commit_unit` just stops when the shed empties), so an
over-large SELL is safe and a later planned SELL still sweeps whatever arrived since.
**Tape needed?** The published implementations read the *tape* to know what "the plan sells soon"
means — but a from-scratch scheduler knows its own forward plan, so this is portable verbatim.
**How to measure.** Sweep `LOOK` in {0, 2, 3, 6, 12} against a fixed opponent set; ReadyStock's whole
contribution is that one sweep.

### 6. Rank the sales *within* one turn by price loss, not by headline revenue (V34's contribution)
**Mechanism.** Reimplement `market_price` exactly inside the agent (V34 copies `_shape`, the `hinge`
branch with `HINGE_GAIN = 8.0`, `PRICE_FLOOR`, and all of `MARKET_PARAMS`, then merges any
`market["params"]` overrides). For each SELL order in a contiguous run of SELLs, score

```
priority(order) = sum_j price(item, inv + j)  -  sum_j price(item, inv + batch + j)      j = 0 .. qty-1
batch = min(24, max(8, rival's visible ripe yield_units of that item))
```

i.e. *how much revenue this lot loses if a plausible rival batch lands first*. Sort the run descending.
Only reorders when the run's items are distinct. `batch` is derived from public tiles only: sum of
`yield_units` over the rival's tiles whose `crop`/`animal` matches the product; the floor of 8 is an
explicit scenario, not a claim about the hidden rival shed.

This is the right objective: the fragile `sq`/`linear` products (WOOL, MELON, MILK, STRAWBERRY) sort
to the front automatically, and WHEAT/EGG sort to the back, without a hand-written priority list.

**Engine rules exploited.** `market_price` is deterministic and fully specified in the public
observation (`market.inventory` + optional `market.params`), so the agent can price its own orders
exactly. Rival ripe yield is public via `farms[1-player].tiles[...]["yield_units"]`.
**Tape needed?** No.
**How to measure.** Same order multiset, priority-sorted vs price-sorted vs plan order.

### 7. Read the opponent's sales exactly, from public data
**Mechanism.** Market inventory is public and town consumption is deterministic, so last turn's rival
supply is recoverable with no hidden information:

```
rival_sold(item) = inv_t(item) - inv_{t-1}(item) + town_drain(t-1, shops) + my_buys - my_sells
town_drain(step, shops) = (step % 4 == 0 ? sum over shop instances: 2 if single-product else 1 : 0)
                        + (step % 24 == 0 ? 1 per non-fertilizer product : 0)
```

The lineage's `_race_town` / `_race_lost` compute exactly this and use it to answer one question:
*did the rival sell a product I am holding, last turn?* If yes, it escalates its sale-pull-forward
horizon from 8 turns to 24.

**Caveat found in their code:** `_race_town` applies the town-centre tick only over
`_RACE_ITEMS = (CARROT,TOMATO,STRAWBERRY,MELON,EGG,MILK,WOOL)`, while the engine's
`TOWN_CENTER_PRODUCTS` is *every* non-fertilizer product — so their wheat attribution is off by one
per day. Get this right in a fresh implementation.

**Engine rules exploited.** `_town_consume` determinism; public `market.inventory`.
**Tape needed?** No.
**How to measure.** Log the estimator against ground truth from a replay; then A/B the behaviour it
gates.

### 8. Hire aggressively and early — labour is nearly free, but only before hour 2
**Mechanism.** `_hire_cost(n) = farmHandCostMult * fib(n)` with `fib = 1,1,2,3,5,8,13,21,34,55`, and
`hires_today` resets every `_end_of_day`. **Ten hands cost $143 for the day.** Hands are wiped each
night (`farm["hands"] = []`), so this is a per-day rental, not an investment.

The binding constraint is not money, it is *daylight*: the lineage's comment sizes a full watering
tour as "2 entry moves + 9 moves between tiles + 10 waters" = 21 turns, so **a hire must be requested
by hour <= 2** to be useful that day; `_v233_request` uses `hour <= 1` for its commit turn and
`hour <= 6` for servicing already-committed work. Hands spawn on shed-access tiles (`_spawn_hand`),
which is also where PICKUP/DROP happen, so the first action of a fresh hand is nearly free.

**Engine rules exploited.** `_do_hire`/`_hire_cost` fib schedule, `hires_today` reset in `_end_of_day`,
`_spawn_hand` placement, `turnsPerDay = 24`.
**Tape needed?** No.
**How to measure.** Sweep the daily hire count at a fixed hire hour, then sweep the hire hour at the
best count; the curve should collapse past hour ~3.

### 9. Fertilizer is free from animals and doubles the watering bonus — route it onto wheat/carrot
**Mechanism.** `_daily_refresh_animals` sets `fertilizer_available = True` on **every** surviving
animal **every day**, so each animal is a free 1 FERTILIZER/day factory via `COLLECT_FERTILIZER`.
`FERTILIZE` sets `fertilized_until_day = day + 2` (3 days inclusive). For non-ongoing crops the
payoff is inside `WATER`: on days `age in [(max_yield_day+1)//2 … max_yield_day]` a watering adds
`2 if fertilized else 1`, capped at `max_yield`.

* WHEAT (`first 2, max_day 4, max_yield 6`): water window days 2-4. Unfertilized harvest = 1+3 = **4**;
  fertilized = 1+6 = 7 -> capped at **6**. One FERTILIZE buys +2 wheat.
* CARROT (`first 2, max_day 3, max_yield 4`): window days 2-3. 1+2 = **3** vs 1+4 = 5 -> capped **4**. +1.

For *ongoing* crops the bonus lives in `_daily_refresh_plants` and requires `was_watered` that day —
fertilizer on an unwatered plant is wasted.

V46's `_r51_input_*` layer turns this into a beam search (width 8, depth 8): for every wheat/carrot
tile still inside its window it forecasts which future turns will water it and when it will be
harvested, values the extra units at `price - 2`, subtracts `1.5 x` the marginal fertilizer price
per application, and routes up to 2 spare workers along the best path that finishes before hour 23.

**Engine rules exploited.** `_apply_unit_action` WATER bonus window and `FERTILIZE` 3-day span;
`_daily_refresh_animals` `fertilizer_available = True` unconditionally; `_daily_refresh_plants`
`fertilized = was_watered and ...`.
**Tape needed?** No (the beam search needs *a* forward plan, which you have).
**How to measure.** Count harvested units per planted tile with the fertilizer router on vs off.

### 10. Skip feeding on days that produce nothing — an animal survives one missed day
**Mechanism.** `_daily_refresh_animals` only removes an animal at `consecutive_unfed >= 2`, and
production fires on `days_since_first % interval == 0` regardless of feeding. Feeding matters for
(a) survival every second day, (b) consuming a `pending_care_bonus` (only counted `if fed_today` on a
production day), and (c) accruing one (`cared_today and fed_today`). So feeding on a day that is
neither a yield day nor a care-accrual day costs 1 WHEAT for nothing.

V46's `_r85_feed` layer does this between day 10 and 28, before hour 22, only when
`consecutive_unfed == 0` (i.e. safe to skip), and only when
`bonus * (price(product) + 5) * 1.25 < price("WHEAT")`, and only when it can confirm the next feed
opportunity exists.

Intervals: GOOSE first 4 / every 1 (EGG), COW first 8 / every 2 (MILK), SHEEP first 6 / every 3 (WOOL).
A sheep therefore yields on one day in three but the naive schedule feeds it three times.

**Engine rules exploited.** `_daily_refresh_animals` escape threshold of 2, yield interval arithmetic,
care-bonus gating on `fed_today`.
**Tape needed?** No.
**How to measure.** Wheat consumed per unit of animal product, with the skip rule on vs off.

### 11. Keep a wheat feed reserve; sell only above it
**Mechanism.** WHEAT is the only product with an input obligation (`FEED` consumes 1 WHEAT from the
unit's inventory). V46's warehouse layer computes `reserve = sum of all future PICKUP WHEAT
quantities up to the next planned BUY_PRODUCT WHEAT` and refuses to sell wheat below it; when the
shed is about to overflow it sells the highest-priced **non-WHEAT, non-FERTILIZER** stock first and
only touches wheat as a last resort. Its `_r95_replenish` layer conversely trims planned wheat
*purchases* down to `reserve - held` on days 10-11. An emergency `_v234_rescue` buys at most 6 wheat
per day, only before hour 14, only when `money >= 1000 + shortage * (quote + 10)` and the shed has room.

**Engine rules exploited.** `FEED` consumes from farmer inventory (not the shed) so the wheat must be
picked up first; `shedCapacity = 100` with **overflow silently destroyed** at `_drop_inventories_to_shed`.
**Tape needed?** No.
**How to measure.** Count animal deaths (`consecutive_unfed >= 2` transitions) and destroyed overflow
units per game.

### 12. Never let the shed overflow at dusk
**Mechanism.** At `_end_of_day`, `_drop_inventories_to_shed` pushes every unit's inventory into the
shed up to `shedCapacity = 100` and **discards the rest**. The lineage's `room_guard` fires at
`step % 24 == 23` and projects
`shed + carried + harvested_this_turn - fed/fertilized/placed + buys - fillable_sells`, and if that
exceeds `capacity - 1` it appends SELLs, preferring products **with no future planned sale first**,
then highest price.
**Engine rules exploited.** `_drop_inventories_to_shed` overflow discard; `_commit_unit` BUY_PRODUCT
and BUY_ANIMAL both refuse when `sum(shed) >= capacity`.
**Tape needed?** No.
**How to measure.** Units destroyed per game (instrument the dusk drop).

### 13. Liquidate everything on the last acting step
**Mechanism.** The episode ends at `episodeSteps = 720`; the interpreter marks DONE at
`step >= episodeSteps - 2`, so **step 718 is the last step whose action is processed**, and reward is
`farm["money"]`. Unsold stock is worth zero. `_terminal_liquidation` replaces the whole market list at
`step >= 718` with `SELL item qty` for the entire projected shed (up to 10 orders).
The lineage also switches its route to a dedicated terminal plan at step 648 (day 27) and spends the
last three days walking everything to the shed. Note the 10-order cap: you can liquidate at most 10
distinct products, which is exactly `len(PRODUCTS)` — but only if you don't waste slots.
**Engine rules exploited.** `interpreter`'s `step >= cfg.episodeSteps - 2` DONE condition; reward = money.
**Tape needed?** No.
**How to measure.** Value left in the shed at the final step; should be 0.

### 14. Detect a clone and race it
**Mechanism.** Two public signals, combined:

* `_r37_similarity`: identical `unlocked_quadrants`, and the fraction of tiles where
  `(crop, animal)` matches between the two farms, over tiles non-empty in either farm, requiring
  `>= 8` such tiles. Empty tiles are deliberately excluded so unrelated layouts can't look alike.
* `_race_positions_equal`: the rival's `farmer` and `hands` position lists are element-wise equal to
  yours. Tracked over a 6-turn history; a clone is declared at `>= 4` of the last 6 matching **and**
  similarity `>= 0.95`.
* V46 adds a one-shot gate at step 1: if the rival's cash after turn 0 equals yours to within 0.5,
  they ran your exact opening.

When a clone is detected, the pull-forward horizon for sales goes 2 -> 8 turns; if the rival is
actually observed winning a sale race (#7), it escalates to 24 turns (a full day).

**Why it matters:** in a mirror, both agents want to sell the same product at the same step, and the
market is shared and lockstep — whoever lists earlier gets the pre-impact quote. Against a clone the
*only* edge available is timing.
**Tape needed?** The detector is tape-free; the thing it escalates (pull-forward) is the portable #5.
**How to measure.** Win rate against a copy of yourself with the horizon fixed at 2 vs escalating.

### 15. The opening wheat round trip — real, but small and situational
**Mechanism.** `_commit_unit` quotes a BUY_PRODUCT at `market_price(item, inventory - 1)`, i.e. at
post-buy inventory, explicitly "so a buy/sell round-trip against an unchanged market nets zero". It
is exactly zero against yourself: buying `n` pays the prices at deficits `1…n` and selling them back
receives the prices at deficits `n…1` — the same multiset. Its *purpose* is that the buy leg drops
market inventory and therefore **lifts the quotes of a rival BUY_PRODUCT at a later index in the same
turn**, while the sell leg gives it all back.

It is also where the lineage's biggest published swing lives, in both directions:

* Pipe-7 changed one constant, `_OPEN_UNITS` 70 -> **5**, and reports 179-1 in a 10-agent, 900-game
  tournament and 1,754-46 over 1,800 games. Their sweep: quantities 5-65 all beat 70; 75 goes 2-48
  and 80 goes 0-50. The round trip is neutral in isolation but **not** once a rival trades inside the
  same lockstep window, and the loss scales with how many units you expose.
* ShopRouter-V7 uses 10. V46 abandons the symmetric trip entirely: it buys
  `[BUY_PRODUCT WHEAT 7, SELL WHEAT 2]` at turn 0 index 0 (keeping exactly the 5 feed units at the
  cheapest quotes of the game), then at turn 1 prepends `BUY_PRODUCT WHEAT 30` at index 0 — ahead of
  where every agent in this lineage buys its feed, at index 1 — and sells the 30 back at turn 2 when
  no tape trades. Gated on `money >= 2860`.

**Honest ranking note:** this is last among the portable items on *expected value for a
from-scratch agent*, because the V46 form is an attack tuned to a specific opponent population (it
assumes the rival buys feed at index 1 of turn 1). The *defensive* half is unconditional and free:
**buy only the feed you actually need, at index 0 of turn 0.** Starting shed is empty
(`_new_private`) and starting money is 3000, so the tape's `SELL WHEAT 60` at step 0 is a no-op that
burns an order slot.
**Engine rules exploited.** `_commit_unit` BUY_PRODUCT quoted at `inventory - 1`; per-index lockstep
in `_process_market`; empty starting shed.
**How to measure.** Sweep opening buy quantity in {0, 5, 10, 30, 70} against a fixed opponent panel —
this is the single cheapest experiment in the whole study.

---

# Tape-dependent tricks

These only work because the agent is replaying a recorded route, and are set aside.

1. **Route selection from a lookup table.** `_router` reads `tuple(unlocked_shops[:2])` at step >= 144
   and indexes `_R108_SHOP_ROUTES` (a table of pre-recorded routes keyed by shop pair), falling back
   to a legacy table `_R110_OLD_SHOPS` when YARN_STORE is one of the first two. At step >= 648 it
   hard-switches to route 2. *Portable residue:* the **timing** (commit at day 6, switch to a terminal
   plan at day 27) and the **key** (the first two shops) — not the table.
2. **`future_sells(route, item, step)`** — suffix sums of planned SELL quantities read off the tape.
   Used by `budget_guard`, `room_guard` and `dead_stock`. A real planner knows its own forward plan,
   so this is a tape *implementation* of a portable idea.
3. **`_block_requirements` / `budget_guard`** — replays tape steps `[t, t+72)` to total up future
   hires, land, seeds, animals and product purchases, then sells to cover the shortfall. The 72-step
   (3-day) block boundary is an artifact of the tape's structure.
4. **`weed_repair` pending queue** — when a tape `PLANT`/`BUILD_*` lands on a weed it substitutes
   `DIG` and re-queues the original for a later step where the tape action would be a no-op, with a
   special case that refuses to replay a PLANT if the tape's next action is a move (so the mandatory
   same-day WATER could not follow). This is entirely about repairing a fixed script; a live planner
   just re-plans.
5. **`_adv_future` / `_r36_reserve` "debts" bookkeeping** — pulling sales forward off the tape while
   tracking which future tape SELL each advanced unit was borrowed from, so the tape's own later SELL
   doesn't double-sell. A live planner mutates its plan instead.
6. **`front_run(opponent_plan)`** — a hook that reads a *supplied copy of the opponent's tape* and
   sells MILK/WOOL/STRAWBERRY/MELON one step before they do. Needs the rival's route. The tape-free
   substitute is #7 (observe their sales) + #14 (detect a clone) + #5 (advance your own).
7. **Hard-coded opening pattern matches.** Every opening layer is guarded by an exact equality test
   against the tape's own order list, e.g.
   `action["market"] == [["BUY_PRODUCT","WHEAT",5],["BUY_PRODUCT","WHEAT",10],["SELL","WHEAT",60]]`,
   and by `standard = all(configuration.get(k,v) == v for ...)` over boardSize/turnsPerDay/
   shedCapacity/maxMarketOrdersPerTurn/startingMoney. Useful pattern to copy (fail safe to the base
   plan under a non-default configuration), useless content.
8. **Day-indexed constants.** `day == 12, hour <= 1` for the sheep commit; `steps 216-227` for the
   cow swap; `days 10-11` for the wheat purchase trim; `day in (24, 27)` for tomato fertilizer.
   These are calendar positions in a specific route, not laws of the game — re-derive them.

---

# Per-agent notes

**V46 — "first turn microstructure and sale timing."** The base chassis plus three things:
(a) the turn-0/turn-1 opening described in #15, replacing the symmetric round trip with a minimal
feed buy at index 0 of turn 0 and a 30-unit quote-lift at index 0 of turn 1 that is unwound at turn 2;
(b) `_ADV_LOOK = 3` sale advance plus `_adv_frontload` order sorting (#3, #5);
(c) a hardened race detector (`_RACE_HORIZON_MIRROR = 24`) that declares a lost race only when the
rival sells a held product *further ahead of the common plan than the lineage's own lead window* —
i.e. it distinguishes "a clone doing what clones do" from "a clone actually beating me", checking
that no sale of that item is planned within the next 5 turns but one is within 24. Reported 88.8%
strict win rate over 1,216 independent games, +24.6 points against the clone family specifically.

**Pipe-7 — "wheat microstructure."** Literally one constant: `_OPEN_UNITS` 70 -> 5. Its notebook is
the most useful of the five as *methodology*: it documents that enabling `clamp_sells` cost 96% of
games, `dead_stock` 58%, and that widening the R37 horizon or the terminal planner did nothing,
because "block boundaries already cap the window". Read it as evidence that the chassis guards are
tape-calibrated and the microstructure constants are not. The claimed effect is ~$250/game.

**ReadyStock — "ready stock, earlier sales."** V46 plus `_ADV_LOOK = 6` (from 3). One constant, the
sale-advance lookahead of #5. Reports 56W/8L on a 64-game local panel vs 48W/16L for its predecessor
and 42W/8L/14T for unchanged V46. Selection was by match points, then worst-opponent match points,
then cash margin, before opening a holdout — a defensible protocol worth imitating.

**ShopRouter-V7 — "shop router reactive."** The clearest expression of #1: a day-6 commitment keyed
on the first two unlocked shops, plus the reactive expansions (tomato on >= 3 PIZZA/FARMERS_MARKET
instances with money >= 12,000 and TOMATO >= 70; sheep on >= 2 YARN_STORE with WOOL >= 220 and
WHEAT <= 45; cow-for-sheep when milk shops >= 2 and no YARN_STORE and MILK >= WOOL). Notably it runs
with `budget_guard`, `room_guard`, `clamp_sells`, `dead_stock`, `terminal_liquidation` and
`front_run` all **False** — only `hand_align`, `weed_repair` and `sell_lead` on. Its top layer is a
clean, self-contained `advance_sales` + `frontload` pair with an affordability simulation before it
accepts a reorder. `OPEN_UNITS = 10`.

**V34 — "observed market timing."** Contributes the exact-pricing layer (#6): a verbatim copy of the
engine's `market_price`/`_shape`/`MARKET_PARAMS` used to rank same-turn sales by price loss against a
plausible rival batch, plus the occupied-tile similarity clone detector (#14). Its own notebook is
refreshingly honest: +68.81 mean own cash (95% bootstrap +37.33 to +103.64) but an outcome interval
of +0.00 to +4.69 points that *includes zero*. Also documents verifying its price function against
13,158 exact cases from real observations — a good acceptance test to steal.

---

# Engine exploits found

Things the code relies on that a plain reading of `kaggriculture.py` does not make obvious.

1. **Hiring is almost free.** `_hire_cost = mult * fib(n_already_today)` with `fib(0) = 1`. The first
   ten hands of a day cost **$143 total**, and `hires_today` resets nightly. The real cost is the
   turns the hand has left in the day, not the money.
2. **Unit actions resolve before the market in the same step.** `interpreter` calls
   `_apply_unit_action` for every unit, *then* `_process_market`, *then* `_town_consume`. Harvest ->
   drop -> sell is one turn, not three. And the last of those means selling at `t % 4 == 0` forfeits
   a tick of scarcity that selling at `t % 4 == 1` would have collected.
3. **A failed market unit aborts the entire order.** In `_process_market`, when `_commit_unit`
   returns False the order is set to `None` — not merely paused. Running out of cash or shed room
   mid-order silently drops the remainder. Hence "sells first, buys second".
4. **Order index is price-relevant only for SELL and BUY_PRODUCT.** BUY_SEED, BUY_ANIMAL, HIRE and
   BUY_LAND are fixed-price; HIRE and BUY_LAND are even lifted out of the per-unit loop and executed
   once at the top of their index, in player order. So they belong at the end of the list.
5. **Floor sales don't add supply.** `_commit_unit`: `if price > 1: market["inventory"][item] += 1`.
   Selling at the $1 floor doesn't deepen anyone's glut.
6. **`hinge` below-curves can explode.** CARROT, TOMATO and EGG use `below_func = "hinge"`, which is
   linear in `deficit/T` up to `T` and then gains `8 * (u-1)^2`. TOMATO's `T` is only 200, so a
   season in which PIZZA_SHOP/FARMERS_MARKET are drawn repeatedly can push tomato past $250 —
   4x base — while wheat (sqrt) only reaches ~$48. This is why the lineage's biggest reactive
   investment is a tomato expansion gated on three tomato-consuming shop instances.
7. **MELON has no shop demand at all.** It appears in none of the 8 `SHOPS` entries; its only sink is
   the town centre's 1/day. Combined with `above_func = "sq", above_target = 3.6` (158 units to the
   floor) it is a high-headline, low-capacity product: the first ~50 melons are the most valuable 50
   units in the game (~12,100) and melon 159 is worth $1.
8. **Shops are drawn with replacement.** `rng.choice(sorted(SHOPS))` per unlock, capped at 8
   instances. Duplicates stack: each instance consumes independently, and a *single-product* shop
   (YARN_STORE -> WOOL, PET_CAFE -> CARROT) consumes at 2x. Two YARN_STOREs are 24 wool/day of demand
   against a supply curve that craters after 59 units — which is exactly the `WOOL >= 220` gate.
9. **Animals emit fertilizer unconditionally and daily.** `_daily_refresh_animals` sets
   `fertilizer_available = True` for every surviving animal every day, regardless of feeding or
   production. A herd is a free fertilizer mine.
10. **An animal survives exactly one missed feeding** (`consecutive_unfed >= 2` escapes), and
    production does not require feeding — only the *care bonus* does. Alternate-day feeding is safe.
11. **Watering has a bonus window, not a per-day effect.** For non-ongoing crops the yield increment
    only applies for `age in [(max_yield_day+1)//2 … max_yield_day]`. Watering a day-0 or day-1 wheat
    plant does nothing for yield — it only resets `consecutive_unwatered`, and two unwatered days turn
    the plant into a WEED.
12. **Atomic PLANT validation.** If the total PLANT requests for a crop in one turn exceed the seeds
    held, the interpreter drops **all** PLANT requests for that crop, not just the excess. Over-issuing
    plant orders loses the whole turn for that crop.
13. **Movement onto LOCKED tiles is allowed**; only tile operations no-op there. Hands can path
    across locked quadrants, and three of the four shed-access tiles start LOCKED — shed ops
    (DROP/PICKUP/PLACE-to-shed) are checked *before* the LOCKED guard, so they work from those tiles.
14. **Step 718 is the last action processed** (`step >= episodeSteps - 2` -> DONE), and reward is
    `money`. Anything in the shed at 719 is worth nothing.
15. **Seeds never pass through the shed.** `private["seeds"]` is separate and is not subject to
    `shedCapacity`; `PLANT` consumes directly from it. Stockpiling seeds is free storage.

---

# Confidence

**Verified in code** (I read the engine function and the agent code that uses it):

* All engine facts in "Engine exploits found" — each is quoted from
  `.conda/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`
  (`_process_market`, `_commit_unit`, `_apply_unit_action`, `_do_hire`/`_hire_cost`,
  `_town_consume`, `_daily_refresh_plants`, `_daily_refresh_animals`, `_drop_inventories_to_shed`,
  `_end_of_day`, `interpreter`, `market_price`, `MARKET_PARAMS`, `SHOPS`, `_new_private`).
* Every threshold quoted in "Portable mechanisms" (`_ADV_LOOK`, `_OPEN_UNITS`, `_ADV_ITEMS`,
  the `>= 2 YARN_STORE / WOOL >= 220 / WHEAT <= 45` gate, the `>= 3 PIZZA/FARMERS_MARKET /
  money >= 12000 / TOMATO >= 70` gate, `min_sell_price = 2`, `block_turns = 72`,
  `_RACE_HORIZON_CLONE = 8`, `_RACE_HORIZON_ESCALATED = 24`, `batch = min(24, max(8, standing))`,
  the `step % 4 != 0` lead condition, `step % 24 == 23` dawn exclusion, `CROP_MIN_PRICE = 70`,
  `MAX_ORDERS = 10`) is read directly from the decoded agent sources.
* The five agents being one codebase: confirmed by diffing the three decoded `main.py` files —
  ReadyStock differs from V46 by 3 appended lines, Pipe-7 by one constant plus the V46-only opening
  and race refinements.

**Computed by me** (ran the engine's own `market_price` and a 200-seed replica of `_town_consume`):

* The glut-capacity table in #2 and the town-deficit table in #1. The town simulation replicates
  `_town_consume` + `_end_of_day`'s shop draw but uses `random.Random(seed)` rather than the engine's
  `Random((seed * 1_000_003) ^ day)` per-day reseed, so the *distribution* is right and any single
  seed's shop sequence is not. Treat the medians as indicative, the price-vs-deficit column as exact.

**Inferred, not proven:**

* The causal story for Pipe-7's 70 -> 5 cliff. I verified that a round trip is exactly cash-neutral in
  isolation and that the buy leg lifts a rival's later-index quotes; I did **not** reproduce the
  0W-50L collapse at quantity 80, and the notebook gives win rates rather than a mechanism. Treat the
  *sweep* as the finding and the explanation as a hypothesis.
* The claim that the day-6 shop commitment is the *right* decision point rather than an artifact of
  two shops existing by then. It is the point at which exactly 2 instances exist, which is suggestive,
  but the lineage never reports a sweep over the commitment day.
* Relative ranking within the portable list. The ordering is my judgement of
  (effect size implied by the notebooks' own ablations) x (lines of code in a fresh scheduler);
  only #15 (opening quantity) and #5 (sale lookahead) have published single-variable sweeps behind them.

**Deliberately not examined:** the recorded action tapes (`_R108_DATA`, `_PAYLOAD`,
`AGENT_GZ_B64`/`SOURCE_B85` route arrays) and the embedded terminal-closure planner blobs.
