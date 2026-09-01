# Fast Track: Guarded Portfolio Challenger

This track exists because a trained RL policy is not the fastest route to the
next strong submission. It shares executors and features with the learning track
so none of the work is throwaway.

## Candidate A: Recovery And Liquidation

**Goal:** remove preventable losses while preserving the calendar whenever its
preconditions still hold.

Implement:

- hand-count and actor-position alignment;
- weed `DIG` then bounded retry/catch-up;
- carried-animal placement repair;
- projected inventory including same-transition `DROP` and shed-directed
  `PLACE`;
- pickup/feed reservations;
- sequential market funding and ten-order enforcement;
- live liquidation during steps 716-718 using exact marginal revenue.

This candidate must be behaviorally identical whenever no recovery or
liquidation guard fires. A fired guard must identify the violated invariant and
record the exact action delta.

## Candidate B: Order-Safe Premium Market

Build on Candidate A.

Implement:

- exact marginal revenue for the next unit sold;
- town-demand timing at hours 0/4/8/12/16/20;
- premium ordering for melon, milk, wool, and strawberry when justified by the
  live quote and projected inventory;
- one-turn shift/repay with per-product debt;
- no new production, quantity, or route changes.

Every shifted unit must either be repaid later or explicitly absorbed by final
liquidation. No market overlay may consume a purchase-financing slot without a
paired affordability proof.

## Candidate C: Public-State Route Portfolio

Build only after A and B clear untouched gates.

Use several complete programmes with:

- shared-prefix execution until their first meaningful divergence;
- shop sequence and duplicate counts;
- public opponent land, hands, crops, animals, structures, and money;
- route-distance thresholds and hysteresis;
- separate physical-route and market-overlay commitments;
- a safe fallback to the current calendar.

Do not select by team name, rank, submission ID, replay ID, or seed.

## Benchmark League

The target panel must include:

- the current frozen calendar;
- our gated and tiered historical controls;
- distinct public notebook families around 1500, 1800, 2200, and 2500;
- current elite replay programmes;
- market-aggressive, weed-stress, failed-purchase, and terminal-capacity stress
  opponents;
- both seats and fresh seeds.

Correlated forks count as one family. A 100-0 result against ten copies of the
same route is one result, not ten independent results.

## Promotion Ladder

1. Mechanic tests for each residual.
2. Exact no-op equivalence when no guard fires.
3. One-residual ablation against the frozen parent.
4. 100 paired games against each route family.
5. 1,000 paired games against the complete target league.
6. Temporal holdout and package/source/simulator equivalence.
7. Upload as the second active slot; keep the current calendar as hedge.

Candidates A and B advance from their 100-game family gates only if they:

- retain at least the parent's wins in every family;
- convert at least one parent loss overall;
- produce zero simulator errors;
- reduce state-drift invalid/no-op actions by at least 50% where their guard is
  applicable;
- preserve exact behavior in every no-guard state.

Candidate C and the combined challenger advance from 1,000 paired games only
if they:

- win at least 55% head-to-head against the parent;
- score at least 50% against every independently sourced target family;
- lose no more than two percentage points versus the parent in any family with
  at least 100 games, and compensate any such regression with a preregistered
  meta-hedge rationale;
- improve bottom-decile margin and the existing hard elite holdout;
- produce zero errors and fewer than 0.1% masked or invalid action attempts.

## Abort Conditions

Reject or roll back a residual if it:

- converts any established parent win into a loss without compensating
  family-level evidence;
- increases invalid/no-op actions;
- improves mean coins but not win probability;
- relies on one exact opponent or shop tuple;
- fails to conserve shifted inventory;
- changes physical route and market timing in the same unablated experiment.

## Relationship To RL

Each deterministic residual becomes a safe executable Option. Offline
counterfactuals can label when that Option beats `KEEP_CALENDAR`. Behavior
cloning and residual RL then learn Option selection and persistence, not raw
movement or market syntax.