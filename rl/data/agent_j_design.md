# Agent J — design, and the evidence behind every choice

Agent J is bespoke. It replays nothing. Every number below comes from this
project's own measurements: 1,006 fresh replays of the current top 200 teams,
347 of them replayed bit-exact, the five published agents read for mechanism,
G's 38 real ladder games, and live head-to-heads against real top code.

Target: **3000** (rank ~10 today). Current best of ours: H2 at 2265.

---

## 1. What we know, and what it forces

### 1.1 The gap to the top is small in coins and huge in games

Live head-to-head, 16 games each, both seats:

| matchup | wins | own score | margin |
|---|---|---:|---:|
| H2 vs aurax7 v7 | 3/16 | 98,271 | **−990** |
| Agent I vs v34 | 8/16 | 82,806 | −6 |
| Agent I vs H2 | 2/16 | 100,987 | −4,437 |
| G vs H2 | 0/16 | 72,416 | −47,928 |

The corpus says the median top-level game is decided by **2,395 coins, 2.3%
of the pot**. So ~1,000–3,000 coins a game separates 2265 from the top 200.
**J does not need a revolution. It needs a few thousand coins, reliably.**

### 1.2 Labour is the binding constraint — the single hardest-won lesson

G spends **49.9%** of worker turns walking and 40.6% working; the top nine
teams run 40–48% walking and 42–53% working. Everything that asked G's crew
for *more* work lost, and the only mechanism that ever gained made existing
work land:

| change to G | own score/game |
|---|---:|
| workers finish the job they walk to | **+5,142** |
| spread more manure | −16,510 |
| carry twice the feed | −11,062 |
| skip meals on quiet days | −6,441 |
| a leaner, sheep-light herd | −18,898 |

**Rule for J: a worker-turn is the scarce resource. Any subsystem that costs
turns must pay for them explicitly, in coins, at the price of the job it
displaces.**

### 1.3 Market microstructure is free money

These cost no worker turns at all, and two of them are already measured on
our own scheduler (+933 and +734 a game, stacking to +1,750):

- **Meter the fragile books.** Units from equilibrium to the price floor:
  WOOL 59, STRAWBERRY 62, MILK 76, MELON 158 — against WHEAT and EGG, whose
  glut curves are logarithmic and absorb thousands. Sell the fragile four in
  small lots; dump wheat and egg freely.
- **Sequence the order list.** `_process_market` walks both players' orders by
  index at the same pre-commit inventory; a unit that fails on cash or shed
  room **aborts its whole order**; anything past the tenth order is dropped.
  Sales first, inventory-priced buys next, fixed-price last.
- **Phase with the town.** `interpreter` runs units → market → town, and the
  town eats every 4 steps, so price steps up at `t % 4 == 1` and is flat
  across the block. (Measured ambiguous on G: +904 coins but −2 wins. J
  should re-test it once its sales are metered rather than continuous.)
- **Price the orders exactly.** `market_price` is deterministic and the
  inventory is public, so J can compute what each unit will actually fetch
  and sort its sales by *price lost if the rival sells first*.
- **Liquidate at 718.** The last processed action is step 718 and the day-29
  tip happens after the final market tick, so anything unsold is worth zero.

### 1.4 Production should follow the town, not a fixed plan

`_town_consume` drains each unlocked shop's basket every 4 steps and the town
centre takes one of every non-fertilizer product daily. Shops unlock on days
3, 6, 9 … with replacement, capped at 8 instances. Simulating 200 seasons of
pure town drain with no player sales, the end-of-season price if nobody sells:

| | WHEAT | CARROT | TOMATO | STRAWBERRY | MELON | EGG | MILK | WOOL |
|---|---|---|---|---|---|---|---|---|
| price | 48 | 58 | 83 | 293 | **280** | 63 | 311 | 246 |
| deficit | 516 | 300 | 192 | 426 | **30** | 210 | 300 | 210 |

**MELON is in no shop basket** — its only demand is the town centre's single
unit a day, and its glut curve is `sq`. It is a lure, and G plants 12 tiles of
it. **TOMATO** is the opposite: winners hold more tomato tiles than losers
(110–56, p = 0.00003), its price *rises* all game (60 → 74) because only two
of eight shop types buy it and three quarters of the field ignores it.

**Rule for J: at day 6, read `town.unlocked_shops` and commit the mid-game mix
to what those shops actually eat.**

### 1.5 Labour is nearly free to hire, and only before hour 2

`_hire_cost = fib(hires_today)` and the counter resets nightly: **ten hands
cost 143 coins for the day**. Hands are wiped each night, so it is a daily
rental, not an investment. A full watering tour is ~21 turns, so a hire is
only useful if requested by **hour ≤ 2**. The field hires 266–316 a season and
plateaus at 11/day.

### 1.6 The lead is built late and held

Median cumulative revenue is 19% by day 10 and 62% by day 20; the last ten
days carry ~45%. **Day-24 cash predicts 263 of 347 results (76%)**, while day-6
cash is a coin flip. So J optimises the day-24 balance, not the early board.

---

## 2. Architecture

Three layers, each measurable on its own.

### 2.1 Plan (cheap, once a day)

- Day 0–5: fixed opening — the corpus's own basket is 7 wheat, 12 melon seed,
  2 cow, 2 sheep in 52 of 69 teams, but that is the *worst* of the four
  families (49% win rate) while the top-10 family runs 9–10 wheat, 6 melon,
  2 cow, **3 sheep** and wins 56%. J starts from the top-10 shape and sweeps.
- Day 6: read the unlocked shops, compute remaining town demand per good over
  the rest of the season, and set tile targets per crop and head per species
  to match the draw, subject to labour.
- Every day: re-cost the plan against worker-turns available (hands × 24).

### 2.2 Schedule (the expensive part)

Reuse what is *proven* in our own code, not copied from anyone:
- global assignment of (worker, job) pairs by value / distance²;
- **commitment**: a worker keeps the job it is walking to unless something
  clearly better appears (+5,142 measured);
- priority bands as a dependency chain: feed → wheat → housing → harvest.

New in J: every job carries an explicit **turn cost**, and the planner refuses
work whose coin value per turn is below the marginal job it displaces. This is
the direct answer to §1.2.

### 2.3 Market (free money, do it exactly)

A reimplementation of `market_price` inside the agent, then: meter the fragile
four, sequence the list, reserve feed wheat, guard shed room at dusk,
liquidate at 718, and rank sales by expected price loss.

---

## 3. How J will be judged

Never on tapes. Every gate is a live head-to-head, 16+ games, both seats,
`actTimeout 60`:

1. **vs H2** — must beat it before anything else is claimed.
2. **vs Agent I** — our own strong baseline.
3. **vs aurax7 v7 and v34** — real top-of-ladder code.
4. Packaged file **played by path**, the check that Agent I's dead submission
   taught us to run.

A subsystem ships only if it wins on (1) and does not lose on (3).

---

## 4. Order of work

1. Market engine alone, bolted to G's existing scheduler → isolates §1.3.
2. Shop-driven plan → isolates §1.4.
3. Turn-costed scheduling → isolates §1.2.
4. Opening sweep → §2.1.
5. Phase and price-loss ranking → the last few hundred coins.

Each step is measured against H2 before the next begins.
