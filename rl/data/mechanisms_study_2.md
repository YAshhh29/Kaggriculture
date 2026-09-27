# Mechanisms study 2: the V54/V55 generation

Companion to `mechanisms_study.md` (five agents, the V34-V46 generation). Same rules: no code
copied, no recorded action tape extracted, no embedded stream library extracted.

## Sources

| Short name | File (`kaggle_cache/notebooks/`) | Payload | Decoded `main.py` |
|---|---|---|---|
| **V55** | `ahmedberatozer__kaggriculture-v55-one-turn-market-race-edge.py` | `SOURCE_BLOB` = `''.join((...))`, b85 + zlib | 1,014,183 B / 6,658 lines |
| **Anhad** | `anhadmahajan06__kaggriculture-autonomous-ai-farming-agent.py` | `_PAYLOAD`, b64 + zlib | 1,020,006 B / 6,638 lines |
| **Lynn** | `lynnsakurai__farmer-john-and-the-idle-seller.py` | `SOURCE_B85`, b85 + zlib | 1,022,106 B / 6,720 lines |
| **Degnon** | `degnonguidi__best-agent-ranking.py` | `FILES` dict (main.py + LICENSE + NOTICE), b85 + zlib | 1,018,142 B / 6,594 lines |

None of these use `%%writefile main.py`, so `rl/public_agents.py` cannot load them as-is; they write
`main.py` from a compressed blob. Decode recipe: parse the writing cell with `ast`, find the largest
`Assign` / `str.join` / `FILES` dict literal, `zlib.decompress(base64.b85decode(...))`. Nine lines in
each file are the tape blobs (>300 chars); everything else is readable policy.

**All four are again one codebase**, two generations on from V46. Diffed as short files (tape lines
elided), V55 vs Anhad is 11 lines, V55 vs Degnon 33, V55 vs Lynn 87 — but V55 vs V46 is 10,280 lines.
The stack has roughly quadrupled: the V46 chassis plus ~40 more reactive layers, several of them
(`# Claude CARROT2 / ORDERPRI2 / CAPHARV / SHEDROOM / HERD2 / COWSWAP layer ... Own implementation`)
clearly machine-built from an ablation harness.

The four differ only in their tails:

* **Anhad** = the common base ("One-More-Wheat + Pipe16 + Metav4"), nothing appended.
* **Degnon** = base + one Apache-2.0 patch ("mature the temporary wheat one extra day") that moves the
  idle-worker harvest from day 2 to day 3.
* **V55** = Degnon's tail + a step-91 visible-wheat-price sale guard (threshold 31) + the headline
  constant `V9_RACE_DEFAULT = 41` (base is 40). **The whole of "one turn market race edge" is `40 -> 41`.**
* **Lynn** = base + a *different* tail: a failure-atomic opening repair and a market-queue closure.
  This is the "idle seller".

---

# New mechanisms

Ranked by (expected value for a from-scratch scheduler) x (ease of implementing without a tape).
Engine references are to `.conda/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`.

### 1. Productive idle workers: grow a throwaway crop on a tile that is not needed yet

**Mechanism.** The route holds several workers on `PASS` for whole days early on, and several tiles
are reserved for structures that are not built until later. Both are free. The shipped opening
(`_alt_install('HybridOpening')`) buys **1 extra WHEAT seed at step 0** and then, on a tile that the
original plan turns into a PASTURE much later:

