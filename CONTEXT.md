# Active System Context

## Competition Objective

Kaggriculture is a two-player 30-day simulation. Final banked coins decide each
game; Kaggle's displayed Score is a win/loss skill rating over ladder games.
Only the latest two submissions are actively tracked.

## Current Agent

The current live candidate is
`agents/experimental_demand_animal_agent.py`. It first selects one of two
deterministic service templates on day 1:

1. frozen deadline capacity;
2. deadline capacity plus zero-travel co-located FEED+CARE pairing.

On day 6 it uses public shop demand to keep the balanced herd or substitute at
most two expansion sheep with cows or geese. Neither selector can issue raw
actions. Movement, crop lifecycle, feeding, market affordability, land
purchase, and final liquidation remain deterministic.

The exact submitted standalone file is
`submissions/demand-animal/main.py`, Kaggle submission `55817911`, SHA-256
`53cbab96eaf7eba10a55adac2208b273636ba45274b5cac34967bedae335f5ac`.
The latest-two tracked pair is demand animal `55817911` plus learned service
`55803952`.

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
```

Never regenerate a submitted package and assume it is the uploaded artifact.
Compare its full SHA-256 first.