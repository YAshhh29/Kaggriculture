# Agent J — progress log

Every line here is a measurement, not an opinion. Gate command:

    PYTHONIOENCODING=utf-8 ./.conda/python.exe -m tools.eval.head_to_head \
        rl.candidate_j:agent --reference rl.candidate_g:agent --seeds 6 --workers 6

## Baseline (skeleton as handed over)

| matchup | wins | own | theirs | median margin |
|---|---|---:|---:|---:|
| J vs G, 12 games | 0/12 | 4,763 | 115,200 | −112,723 |

## What the day-by-day trace found (seed 11, seat 0)

New tool: `tools/analysis/trace_day.py` wraps the engine's own
`_apply_unit_action` and `_initialize`, so every unit action is counted at
source and the portfolio is read off the real board each dusk.

```
day     money       opp  plants animals pens weeds empty hands shed
  0        95       429    17     4      0     0     4     3
 10     1,355     3,802    23    10      1     3    38    11
 20       124    36,791    11    29      1     1    33    11
 29     6,957   129,369     0    16     14     1    44    11
```

Six defects, each traced to a line:

1. **Runaway feed buying.** `market_orders` step 2 buys
   `min(short, 8, ...)` wheat *every turn* whenever
   `animals*2 > shed wheat`. With 29 head that is 8 units a turn, ~30 coins
   each, ~5,700 coins a day. It is the entire reason the money curve is flat
   at 100–1,400 for thirty days while the farm harvests 775 times.
2. **The order list is jammed by sales.** Nine sell orders are emitted
   before any buy, and `(sells + buys + fixed)[:10]` silently drops HIRE,
   BUY_LAND, BUY_ANIMAL and BUY_SEED once the shed holds five goods.
3. **The herd is all geese.** Both the pen-build loop and the purchase loop
   iterate `ANIMAL_HOME` and `break` on the first entry, which is GOOSE, so
   a PASTURE is never built and a cow or sheep can never be placed.
   29 geese, 0 cows, 0 sheep.
4. **Wheat monoculture.** `crop_targets` returns `[("WHEAT", 10_000)]`
   whenever the flock is short of feed, which with 29 geese is always. From
   day 13 the farm grows nothing else, and no other seed is ever bought
   because the same function drives the seed order.
5. **Plants weed on the day they are sown.** `_new_plant` sets
   `consecutive_unwatered = 1`, so an unwatered planting day takes it to 2 and
   `_daily_refresh_plants` turns the tile into a WEED that night. Nothing in
   the skeleton pairs PLANT with a same-day WATER. 175 DIGs and up to 12
   standing weeds a day are the visible cost.
6. **Ongoing crops were watered every day.** They only die at two
   consecutive dry days, so every other day is enough — half the watering
   labour on tomato and strawberry was being spent for nothing.

## The goods ledger: J does not have a market problem

New tool: `tools/analysis/goods_pipeline.py`. It hooks the engine rather
than reading the board, because the shed takes the day's deposits and pays
the day's sales in the same step, so a net delta hides both. Every unit is
counted where the engine moves it: `_commit_unit` for anything sold, bought
or refused, `_apply_unit_action` for harvests, feeding and drops, and
`_drop_inventories_to_shed` for overflow. It runs both seats in the same
game, so the numbers are against a top-200 team on the same seed.

Four games, J against four different top-200 tapes:

```
                  grown   sold   revenue   refused  binned   left
J                  5066   3463   366,539         0      65      0
top-200 team          -   5489   519,783         -       -      -
```

Five things this kills outright as explanations:

* **No wasted plantings.** 238 PLANT actions issued, 238 tiles planted.
* **No same-day weeding.** `_new_plant` starts at `consecutive_unwatered = 1`,
  but J already pairs every sowing with a watering: 0 tiles went
  PLANT -> WEED on their sowing day.
* **No dead market orders.** 0 units refused across 2,578 orders.
* **Nothing binned at the shed door.** `DROP` deletes an inventory entry
  whether or not the shed had room, so it can lose goods silently. It lost
  none: 0 units, same as the opponent.
* **Nothing left unsold.** The shed is empty at the final step.

J sells what it grows -- 765 of 767 wool, 324 of 324 melon, 328 of 328
milk, 216 of 219 strawberry. The deficit is upstream, in production:

