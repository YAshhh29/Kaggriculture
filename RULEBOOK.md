# Kaggriculture Rulebook

This is the project reference for simulator version 1.32.7. It summarizes the
rules that affect strategy, routing, profitability, and terminal score. When a
replay or intuition disagrees with this file, verify the current simulator
source before changing an agent.

## Match Objective And Clock

| Rule | Value |
| --- | --- |
| Objective | Finish with more **banked coins** than the opponent |
| Starting bank | 3,000 coins |
| Season | 30 days |
| Turns per day | 24 |
| Replay records | 720 total: record 0 plus 719 executed transitions |
| Score | Final bank balance only |
| Unsold value | Crops/products on tiles, worker inventory, seeds, and shed stock do not count until sold |
| Players | Two farms sharing one dynamic market and town demand |
| Determinism | A fixed agent and seed reproduce when all observations/actions match |

The observation uses zero-based `day` and `hour`. The visualizer presents them
as days 1-30 and turns 1-24.

## Board, Coordinates, And Land

The board is 10x10. `tiles[y][x]` uses `x` from left to right and `y` from top
to bottom. The planning block number is:

```text
block = y * 10 + x + 1
```

| Quadrant | Coordinates | Block range pattern | Initial state | Purchase cost/order |
| --- | --- | --- | --- | --- |
| NW | `x=0..4`, `y=0..4` | 1-5, 11-15, ..., 41-45 | Unlocked | Already owned |
| NE | `x=5..9`, `y=0..4` | 6-10, 16-20, ..., 46-50 | Locked | First purchase: 1,000 |
| SW | `x=0..4`, `y=5..9` | 51-55, ..., 91-95 | Locked | Second purchase: 2,000 |
| SE | `x=5..9`, `y=5..9` | 56-60, ..., 96-100 | Locked | Third purchase: 4,000 |

Land purchases are forced in the order **NE -> SW -> SE**. NW cannot be
purchased because it is the starting quadrant.

### Shed Geometry

The shed is not a board tile. Its four access tiles are:

| Block | Coordinate | Quadrant |
| ---: | --- | --- |
| 45 | `(4,4)` | NW |
| 46 | `(5,4)` | NE |
| 55 | `(4,5)` | SW |
| 56 | `(5,5)` | SE |

Those blocks remain usable for crops or structures. A worker standing on any
of them can use `PICKUP`, `DROP`, or shed-directed `PLACE`, even when that
quadrant is locked.

### Movement And Terrain

| Rule | Effect |
| --- | --- |
| Movement | `NORTH`, `SOUTH`, `EAST`, `WEST`; one block per action |
| Locked land | Workers may cross it, but normal tile actions are no-ops there |
| Empty-tile weeds | Each empty unlocked tile has a 0.005 daily weed-spawn chance |
| `DIG` | Removes a weed, plant, or empty structure; cannot remove a placed animal |
| Tile occupancy | One crop or one structure/animal per tile |

Buying unused land increases the number of empty tiles that can randomly grow
weeds. Land should have a funded use and enough remaining season to repay it.

## Workers And Hiring

The main farmer is free and permanent. Hired hands disappear at day end after
their inventory is dropped into the shed. They must be rehired each day.

| Hand number | Marginal cost | Cumulative daily cost |
| ---: | ---: | ---: |
| 1 | 1 | 1 |
| 2 | 1 | 2 |
| 3 | 2 | 4 |
| 4 | 3 | 7 |
| 5 | 5 | 12 |
| 6 | 8 | 20 |
| 7 | 13 | 33 |
| 8 | 21 | 54 |
| 9 | 34 | 88 |
| 10 | 55 | 143 |
| 11 | 89 | 232 |
| 12 | 144 | 376 |
| 13 | 233 | 609 |
| 14 | 377 | 986 |

Costs reset every day. Hands spawn on the four shed-access tiles, preferring
the least occupied tile and then NW, NE, SW, SE order.

## Crop Reference

Base prices are starting-market prices, not guarantees. Base net below is
`unfertilized maximum units * base price - seed cost`; it excludes labor,
movement, land, fertilizer opportunity cost, and market movement.

| Crop | Seed | Base price | First yield | Peak/final schedule | Unfertilized units | Base gross | Base net |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Wheat | 10 | 25 | Age 2 | Peak age 4 | 4 | 100 | 90 |
| Carrot | 20 | 35 | Age 2 | Peak age 3 | 3 | 105 | 85 |
| Tomato | 50 | 60 | Age 8 | Ages 8, 9, 10, 11 | 4 total | 240 | 190 |
| Strawberry | 100 | 120 | Age 10 | Ages 10, 12, 14, 16 | 4 total | 480 | 380 |
| Melon | 80 | 250 | Age 10 | Reaches six units at age 10 | 6 | 1,500 | 1,420 |

