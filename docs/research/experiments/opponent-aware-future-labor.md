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
- Kaggle submission: `55821334`
- Validation: episode `100974134`, 52,718-52,990, `COMPLETE`
- Status: submitted unchanged

## Live Measurement

At 24 ladder games, future labor is 13-11 at Score 674.8 with mean reward
68,738.58. Demand animal's first 23 games were 12-11 at Score 658.9609 with
mean reward 67,795.91; its current displayed Score is 655.8. Future labor is
the stronger tracked submission, but this is still not progress near 1000.

The new branch activated in six of the 23 games. Those games finished 5-1,
with roughly 84.7k mean reward and +22.3k mean margin. The 17 fallback games
finished 7-10, around 64.3k mean reward and -5.6k mean margin. The branch works
when selected; the inherited fallback is the current weakness.

The first loss, episode `100978351`, reproduced exactly at 73,394-79,127 on
resolved seed `1426717232`. It did not activate future labor. The opponent used
13 hands, 48 peak crops, 877 crop tile-days, 130 plantings, and 32 fertilizer
actions; we used 12 hands, 39 peak crops, 572 crop tile-days, 69 plantings, and
zero fertilizer actions.

A compact counterfactual league reproduces all 11 live losses before testing
safe macro arms. Every fixed arm was rejected on our own mean reward:

| Arm | Mean reward delta | Improved / tied / worse |
| --- | ---: | ---: |
| Crop-pressure labor | -3,040.00 | 1 / 6 / 4 |
| Lean herd | -4,105.73 | 1 / 5 / 5 |
| Late strawberries | -2,822.73 | 0 / 9 / 2 |
| Pressure labor + late strawberries | -2,924.18 | 1 / 6 / 4 |
| Fertilizer hold at 70 | -1,902.64 | 4 / 0 / 7 |

Fixed replay wins caused by depressing the opponent's market are not counted
as improvements.

## Zero-Travel Crop Service

The prior fertilizer scheduler routed two workers to each target and displaced
other work. A deeper deterministic bundle was tested instead. It acts only
when workers are already co-located on a productive strawberry and one already
carries fertilizer. Worker-index ordering guarantees `HARVEST`, `FERTILIZE`,
then `WATER`; before first yield it uses `FERTILIZE`, then `WATER`. It performs
no movement or shed pickup.

On the 11 live losses it improved seven and tied four, with no regression and
+217.82 mean own reward. The unconditional version preserved all 12 captured
wins but had one -14,602 own-reward market cascade. A frozen day-6 guard enables
the bundle only when normalized fertilizer price is at most 0.965. The guarded
version improved seven and tied five on those 12 wins, with +162.33 mean own
reward and no negative context. It also improved the next live win by 395.

A depth-1/2 selector was trained on all 23 day-6 contexts using leave-one-
episode-out validation and excluding player position. Its fertilizer-price
split suggested the guard but did not itself validate under leave-one-episode-
out evaluation. The frozen guard was therefore tested separately. Across all
24 ladder contexts it improved 15, tied nine, and regressed none.

Two untouched broad gates remained tied on wins. Seed 215 was 12-4 for both
candidate and control, while seed 216 was 11-5 for both. Candidate mean margin
improved by 178.28 across the combined 23-9 result. The primitive remains
research-only because it created no additional broad-gate win.

## Contextual Carried-Fertilizer Service

Larger historical policies were screened against all 11 losses and rejected
on own reward. Full capacity, center-out, pressure-aware investment, and
dynamic replacement had mean deltas of -6,623.27, -24,771.00, -33,160.64, and
-10,944.36. Adding own workload and herd-composition features did not rescue
their leave-one-episode-out selector; it still chose control in every game.

The existing carried-fertilizer scheduler was then bounded to one strawberry
per quadrant and combined with the low-price guard. Unconditional routing was
mixed at five improved, one tied, and five worse. A frozen conservative rule
routes only when day-6 normalized wheat price is above 1.30, there is no wool
shop, and the opponent has at most three wheat crops. All other contexts retain
only guarded zero-travel service.