* steps 2-4: hand 1 walks WEST x3 from the shed access tile to (2,4);
* step 5: `PLANT WHEAT`; step 6: `WATER` (same day — mandatory, see #9);
* step 29 (day 1): the hand that was scheduled to `BUILD_PASTURE` there `WATER`s instead — the pasture
  is not needed yet;
* steps 49-57 (day 2): another idle hand walks WEST x3, `WATER`, `HARVEST`, `BUILD_PASTURE` (restores
  the invariant the rest of the route depends on), `EAST` x2, `DROP`;
* the DROP is detected at step 57 and the harvested wheat is appended to that same turn's SELL order.

Marginal cost: **one $10 seed and zero hires**. Marginal revenue: 4-6 wheat sold on day 2.
Degnon's V54 patch delays the whole second half by one day (harvest at steps 84-91 instead of 49-57)
so the plant gets one more watering inside its bonus window: wheat's window is days 2-4
(`(max_yield_day+1)//2 = 2` to `4`) and `max_yield = 6`, so an extra day is up to +2 units.

Lynn's notebook states the admissibility condition explicitly:
`T_walk + T_plant + T_care + T_harvest + T_restore + T_return <= D`, where `D` is the deadline of the
next obligation the displaced worker actually has, and every displaced command must have been idle
or explicitly restored.

**Engine rules exploited.** `_new_plant` (`yield_units = 1` at planting for non-ongoing crops,
`max_lifespan_step = (day + max_yield_day + 1) * turns_per_day`); `_apply_unit_action` WATER bonus
window; `_end_of_day` wipes hands so an early idle hand costs nothing later; `CROPS["WHEAT"]["seed"] = 10`.
**Tape needed?** No — but it needs *a forward plan*, so you know which tile is free until day k and
which worker is idle until then. A from-scratch scheduler has exactly that.
**Threshold to copy.** Substitute only when the full cycle including the restore fits before the tile's
and the worker's next obligation.

### 2. Empty market slots: turn dead sales into holes, then pull live sales left into them

**Mechanism (Lynn's `_ig_close_queue`, generalising EXP334/EXP335 in the base).** `_parse_order`
returns `None` for `[]` and for any order with `n <= 0`, and `_process_market` iterates the *index*
`i` regardless — so an unfillable SELL **still burns its index**, and the rival's order at that index
gets an unlifted quote all to itself.

Procedure, run on the final action every turn:

1. Compute the projected shed (shed after this turn's unit actions, before the market).
2. Walk the order list in order; for each SELL of a **cash product**
   (`CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL`) compute the executable quantity
   `e_k = min(q_k, max(0, stock_i - sum_{j<k, same item} e_j))`. If `e_k == 0`, replace the order with `[]`.
3. Left-to-right, move each executable cash SELL into the earliest hole to its left; the vacated
   index becomes a hole and joins the queue.

Invariants Lynn's notebook proves and the code preserves: list length unchanged, total executable
quantity per item unchanged, every fixed-price order (BUY_SEED / BUY_ANIMAL / HIRE / BUY_LAND) and
every BUY_PRODUCT keeps its index, and `slot'(u) <= slot(u)` for every unit. The dominance argument is
that cash products cannot be bought by anyone, so their price is non-increasing in market inventory
and moving the same units to a lower index is weakly better.

The base's EXP334 form only does this inside contiguous cash-SELL segments of length >= 2 and only
from `step >= 144`; EXP335 widens it to the case where every order is a SELL. Lynn's version is
unconditional (gated only on `_ig_standard`: boardSize 10, turnsPerDay 24, shedCapacity 100,
maxMarketOrdersPerTurn 10).

**Engine rules exploited.** `_parse_order` returning `None` for `[]` and `n<=0`; the `for i in range(max_len)`
index loop in `_process_market`; `market_price` monotone in inventory.
**Tape needed?** No. Pure post-processing of your own order list — the cheapest item in this study.

### 3. Fit the sale-reservation horizon to the rival's *observed* lead (V55's headline)

**Mechanism.** Study 1 #7 recovered the rival's sales; this generation turns that into a control loop.
Each turn, for every item in `("CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL")` whose last
price was `> 3`:

```
rival_sold = inv_t - inv_{t-1} + town_draw(t-1, shops) - own_sold_{t-1}
```

(`town_draw` = per unlocked shop instance, 2 if the shop sells one product else 1, at `step % 4 == 0`,
plus 1 per item at `step % 24 == 0`). Sales at the $1 floor never enter inventory, hence the `price > 3` gate.
A sale of `>= 2` units counts. If you still hold stock of that item *and* your plan sells it later *and*
the rival's sale is not a "late fill" of your own previous lot (your previous planned sale was at least
`V9_RACE_GAP = 3` turns ago), then `lead = (turns until your next planned sale of that item)` and

```
horizon = clamp(max_lead_seen + V9_RACE_MARGIN, V9_RACE_DEFAULT, V9_RACE_MAX)
```

The horizon is how far ahead of the plan a lot may be pulled forward and sold now. Shipped constants:

| | value | note |
|---|---|---|
| `V9_RACE_DEFAULT` | 40 (Anhad, Degnon, Lynn) / **41 (V55)** | the entire V55 change |
| `V9_RACE_MAX` | 48 | |
| `V9_RACE_MARGIN` | 12 | was 4 |
| `V9_RACE_GAP` | 3 | |
| `V9_RACE_WINDOW` | 30 | turns of plan searched around a rival sale |
| reservation window | `192 <= step < 696` | was 288; day 8, not day 12 |

Published sweeps (their own mirror panels, 80 games/arm): 40/12 beats 6/4 73-7 and beats the previous
32/12 build 74-6. **Deeper is not monotonically better**: 44/12 beats 40/12 head-to-head but its record
against the shallow baseline drops to 65-15, and a constant 48 goes 14-26 against 40/12 — "a horizon
past the rival's next lot gives up town-demand recovery for nothing." V55 reports 41 beating 40 on
110 games/arm (75/9/26 -> 91/15/4, match points 0.800 -> 0.845, paired margin +$61.9) and explicitly
rejects 42 and 43 as regressions. Moving the window start from 288 to 192 was worth 32-0 / 30-2 / 30-2
on three fresh mirror blocks — the first milk and wool lots land on days 8-11 and the same-day
reservation is what takes their price.

**Honest reading:** the horizon curve is flat-topped and noisy near 40; treat "reserve *deep*, around
40 turns, from day 8" as the finding and 41-vs-40 as within noise. The mechanism that matters is
*measuring the rival's lead from public data and sizing your own lead from it*.
**Engine rules exploited.** `_town_consume` determinism; `_commit_unit`'s `if price > 1` inventory guard;
public `market.inventory`.
**Tape needed?** The *implementation* reads the tape to know "when does my plan next sell this". A live
planner reads its own plan. Portable.

### 4. Glut gate: only race a book that is still above its base price

**Mechanism (RACEPX + RACEGATE).** Both the one-turn lead sale and the deep reservation are skipped
for any item whose current quote is at or below its base price:

```
base = {WHEAT 25, CARROT 35, TOMATO 60, STRAWBERRY 120, MELON 250,
        EGG 50, MILK 160, WOOL 200, FERTILIZER 100}      margin = 0
blocked = { item : prices[item] <= base[item] + margin }
```

Reasoning in their own comment: pulling a lot one turn earlier is what takes the price when both sides
hold the same lot — but if the book is already *above* `I0` (quote below base) those units only fetch
less, and one turn of town drain does not pay for it. Their measured realised prices on the frozen
top-20 panel, which is the evidence for the gate:

| | STRAW | MILK | WOOL | MELON | FERT | WHEAT | CARROT | TOMATO | EGG |
|---|---|---|---|---|---|---|---|---|---|
| realised | 107-123 | 98-107 | 129-139 | 212 | 43 | 38 | 54 | 125 | 52 |
| base | 120 | 160 | 200 | 250 | 100 | 25 | 35 | 60 | 50 |

i.e. the shipped build was *flooding* exactly the four products study 1 #2 flags as `sq`/`linear`, and
realising below base on all of them. The gate is the fix.
**Engine rules exploited.** `market_price` above/below branches and `MARKET_PARAMS` base prices.
**Tape needed?** No.

### 5. Exact two-player lockstep simulation as the order-sorting objective

**Mechanism (`_v44y_lockstep`).** Reimplement `_process_market`'s inner loop exactly — per index,
quote both players at the same pre-commit inventory, commit both, repeat — money- and capacity-
unbounded, and return `(my revenue, rival revenue)`. Then, from `step >= 216`, assume the rival
submits *the same order list you are about to submit* (the mirror is the real opponent on this ladder),
find every contiguous run of SELL orders of length 2..6, and brute-force all permutations of each run,
maximising `my_revenue - rival_revenue`. Accept only a gain `> 0.5`.

Two practical points that make the brute force cheap: revenues are additive per item when cash and
shed room are not binding, so the search caches a value per `(item, order-schedule)` key; and runs
longer than 6 are skipped.

This is a strict upgrade on study 1 #6 (`priority = revenue lost if a plausible rival batch lands
first`): instead of a scalar "batch" guess it simulates the actual interleaving, so it captures the
fact that your index-`i` unit and their index-`i` unit are quoted on the *same* inventory and commit
in player order.
**Engine rules exploited.** The whole of `_process_market` / `_commit_unit`; `market_price` is fully
determined by public `market.inventory` + `market.params`.
**Tape needed?** No.

### 6. Track the rival's shed, don't guess it

**Mechanism (`ORDERPRI2`).** Maintain a running estimate `stock[item]` of the rival's sellable stock,
updated every turn from public data only:

* **In:** diff the rival's tiles against last turn. A non-ongoing crop tile that vanished (and is not a
  WEED) or whose `planted_day` changed -> all of its `yield_units` went into their shed. An animal tile
  whose `yield_units` fell -> the drop went into their shed; at `step % 24 == 0` only count it if the new
  value is 0, because `_daily_refresh_animals` also moves it.
* **Out:** the inventory-delta estimator of #3 — every unit they put on the market leaves their shed.

Then sort SELLs by `exposure(item, qty, batch) = sum_{j<qty} price(inv+j) - price(inv+batch+j)` with
`batch = min(30, stock[item])` (`_OR2_CAP = 30`) — i.e. the revenue this lot loses if their *actual*
holdings land first.

**Slot swap.** Between steps 288 and 694, when the list is already at the 10-order cap: find the
highest-exposure premium item (`MILK, STRAWBERRY, WOOL, MELON, EGG`) that is not listed and not being
bought; if its exposure beats the weakest listed SELL by more than `_OR2_SLOT_MARGIN = 20.0`, drop the
weakest (refunding its reservation debts nearest-due-first) and append the new one. The 10-order cap is
a real constraint and this is the only layer that treats it as one.
**Engine rules exploited.** `maxMarketOrdersPerTurn = 10`; public `farms[1-p].tiles[...]["yield_units"]`;
`_daily_refresh_animals`/`_decay_plants`/`_daily_refresh_plants` timing.
**Tape needed?** No.

### 7. Courier: never let premium goods sleep in a worker's hands

**Mechanism (`_v9_courier`).** From `hour >= 12`, any worker that (a) carries
`STRAWBERRY / MILK / WOOL / MELON`, and (b) whose every remaining command today is in
`{PASS, NORTH, SOUTH, EAST, WEST, DROP}`, is rerouted: Manhattan walk to the nearest shed-access tile
(`(4,4),(5,4),(4,5),(5,5)` on a 10-board), then `DROP`. The dropped units are then **inserted at market
index 0** (merged into an existing SELL for that item and that order moved to index 0), skipping items
quoted below $2.

Why it pays, in their own words and confirmed in the engine: `_drop_inventories_to_shed` runs inside
`_end_of_day`, i.e. *after* `_process_market` for step 23 — so cargo left in hand can only be sold the
next morning. And **no town tick falls between hour 20 and the next dawn's market**, so the evening
sale gets the same quote a full day earlier than a rival who waits for the auto-drop. Their own
telemetry: "roughly 40% of the tape's strawberries and milk are still in workers' hands when the day ends."

The walk is free because `_end_of_day` does `farm["farmer"] = _default_spawn(...)`, `farm["hands"] = []`
and `private["inventories"] = [{}]` — **end-of-day position is worthless and hands are re-rented every
morning at shed-access tiles (`_spawn_hand`)**. A worker never needs to "come home".
**Engine rules exploited.** Statement order in `interpreter`; `_end_of_day` position reset and hand wipe;
`_spawn_hand` NWSE shed-access placement.
**Tape needed?** No (it needs to know a worker's remaining commands today — your own plan).

### 8. Value an investment against a simulated forward price path, not against a spot price

**Mechanism (`HERD2` / `COWSWAP`).** To decide whether to buy `k` animals of a species, simulate the
market inventory of its product day by day to day 30:

```
inv_{d+1} = inv_d
          - (6 * (2 if shop sells one product else 1)) summed over unlocked instances   # shop drain
          - 1                                                                            # town centre
          - expected_extra_demand * (shop unlocks expected between now and d)
          + (our scheduled production on day d) + (rival's scheduled production on day d)
price_d = market_price(item, round(inv_d))
```

"Scheduled production" comes from every animal tile on *both* farms (`placed_day`, first-yield day,
interval), plus animals held in shed/hand, plus your own planned purchases — and, if
`similarity >= 0.9`, the rival is assumed to make the same purchases. Per-animal daily output is
`1 + (per - 1) * CARE` with `CARE = 0.8` and `per` = 2 (GOOSE) / 3 (COW) / 4 (SHEEP).

Then

```
EV(option, k) = revenue of the new units along the with-new path
              + sum_d (price_d^with_new - price_d^base) * (our existing future units - rival's existing future units)
              - cost * k
```

The second term is the whole point: extra supply **lowers the price you get for everything else you
were going to sell, and lowers the price the rival gets too** — so the price swing is worth
`(mine - theirs)`, which can be positive when the rival is the bigger holder. Gate to act:
`EV(best) >= 1.3 * EV(status quo)` (`_HD2_RATIO`) **and** `EV(best) - EV(status quo) >= $600`
(`_HD2_MIN_GAIN`). Windows: steps 192-360 (HERD2, at the tape's goose purchase), 144-192 (COWSWAP).

A cheaper shop/price-gated version also ships (`_v9_herd_choose`): SHEEP if `YARN_STORE` unlocked and
`WOOL >= 150` and at most 1 egg shop (BAKERY/BRUNCH_SPOT); else COW if `>= 3` milk shops
(PIZZA/ICE_CREAM/SMOOTHIE) and `MILK >= 150` and 0 egg shops; else keep geese. Compare with study 1's
`WOOL >= 220` / `MILK >= WOOL` gates — this generation lowered the wool bar and added an egg-shop veto.
**Engine rules exploited.** `market_price`, `_town_consume` drain arithmetic, `ANIMALS` yield schedules,
`townShopUnlockInterval = 3`, `MAX_SHOP_INSTANCES = 8`.
**Tape needed?** No.

### 9. Never issue a PLANT that cannot be watered the same day

**Mechanism (`_r127_last_hour`).** `_new_plant` sets **`consecutive_unwatered = 1` — "planting day
counts as unwatered"** — and `_daily_refresh_plants` converts the tile to a `WEED` at
`consecutive_unwatered >= 2`. So a plant that receives no WATER on its planting day **is a weed by
dawn**: the seed, the tile and the turn are all lost, and you inherit a DIG.

At `step % 24 == 23` the layer clones the farm state, applies its own turn's unit actions, and drops
any PLANT whose tile does not end the turn as a `PLANT` of that crop with `planted_day == today` and
`watered_today == True` (i.e. some *other* unit on that tile watered it in the same turn — the planter
cannot). It then **re-runs the check**, because removing a rejected request can unblock the engine's
atomic per-crop PLANT batch (study 1, engine exploit #12).
**Engine rules exploited.** `_new_plant` initial `consecutive_unwatered = 1`; `_daily_refresh_plants`
weed threshold; atomic PLANT validation.
**Tape needed?** No.

### 10. Harvest animals that are about to hit their production cap

**Mechanism (`CAPHARV`).** `_daily_refresh_animals` does
`tile["yield_units"] = min(a["max_held"], yield_units + base + bonus)` with
`max_held = 4` (GOOSE) / `6` (COW) / `6` (SHEEP). Production above the cap is **silently destroyed**.
The layer projects every tile's remaining visits today (walking each worker's remaining commands
forward, including hands that a pending HIRE will spawn), and if an animal would be clamped tonight it
rewrites a `COLLECT_FERTILIZER` or `CARE` on that tile into a `HARVEST`. Shed guard: it stops when the
projected shed is at or above `_CH_SHED = 90`.
A goose at 2 eggs/day with `max_held = 4` must be harvested every other day or it stops paying.
**Engine rules exploited.** `ANIMALS[*]["max_held"]`, `_daily_refresh_animals` clamp.
**Tape needed?** No.

### 11. Ripe crops rot: `_decay_plants` runs every step

**Mechanism.** Not a layer — an engine rule the `_ca_yield_path` forecaster encodes and study 1 missed.
`_decay_plants(farm, step)` runs **every step**, after the market and town tick. For a non-ongoing plant
with `max_lifespan_step = (planted_day + max_yield_day + 1) * 24`, once `step >= mls` and
`(step - mls) % 2 == 0`, the tile loses **1 yield unit every 2 steps** and becomes a `WEED` at 0.

A ripe 6-unit wheat therefore evaporates completely in 12 steps — **half a day** — after the start of
day `planted_day + 5`. Their forecaster (`_ca_yield_path`) simulates a tile's future as a list of
`(step, unit, op)` visits and returns `(harvest_units, best_rescue_units, rescue_step)`, so it can
choose to harvest *early at a lower yield* rather than late at zero.
**Engine rules exploited.** `_decay_plants`, `_new_plant["max_lifespan_step"]`.
**Tape needed?** No.

### 12. Overflow management: sell the *cheapest* spare, and do it at hour 21, not 23

**Mechanism (`SHEDROOM` + the v44y pre-guard).** At hours 21/22/23 project
`night_shed + carried - shedCapacity + _SR_MARGIN(8)`; `carried` is computed by walking each unit's
command (DROP on a shed-access tile zeroes it, HARVEST adds the tile's `yield_units`,
COLLECT_FERTILIZER adds 1, FEED/FERTILIZE subtract 1, PICKUP adds). If positive, reserve the next 24
turns' `FEED` wheat and `FERTILIZE` fertilizer, then sell the surplus **cheapest item first**
(`cands.sort()` ascending on price).

That is the opposite of study 1's `room_guard` (highest price first) and is the better rule: you are
choosing which units to give up, and giving up the cheap ones costs least while leaving the premium
stock for its scheduled window.

Separately, the **pre-guard** runs the same dump one or two steps early, at hours 21-22 for
`MILK, STRAWBERRY, MELON, WOOL, TOMATO` — same 4-step town window (so the same quote), but it quotes
*before* a same-tape rival's hour-23 dump.
**Engine rules exploited.** `_drop_inventories_to_shed` overflow discard; `townShopSellInterval = 4`
price blocks; per-index lockstep.
**Tape needed?** No.

### 13. The cash-safe opening — study 1 #15 is now obsolete

**Mechanism.** This generation's tape still opens with the round trip
`step 0: BUY 13, BUY 30, SELL 30` / `step 1: SELL 13, BUY 5` (net +5 wheat), and `_v9_opening`
**replaces it** with `step 0: BUY_PRODUCT WHEAT 20, SELL WHEAT 15` and *nothing at step 1*.

Their stated reason is a cash-cascade, not microstructure: the round trip leaves only ~$6 of slack at
step 32, and against openings that dump wheat into the same slots (`BUY 43 / SELL 20 / SELL 22`, or
`BUY 30 / SELL all`) it ends step 1 **up to $75 short**; the day-1 wheat and HIRE orders then fail, the
herd goes unfed, and by days 5-8 the strawberry seed orders fail too — 18-21 plants instead of 33,
**-$20k to -$65k**. The replacement was verified to leave `>= $1,050` after step 1 against **all 6,648
recorded openings** in their replay corpus (exact market simulation), and $2 more than the round trip
against their own lineage.

Combine with study 1's Pipe-7 finding (`_OPEN_UNITS` 70 -> 5): the whole family has converged on
*buy a small amount, sell most of it back, keep exactly the feed you need, and never be cash-tight*.
**Engine rules exploited.** `_commit_unit` aborting the entire order on a cash failure; `startingMoney = 3000`.
**Tape needed?** No.

### 14. Price the contested buy correctly: `inventory - (2j - 1)`

**Mechanism (`_r127_prefix_bound`).** When both players buy the same product at the same order index,
"both players quote one unit before either commits", so before your `j`-th unit at most `j-1` of your
own and `j-1` of theirs have depleted inventory. The worst-case cost of buying `q` wheat is therefore

```
cost(q) = sum_{j=1..q} market_price("WHEAT", inventory - (2j - 1))
```

not `sum_j price(inv - j)`. The layer subtracts this bound from a hypothetical cash balance and
re-runs its whole budget feasibility check before it will prepend an emergency wheat buy at index 0.
**Engine rules exploited.** `_process_market` quote-both-then-commit-both ordering; `_commit_unit`
BUY_PRODUCT quoted at `inventory - 1`.
**Tape needed?** No.

### 15. Failure-atomic scripted actions (Lynn's `_ig_guard_opening`)

**Mechanism.** The route unconditionally issues `WATER` at step 29 for hand 2, which is only correct if
the step-5 `PLANT` succeeded. Lynn gates it on an observed predicate — tile (4,2) is a `PLANT` of
`WHEAT` with `planted_day == 0` — and if the predicate is false, rewrites the command back to the
original `BUILD_PASTURE`. Generalisable rule for any planner that commits ahead: **every scheduled
action carries its precondition and a fallback**, and the fallback is the action the plan would have
taken had the earlier step not been attempted.

### 16. Cheap substitutions that reuse an existing worker schedule

Three layers share one idea: **swap what a tile/animal produces without touching a single worker
command**, because the schedules coincide.

* **Carrot for wheat** (`V9 CARROT`). CARROT (`first_yield_day 2, max_yield_day 3, max_yield 4`) fits
  the same plant-water-water-harvest cycle as WHEAT (`2, 4, 6`). Watered wheat yields 4, carrot 3, for
  $10 more seed, so swap when `price(CARROT) >= 1.8 * price(WHEAT)` (`V9_CARROT_RATIO`), days 10-23
  (`V9_CARROT_FIRST_DAY/LAST_DAY`), and only while total wheat held `>= 40`
  (`V9_CARROT_WHEAT_RESERVE`) because wheat is feed. Above ratio **3.5** (`V9_CARROT_BOOM_RATIO`) it
  *buys* the feed wheat instead of growing it and drops the reserve to 10.
* **Sheep/cow for goose** (`V9 HERD`, #8 above) — the tape already handles geese exactly like pasture
  animals (build, pickup, place, feed, care, collect fertilizer, harvest), so the species is a free
  parameter at the purchase order.
* **Fertilize instead of water** (`V9 FERT`). From day 14 (`V9_FERT_FIRST_DAY`), a worker carrying
  fertilizer that is about to `WATER` a WHEAT/CARROT planted exactly **1 day ago** (`V9_FERT_AGES = (1,)`
  — watered on its planting day, not yet fertilized) issues `FERTILIZE` instead, and the plan's later
  waters do the rest. Zero turn cost. Rationale: the fertilizer *book* falls from $55 on day 14 to $10
  by day 27, so by then a unit of fertilizer is worth less than two wheat, while fertilizing lifts a
  wheat plant's cap from 4 to 6. It carefully excludes fertilizer that the worker's own remaining
  commands today will spend.

### 17. Skip work that only preserves, on days when preserving is free

**Mechanism (`V13V`).** The tomato crew is hired every day from day 19, but tomatoes planted on day 18
only produce at the refreshes ending days 25-28 — before that, watering only keeps them alive, and a
plant survives one dry day. So on `V13V_SKIP_DAYS = (19, 21, 23)`, if every committed tomato has
`consecutive_unwatered == 0`, **no crew is hired and nobody waters**. Same shape as study 1 #10
(alternate-day feeding), applied to watering. Compounds with #9: you may skip a water, but you may
never skip the *planting-day* water.

### 18. Rival fingerprinting from turn-2 cash (not portable content, portable idea)

`CT_TABLE` maps `(rival money, market WHEAT inventory)` observed at turn 2 to a specific counter-order
script. Their note: under the `BUY 20 / SELL 15` opening this pair "identifies [a rival tape] exactly
(checked unique over 4,604 recorded games)". Two entries ship: `(979.0, 9989)` and `(33.0, 9990)`.
The table is worthless to us; the fact that **the rival's post-opening cash is a near-unique fingerprint
of their opening** is worth knowing, and is the cheapest opponent-model feature in the game.

### 19. Set aside: the prediction library (`v9/2 PREDICT`, `PREDICT2`)

Two layers score the rival's recovered sale ticks over the last 240 turns against **a library of
recorded opponent streams** keyed by the first two unlocked shops, and pre-empt when most of the best
`TOP` streams sell `>= K` units in the next two turns. Parameters: `H = 48`, `K = 4`, `TOP = 1`,
`EVERY = 3`, items `MILK, WOOL, STRAWBERRY`. **This needs a recorded corpus**, and the library excludes
same-parity episodes — a leakage guard worth noting. Not extracted; not portable.

---

# Answers to our weaknesses

### W1. We spend 57% of worker turns walking; they spend 42%

What they do instead, with the code evidence:

1. **They never walk home.** `_end_of_day` sets `farm["farmer"] = list(_default_spawn(board_size))`,
   `farm["hands"] = []` and `private["inventories"] = [{}]`, and `_spawn_hand` puts every new hand on a
   shed-access tile. The courier comment states it outright: *"moves are free: workers respawn at the
   shed at dawn."* Any return trip in the last hours of a day that is not carrying cargo is pure waste.
   Check our agent for end-of-day return walks — that alone could be several percent.
2. **They only walk when the walk ends in a sale.** `_v9_courier_plan` fires only for a worker carrying
   `STRAWBERRY/MILK/WOOL/MELON` whose every remaining command today is in
   `{PASS, NORTH, SOUTH, EAST, WEST, DROP}`, and only if `len(walk) <= end - step`. The walk is the
   cheapest available conversion of an otherwise-idle worker into cash.
3. **They walk *short*.** `_v9_courier_walk` targets `min(access, key=Manhattan)` over the four
   shed-access tiles — and study 1 notes shed ops are checked *before* the LOCKED guard, so all four are
   usable from turn 0. Work is clustered: the sheep/wool expansion uses a fixed 6-tile block
   `((5,5),(6,5),(7,5),(7,6),(6,6),(5,6))` with a nearest-first tour (`_sl_path`), so inter-task moves
   are 1 step.
4. **Their walking is amortised across a whole day's route**, not re-derived per turn. The reactive
   layers rewrite *market* orders freely and unit commands only rarely, and almost every unit rewrite
   (fertilize-instead-of-water, harvest-instead-of-care, plant-instead-of-pass) is an **in-place
   substitution on a tile the worker is already standing on** — zero extra movement.

The concrete test to run on our agent: classify each worker-turn as `move / work / idle`, then for
every `move` ask whether the destination task was already decided when the move started. Moves that
exist because the target changed mid-walk are the recoverable ones.

### W2. We sell 826 units a game; they sell 1,723 at similar prices

Six separate leaks, all of which they plug:

1. **Cargo sleeping in hands.** Courier (#7). Their own number: ~40% of strawberries and milk are still
   in workers' hands at day end, and `_drop_inventories_to_shed` runs *after* the last market of the day.
2. **Dead order slots.** #2 — an unfillable SELL burns its index (`_parse_order` -> `None`), and `EXP334`
   / Lynn's closure recover them. Instrument this on our agent: count orders per turn whose executable
   quantity is 0.
3. **The 10-order cap binding.** `_OR2` slot swap trades the weakest listed SELL for the highest-exposure
   unlisted one whenever the list is full between steps 288 and 694, with a $20 hysteresis margin.
4. **Selling only what the plan planned.** Their reservation horizon is **40 turns from day 8**
   (#3); study 1's generation used 2-6. Any unit sitting in the shed that the plan sells within ~1.7 days
   is sold now.
5. **Production destroyed at the cap.** `min(max_held, ...)` in `_daily_refresh_animals` (4/6/6) and
   `_decay_plants`' 1-unit-per-2-steps rot (#10, #11). Units that never reach the shed can't be sold.
6. **Overflow destroyed at dusk.** `SHEDROOM` sells down to capacity at hours 21-23, cheapest first,
   after reserving 24 turns of FEED/FERTILIZE inputs (#12).

Note that (4) and (5) also explain "at similar prices": they sell 2x the units without crashing the book
because the units are spread over more turns *and* gated on `price > base` (#4).

### W3. We work 35% of turns; they work 51%

1. **Idle workers get a whole production cycle** (#1): plant/water/harvest/restore/deliver a throwaway
   wheat on a tile reserved for a later structure, for one $10 seed and **no extra hire**. Degnon's
   entire published contribution is tuning *when* that crop is harvested.
2. **They convert low-value work into high-value work in place** rather than adding turns:
   FERTILIZE instead of WATER (#16), HARVEST instead of CARE/COLLECT_FERTILIZER (#10),
   BUILD_PASTURE instead of WATER when the plant failed (#15), DROP+SELL instead of PASS (#7).
3. **They delete work that does nothing**: `V13V` skips whole watering days when every plant has
   `consecutive_unwatered == 0` (#17); study 1 #10's feed-skip is still in the stack (`_R85_FEED`).
   Deleted turns become available for (1) and (2).
4. **Hiring is not the constraint, daylight is** (study 1 #8, unchanged here) — `_v233_request` still
   commits at `hour <= 1`.

The measurement to copy: they carry a per-layer telemetry dict (`courier_trips`, `ch_collect_swaps`,
`sr_units`, `or2_slot_swaps`, `v_skipped`, ...) reset at step 0, so every layer's contribution is
countable in a single game. We should do the same before tuning anything.

### W4. Our farm holds 27 crops standing on day 20; they hold 56

1. **"Standing crops" is a flow, not a stock.** `_decay_plants` removes 1 yield unit every 2 steps once
   `step >= (planted_day + max_yield_day + 1) * 24`, and the tile becomes a `WEED` at 0 (#11). A field
   at 56 on day 20 is being *continuously replanted*, not held.
2. **We may be weeding our own plants.** `_new_plant` starts at `consecutive_unwatered = 1`; an unwatered
   planting day is an immediate weed at the first `_daily_refresh_plants` (#9). Any PLANT we issue at
   hour 23, or whose watering worker gets diverted, is a destroyed tile *and* a DIG obligation.
   `_r127_last_hour` exists precisely because this happens. **Check this first — it is cheap to
   instrument** (count tiles that go PLANT -> WEED with `planted_day == day`).
3. **Over-issuing PLANT drops the whole batch** for that crop (study 1 engine exploit #12), and
   `_r127_last_hour` re-runs its filter *because dropping one request can unblock the batch*. If our
   planner ever issues more PLANTs than seeds held, its planting rate silently collapses to zero for that
   crop — which matches the symptom "seed in hand, room under the cap, and still does not plant."
4. **They plant on tiles that are not yet needed** (#1) and swap crop species without changing the
   schedule (#16), so the tile count is driven by worker-visit capacity, not by tile availability.

### W5. We have free tiles, seed in hand, room under every cap — and planting still loses the per-turn auction

This is the deepest one, and the answer is structural: **none of these agents run a per-turn value
auction.** Planting is a scheduled obligation with a deadline, produced by a route; the reactive layers
are allowed to rewrite the *market* list freely and unit commands only as local substitutions. A
per-turn auction will systematically lose planting because:

* the payoff is 2-10 days away (wheat 4 days, tomato 8, strawberry 10, melon 10-12);
* the payoff is not in this turn's currency — it is a *price path* effect on a book;
* the true cost is not the seed ($10 for wheat; `private["seeds"]` is outside the shed cap and is free
  storage, study 1 engine exploit #15) — it is the **watering visits** on days
  `(max_yield_day+1)//2 .. max_yield_day`, plus the mandatory planting-day water.

What to copy instead:

1. **Value the investment, not the turn** — `_hd2_ev` (#8) is the template. Simulate the product's
   inventory path to day 30 with town drain, expected future shop unlocks, and *both* farms' scheduled
   production; then value `k` new units as `revenue along the path + sum_d Δprice_d * (our future units -
   their future units) - cost`. Act only when the best option clears `1.3x` the status quo *and* gains
   `>= $600`. Apply the identical formula to a block of `k` new plants.
2. **Reserve, don't auction.** Book the tile, the planter and the watering visits as a triple, at the
   time the investment decision is made, with a deadline. Let the auction schedule only the
   *discretionary* leftovers — which is exactly what the courier and fertilizer layers do.
3. **Score a candidate plant by whether its waterings are already on someone's path.** `_ca_yield_path`
   forecasts a tile's outcome from the list of `(step, unit, op)` visits the plan already contains: yield
   grows by `2 if fertilized else 1` per watered day inside the window, capped at `max_yield`, and decays
   after `mls`. A plant whose waterings are free rides is nearly pure profit; one that needs new trips
   should be compared against the courier trip it displaces.
4. **Plant early in the day.** The plant must be watered the same day and the planter cannot do both, so
   either a second unit waters it in the same turn (later unit index) or the planter waters at `h+1`.
   Either way `h <= 22`, and in practice much earlier so the watering fits the bonus window on later days.

---

# Confidence

**Verified in engine code** (read in `kaggriculture.py` this session):

* `_parse_order` returns `None` for `[]` and for `n <= 0`, and `_process_market` still advances the index —
  the basis of #2.
* `_process_market` quotes both players at the same pre-commit inventory then commits both, in player
  order — the basis of #5 and #14.
* `_decay_plants`: `mls = tile["max_lifespan_step"]`, skip if `step < mls` or `(step - mls) % 2 != 0`,
  else `yield_units -= 1` and `WEED` at `<= 0`; called every step after `_town_consume` — #11.
* `_new_plant`: `"consecutive_unwatered": 1,  # planting day counts as unwatered`;
  `max_lifespan_step = (day + max_yield_day + 1) * turns_per_day` — #9, #11.
* `_daily_refresh_plants`: `WEED` at `consecutive_unwatered >= 2` — #9, #17.
* `ANIMALS` `max_held` = 4 / 6 / 6 and the `min(a["max_held"], ...)` clamp — #10.
* `_end_of_day`: `_drop_inventories_to_shed` then `farm["farmer"] = _default_spawn(...)`,
  `farm["hands"] = []`, `private["inventories"] = [{}]`, `hires_today = 0`; shop draw
  `rng.choice(sorted(SHOPS))` under `random.Random((seed * 1_000_003) ^ day)` — #7, W1.
* `_spawn_hand` = first free shed-access tile, NWSE order, ties by occupancy — #7, W1.
* `CROPS` / `ANIMALS` tables quoted in #8, #16.

**Verified in the decoded agent sources** (every constant below read directly):

`V9_RACE_DEFAULT` 40 / **41 in V55**, `V9_RACE_MAX` 48, `V9_RACE_MARGIN` 12, `V9_RACE_GAP` 3,
`V9_RACE_WINDOW` 30, reservation window `192 <= step < 696`; `V9_RACEPX_BASE` / `V9_RACEGATE_BASE`
tables and `MARGIN = 0`; `V9_COURIER_ITEMS`, `V9_COURIER_FROM_HOUR = 12`, `_V9_COURIER_ACCESS`,
`_V9_COURIER_IDLE`; `V9_CARROT_RATIO 1.8`, `_FIRST_DAY 10`, `_LAST_DAY 23`, `_WHEAT_RESERVE 40`,
`_BOOM_RATIO 3.5`, `_BOOM_RESERVE 10`; `V9_FERT_CROPS`, `V9_FERT_AGES (1,)`, `V9_FERT_FIRST_DAY 14`;
`V9_HERD_MIN_WOOL/MILK 150`, `MAX_EGG_SHOPS 1 / 0`, `MIN_MILK_SHOPS 3`; `V9_OPENING_STEP0`
`(BUY_PRODUCT WHEAT 20, SELL WHEAT 15)`; `_HD2_FROM/TO 192/360`, `_HD2_RATIO 1.3`,
`_HD2_MIN_GAIN 600`, `_HD2_CARE 0.8`; `_CS_FROM/TO 144/192`; `_OR2_CAP 30`, `_OR2_SLOT_H 6`,
`_OR2_SLOT_MARGIN 20.0`, slot-swap window `288 <= step < 694`; `_CH_SHED 90`; `_SR_MARGIN 8`,
`_SR_HOURS (21,22,23)`; `_Y_HOURS (21,22)`, `_Y_ITEMS`, `_Y_MARGIN -6`; `V13V_SKIP_DAYS (19,21,23)`;
`_V44Y` SELL-run length 2..6 and `step >= 216`; `_E334` `step >= 144`; Lynn's `_IG_CASH` set and
`_ig_standard` configuration gate; the HybridOpening step numbers (2-6, 29, 49-57) and Degnon's
(53-57 blanked, 84-91).

**Reported by the notebooks, not reproduced by me:** every win/loss record quoted — V55's three panels
(75/9/26 -> 91/15/4 over 110 games/arm, +$61.9 paired margin), the 40/12 sweep (73-7, 74-6, 65-15,
14-26), the step-192 window blocks (32-0, 30-2, 30-2), the RACEPX panels, the "$1,050 after step 1
against all 6,648 recorded openings", the "-$20k..-$65k" opening cascade, and "~40% of strawberries and
milk still in hand at day end". These are self-reported and the panels are their own.

**Inferred, not proven:**

* That `41` is materially better than `40`. Their own numbers show 42 and 43 regressing and 44 winning
  head-to-head while losing to the shallow baseline — a flat, noisy ridge. I would implement "deep
  reservation, ~40 turns, from day 8" and not chase the last turn.
* The ranking above. #1, #2, #7, #9 and #11 are ranked high because they are cheap and target our
  measured weaknesses directly, not because anyone published a single-variable sweep for them.
  The only single-variable sweeps in these four notebooks are V55's `40 -> 41` and Degnon's one-day
  harvest delay.
* That cheapest-first overflow selling (#12) beats study 1's highest-first `room_guard`. Both ship in
  different layers of the *same* stack, at different hours; I did not find an ablation.

**Deliberately not examined:** the nine tape blob lines in each file (`_R108_DATA`, route arrays), the
`_V92_P_RAW` recorded stream library, the `CT_TABLE` fingerprints beyond their two keys, and the
embedded terminal-closure planner.
