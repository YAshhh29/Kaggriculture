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

The active research arm is
`agents/experimental_tiered_value_fertilizer_agent.py`. At day 12 hour 12 it
uses current strawberry price to choose between co-located-only fertilizer and
at most two steps of otherwise-idle carrier staging. It caps the episode at
four applications and never replaces a productive worker action. It converted
two captured losses and had no own-reward regression over 33 ladder contexts,
but untouched seeds 219-221 added no wins. It is not packaged or submitted.

## Decision Flow

```text
observation
  -> day-1 service arm selection
  -> day-6 expansion-animal demand selection
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

The current replay dataset contains 16 verified losses and 17 verified wins.
It captures day 9-12 carrier positions, due premium crops, harvest backlog, and
pending animal work. Audited tiered value fertilizer improved/tied/worsened
30/3/0, averaging +1,220.21 own reward and preserving all 17 wins. The current
source rerun over broad seeds 219-221 tied the exact control at 31-17 while
improving mean margin by 768.02. Seed 222 remains
untouched. Economic wheat retention is implemented as a research control but
rejected because shared-market effects produced a -23,649 own-reward case.