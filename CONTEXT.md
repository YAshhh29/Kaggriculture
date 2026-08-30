# Active System Context

## Competition Objective

Kaggriculture is a two-player 30-day simulation. Final banked coins decide each
game; Kaggle's displayed Score is a win/loss skill rating over ladder games.
Only the latest two submissions are actively tracked.

## Current Agent

The current tracked incumbent is
`agents/experimental_future_labor_agent.py`. It inherits two deterministic
service templates selected on day 1:

1. frozen deadline capacity;
2. deadline capacity plus zero-travel co-located FEED+CARE pairing.

On day 6 it uses public shop demand to choose a bounded expansion herd, then
adds one peak-production hand only when a cheaper cow/goose choice coincides
with an opponent whose non-wheat footprint exceeds its wheat footprint.
Movement, lifecycle, feeding, affordability, land purchase, and liquidation
remain deterministic.

Its exact standalone package is `submissions/future-labor/main.py`, SHA-256
`200fef67c5a8e8b001b4a54986bb853d22b80f869af7460b67ec8eda169c70e3`.
It was uploaded unchanged as Kaggle submission `55821334`; validation episode
`100974134` completed 52,718-52,990. Its 24-game snapshot is 13-11 at Score
674.8. The first 23 games split 5-1 for the 13-hand branch and 7-10 for the
inherited fallback. The latest-two tracked pair is future labor `55821334` plus
demand animal `55817911`, currently displayed at 655.8.

Tiered fertilizer submission `55858409` is live from the exact package at
`submissions/tiered-fertilizer/main.py`. Its first 27 public games went 15-12,
reaching rating 671.96 at that snapshot; it is currently displayed at 649.3
and remains the public leaderboard selection. It executes reliably: zero
unfinished crop cycles, zero missed planting-day watering, and only one
livestock loss across those games. Losses are primarily against larger mixed
cow/sheep or goose economies, not basic service failure.

The next live-measurement candidate is
`agents/experimental_tiered_late_strawberry_agent.py`. It retains tiered
fertilizer and locks a day-6 value gate. When normalized strawberry price is at
least 1.30 and day-9 demand selects strawberry, it replaces eight spent melon
slots with a late strawberry cohort. Across the 27 exact live schedules it
improved two losses, tied 25 games, regressed none by own reward, and changed
the record from 15-12 to 17-10. Fresh seeds 222 and 223 tied control at 11-5
each while improving mean margin, so the strict more-wins promotion gate still
reports REJECT. The package is prepared for the explicitly requested live
measurement at `submissions/gated-late-strawberry/main.py`. It was uploaded as
submission `55887535`; validation episode `103192514` completed 49,447-49,745
at initial score 600.0. The tiered incumbent remains selected while ladder
matches evaluate the successor.

## Decision Flow

```text
observation
  -> day-1 service arm selection
  -> day-6 expansion-animal demand selection
  -> day-6 late-strawberry value gate
  -> day-9 crop-demand selection
  -> day-12 idle-fertilizer distance selection
  -> active animal and crop plans
  -> urgent feed / crop-deadline assignments
  -> setup and routine animal service
  -> routine crop service and paired PLANT+WATER
  -> sales, land, hiring, seed, and livestock orders
  -> affordability and ten-order filtering
```

## Routing Facts

- The board has no impassable movement tiles. Manhattan distance is the exact
  shortest-path distance, so Dijkstra or A* would return the same path at more
  runtime cost.
- `core.routing.step_toward` takes one exact shortest-path step; legacy agents
  use compatibility aliases so submitted behavior remains unchanged.
- Most visible routing failures come from choosing the wrong target or fixing a
  worker to the wrong quadrant, not from path search.
- A global nearest-empty-slot planting experiment lost 6-14 against the frozen
  submitted package. Route distance must be optimized after urgency, lifecycle,
  and economic value, not instead of them.
- A second worker-relative nearest-vacancy experiment lost 0-2 and created
  seven weeds because the selected target changed while workers approached it.
  The live loss gap was crop throughput and idle capacity, not path length.

## Demand Facts

- Every open shop consumes its listed products every four turns.
- Repeated shop instances consume independently.
- A single-product shop consumes two units each interval.
- The town center consumes one unit of every product except fertilizer daily.
- Shop demand reduces market inventory and therefore raises price.
- Melon has no dedicated shop. Without favorable market scarcity, melon sales
  can create glut despite its high nominal base value.

## Required Validation

```powershell
.\.conda\python.exe -m unittest -v
.\.conda\python.exe -m tools.validation.validate_submission submissions\demand-animal\main.py --seed 186
.\.conda\python.exe -m tools.validation.validate_demand_animal_equivalence submissions\demand-animal\main.py --seed 186
.\.conda\python.exe -m tools.validation.validate_submission submissions\future-labor\main.py --seed 214
.\.conda\python.exe -m tools.validation.validate_future_labor_equivalence submissions\future-labor\main.py --seed 214
.\.conda\python.exe -m tools.validation.validate_submission submissions\gated-late-strawberry\main.py --seed 223
.\.conda\python.exe -m tools.validation.validate_gated_late_strawberry_equivalence submissions\gated-late-strawberry\main.py --seed 223
```

Never regenerate a submitted package and assume it is the uploaded artifact.
Compare its full SHA-256 first.

The current live-loss feedback loop is:

```powershell
.\.conda\python.exe -m research.collection.collect_live_replay_league ...
.\.conda\python.exe -m research.evaluation.evaluate_live_macro_arms ...
```

The evaluator first requires the frozen package to reproduce every live reward
exactly, then ranks safe arms by our own reward delta rather than fixed-opponent
win status.

Guarded zero-travel strawberry service improved 15 of 24 ladder contexts and
tied nine, with no own-reward regression. Broad seeds 215-216 tied control at
23-9, so it was not promoted. Contextual carried-fertilizer service improved
eight of 11 losses, tied three, and converted one fixed replay; all 12 captured
wins and the next live win were preserved. Broad seeds 217-218 again tied
control at 22-10 despite +226.72 mean-margin improvement. No new submission is
justified without a fresh broad-gate win.

The tiered submission's 27-game replay dataset contains 12 verified losses and
15 verified wins. Losses average 318.8 harvested units versus 327.7 in wins,
but the larger separator is opponent reward: 77.5k in losses versus 53.1k in
wins. A day-6 strawberry-value gate prevents the late cohort's one observed
own-reward regression. The gated eight-slot arm converts episodes `102176636`
and `102511739`, preserves every live win exactly, and improves/ties/worsens
own reward 2/25/0. Untouched broad seeds 222 and 223 each tie the control's
11-5 record with zero errors and positive margin deltas. Economic wheat
retention remains rejected because shared-market effects produced a -23,649
own-reward case.