### Crop Survival

| Rule | Consequence |
| --- | --- |
| New crop state | Starts with `consecutive_unwatered = 1` |
| Planting day | Must receive `PLANT` and `WATER` before that night |
| One missed day after watering | Crop survives, counter becomes 1 |
| Two consecutive missed refreshes | Crop immediately becomes a weed |
| Watering twice in one day | Second action is a no-op |

Safe admission rule: never plant unless a second worker can water that exact
tile in the same simulator transition.

### One-Time Crop Yield Windows

| Crop | Productive watering | Safe maximum without fertilizer | Harvest deadline |
| --- | --- | ---: | --- |
| Wheat | Ages 2-4 | 4 | Harvest before age-5 decay |
| Carrot | Ages 2-3 | 3 | Harvest before age-4 decay |
| Melon | Ages 6-10 | 6 | Harvest before age-13 decay; ages 11-12 add nothing at cap |

One-time crops begin with one unit. Each productive watering adds one; a
fertilized productive watering adds two, up to the crop cap. Fertilized wheat
can reach 6 and carrot 4, but fertilizer is often worth more when sold.

### Ongoing Crop Schedules

| Crop | Production observations | Water/fertilizer action days before refresh | Unfertilized lifetime | Fully fertilized potential* |
| --- | --- | --- | ---: | ---: |
| Tomato | Ages 8, 9, 10, 11 | Current ages 7, 8, 9, 10 | 4 | 8 |
| Strawberry | Ages 10, 12, 14, 16 | Current ages 9, 11, 13, 15 | 4 | 8 |

`*` The held-yield cap is 4, so harvest between production events to avoid
discarding doubled output.

Ongoing plants stop after four production events. Harvest does not remove
them. After the final harvest, `DIG` the spent plant before decay turns it into
a weed.

## Fertilizer

| Rule | Value |
| --- | --- |
| Market base price | 100 |
| Source | Every surviving animal exposes one fertilizer at each day end |
| Tile storage | One unit maximum per animal; uncollected fertilizer does not accumulate |
| Plant duration | Current day plus the following two days |
| One-time effect | Productive water adds 2 instead of 1 |
| Ongoing effect | A watered production event yields 2 instead of 1 |

Fertilizer strategy:

- Usually sell rather than apply it to wheat or carrot.
- Timed use can shorten melon occupancy, but melon market demand is weak.
- It is strongest on strawberries when production and harvest are scheduled to
  prevent the four-unit held cap from wasting doubled output.
- Two timed applications can cover strawberry's four production events:
  fertilize around current ages 9 and 13, with water on 9, 11, 13, and 15.

## Animal Reference

Animal purchase price includes no structure fee; building the coop or pasture
costs one worker action. Base daily margin assumes steady full CARE, base
prices, one fertilizer collected/sold daily, one wheat feed at 25, and excludes
purchase, wages, movement, and market changes.

| Animal | Structure | Cost | Product/base | First yield | Interval | Held cap | Full-CARE steady output | Base daily margin |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: |
| Goose | Coop | 300 | Egg / 50 | Day 4 | Daily | 4 | About 2 eggs/day | 175 |
| Cow | Pasture | 400 | Milk / 160 | Day 8 | Every 2 days | 6 | About 3 milk/2 days | 315 |
| Sheep | Pasture | 500 | Wool / 200 | Day 6 | Every 3 days | 6 | About 4 wool/3 days | 341.67 |

### Feed, Escape, And CARE

| Rule | Effect |
| --- | --- |
| Feed input | One wheat per animal per fed day |
| New animal | Starts at zero consecutive unfed days; first-day grace exists |
| Two unfed refreshes | Animal escapes permanently; structure remains |
| `CARE` alone | No bonus unless the animal is also fed that day |
| Fed + cared day | Banks `+1` for the next scheduled production |
| Fed production day | Produces base 1 plus the entire banked CARE bonus |
| Unfed production day | Produces base 1 but loses the banked bonus |
| Product held cap | Goose 4, cow/sheep 6; excess production is discarded |

At base prices, CARE adds roughly 50 coins/day for a goose, 160/day for a cow,
and 200/day for a sheep before labor and market effects. When premium products
fall near the one-coin price floor, CARE may no longer beat an alternative task.

## Shed And Inventory

| Rule | Value |
| --- | --- |
| Non-seed shed capacity | 100 total items |
| Seeds | Separate, uncapped seed inventory |
| Harvest destination | The acting worker's inventory |
| `PICKUP` | Moves shed inventory to one worker at a shed-access tile |
| `DROP` | Deposits the worker's entire inventory at a shed-access tile |
| End of day | All worker inventories auto-drop; overflow is discarded |
| Selling | Only current shed inventory can be sold |