| good | J grows | they sell | ratio |
|---|---:|---:|---:|
| STRAWBERRY | 219 | 858 | 3.9x |
| EGG | 58 | 274 | 4.7x |
| MILK | 328 | 757 | 2.3x |
| CARROT | 242 | 449 | 1.9x |
| WOOL | 767 | 641 | 0.8x |

And it is yield per asset, not asset count. They sow 116 strawberry to our
66 -- 1.8x -- and harvest 3.9x the fruit. They feed 1,292 times to our
1,155 -- 1.1x -- and take 2.7x the milk and eggs.

## The watering that was priced at nothing

`_daily_refresh_plants` pays the manure bonus only on a day the tile was
also watered:

```python
fertilized = was_watered and tile.get("fertilized_until_day", -1) >= current_day
tile["yield_units"] = min(cd["max_yield"], tile["yield_units"] + (2 if fertilized else 1))
```

J's WATER branch left `gain = 0.0` for every ongoing crop and priced the
job only as a rescue, once the tile was already a day dry -- the comment
above it counted halving that labour as a saving. So J paid for the
manure, spread it on the strawberry, and then let the bonus lapse for want
of a watering can. On a production day a watering is not upkeep; it is the
second unit, about 170 coins for one turn.

`WATER_ONGOING = 1.0` prices it. Measured on the same 14 tapes, 28 games:

| | wins | our median | median vs rank 1-50 |
|---|---:|---:|---:|
| `WATER_ONGOING 0.0` | 4/28 | 70,666 | 56,446 |
| `WATER_ONGOING 1.0` | 2/28 | 74,698 | 72,724 |

+16,278 a game against the hardest twelve opponents in the panel, and the
two lost wins are both inside a four-game band. Held for the 60-game panel
before adopting.

## The flock: what the engine settles at dusk

New tool: `tools/analysis/herd_service.py`, hooking
`_daily_refresh_animals` so every care day is followed to its end. The
refresh is stricter than it reads:

```python
if days_since_first >= 0 and days_since_first % interval == 0:
    bonus = tile.pop("pending_care_bonus", 0) if tile["fed_today"] else 0
    tile["yield_units"] = min(max_held, yield_units + 1 + bonus)
    tile["pending_care_bonus"] = 0          # wiped either way
if tile["cared_today"] and tile["fed_today"]:
    tile["pending_care_bonus"] += 1
```

So a care day pays only if the animal is still fed on the production night
that follows, and an unfed production night pays nothing *and* destroys
every care day banked since the last one. With `1 + interval` units an
event, care roughly triples a cow and quadruples a sheep.

Three games against top-200 tapes, before any change:

```
                          ours   theirs
animal-days held          1119     1220
days fed                   781      975
units produced             678     1257
care banked as units       471      857
care wiped, unfed night    214       42
animals escaped             24       13
units per animal-day      0.61     1.03
```

J held 92% of their animals and took 54% of the produce, throwing away 31%
of its own care days against their 4.7%.

`placed_day`, `pending_care_bonus` and `yield_units` are all in the public
tile, so the night's settlement can be priced exactly rather than guessed.

### Pricing it at full value loses, and the flock's own numbers improve

First attempt charged the production night at `min(room, 1 + pending) *
price` with no discount. The flock got much better and the farm got poorer:

| | care wiped | units made | wins | median |
|---|---:|---:|---:|---:|
| flat estimate | 214 | 678 | 4/60 | 70,593 |
| full value | 42 | 922 | 2/60 | 63,378 |

A sheep's production-night meal came out at 848 coins for one turn and beat
every crop in the auction. The units were real. They were not worth what
they displaced. This is the same shape as the wheat-floor regression: a
local measure improved while the labour came out of somewhere better.

### What the flat estimate got wrong in both directions

`price * (1 + interval * CARE_RATE) * 0.5` charged the same for every
night. But an ordinary night yields nothing at all -- it only buys the
right to bank one care day -- while a production night cashes the lot. For
a sheep the old price was 329 either way, against a true 106 and 424.
`FEED_PRODUCTION_SHARE = 0.5` keeps the old amortisation, which stands for
the harvest turn behind each unit and the grain itself, and puts the shape
back:

```
production night   min(room, 1 + pending) * price * 0.5
any other night    price * 0.5
```