On the 11 loss schedules, this contextual arm improved eight, tied three,
regressed none, and gained 1,303.09 mean own reward. Episode 100989827 changed
from a 91,939-93,752 loss to a 95,691-94,332 win: nine fertilizer actions
produced 23 additional harvested units with the same one weed, no animal loss,
and no terminal sellable inventory. The separate 12-win set stayed 12-0 with
seven improvements, five ties, no regressions, and +364.17 mean own reward.
The next live win also improved by 395.

Untouched broad seeds 217 and 218 were safe but did not add wins:

| Gate | Candidate | Control | Candidate margin | Control margin |
| --- | ---: | ---: | ---: | ---: |
| Seed 217 | 11-5 | 11-5 | +552.94 | +199.19 |
| Seed 218 | 11-5 | 11-5 | +3,910.56 | +3,810.88 |
| Combined | 22-10 | 22-10 | +2,231.75 | +2,005.04 |

Both gates had zero errors, positive margin deltas, and no opponent-level win
regression, but both failed the required more-wins check. The candidate is not
packaged or submitted. Its replay conversion is a useful direction, not a
leaderboard claim.

The next iteration needs either more genuinely new live losses or a mechanism
that converts a fresh broad-gate game. Another threshold over the same 11
losses is not justified.

## Late Value Fertilizer And Feed Iteration

The live replay league was refreshed from public metadata to 33 ladder games:
16 losses and 17 wins. Player identity is now resolved from the replay's agent
names instead of the winner-first browser card. Each record captures day 9-12
at hours 8 and 12, including worker positions, carried fertilizer, due melons
and strawberries, harvest backlog, and pending animal service.

The economic layer estimates fertilizer's marginal three-day crop units and
compares their conservative sale value with selling the fertilizer. It also
estimates whether animal product value justifies retaining one, two, or three
days of wheat feed. The broad economic-feed arm was rejected: on the 16 losses
it created four fixed-replay wins but improved/tied/worsened 9/0/7 on own
reward, with a -23,649 floor. Shared-market wins do not repair that risk.

Routed late strawberry service improved many contexts but displaced later work
or shifted market timing. A four-application budget reduced the risk and
converted two captured losses, but one independent win still lost 11,538 own
reward. Restricting fertilizer to otherwise-idle carriers removed direct action
displacement; restricting the staging distance to zero removed the remaining
route-sensitive regression but reduced upside.

The final research policy uses two tiers at day 12 hour 12:

- strawberry price above 1.30 times base: an otherwise-idle fertilizer carrier
  may move at most two steps toward an already-serviced or already-watered
  strawberry;
- otherwise: only an already-colocated idle carrier may fertilize; and
- the full episode is capped at four applications with at least 50 coins of
  modeled marginal value per application.

It never overwrites feed, CARE, harvest, water, planting, or another assigned
action. It retains the inherited three-land expansion and demand-selected herd.
Exact replay validation:

| Set | Result | Mean own delta | Minimum delta |
| --- | ---: | ---: | ---: |
| 16 captured losses | 2 converted; 14/2/0 improved/tied/worse | +1,266.38 | 0 |
| 17 captured wins | 17 preserved; 16/1/0 improved/tied/worse | +1,176.76 | 0 |
| Combined | 30/3/0 improved/tied/worse | +1,220.21 | 0 |

Untouched broad gates still failed the required more-wins check:

| Candidate | Seed | Candidate | Control | Margin delta |
| --- | ---: | ---: | ---: | ---: |
| Colocated-only | 219 | 10-6 | 10-6 | +623.81 |
| Colocated-only | 220 | 11-5 | 11-5 | +510.57 |
| Tiered | 221 | 10-6 | 10-6 | +537.38 |

All three gates had zero errors and no opponent-level win regression. On seed
221, four applications narrowed the closest loss from 1,321 to 689 coins. A
fifth narrowed it to 440; a sixth worsened it to 513 and added no harvested
units. More fertilizer is not monotonic. The tiered policy remains
research-only and seed 222 is untouched.

After the final audit corrected sale-to-sale opportunity costs and separated
melon from strawberry proximity features, the exact current source was rerun
over all three spent broad seeds. Candidate and control both finished 31-17;
candidate mean margin improved from -8,470.54 to -7,702.52, a +768.02 delta.
Every opponent-level win count was preserved. The formal decision remains
`REJECT` because total wins did not increase.