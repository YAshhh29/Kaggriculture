# Opponent-Aware Future Labor

## Replay Diagnosis

Three demand-animal ladder losses finished 73,803-88,457,
76,431-103,917, and 71,521-115,015. The losses did not show a shortest-path
algorithm failure:

- the board has no obstacles, so Manhattan movement is the exact Dijkstra/A*
  distance;
- our workers used fewer movement actions than the 103k and 115k opponents;
- our peak crop footprint was 35-41, while opponents reached 50-55;
- our plantings were 79-83, while opponents reached 84-194;
- our fertilizer applications were zero, while two opponents used 72 and 85;
  and
- our PASS load was 1,378-1,567, while the 115k opponent used 213.

The controlling gap was productive capacity and scheduling, not the direction
chosen for a single movement step.

## Rejected Axes

Changing paired planting to the currently nearest vacancy caused target churn.
It lost 0-2 to the exact package on seed 198, averaged -5,426.5 margin, and
created seven weeds. A stable center-distance ordering was safer but still went
1-1 at -1,020 margin with five weeds on seed 199. Both were rejected; exact
shortest movement remains, while the proven contiguous plan order is retained.

Demand-selected crop slots also failed to generalize. On seeds 203-204, one
dynamic slot went 1-3 and two slots went 0-4. Four slots doubled the same-seed
control's weed count from four to twelve. Dynamic crop replacement is therefore
not part of the candidate.

Demand-gated strawberry fertilizer went 0-2 at -14,031.5 mean margin on seed
205. Combining it with extra labor also went 0-2 at -12,362.5. The scheduler
applied only 18 fertilizer actions across the fertilizer-only games and lost
too much crop and animal service capacity. Fertilizer remains an open
scheduling problem, not a promoted switch.

Increasing the protected crop-worker reserve from two to three or four also
went 0-2 for each arm. Four workers completed more crops but starved profitable
animal CARE and collection, producing -21,201 mean margin.

## Promoted Candidate

The useful isolated axis was one additional hand during days 9-22. A fixed
13-hand schedule beat the exact demand-animal package 6-0 on seeds 206-208, but
did not generalize against an all-wheat scale opponent.

The final rule locks at day 6:

1. Keep the submitted labor schedule for the balanced sheep herd.
2. Cow- or goose-biased demand plans make one sheep substitution cheaper.
3. Reinvest that capital in a 13th peak-production hand only when the
   opponent has more non-wheat crops than wheat crops.
4. Otherwise use the exact submitted labor schedule.

The rule uses only public state, remains fixed for the episode, and cannot
change crop, animal, movement, lifecycle, affordability, or liquidation safety.

## Holdout Results

Each holdout used the exact demand-animal package as control, both player
positions, the incumbent itself, compact, adaptive, lifecycle, scale, learned
service, and two captured elite schedules.

| Gate | Candidate | Control | Candidate margin | Control margin |
| --- | ---: | ---: | ---: | ---: |
| Seed 212 | **12-4** | 10-6 | -4,036.19 | -4,264.00 |
| Seed 213 | **10-6** | 9-7 | -8,940.38 | -9,539.12 |
| Combined | **22-10** | 19-13 | -6,488.29 | -6,901.56 |

Both gates had zero errors, more candidate wins, a positive margin delta, and
no opponent-level win regression. The direct incumbent holdout improved from
2-2 to 3-1, and learned service improved from 2-2 to 4-0.

The elite replay result remains 0-8 for both candidate and control. This is an
incumbent improvement, not evidence of a 1000-level ladder policy.

## Package

- Source: `agents/experimental_future_labor_agent.py`
- Package: `submissions/future-labor/main.py`
- SHA-256: `200fef67c5a8e8b001b4a54986bb853d22b80f869af7460b67ec8eda169c70e3`
- Loader: `DONE/DONE`, 92,478-90,174 on seed 214
- Equivalence: 1,438 decisions, zero mismatches
- Status: packaged, not submitted