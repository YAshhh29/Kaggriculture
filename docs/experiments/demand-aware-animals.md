# Demand-Aware Expansion Animals

## Hypothesis

The frozen balanced herd ignores observed shop demand. Replacing at most one
expansion sheep in NE and SW with a demanded species may raise output without
changing the NW opening, land timing, workforce, crop load, or safety scheduler.

## Mechanism

- Keep the NW opening unchanged.
- Wait until day 6, immediately before expansion, so two shop draws are visible.
- Compare public egg, milk, and wool opportunities.
- Replace at most one expansion sheep per new quadrant.
- Lock the choice for the episode.
- Fall back to the balanced herd when opponent day-6 bank is below 0.5k, outside
  observed normal-game support.

## Results

Against exact submitted learned-service package
`684693161aebb51bd6293a497033d630218af5eabf92870899efabef69d158b2`:

| Gate | Seeds | Result | Mean margin |
| --- | --- | ---: | ---: |
| Development | 140-149, both positions | 13-7 | +1,057.45 |
| Validation | 159-163, both positions | 7-3 | +2,628.00 |

Other validation opponents on seeds 159-163, both positions:

| Opponent | Result |
| --- | ---: |
| Compact | 10-0 |
| Adaptive | 10-0 |
| Center-out | 10-0 |
| Lifecycle | 7-3 |
| Scale | 10-0 |

Aggregate non-incumbent league: **47-3**.

Captured elite scripts remain 0-4. The out-of-distribution fallback reproduces
the deadline baseline exactly: 50,463.5 mean against current top and 68,335 mean
against rank two.

## Rejected Sibling Hypotheses

- Selecting crop rotation from the first three shops lost 3-7.
- Combining crop and animal choices was neutral at 5-5.
- Selecting expansion species after one shop chose geese on seed 149 and lost
  0-2; waiting for the second shop changed the choice to sheep and restored 1-1.
- Globally selecting the nearest equal-priority planting slot lost 6-14. Route
  distance must remain subordinate to lifecycle and economic target value.

## Decision

Advance demand-aware expansion animals to contextual counterfactual training and
an untouched gate. Do not promote demand-aware crop rotation.