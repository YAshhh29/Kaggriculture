# Active System Context

## Competition Objective

Kaggriculture is a two-player 30-day simulation. Final banked coins decide each
game; Kaggle's displayed Score is a win/loss skill rating over ladder games.
Only the latest two submissions are actively tracked.

## Current Agent

The promoted source is `experimental_learned_service_agent.py`. It selects one
of two deterministic service templates on day 1:

1. frozen deadline capacity;
2. deadline capacity plus zero-travel co-located FEED+CARE pairing.

The learned policy cannot issue raw actions. Movement, crop lifecycle, feeding,
market affordability, land purchase, and final liquidation remain deterministic.

The exact submitted standalone file is
`submission-learned-service/main.py`, Kaggle submission `55803952`, SHA-256
`684693161aebb51bd6293a497033d630218af5eabf92870899efabef69d158b2`.

## Decision Flow

```text
observation
  -> day-1 service arm selection
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
- `_act_at_or_move` already takes one shortest-path step.
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
.\.conda\python.exe -m tools.validation.validate_submission submission-learned-service\main.py --seed 184
.\.conda\python.exe -m tools.validation.validate_learned_service_equivalence submission-learned-service\main.py --seed 184
```

Never regenerate a submitted package and assume it is the uploaded artifact.
Compare its full SHA-256 first.