Worker actions execute before market orders. Therefore a worker can `DROP` and
the agent can sell the projected deposited quantity in the **same transition**.

## Market

| Rule | Value |
| --- | --- |
| Market orders per turn | Maximum 10; later entries are silently ignored |
| Seed/animal prices | Fixed |
| Product prices | Dynamic shared inventory curves, rounded, floor 1 |
| Initial product inventory | 10,000 units each |
| Supply lower than 10,000 | Scarcity raises price |
| Supply higher than 10,000 | Glut lowers price |
| Purchasable products | Wheat and fertilizer only |
| Sellable products | Every crop, animal product, and fertilizer |

### Price Sensitivity

`T` is the simulator's one-field 24-day production reference. These columns
show prices at initial supply, one `T` scarce, and one `T` oversupplied.

| Product | Base | Scarce `I0-T` | Glut `I0+T` | Main risk |
| --- | ---: | ---: | ---: | --- |
| Wheat | 25 | 45 | 20 | Relatively glut-tolerant |
| Carrot | 35 | 70 | 10 | Can reach 1 under larger glut |
| Tomato | 60 | 84 | 24 | Moderate glut sensitivity |
| Strawberry | 120 | 204 | 1 | Premium; severe glut collapse |
| Melon | 250 | 300 | 1 | Highest base, almost no specialist demand |
| Egg | 50 | 70 | 40 | Most glut-tolerant animal product |
| Milk | 160 | 256 | 1 | Premium; demand-dependent |
| Wool | 200 | 240 | 1 | Premium; demand-dependent |
| Fertilizer | 100 | 140 | 60 | Relatively stable |

High nominal price is not guaranteed profit. Strawberry, melon, milk, and wool
can fall to 1 when both players oversupply them without matching town demand.

## Town Demand

The town center consumes one of every product except fertilizer once per day.
A shop instance consumes its listed products every four turns. Shops unlock
every three days, are drawn with replacement, remain active, and stop after
eight total instances. Duplicate shops each consume independently.

| Shop | Demand |
| --- | --- |
| Bakery | Egg, wheat |
| Pizza Shop | Milk, tomato, wheat |
| Brunch Spot | Egg, wheat, strawberry |
| Yarn Store | Wool at double single-product rate |
| Ice Cream Shop | Strawberry, milk, wheat |
| Pet Cafe | Carrot at double single-product rate |
| Smoothie Shop | Strawberry, milk |
| Farmers Market | Wheat, carrot, tomato, strawberry |

Demand grows monotonically because shops never disappear. Crop and species
expansion should use the observed list, including duplicate instances.

## Turn Processing Order

For each simulator transition:

1. Validate atomic seed availability for all `PLANT` actions.
2. Execute the main farmer action.
3. Execute hired-hand actions in hand order.
4. Process both players' market orders concurrently, one unit at a time.
5. Process town consumption.
6. Apply plant decay.
7. At day end: refresh crops and animals, spawn random weeds, drop inventories,
   remove hired hands, reset positions, and unlock a shop when scheduled.
8. On the final transition, set status and reward from banked coins.

This order explains why same-turn `PLANT` + `WATER` works and why same-turn
`DROP` + `SELL` works.

## Strategy Safety Gates

Before promoting any policy, require:

| Area | Required evidence |
| --- | --- |
| Crop admission | Every planted crop receives planting-day water |
| Crop completion | Zero policy-created weeds and zero unfinished cycles |
| Animal safety | Zero escapes, including before endgame |
| CARE | Track fed/cared production days and any forfeited profitable bonus |
| Inventory | No sellable shed/carried inventory at terminal state |
| Land | New quadrant has a funded block plan and conservative payback |
| Labor | Workload includes movement plus an emergency reserve; wages included |
| Market | Both positions, shared-market direct opponents, and demand-poor seeds |
| Reproducibility | Full 720 records, exact source/package hashes and actions |
| Submission | Never replace the live package without explicit approval |

## Planning Checklist

For a proposed block strategy, specify:

1. Animal core blocks and species.
2. Crop blocks in exact center-out order.
3. Which worker pair owns each contiguous route.
4. Maximum simultaneous slots for each crop.
5. Fertilizer schedule and reserve.
6. Feed reserve and daily animal workload.
7. Land purchase day, cash reserve, and remaining payback window.
8. Hiring target by land stage and the cumulative daily wage.
9. Last planting/feeding/collection dates.
10. Final return, `DROP`, and sale plan.

The interactive numbering reference is
[`field_strategy_planner.html`](field_strategy_planner.html).