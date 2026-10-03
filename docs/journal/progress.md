# Kaggriculture Progress Journal

Last updated: August 19, 2026

This file is the durable record of what we are doing, why we are doing it,
how we verify it, what went wrong, how we fixed it, and what comes next. Update
it whenever we complete an experiment or learn something that changes our
approach.

## Current Objective

Reverse-engineer the public leaderboard's large-scale economies and build a
stronger opponent-facing policy while keeping promoted v9 frozen as the
deterministic submission control.

### Live Ladder And Leader Scouting

The one-goose submission completed Kaggle validation. Its first observed live
rating was 257.1, below v9's previous best 299.2, despite gaining 1,997 coins on
average over v9 on the fresh local holdout. A later leaderboard refresh showed
the team at 333.6 after more episodes. This confirms that profit against the
local `starter` opponent is not a sufficient metagame test: ladder rating is
driven by wins and losses against other submitted economies, not victory
margin against the starter.

We therefore began scouting public leaderboard episodes. The leader,
カワシギ, used team ID 16677252 and submission ID 55540317. Kaggle listed 147
public episodes for that submission. Two useful verified outcomes are:

| Episode | Leader coins | Opponent coins | Result |
| --- | ---: | ---: | --- |
| 94173913 | 111,082 | 109,547 | Win |
| 94247823 | 78,795 | 84,889 | Loss |

The Episode Player revealed a simpler public route than the generated SDK:
`GET /competitions/episodes/<episode-id>/replay.json`. We captured the complete
720-record win and loss replays without exposing credentials, then added
`analyze_public_replay.py` to summarize worker, land, crop, animal, structure,
market, bank, and terminal-state behavior.

Episode 94173913 maps player 1 to カワシギ and seed 1507302619. Its exact opening
was five hands, two cows, two sheep, seven wheat seeds, twelve melon seeds, and
one pasture build on turn 0. Across the full season, the leader:

- hired 277 hands, reaching 12 simultaneously;
- built 18 pastures and placed 6 cows plus 12 sheep;
- bought land on day 6 hour 4, day 11 hour 0, and day 12 hour 0;
- planted wheat, melon, strawberry, and carrot;
- sold 1,575 fertilizer, 1,525 wheat, 266 wool, and 188 milk, plus crops; and
- ended at 111,082 coins with no sellable shed or carried inventory.

The opponent used the same 277-hire schedule, land timing, and 6-cow/12-sheep
structure, yet scored 109,547. This was a contest between two similar
large-scale policies, not a leader farming an easy baseline.

In episode 94247823, カワシギ again hired 277 hands and bought its first two
extra quadrants on the same schedule, but shifted to 10 cows and 4 sheep and
finished with only three quadrants. The opponent won 84,889 to 78,795 using 311
hires, 6 cows, 7 sheep, and 3 geese. The evidence therefore separates a stable
backbone from an adaptive layer: cheap labor is persistent, while animal mix
and capital timing vary with the episode.

Artifacts:

- `artifacts/top-replays/episode-94173913-replay.json` and its compact
  `episode-94173913-strategy.json` report;
- `artifacts/top-replays/episode-94247823-replay.json` and its compact
  `episode-94247823-strategy.json` report; and
- `analyze_public_replay.py`, with synthetic schema tests.

### Two-Hand Candidate: Corrected Evidence

The first isolated response to the replay evidence was two hands hired at hour
0 each day around the one-goose policy. The first two daily hires cost one coin
each, so the full-season labor bill is only 60 coins. The coordinator assigns
distinct urgent-water, normal-water, harvest, and planting targets across the
farmer and hands. The farmer retains goose setup and service ownership.

A workload sweep on seed 30, both positions, selected twelve wheat plots:

| Wheat target | Mean coins |
| ---: | ---: |
| 10 | 12,061.5 |
| 12 | 12,958.0 |
| 14 | 11,854.0 |
| 16 | 10,628.0 |

Compact near-shed planting reduced travel but also reduced cash to 12,489, so
it was rejected. The inventory helper was then fixed to inspect only the main
farmer's inventory; wheat carried by a hand cannot satisfy a farmer `FEED`.
The seed-30 gate reproduced exactly after that fix.

Current-code development seeds 30-39, both positions:

| Metric | One goose | Two hands + twelve wheat | Difference |
| --- | ---: | ---: | ---: |
| Wins | 20 | 20 | Preserved |
| Mean coins | 9,884.5 | 12,333.3 | +2,448.8 |
| Improved / tied / worse games | - | 20 / 0 / 0 | Passed |
| Minimum paired gain | - | +1,588 | All positive |

The corrected all-worker report records 20,838 movement turns, 3,945 matched
wheat sales, 316 weeded cycles, and no terminal shed or carried inventory.
Unused seed inventory remains, so twelve plots is a useful labor baseline, not
an optimized end state.

### Plain Cow Candidate: Development And Frozen Holdout

The next isolated axis added one uncared-for cow and pasture at `(3,4)` while
retaining the goose at `(4,4)`, two daily hands, twelve wheat plots, no land,
and no CARE. A new explicit multi-animal scheduler handles setup, carried feed,
urgent feeding, fertilizer, and capped or day-28 product harvest separately for
each species. The crop coordinator now accepts protected tiles so crops cannot
occupy livestock structures; the default hands policy is unchanged.

Development seeds 30-39, both positions:

| Metric | Two-hand control | Plain cow candidate | Difference |
| --- | ---: | ---: | ---: |
| Wins | 20 | 20 | Preserved |
| Mean coins | 12,333.3 | 16,634.3 | +4,301.0 |
| Minimum candidate coins | - | 14,844 | - |
| Maximum candidate coins | - | 17,623 | - |
| Improved / tied / worse games | - | 20 / 0 / 0 | Passed |
| Minimum paired game gain | - | +1,894 | Passed the +1,500 gate |

The exact candidate was frozen before holdout with SHA-256
`aec06f1da0dd046a98af9e57d391ec779cb7fd690e0fb8e34d4044f9057cd9b5`.
Untouched seeds 60-69 were then used once, in both positions:

| Metric | Two-hand control | Frozen cow candidate | Difference |
| --- | ---: | ---: | ---: |
| Wins | 20 | 20 | Preserved |
| Mean coins | 11,768.3 | 16,694.75 | +4,926.45 |
| Candidate range | - | 15,646-17,902 | - |
| Improved / tied / worse games | - | 20 / 0 / 0 | Passed |
| Minimum paired game gain | - | +3,536 | All positive |

Every development and holdout game bought exactly one goose and one cow and
sold exactly 25 eggs, 11 milk, and 56 fertilizer. No game used CARE, repurchased
an animal, or ended with sellable shed/carried inventory. The candidate remains
development-only: `main.py`, `submissions/legacy/baseline/main.py`, and
`submissions/legacy/goose/main.py` are unchanged, and no third Kaggle agent was
submitted.

Decision: promote the plain cow policy as the strongest validated local
candidate, not as a proven leaderboard policy. Its 16.7k local economy is still
far below the 78k-111k public replay scale, and `starter` is not a representative
opponent. The next development axis should increase daily labor and livestock
capacity in a controlled stage before adding land or CARE.

### Overnight Scale Candidate: Frozen, Held Out, And Packaged

The valid next step was not another small sale threshold. The two live agents
were rated around 300 and 333, while captured top episodes operated at 78k-111k
coins. We therefore built a replay-inspired scale policy one axis at a time
around the frozen plain-cow control.

Seed-30 gates first selected labor and crop capacity while keeping one goose and
one cow fixed:

| Axis | Candidates | Selected result |
| --- | --- | ---: |
| Daily hands | 2, 3, 4, 5, 6, 8 | 5 hands at 18,021 before CARE |
| Wheat target | 12, 16, 20, 23 | 16 wheat at 18,715 |
| Four-animal opening | 2 cows + 2 sheep | 24,773 |
| CARE | off versus on | CARE raised the gate to 33,645 |

CARE changed the labor optimum. Under CARE, eight hands reached 35,993 while
ten and twelve fell to 33,050 because expensive or truncated hires stopped
returning value. Animal-density gates then selected four cows plus four sheep:

| Species mix | Seed-30 mean coins |
| --- | ---: |
| 4 cows + 4 sheep | 48,697 before feed repair |
| 6 cows + 2 sheep | 43,980 |
| 8 cows | 45,144 |

The first eight-animal prototype hid five escapes per game behind replacement
purchases. New benchmark instrumentation now records animal placements, loss
events, maximum active counts, and pre-endgame losses. The trace exposed two
root causes: expansion animals were placed too late on day 0, and feed purchases
were ordered after hires and expansion. The corrected policy:

- begins with two cows and two sheep;
- adds cows on days 3 and 5 and the final two sheep from day 7;
- feeds daily and protects required wheat from sale;
- prioritizes realized sales, feed, hires, animal expansion, land, then seeds;
- lets every worker carry, place, feed, care for, collect from, and harvest an
  animal; and
- reserves all livestock tiles from crop assignment.

The safe zero-loss gate scored 65,052. The exact final source was frozen at
SHA-256 `acfc19dd312dcd281428e62ff8d4c2919150b1aed0776d093e14470a0380cfb5`.
Its default policy is eight daily hands, sixteen wheat, four cows, four sheep,
daily feeding, CARE, staged expansion, and no land.

Development seeds 30-39, both positions:

| Metric | Plain cow control | Frozen scale |
| --- | ---: | ---: |
| Wins | 20 | 20 |
| Mean coins | 16,634.3 | 58,853.4 |
| Minimum / maximum | 14,844 / 17,623 | 38,264 / 65,579 |
| Mean paired gain | - | +42,219.1 |
| Minimum paired gain | - | +22,524 |
| Improved / tied / worse | - | 20 / 0 / 0 |
| Animal losses | 0 | 0 |

The source was not changed after this gate. It was evaluated exactly once on
untouched seeds 70-79, both positions:

| Metric | Plain cow control | Frozen scale |
| --- | ---: | ---: |
| Wins | 20 | 20 |
| Mean coins | 17,052.3 | 57,231.45 |
| Minimum / maximum | 16,102 / 18,346 | 43,745 / 65,110 |
| Mean paired gain | - | +40,179.15 |
| Minimum paired gain | - | +27,367 |
| Improved / tied / worse | - | 20 / 0 / 0 |
| Pre-endgame animal losses | 0 | 0 |
| Terminal shed / carried inventory | Empty | Empty |

The frozen policy also won every direct local match against the two active
submission policies on development seeds 30-39, both positions:

- 20/20 versus v9, averaging 57,713.6 versus 7,954.9; and
- 20/20 versus the one-goose policy, averaging 55,996.05 versus 9,362.4.

We added a research-only opponent that replays the captured rank-one action
sequence. This is a scripted stress test, not an adaptive copy of the leader.
On the original replay seed, the frozen scale candidate lost 41,702 to 113,032
from both positions. The result prevents a false claim that 57k against
`starter` equals leaderboard strength. The remaining strategic gap is larger
capital scale and market allocation: the script runs 18 animals, all land, and
up to 12 hands.

Two direct attempts to copy that topology were rejected:

- one extra land plus 24 wheat averaged 54,376.9 on a five-seed development
  screen, below the 58,853.4 no-land control; and
- a 12-hand, 6-cow, 12-sheep, three-land, 32-wheat gate scored 52,536.5 and
  activated only 6 cows and 2 sheep before service/crop churn dominated.

Decision: the no-land 4-cow/4-sheep policy is the strongest safe candidate from
this run. `submissions/legacy/scale/main.py` is built and ready but was not uploaded.
Kaggle's real loader completed full self-play with both statuses `DONE`.
Packaged and source agents both scored 55,138 against `starter` on seed 70 and
18,389-18,389 in self-play, proving behavioral equivalence.

- candidate source hash:
  `acfc19dd312dcd281428e62ff8d4c2919150b1aed0776d093e14470a0380cfb5`;
- packaged file hash:
  `a478741d32205b1ec772aced6879796c718249b695b0a8b5d85bb65ad893dac2`;
- package: `submissions/legacy/scale/main.py`;
- manifest: `submissions/legacy/scale/manifest.json`; and
- full suite: 98 tests passed.

Recommended live action: replace the weaker active submission with this frozen
scale package only after explicit approval. Keep the other slot as a control.
Do not describe this candidate as a leaderboard winner; describe it as a
zero-loss, holdout-validated step from 10k-17k local economies into the 57k
range, with a measured 71k deficit against the rank-one script.

### Live Scale And Pressure-Aware Investment Submissions

Kaggle labels the submission column `Score`. We should use that exact term.
It is not the farm's terminal coin total: the rules state that submissions are
scored from episode performance and those episode performances are aggregated
for leaderboard position. This explains why a 55,138-coin local episode and a
Kaggle Score near 600 can both describe the same agent.

The frozen scale package was uploaded with SHA-256
`a478741d32205b1ec772aced6879796c718249b695b0a8b5d85bb65ad893dac2`.
It completed at an initial Score of 600.0, then moved to 567.0 and 539.3 as more
competitive episodes were aggregated. Both older agents remained much lower:
the goose at 321.6 and v9 at 299.8. This is live evidence that the scale agent
is substantially stronger, while also showing why an initial Score is not
stable after only a few episodes.

The exact uploaded package was replayed locally on seed 70 and is available at:

- `artifacts/v1327-scale-submission-vs-starter-seed70-720.html`; and
- `artifacts/v1327-scale-submission-vs-starter-seed70-720-replay.json`.

It scored 55,138 versus 3,625, placed four cows and four sheep with zero losses,
and ended with no sellable shed or carried inventory.

We then implemented the requested investment strategy as a separate policy. It
clusters 6 cows and 12 sheep around central routes, buys all three quadrants,
uses adaptive labor up to ten hands, feeds and cares daily, and prioritizes
sales, feed, land, animals, labor, then seeds. Its first full gate reached
85,611 mean coins with all land, all 18 animals, and zero losses.

The raw 12-hand/24-wheat version averaged only 58,647 and lost 12 of 20 paired
games to the scale control. Lowering it to ten hands and twelve wheat improved
standalone development to 63,566.25. Direct shared-market tests then exposed a
catastrophic over-investment case: animal products fell toward the price floor
while wheat feed rose above 50 coins. A pressure-aware target now observes the
opponent's active animal count and reduces our own livestock, land, and labor
targets instead of blindly creating a shared glut.

Frozen pressure-aware source SHA-256:
`d93dd956bfb6951cc9c958bc93caf090dcb77c1b6f897e52ab4707699fe0beac`.

Untouched seeds 80-89, both positions:

| Metric | Pressure-aware investment |
| --- | ---: |
| Wins | 20 / 20 |
| Mean coins | 56,501.8 |
| Minimum / maximum | 42,577 / 88,136 |
| Animal losses | 0 |

It won 16 of 20 direct development games against the frozen scale policy and
lost 4, so it is deliberately the aggressive complement, not a universal
replacement. Against the captured rank-one script it lost 34,243 to 66,697,
cutting the earlier scale candidate's scripted deficit from 71,330 to 32,454.

The investment package was validated through Kaggle's real loader:

- package: `submissions/legacy/investment/main.py`;
- package SHA-256:
  `305db546dbef37b266833df3853633989ec7e9ea1d03255e9077cb258abe3287`;
- self-play: both `DONE`, 48,433 versus 48,085 on seed 80; and
- packaged/source equivalence: 44,147 versus `starter` on seed 80.

It was submitted with four daily submissions remaining and completed at a live
Score of 491.3. The frozen scale agent currently scores 537.4 and remains the
safer live control. No further submission should be selected from this run until
both new Scores have enough episodes to stabilize.

### Live Episode 94524971 And Zoned Routing Experiment

The screenshot showing 34,452 coins is correct. It is episode 94524971, seed
156033218: our scale submission lost 34,452 to dankwa wadie's 42,465. The 58k
number was a multi-seed `starter` development mean, never a promise that every
live episode would score 58k.

The replay separates two causes:

1. **Shared-market prices:** our live game sold almost the same quantities as
  the local seed-70 run: 198 fertilizer, 126 milk, 92 wool, and 58 wheat versus
  198, 126, 92, and 50 locally. The lower cash therefore came primarily from
  both players selling overlapping products into the same market.
2. **Routing/layout:** our scheduler formed planting tasks by scanning rows and
  slicing the first `available_seeds` empty positions before worker distance
  was considered. With sixteen seeds, the legal planting candidates were
  `(0,0)` through `(9,1)`. All 326 live crop tasks stayed in NW with a mean tile
  position of `(2.15, 1.49)`, and the farm ended with 16 weeds.

The opponent used the spatial idea raised during review:

- bought NE on day 6;
- used 7-8 daily hands;
- placed 12 cows and 4 sheep in a dense strip around the shed spanning NW/NE;
- performed 406 crop tasks in NW and 284 in NE;
- planted 122 wheat plus 5 melon cycles; and
- finished with only 3 weeds and 42,465 coins.

We created `experimental_zoned_agent.py` as a separate research agent. It does
not modify either submitted package. The first review replay proved a specific
top-row defect: row 0 was planted six times; only `(1,0)` was watered and
harvested, while the other five fresh crops crossed the day boundary unwatered
and became weeds.

The simulator starts a crop at `consecutive_unwatered = 1`, so a crop planted
without same-day water dies at that day's refresh. The corrected crop policy:

- ranks empty planting tiles from the shed outward instead of row-major order;
- gives worker IDs 0-4 near/NW planting ownership;
- gives worker IDs 5+ far/NE planting ownership after land unlock;
- commits a seed only when a second co-located worker waters it in the same
  simulator transition;
- keeps urgent watering, normal watering, and harvesting globally accessible;
- retries hires displaced by the ten-entry market-order cap later that day; and
- still performs feed, setup, fertilizer, harvest, and CARE before crop work.

The paired policy is source SHA-256
`b6b23889ece1a474be45ad58ada49344f43f5397c8b3d90e37556a3ab3c111f2`.

Development results, seeds 30-39, both positions:

| Candidate | Mean | Min-max | First-water misses | Animal losses |
| --- | ---: | ---: | ---: | ---: |
| Paired no-land: 8 hands, 4 cows, 4 sheep | 62,989.8 | 49,400-72,702 | 0 / 1,412 | 0 |
| Paired NE: 10 hands, 6 cows, 8 sheep | 64,549.75 | 25,677-94,567 | 0 / 1,240 | 0 |

The NE expansion is `experimental_zoned_expansion_agent.py`, source SHA-256
`b0cb1a2748ed8aaff29c7f10d0a9d7cdf7a2fec76f59cf278cac684f01bc1ac4`.
It buys one right-side quadrant and stages fourteen animals around NW/NE. It
wins 20/20 direct games against scale (50,300.2 versus 36,681.3 mean) and 18/20
against pressure-aware investment (49,506.4 versus 38,135.55 mean).

The variance is economic rather than a hidden service failure. In seed 38, all
fourteen animals survived and every fresh crop was watered immediately, but the
town had no milk or wool buyer: late milk fell to 3 and wool to 5. The same mix
reached 87,623 on seed 30, where milk/wool demand kept prices high. The NE agent
is therefore a high-upside research variant, not a universally safer control.

Top-leaderboard comparison remains a hard boundary. Against the captured
rank-one action script on its original seed, NE lost both positions, averaging
67,444.5 versus 117,806. The public leader used all land, up to twelve hands,
six cows, twelve sheep, multiple crop markets, and fertilizer. Our first-land
timing and livestock density are closer, but our wheat-only crop mix and
unconditional animal-product selling remain materially behind.

Rejected measured alternatives:

| Experiment | Seed-30 mean | Why rejected |
| --- | ---: | --- |
| NE land with 24 wheat / 10 hands | 54,895.5 | movement and wheat glut exceeded added harvest value |
| All land, 6 cows / 12 sheep / 10 hands | 48,039 | all land unlocked safely, but service and capital costs dominated |
| Harvest before ordinary watering | 57,245 | harvested sooner but sacrificed wheat yield |
| Water then globally prioritize harvest | 64,487.5 | better crop completion but lower field throughput |
| Local current-tile harvest completion | 67,430 | still below the 87,623 accepted expansion gate |
| Reserve row 0 from planting | 65,874 | hid usable land and reduced profit |

The important conclusion is nuanced: guaranteed first watering fixes the
original dead-row behavior, and NE pays only as a complete animal/labor bundle.
Buying all land still does not. One worker cannot service eight animals alone
because FEED, CARE, and fertilizer collection already require 24 tile actions
per service day before movement or animal-product harvesting.

The new seed-30 expansion replay has 720 records and scores 87,623. All 64
plant actions have a same-transition WATER action. Row 0 is no longer planted
once and abandoned: it has eight crop cycles, five harvested and three weeded
later in their lifecycle. The captioned viewer places every farmer/hand action,
readable market order, observed hire/land/animal change, bank delta, and board
delta underneath the official visualizer:

`http://127.0.0.1:8765/artifacts/ui/captioned_replay.html?replay=%2Fartifacts%2Fv1327-zoned-expansion-vs-starter-seed30-720.html&audit=%2Fartifacts%2Fv1327-zoned-expansion-vs-starter-seed30-720-audit.json`.

At the user's explicit request, the exact NE policy was packaged as
`submissions/legacy/zoned-expansion/main.py`. The package produced zero action
mismatches against the source across all 719 seed-30 transitions and both
finished at 87,623. Kaggle's real file loader completed 720-step self-play with
both agents `DONE`.

Live submission record:

- submission ID: `55630744`;
- status after validation: `Complete`;
- initial Kaggle Score: `600.0`;
- uploaded SHA-256:
  `3414e23178a61b162fbbc1910b215aac3bee973d8f259216b81fa101fe788283`;
- upload description: `Zoned NE expansion: 10 daily hands, 16 wheat, 6 cows,
  8 sheep; paired PLANT+WATER, staged same-day hiring, zero first-water misses
  and animal losses`; and
- daily submissions remaining before upload: 3.

The no-land policy remains the safer research control. The submitted NE policy
has the stronger mean and direct-match record but the weaker standalone floor.
The next justified discussion is demand-aware product/crop allocation and
worker routing, not another unconditional land purchase.

### Deterministic Lifecycle Crews And Admission Control

The submitted NE replay still lost 270 of 1,240 development crop cycles to
later weeds. We tested the user's hypothesis that workers should retain primary
roles and crops should be admitted only when their owners can complete them.
This work is separate from live submission `55630744`; the live package was not
changed or replaced.

The simulator rules answer two timing questions precisely:

- a fresh crop starts at `consecutive_unwatered = 1`, so planting-day water is
  mandatory;
- wheat age 1 is outside its yield window, so watering can be skipped when
  `consecutive_unwatered == 0`;
- wheat ages 2-4 are its productive water window and should be watered;
- mature wheat must be harvested before age-5 decay removes its yield; and
- animals are different: skipping feed forfeits that day's CARE bonus and moves
  the animal toward escape, so daily feed remains economically justified.

The selected `experimental_lifecycle_compact_agent.py` uses:

- ten daily hands, matching the submitted NE capital footprint;
- six primary animal specialists;
- two crop pairs with deterministic vertical patch ownership;
- one floater;
- paired same-turn planting and watering;
- five wheat slots per pair by default and six only after public wheat demand
  (two wheat-consuming shop instances or price at least 35);
- no long-distance optional retargeting; an idle crop worker helps an animal
  only within Manhattan distance two;
- late hiring taper after crop and animal deadlines; and
- two final-day hands plus the farmer collect the highest-value reachable
  animal output, return by hour 22, `DROP` at the shed, and sell the deposited
  inventory in the same transition.

Fresh holdout seeds 80-89, both positions:

| Metric | Submitted NE | Lifecycle compact |
| --- | ---: | ---: |
| Wins | 20 / 20 | 20 / 20 |
| Mean coins | 70,781.85 | 70,527.35 |
| Minimum / maximum | 56,832 / 89,648 | 51,034 / 90,124 |
| Crop cycles | 1,276 | 1,144 |
| Harvested cycles | 818 | 1,144 |
| Weeded cycles | 301 | **0** |
| Unfinished cycles | 157 | **0** |
| First-water misses | 0 | 0 |
| Animal losses | 0 | 0 |
| Worker movement turns | 83,408 | 58,959 |

Lifecycle compact now trails by only 254.5 mean standalone coins, while it completes
every admitted holdout crop, eliminates all 301 weeds and 157 unfinished
cycles, harvests 326 more crop cycles, and cuts movement by 29%. The final-day
liquidation change improved all 20 paired holdout games over the farmer-only
control by 951-2,339 coins (mean +1,631.8). In the shared market, the final
policy wins 19/20 direct development games against submitted NE and 20/20
against pressure-aware investment. It improved all 20 paired direct games
against each prior lifecycle control, by means of +821.55 and +859.55.

The result also disproves several tempting shortcuts:

- buying SW with unchanged workload scored 73,902 versus the 80,662 lifecycle
  NE gate;
- replacing four wheat slots with four fully managed SW melons scored 55,514
  after liquidation, so lower land and melons did not repay their cost;
- seven wheat per pair still had zero weeds but fell to 59,457.5 from self-glut;
- eight per pair reintroduced weeds and fell to 47,398;
- twelve hands controlled crops perfectly but lost 0/20 direct games to the
  submitted NE policy because its labor and wheat market footprint were larger;
  and
- five animal specialists underserviced milk/wool, while six plus nearby idle
  assistance recovered animal output without global wandering.

Against the captured rank-one script, lifecycle compact still loses both games,
12,684 versus 60,954 mean. The remaining frontier is diversified product and
market timing, not more unconditional land or wheat.

The old 88,602 replay appeared to stop growing after record 697 because the
day-29 hour-0 sale emptied the shed, while later animal output stayed on tiles
or in worker inventories. Only shed inventory can be sold. A farmer-only
return route raised seed 30 to 90,058; five hands raised it to 90,673; the full
0-10 hand frontier selected two hands because they recover the same output at
the lowest Fibonacci wage. Ten hands fell to 90,541. The final review replay
scores 90,685 versus 3,602 and is captioned at:

`http://127.0.0.1:8765/artifacts/ui/captioned_replay.html?replay=%2Fartifacts%2Fv1327-lifecycle-compact-vs-starter-seed30-720.html&audit=%2Fartifacts%2Fv1327-lifecycle-compact-vs-starter-seed30-720-audit.json`.

The review package `submissions/legacy/lifecycle/main.py` is Kaggle-loader valid and
source-equivalent across all 720 records in both player positions. Source and
package scored 90,685 as player 0 and 90,440 as player 1 with zero action
mismatches. Package SHA-256:
`aeb70a14f97d9c9778a1eadad9f424b97adc333470071432f7ca030b28de85a7`;
combined source SHA-256:
`98d1725c4297ae046e0ba98cb6f50e106bdf62cc24af9f46dbc71af85dcc0f91`.
It is not submitted. Keep submitted NE live until the user reviews the remaining
254.5-coin standalone gap.

### Center-Out Diversified NW-NE-SW Challenger

We implemented the user's spatial plan as a separate research agent without
changing the live submission or lifecycle package. NW is already owned, so the
forced purchase sequence is NE then SW. The strategy uses:

- animal cores at NW blocks 34/35/44/45, NE 36/37/46/47, and SW
  54/55/64/65;
- two cows and two sheep in each four-block core;
- three fixed crop pairs, one per quadrant;
- six managed center-out crop blocks per pair;
- wheat/carrot staples plus tomatoes, four strawberries, and two melon
  locations;
- two timed fertilizer windows per strawberry, each paired with water;
- eleven daily hands through day 28 and four final-day liquidation hands; and
- exact same-turn planting water, feed/CARE safety, deadline admission, and
  terminal `DROP`/sale rules.

The initial 12-slot design admitted more work than two workers per quadrant
could complete. It scored 75,051 on seed 30 with 23 crop losses. Eight slots
reduced losses but underused premium crops. Six slots plus shared seed-admission
logic and quadrant-local one-time capacity produced the final zero-loss policy.
Geese were screened and rejected; the balanced 6-cow/6-sheep farm had the best
five-seed floor. Delaying SW reduced seed-30 return; NE-only lost 15,583 versus
the current full NW/NE/SW workload.

Starter development seeds 30-34, both positions:

| Metric | Center-out diversified | Lifecycle control |
| --- | ---: | ---: |
| Wins | 10 / 10 | 10 / 10 |
| Mean coins | **72,202** | 54,287.7 |
| Minimum / maximum | **60,571 / 83,355** | 31,332 / 90,685 |
| Crop cycles | 642 | 562 |
| Harvested / weeded / unfinished | **642 / 0 / 0** | 562 / 0 / 0 |
| Animal losses | 0 | 0 |
| Final animals per game | 6 cows, 6 sheep | 6 cows, 8 sheep |
| Land purchases per game | NE + SW | NE |
| Strawberry fertilizer actions | 8 per game | 0 |

The shared-market check remains the blocker. Against lifecycle compact over
the same seeds and both positions, center-out loses 0/10, averaging 42,203.5
against 50,353.2. The cause is economic: extra SW capital, more labor, feed,
and overlapping milk/wool/fertilizer sales. A premium-price holding screen did
not recover the matchup. This agent is therefore a successful spatial and
diversification prototype, not an approved submission candidate.

The standalone review package `submissions/legacy/center-out/main.py` is Kaggle-loader
valid and source-equivalent across all 720 records in both player positions.
Source and package each score 83,355 versus starter on seed 30 with zero action
mismatches. Package SHA-256:
`cd3d7e92b114dd1bcdef085a3b9fd36d4c37b36146e3c8bd40b58254efe51284`.
The manifest remains explicitly review-only because the 0/10 direct gate has
not been solved.

At the user's explicit request, the exact package was then submitted to Kaggle:

- submission ID: `55666322`;
- submitted: `2026-08-21T09:46:47.587Z`;
- status: `COMPLETE`;
- initial public Score: `600.0`;
- uploaded bytes: `84,971`; and
- uploaded SHA-256:
  `cd3d7e92b114dd1bcdef085a3b9fd36d4c37b36146e3c8bd40b58254efe51284`.

The upload does not erase the local 0/10 direct-match result. Treat 600.0 as an
initial leaderboard observation and monitor episodes before promoting this
policy over the prior controls.

The final seed-30 replay scores 83,355 versus 3,393 and shows all workers,
market orders, bank changes, land unlocks, and crop/animal changes:

`http://127.0.0.1:8765/artifacts/ui/captioned_replay.html?replay=%2Fartifacts%2Fv1327-center-out-diversified-vs-starter-seed30-720.html&audit=%2Fartifacts%2Fv1327-center-out-diversified-vs-starter-seed30-720-audit.json`.

Source SHA-256:
`fb2d94b2e51ed81afb46d277d7ea8913f51cbf690ab42860591ec8c7decfc546`.
The durable rules and planning tools are `RULEBOOK.md` and
`artifacts/ui/field_strategy_planner.html`.

### One-Goose Candidate: Promotion Evidence

After the first v9 Kaggle submission validated at rating 600, we isolated one
livestock change. The candidate builds a coop on `(4,4)`, the unlocked
northwest shed-access tile, and keeps six wheat plots on the adjacent route. It
does not place animals far away: feeding, egg harvest, and fertilizer collection
are recurring services, so proximity to the shed and crop route minimizes labor.

The candidate buys and places one goose, feeds it every other day when escape
risk becomes urgent, harvests at the four-egg cap, and collects fertilizer
through day 28. It immediately sells eggs and fertilizer. The first prototype
accidentally bought wheat every turn and mixed livestock value with wheat
trading; feed purchasing was corrected to happen only when urgent. The final
policy buys about seven feed wheat per game.

Late-cycle analysis found every useful final wheat planting occurred by day 21.
Moving the goose policy's planting cutoff from day 24 to day 21 removed 3-4
terminal seeds per game while preserving crop and animal output. The candidate
also skips fertilizer collection on the final day and can repurchase a goose
for an empty coop after animal loss.

Development seeds 30-39, both positions:

| Metric | V9 | One goose | Difference |
| --- | ---: | ---: | ---: |
| Wins | 20 | 20 | Preserved |
| Mean coins | 8,093.8 | 9,884.5 | +1,790.7 |
| Improved games | - | 20 / 20 | All improved |

The exact candidate hash was frozen before fresh holdout evaluation:
`67621bc08c296b90f3d6f5e6ca6ff54a19c560822c2e4bbb7cdb09dd876367bf`.

Fresh seeds 50-59, both positions:

| Metric | V9 | One goose | Difference |
| --- | ---: | ---: | ---: |
| Wins | 20 | 20 | Preserved |
| Mean coins | 7,920 | 9,917 | +1,997 |
| Minimum paired gain | - | +1,355 | All positive |
| Maximum paired gain | - | +2,911 | - |
| Improved / tied / worse | - | 20 / 0 / 0 | Passed |
| Terminal inventories | Empty | Empty | Clean |

The goose policy produces less wheat than v9: 2,200 versus 2,960 harvested
units. That deliberate trade buys 480 eggs and 560 fertilizer sales across the
suite, more than repaying the animal, feed, and service-turn costs. This is the
first non-wheat strategy to pass both development and untouched holdout gates on
every seed and position.

Decision: approve the one-goose candidate as the next Kaggle submission while
retaining the validated v9 bot as the other active submission. The source stays
in `experimental_goose_agent.py` until the upload decision is explicitly
approved; the existing submitted `main.py` is unchanged.

### First Live Kaggle Submission

On August 18, 2026, the verified v9 `main.py` was uploaded to the live
Kaggriculture competition under the signed-in YASH JAIN account.

- description: `v9 verified baseline: six wheat plots, daily watering,
  day-24 planting cutoff, guarded price-aware selling`;
- submitted file: `submissions/legacy/baseline/main.py`;
- SHA-256: `eee28ea012df8880c834e59d761a2551d0e9dd26f2ac55535fd1585586eba38a`;
- daily quota before submission: 5 remaining;
- daily quota consumed: 1;
- Kaggle status immediately after upload: `Pending`;
- local Kaggle self-play before upload: both `DONE`, 7,467–7,467.

The uploaded file is exactly the promoted v9 submission hash, not the
development-only ridge agent. No private GitHub repository link or code was
published on Kaggle.

Status: simulator 1.32.7 is installed in the existing project-local `.conda`.
V9 passed a new generalization check against immediate sale, a checkpointed
4,154-row market-decision dataset was collected, and neighboring thresholds 34
and 36 were evaluated with separate tuning and holdout seeds. Threshold 36 was
promising but did not satisfy the predeclared every-seed holdout gate, so
`main.py` correctly remains unchanged at threshold 35.

### Second Overnight Run: Broader Labels And Full Learned Rollouts

The repository was initialized and pushed to
`https://github.com/YAshhh29/Kaggriculture` as 14 logical commits before this
run. Local environments and caches remain excluded; source, tests, reports,
datasets, audits, replays, and visual evidence are tracked.

The counterfactual collector was then made resumable. Its checkpoint records
the simulator version, agent hash, seed range, positions, sampled prices, and
branch limit. It refuses to append incompatible data and writes after every
completed seed, so interrupted state-branch runs no longer lose finished work.

We expanded development-only counterfactual coverage from prices 34-36 to
28-40 on seeds 30-39. The resulting dataset has 120 states:

| Counterfactual label | States |
| --- | ---: |
| HOLD preferred | 71 |
| SELL preferred | 13 |
| Tie | 36 |
| Total | 120 |

Dataset:
`artifacts/datasets/v1327-v9-market-counterfactuals-broad-seeds30-39.json`.

Model evaluation now reports total and worst-seed one-step regret. A grid of
20 shallow trees and 5 standardized ridge models was evaluated by leaving one
entire seed out at a time. V9 had 604 total regret and 489 worst-seed regret.
Several numerical winners were actually constant HOLD policies, so the model
gate was tightened to require both HOLD and SELL predictions.

The selected genuinely state-dependent family was ridge regression with
`alpha=100`. It initially made 21 SELL predictions and reduced total regret to
541 and worst-seed regret to 458. A development-only confidence grid selected
an 8-coin minimum predicted SELL advantage; that reduced SELL predictions to 3
and regret to 494 total / 455 worst seed.

We embedded those fixed coefficients in `experimental_ridge_agent.py`, not in
the submission. The wrapper preserves v9's farmer, seed, 72-unit inventory cap,
day-25 liquidation, and out-of-training-range fallback. It changes only wheat
HOLD/SELL within prices 28-40 when predicted advantage exceeds 8 coins.

Full policy rollout on development seeds 30-39:

| Metric | V9 | Guarded ridge | Difference |
| --- | ---: | ---: | ---: |
| Wins | 20 | 20 | Preserved |
| Mean coins | 8,093.8 | 8,250.2 | +156.4 |
| Improved independent seeds | - | 10 / 10 | Passed |
| Harvested and sold wheat | 2,960 | 2,960 | 0 |

This passed the development gate, so the fully frozen candidate was evaluated
once on untouched seeds 40-49. No further tuning occurred before that run.

Fresh holdout result:

| Metric | V9 | Guarded ridge | Difference |
| --- | ---: | ---: | ---: |
| Wins | 20 | 20 | Preserved |
| Mean coins | 7,972.4 | 8,088.4 | +116.0 |
| Minimum coins | 7,208 | 7,183 | -25 |
| Maximum coins | 8,450 | 8,647 | +197 |
| Improved independent seeds | - | 9 / 10 | One regression |
| Harvested and sold wheat | 2,960 | 2,960 | 0 |

The seed-level one-sided sign-test probability is 0.0107421875. The candidate
improved nine fresh seeds by 34-197 coins but lost seed 48 by 25 coins. A trace
showed only three differing sale moments; the first was a day-22 sale of 32
wheat at price 34 with a predicted +14.49 advantage. That intervention changed
later inventory timing and ultimately reduced terminal cash.

Decision: do not promote. The learned policy is a strong research candidate,
but it failed the predeclared every-seed consistency gate. `main.py` remains v9
threshold 35. Seeds 40-49 are now spent holdout data and cannot be used to tune
another candidate. The next untouched range begins at seed 50.

Key second-run artifacts:

- broad labels:
  `artifacts/datasets/v1327-v9-market-counterfactuals-broad-seeds30-39.json`;
- model grid:
  `artifacts/models/v1327-market-model-grid-broad-seeds30-39.json`;
- confidence grid:
  `artifacts/models/v1327-market-ridge-alpha100-threshold-grid.json`;
- development paired report:
  `artifacts/benchmarks/v1327-experimental-ridge-threshold8-vs-v9-dev-paired.json`;
- fresh holdout paired report:
  `artifacts/benchmarks/v1327-experimental-ridge-threshold8-vs-v9-fresh-holdout-paired.json`;
- seed-48 failure trace:
  `artifacts/diagnostics/ridge-threshold8-vs-v9-seed48-trace.json`.

Current baseline report:

`artifacts/benchmarks/v1327-price-aware-sell-35-cap72-liquidate25-vs-starter-seeds0-9.json`

### Overnight Refinement: Generalization And Learning Data

We first verified that the immediate-sale control could be reproduced without
editing `main.py`: setting the experimental threshold to 1 scored exactly
7,663 in both seed-0 positions, matching the historical v5 fingerprint.

We then compared frozen v9 with that control on seeds 10-19, both positions:

| Metric | Immediate-sale v5 | V9 threshold 35 | Difference |
| --- | ---: | ---: | ---: |
| Wins | 20 / 20 | 20 / 20 | Preserved |
| Mean coins | 7,450.45 | 7,705.95 | +255.50 |
| Minimum coins | 5,931 | 6,086 | +155 |
| Maximum coins | 8,197 | 8,394 | +197 |
| Harvested and sold wheat | 2,956 | 2,956 | 0 |

V9 improved every one of the 20 paired position-runs and all 10 independent
seeds. The conservative seed-level one-sided sign-test probability is
0.0009765625 under a no-advantage null. Seed 11 had already been viewed before
this suite; excluding it still left all 9 remaining seeds improved, with a
254.22-coin mean gain and probability 0.001953125. This is strong evidence that
v9's improvement was market timing rather than overfitting seeds 0-9.

Durable evidence:

- v9 report: `artifacts/benchmarks/v1327-v9-vs-starter-unseen-seeds10-19.json`;
- immediate-sale report:
  `artifacts/benchmarks/v1327-v5-immediate-sale-vs-starter-unseen-seeds10-19.json`;
- paired comparison:
  `artifacts/benchmarks/v1327-v9-vs-v5-paired-seeds10-19.json`.

Next, a checkpointed collector ran v9 on training seeds 30-39 in both
positions. It produced 20 unique episodes, all wins, and 4,154 decision rows:
3,848 `HOLD` and 306 `SELL`. Every row records seed, position, behavior-policy
hash, decision-time features, the observed action, and outcomes in separate
objects. Terminal information is deliberately excluded from `features` to
prevent target leakage. Raw replays were audited in memory and were not saved,
keeping the dataset compact.

The dataset is
`artifacts/datasets/v1327-v9-market-decisions-train-seeds30-39.json`.
It is suitable for validating schemas and analyzing v9, but not yet for
claiming policy improvement: all outcomes come from one deterministic behavior
policy. Training now would mostly clone the threshold rule, not learn the value
of an action v9 did not take.

Observed v9 triggers explain the next research direction. Of 306 sale rows,
300 included the price trigger, only 4 included the 72-unit cap, and 2 were
liquidation-only. We therefore varied only the price threshold while keeping
the cap and liquidation safeguards fixed.

| Threshold | Seeds | Mean coins | Paired result vs 35 | Decision |
| ---: | --- | ---: | --- | --- |
| 34 | 30-39 | 8,066.4 | -27.4; worse on all 10 seeds | Reject |
| 35 | 30-39 | 8,093.8 | Control | Keep |
| 36 | 30-39 | 8,149.9 | +56.1; better on all 10 seeds | Advance once |

Threshold 36 was then evaluated exactly once on untouched seeds 20-29. It won
all games and averaged 7,999.3 versus v9's 7,957.6, a gain of 41.7. However,
it improved 8 of 10 independent seeds and lost on seeds 28 and 29 by 1 and 2
coins. The seed-level sign-test probability was 0.0546875. Production and
terminal liquidation were identical, so this is a real but insufficiently
consistent timing difference.

Decision: reject threshold 36 under the predeclared every-seed promotion gate
and keep v9 threshold 35. Seeds 20-29 are now spent holdout data and must not be
used to select another candidate. At that point, 40-49 became the next untouched
holdout; the later guarded-ridge experiment below has now spent it.

New tooling:

- `compare_benchmarks.py` creates checked game- and seed-level paired reports;
- `export_market_dataset.py` enforces the feature/decision/outcome boundary;
- `collect_market_dataset.py` collects compact trajectories and resumes from
  policy-hash-checked checkpoints.

### First True Counterfactual Labels And Value Model

The installed environment exposes `clone()` and `step()`, so we tested whether
one live decision could branch into matched HOLD and SELL futures. Initial API
inspection found a serious trap: Kaggle's generic `clone()` copies the episode
steps but not `env.info`, where Kaggriculture stores its resolved seed. Without
repair, future weeds and shop unlocks in a clone would silently use seed 0.

The counterfactual collector therefore deep-copies `env.info` into every clone.
Tests and runtime probes verified that:

- branch execution does not mutate the source state;
- identical actions from identical clones produce identical next states;
- seed metadata is independent and preserved;
- Kaggriculture's daily randomness is deterministically keyed by seed and day;
- the built-in `starter` opponent is deterministic; and
- every unbranched baseline reproduced its known episode score.

At each sampled state, the collector preserves the farmer action and all other
market orders, forces exactly one `HOLD` or `SELL WHEAT` choice, then returns
both branches to frozen v9 through the end of the season. This yields a matched
terminal coin difference for an action v9 did and did not take.

The targeted dataset samples prices 34, 35, and 36 across development seeds
30-39, one position per seed:

| Label | States |
| --- | ---: |
| HOLD preferred | 7 |
| SELL preferred | 8 |
| Tie | 13 |
| Total | 28 |

The mean `SELL - HOLD` terminal value was -2.5357 coins. The data show why one
global threshold is imperfect. In seed 30, for example, selling 28 wheat at
price 34 was worth +2 coins, holding instead of selling 48 wheat at price 35
tied, and holding 16 wheat once at price 36 was worth +5 coins. Day, stock, and
the future price path matter in addition to current price.

Dataset:
`artifacts/datasets/v1327-v9-market-counterfactuals-train-seeds30-39.json`.

We then fit a dependency-free shallow regression tree to predict terminal
`SELL - HOLD` value and evaluated it by leaving one entire seed out at a time.
The depth-2 tree had 91 coins of total one-step regret versus v9's 62. Although
it chose an optimal action in more individual states, its few mistakes were
more expensive. A small depth/minimum-leaf grid found a 33-coin result only for
a depth-0 constant HOLD policy; every state-dependent tree scored 91-96.

Decision: do not promote a learned policy. The best result is not conditional
learning, and the conditional models overfit 28 states. This is still concrete
progress: we now have trustworthy counterfactual labels, a seed-grouped
validation metric, and evidence that broader price/day/inventory coverage is
required before another model fit.

Model reports:

- `artifacts/models/v1327-market-value-tree-depth2-seeds30-39.json`;
- `artifacts/models/v1327-market-value-tree-grid-seeds30-39.json`.

Current route finding: six crops already form a near-minimum watering sweep, but
the farmer traverses them again to harvest. A naive same-tile harvest scheduler
was tested and rejected because it caused nine late, unwatered plantings across
two games and did not improve mean cash.

Captioned visual replay: serve the repository root and open
`http://127.0.0.1:8765/artifacts/ui/captioned_replay.html`. It places the official Kaggle
1.32.7 visualizer beside a synchronized explanation of each record's farmer
action, destination, market order, cash, inventory, and board changes.

### Historical v5 Full 720-Record Audit

A complete seed-0 game against `starter` is stored in three forms:

- raw replay: `artifacts/v1327-agent-v5-vs-starter-seed0-720-replay.json`;
- official visual replay: `artifacts/v1327-agent-v5-vs-starter-seed0-720.html`;
- transparent turn audit: `artifacts/v1327-agent-v5-vs-starter-seed0-720-audit.json`.

Kaggle stores 720 indexed replay records. Record 0 is initialized state with a
placeholder action; records 1-719 are 719 executed state transitions. The audit
preserves all 720 and labels this framework convention explicitly.

The cash ledger reconciles exactly:

```text
3,000 starting cash
+ 5,043 realized wheat-sale revenue
-   380 successful seed spending
= 7,663 final bank
```

The agent sold 148 wheat at a weighted average of 34.0743 coins. Batch averages
ranged from 26.7083 early to 44 late. The rising price provides a concrete
market-timing hypothesis: hold some low-price early wheat, but cap stock below
the shed's 100-item limit and liquidate before season end.

This v5 audit is the immediate-sale control that motivated v9. The
machine-readable current policy and experiment gates are in `strategy.json`.

### Promoted v9 And Recorded Seed-11 Game

V9 changed only the sale policy. It holds wheat while price is below 35, then
releases all shed wheat if price reaches 35, stock reaches the 72-unit safety
cap, or day 25 begins. The six-plot production and route policy stayed fixed.

Across seeds 0-9 and both player positions, v9 completed and won all 20 games:

| Metric | v5 control | Promoted v9 | Difference |
| --- | ---: | ---: | ---: |
| Mean coins | 7,501.1 | 7,849.9 | +348.8 |
| Minimum coins | 6,760 | 7,150 | +390 |
| Maximum coins | 8,253 | 8,450 | +197 |
| Harvested and sold units | 2,960 | 2,960 | 0 |
| Mean harvest-to-sale delay | 10.05 | 63.05 | +53.00 turns |

V9 ended with no wheat, seeds, or carried inventory. A separate file-loaded
seed-0 gate, with no experiment overrides, scored 7,992 in both positions.
This confirms the promoted constants in `main.py`, not merely the benchmark
parameter path, produce the measured behavior.

A fresh file-loaded seed-11 game then ran on simulator 1.32.7 for all 720
official replay records against `starter`:

- agent score: 8,161;
- starter score: 3,677;
- both statuses: `DONE`;
- raw replay: `artifacts/v1327-agent-v9-vs-starter-seed11-720-replay.json`;
- interactive official visualizer:
  `artifacts/v1327-agent-v9-vs-starter-seed11-720.html`;
- exact turn audit:
  `artifacts/v1327-agent-v9-vs-starter-seed11-720-audit.json`; and
- synchronized explanation wrapper: `artifacts/ui/captioned_replay.html`.

The seed-11 ledger also reconciles exactly:

```text
3,000 starting cash
+ 5,541 realized wheat-sale revenue
-   380 successful seed spending
= 8,161 final bank
```

The agent sold all 148 harvested wheat at a weighted average of 37.4392 coins,
versus 34.0743 in the audited v5 seed-0 control. The caption page was browser
verified at 4x playback: its record number advanced with the official slider.
At record 295 it correctly showed `NORTH`, the next water target, `SELL WHEAT
48`, and bank movement from 2,810 to 4,401, a realized gain of 1,591.

Decision rule: compare current-version reports only with the same seeds,
positions, opponent, and simulator version. A scheduler candidate must preserve
all wins, raise repeated cash, and not increase late unwatered plantings.

## The Approach In Simple Terms

We are treating the agent like a farm manager whose decisions can be tested.
We are not asking it to do everything immediately.

1. Build a small strategy that works reliably.
2. Run the exact same strategy in many repeatable games.
3. Measure wins, coins, idle actions, and failures.
4. Change one idea at a time.
5. Keep a change only when repeated games show an improvement.

This matters because one winning game can be luck. A strategy becomes credible
when it works across different random seeds and from both player positions.

The current agent manages six wheat plots. It buys seeds, plants wheat,
waters it, waits for maximum yield, harvests it, and sells it. This is simple
enough to understand completely, which makes it a useful control group for
future experiments.

## Why We Start Without Machine Learning

The environment already gives us structured facts such as crop age, water
state, position, inventory, money, and prices. Our first problems are therefore
scheduling and resource allocation:

- Which task is urgent?
- Where should the farmer move next?
- Is another plot worth the extra walking and care actions?
- Does a farm hand earn more than it costs?
- Should produce be sold now or later?

A deterministic policy lets us learn those mechanics and detect mistakes.
Machine learning would add uncertainty before we have a trustworthy baseline
or a clear target to improve.

That prerequisite is now partly satisfied: v9 gives us a deterministic control,
repeatable evaluation, route metrics, and exact reward accounting. The plan is
therefore hybrid rather than heuristic-only or RL-only:

1. Freeze v9 and test it on unseen seeds 10-19 in both positions.
2. Save audited trajectories containing compact state features, legal
  high-level choices, the chosen choice, subsequent market outcomes, and final
  banked cash.
3. Train a supervised value or ranking model first on a narrow decision such as
  hold versus sell.
4. Keep deterministic legality, crop survival, shed capacity, and endgame
  liquidation rules around any learned score.
5. Evaluate on held-out seeds and additional opponents, with v9 as fallback.
6. Consider offline RL or self-play only when this action abstraction and
  evaluation split are stable.

Starting directly with raw farmer moves and only the final 720-record reward is
a poor first learning experiment. The reward is sparse, legal actions depend on
state, many failures have delayed effects, and a model could appear to improve
while exploiting a small seed set. A compact choice model gives us examples we
can inspect and a clean comparison against the rule it may replace.

## Current Project Map

| File | Purpose |
| --- | --- |
| `main.py` | The single-file competition submission and current policy. |
| `test_main.py` | Unit tests for individual farming decisions and packaging. |
| `run_match.py` | Runs one local match and optionally saves its replay. |
| `benchmark.py` | Runs repeatable games across seeds and player positions. |
| `test_benchmark.py` | Tests benchmark arithmetic and action counting. |
| `audit_episode.py` | Reconciles every replay transition, action, and cash flow. |
| `analyze_public_replay.py` | Extracts workforce, land, crop, livestock, and market strategy from public replays. |
| `experimental_hands_agent.py` | Development-only two-hand, twelve-wheat labor policy. |
| `experimental_cow_agent.py` | Development-only goose, cow, and two-hand policy. |
| `artifacts/ui/captioned_replay.html` | Explains each official visualizer step in plain language. |
| `requirements-simulator.txt` | Minimal Windows runtime dependencies. |
| `README.md` | Setup and usage guide. |
| `progress.md` | This experiment and problem-solving journal. |

## Completed Work

### 1. Created A Deterministic Baseline

The first policy targets four wheat tiles and uses this priority order:

1. Rescue wheat that has already missed a watering day.
2. Water all other unwatered wheat.
3. Harvest mature wheat after daily watering is complete.
4. Plant available wheat seeds on empty unlocked tiles.
5. Pass when no useful action is available.

The market logic sells wheat in the shed and buys enough seeds to maintain the
four-tile target.

Why four tiles: it creates a small, understandable workload. We can later test
whether more plots increase profit or merely waste movement and watering turns.

### 2. Added Decision Tests

`test_main.py` checks that the agent:

- buys four seeds initially;
- plants on an empty tile;
- moves toward the nearest unwatered wheat;
- waters before harvesting;
- harvests mature, watered wheat;
- sells stored wheat and replenishes seeds; and
- remains the final function in `main.py` for Kaggle's loader.

Verified command:

```powershell
./.conda/python.exe -m unittest test_main -v
```

Result: 8 tests passed, including the local plot-target experiment hook.

### 3. Built A Local Match Runner

`run_match.py` runs short smoke tests or complete seasons. It supports the
`pass`, `random`, and `starter` built-in opponents and can save replay JSON.

Verified full-season results on seed 7:

| Opponent | Our coins | Opponent coins | Result | Status |
| --- | ---: | ---: | --- | --- |
| `pass` | 6,854 | 3,000 | Win | Both `DONE` |
| `starter` | 6,485 | 3,503 | Win | Both `DONE` |

These results prove that the submission executes and the wheat loop is
profitable. They do not prove that the policy is generally strong because both
measurements use the same seed and player position.

### 4. Built A Multi-Seed Benchmark

`benchmark.py` records:

- seed and agent player position;
- agent and opponent status;
- win, loss, tie, or error;
- final coins and coin margin;
- aggregate win rate and score rate;
- farmer action counts;
- market order counts;
- results split by player position;
- simulator version; and
- SHA-256 hash of the exact agent file tested.

Testing both positions checks whether moving the same agent from player 0 to
player 1 changes the outcome. Hashing `main.py` prevents us from accidentally
comparing reports produced by different untracked policies.

Focused benchmark tests:

```powershell
./.conda/python.exe -m unittest test_benchmark -v
```

Result: 5 tests passed, including parameterized agent loading and partial-report
checkpointing.

Integration smoke test:

```powershell
./.conda/python.exe benchmark.py --seed-start 0 --seed-count 1 `
  --steps 48 --output artifacts/benchmarks/smoke.json
```

Result: two completed ties at 2,960 coins. This is expected because a 48-turn
episode is only two in-game days, while the policy waits four days to harvest
wheat at maximum yield.

### 5. Established The 20-Game Baseline

The unchanged four-plot policy was evaluated over seeds 0-9 in both player
positions against `starter`.

| Metric | Baseline v1 |
| --- | ---: |
| Games completed | 20 / 20 |
| Wins / losses / ties / errors | 20 / 0 / 0 / 0 |
| Win rate | 100% |
| Mean agent coins | 6,647.6 |
| Minimum agent coins | 6,228 |
| Maximum agent coins | 6,890 |
| Mean opponent coins | 3,501.2 |
| Mean winning margin | 3,146.4 |

Player-position split:

- player 0: 10 wins from 10 games;
- player 1: 10 wins from 10 games; and
- each seed produced the same score in either position, so this benchmark found
  no first-player advantage for these deterministic policies.

Farmer action usage across 14,400 turns:

| Action group | Turns | Share |
| --- | ---: | ---: |
| Pass | 7,720 | 53.6% |
| Movement | 2,520 | 17.5% |
| Plant, water, or harvest | 4,160 | 28.9% |

Every individual game used the same action pattern: 386 passes, 126 movement
turns, 147 waterings, 33 plantings, and 28 harvests. The market placed 30 seed
orders and 12 sell orders per game.

Interpretation: the baseline is reliable against `starter`, but more than half
of the farmer's turns are unused. That is strong evidence that labor capacity,
not action scarcity, permits a larger workload. It does not yet prove that a
larger workload is more profitable because extra plots also require movement,
watering, seeds, and timely harvesting.

### 6. Rejected The Eight-Plot Candidate At The Gate

Candidate v2 changed only the local benchmark parameter from four wheat plots
to eight. It was tested on seed 0 in both player positions before a full suite.

| Player | Four-plot baseline | Eight-plot candidate | Difference |
| --- | ---: | ---: | ---: |
| 0 | 6,633 | 6,138 | -495 |
| 1 | 6,633 | 6,408 | -225 |

Both candidate games still beat `starter` and completed with status `DONE`, but
both failed the predeclared profitability gate.

Action evidence across the two candidate games:

| Action group | Four-plot baseline pattern | Eight-plot candidate | Meaning |
| --- | ---: | ---: | --- |
| Pass | 772 | 179 | Idle time fell sharply. |
| Movement | 252 | 687 | Walking grew from 17.5% to 47.7% of turns. |
| Plant | 66 | 97 | More seeds reached the field. |
| Harvest | 56 | 52 | Fewer crop cycles actually completed. |

Conclusion: unused turns alone did not mean the farmer could efficiently manage
twice as many plots. The nearest-task policy spent the recovered capacity
walking between a larger set of tiles. It planted more often but harvested less
often, so seed spending and movement increased without enough saleable wheat.

Decision: reject eight plots and do not run the remaining 18 games. This is the
purpose of the cheap gate: falsify weak ideas before paying for a full suite.

Next adjustment: test six plots. This changes the workload by two rather than
four plots and asks whether a middle point captures some idle capacity without
overwhelming the current movement policy.

### 7. Six Plots Passed The Seed-0 Gate

Candidate v3 changed only the target from four plots to six and ran on seed 0
in both positions.

| Metric per game | Four plots | Six plots | Difference |
| --- | ---: | ---: | ---: |
| Final coins | 6,633 | 8,111 | +1,478 |
| Pass turns | 386 | 197 | -189 |
| Movement turns | 126 | 233 | +107 |
| Plant actions | 33 | 45 | +12 |
| Water actions | 147 | 207 | +60 |
| Harvest actions | 28 | 38 | +10 |
| Sell orders | 12 | 19 | +7 |

Six plots converted idle capacity into ten additional completed harvests. Its
movement share rose from 17.5% to 32.4%, but stayed well below eight plots at
47.7%. It also retained 197 pass turns, or 27.4%, so the farmer was busy without
being fully saturated.

Both positions produced the same 8,111 score, both agents finished `DONE`, and
the candidate passed the predeclared profitability gate. Decision: proceed to
the complete seeds 0-9 comparison before changing the submission default.

### 8. Six Plots Won The Full Comparison

Candidate v3 completed all 20 requested games on the same seeds, positions, and
opponent as baseline v1.

| Metric | Four plots | Six plots | Difference |
| --- | ---: | ---: | ---: |
| Completed games | 20 | 20 | 0 |
| Wins / losses / ties / errors | 20 / 0 / 0 / 0 | 20 / 0 / 0 / 0 | Preserved |
| Mean coins | 6,647.6 | 7,824.1 | +1,176.5 |
| Minimum coins | 6,228 | 7,403 | +1,175 |
| Maximum coins | 6,890 | 8,297 | +1,407 |
| Mean winning margin | 3,146.4 | 4,320.9 | +1,174.5 |

The mean score improved by 17.7%, and even the candidate's worst game exceeded
the baseline's worst game by 1,175 coins. Both policies won every game, so the
coin evidence is used to choose between two equally perfect win records.

Action usage across 14,400 turns:

| Action group | Four plots | Six plots | Difference |
| --- | ---: | ---: | ---: |
| Pass | 7,720 (53.6%) | 3,940 (27.4%) | -3,780 |
| Movement | 2,520 (17.5%) | 4,660 (32.4%) | +2,140 |
| Plant, water, or harvest | 4,160 (28.9%) | 5,800 (40.3%) | +1,640 |
| Harvest actions | 560 | 760 | +200 |
| Sell orders | 240 | 380 | +140 |

Interpretation: six plots use substantially more walking, but unlike eight
plots they convert the larger workload into completed harvests and sales. The
farmer still passes on more than a quarter of turns, leaving scheduling slack.

Decision: promote `TARGET_WHEAT_TILES` from 4 to 6. The focused policy suite
passes all 8 tests.

### 9. Validated The Promoted Submission Path

After changing the default constant, the agent was rerun through Kaggle's file
loader with no `--target-wheat-tiles` experiment override.

- seed 0, player 0: 8,111 coins, status `DONE`;
- seed 0, player 1: 8,111 coins, status `DONE`;
- opponent: 3,499 coins in both games;
- report `complete`: true; and
- promoted agent SHA-256 starts with `0b4555aa`.

The complete project suite then passed 13 tests: 8 policy and packaging tests
plus 5 benchmark tests. All relevant files had zero editor diagnostics.

Conclusion: candidate v3 is now baseline v3. The local experiment and the
actual single-file submission path behave identically.

### 10. Rejected Seven Plots At The Gate

Candidate v4 tested the only integer workload between the successful six-plot
policy and failed eight-plot policy.

| Metric per game | Six plots | Seven plots | Difference |
| --- | ---: | ---: | ---: |
| Final coins | 8,111 | 7,518 | -593 |
| Pass turns | 197 | 213 | +16 |
| Movement turns | 233 | 210 | -23 |
| Plant actions | 45 | 42 | -3 |
| Water actions | 207 | 215 | +8 |
| Harvest actions | 38 | 40 | +2 |
| Sell orders | 19 | 10 | -9 |

Both positions produced the same result and finished `DONE`. Seven plots did
not fail from excess movement: it walked less and harvested slightly more than
six. However, it sold on roughly half as many turns and banked less money.

The current benchmark counts sell orders, not units inside each order, and does
not retain final private inventory. Therefore it cannot yet prove whether seven
plots sold fewer units, sold larger batches at worse times, or ended with
unsold wheat that did not count toward reward.

Decision: reject seven plots under the current policy and keep six as baseline
v3. Improve measurement before changing sale timing or spatial logic.

### 11. Found The Seven-Plot Cash-Conversion Loss

The six- and seven-plot seed-0 gates were rerun after extending benchmark
reports with market unit quantities and final private inventory.

| Metric per game | Six plots | Seven plots | Difference |
| --- | ---: | ---: | ---: |
| Wheat units requested for sale | 148 | 135 | -13 |
| Final carried wheat | 4 | 20 | +16 |
| Final shed wheat | 0 | 0 | 0 |
| Final wheat seeds | 0 | 5 | +5 |
| Seed units purchased | 45 | 47 | +2 |
| Approx. produced units: sold + carried | 152 | 155 | +3 |

Conclusion: seven plots did produce slightly more wheat, but much of its final
harvest remained on the farmer and never became banked money. It also ended
with five purchased seeds that could no longer produce a sale. Because reward
counts only banked coins, those assets were strategically worthless at season
end.

The timing mechanism explains this: wheat planted on day 25 reaches its
day-four maximum on day 29. A harvest goes into farmer inventory, while this
policy sells only from the shed. The normal end-of-day drop leaves no later day
for a market sale. Day 24 is therefore the latest planting day that targets a
day-28 harvest, an end-of-day shed drop, and a day-29 sale.

Next experiment: apply this day-24 cutoff to six plots only. This isolates
endgame timing from workload size.

### 12. Day-24 Cutoff Passed The Gate

Candidate v5 ran on seed 0 in both positions and scored 8,181 each, 70 more than
baseline v3's 8,111.

| Metric per game | Baseline v3 | Cutoff candidate | Difference |
| --- | ---: | ---: | ---: |
| Banked coins | 8,111 | 8,181 | +70 |
| Wheat units sold | 148 | 148 | 0 |
| Seed units purchased | 45 | 38 | -7 |
| Final carried wheat | 4 | 0 | -4 |
| Final seeds | 0 | 0 | 0 |

The gain has a direct accounting explanation: seven avoided seeds at 10 coins
each equals 70 coins. The candidate did not rely on a favorable wheat price or
extra sales. It simply stopped paying for inputs that could not return cash
before season end.

Both positions finished `DONE` and produced identical results. Decision:
proceed to the full 20-game comparison because the gain is small enough that we
still need repeated evidence before changing the submission default.

### 13. Promoted The Day-24 Cutoff

Candidate v5 completed all 20 games on the same baseline seeds and positions.

| Metric | Baseline v3 | Cutoff v5 | Difference |
| --- | ---: | ---: | ---: |
| Completed games | 20 | 20 | 0 |
| Wins / losses / ties / errors | 20 / 0 / 0 / 0 | 20 / 0 / 0 / 0 | Preserved |
| Mean coins | 7,824.1 | 7,894.1 | +70 |
| Minimum coins | 7,403 | 7,473 | +70 |
| Maximum coins | 8,297 | 8,367 | +70 |
| Mean winning margin | 4,320.9 | 4,390.9 | +70 |

Every completed candidate game ended with an empty shed, no carried produce,
and no seeds. The exact 70-coin shift across mean, minimum, and maximum matches
the seed-cost accounting observed at the gate.

Decision: promote `LAST_WHEAT_PLANTING_DAY = 24`. The public `agent` now uses
the cutoff by default. A no-override file-loaded validation scored 8,181 in both
positions with status `DONE`, and the final project suite passed 16 tests with
zero editor diagnostics.

Historical v5 action shares over the 20-game 1.32.3 suite:

- pass: 4,960 turns, or 34.4%;
- movement: 4,240 turns, or 29.4%; and
- planting, watering, or harvesting: 5,200 turns, or 36.1%.

### 14. Seven Plots Still Failed With The Cutoff

Candidate v6 retained the promoted day-24 cutoff and changed only the workload
from six plots to seven. It scored 7,588 in both seed-0 positions, 593 below
baseline v5's 8,181.

| Metric per game | Six plus cutoff | Seven plus cutoff | Difference |
| --- | ---: | ---: | ---: |
| Banked coins | 8,181 | 7,588 | -593 |
| Wheat units sold | 148 | 135 | -13 |
| Plant actions | 38 | 35 | -3 |
| Harvest actions | 37 | 35 | -2 |
| Movement turns | 212 | 175 | -37 |
| Pass turns | 248 | 295 | +47 |
| Seed units purchased | 38 | 40 | +2 |
| Final seeds | 0 | 5 | +5 |

This result disproves the idea that seven failed only because of endgame waste.
With equal cutoff logic, seven completed fewer full crop cycles and sold fewer
units. It did not simply walk too much; it also passed more and left five seeds
unplanted. Saving those five seed costs would recover only 50 of the 593 lost
coins.

Decision: reject candidate v6 and keep baseline v5. Do not test additional plot
counts until task routing or cycle scheduling changes.

## Problems Faced And Fixes

### VS Code's Initial Project Command Created No Files

Problem: the standard Python project command reported success but left the
workspace empty.

Fix: created the small project explicitly and validated each file with tests.

Lesson: check observable filesystem results instead of trusting a success
message by itself.

### Python 3.13 Could Not Resolve The Full Simulator Stack

Problem: the machine's system Python was 3.13. Kaggle's package includes older
and unrelated game dependencies that did not resolve cleanly on that version.

Fix: created a project-local Conda environment using Python 3.12.13 at
`.conda`. The system Python installation was left untouched.

Lesson: isolate competition dependencies from the machine's global Python.

### A VS Code Helper Mixed Two Python Versions

Problem: an environment helper overwrote a Conda environment with Python 3.13
virtual-environment metadata. The root interpreter and package paths then
disagreed.

Fix: removed the mixed environment and recreated it under the `.conda` name,
which matches the convention used by other projects on this machine.

Lesson: verify `sys.version`, `sys.prefix`, and package imports after creating
an environment.

### The Full Kaggle Dependency Set Hit Windows Path Limits

Problem: an Orbax compatibility test fixture has a deeply nested path that
Windows could not create. Orbax belongs to other Kaggle environments and is not
used by Kaggriculture.

Fix: verified a minimal fresh installation containing `jsonschema`, `requests`,
and `kaggle-environments==1.32.3` installed with `--no-deps`. A real
Kaggriculture episode completed successfully in that environment.

Lesson: validate the narrow runtime path we need instead of installing every
optional ecosystem bundled by a general package.

### Kaggle Loaded The Wrong Function From `main.py`

Problem: a file-based match called `_act_at_or_move` and failed because Kaggle's
loader selects the last callable created while executing the file.

Fix: moved `agent` to be the final function definition in `main.py` and added a
regression test that enforces this rule.

Lesson: a Python file that imports correctly is not automatically packaged
correctly for Kaggle's file loader.

### A Short Match Looked Unprofitable

Problem: after 48 turns, the agent had 2,960 coins while `pass` retained 3,000.

Explanation: the agent had spent 40 coins on four seeds, but the episode ended
two days before its planned day-4 harvest.

Fix: use short games only to detect runtime failures. Use complete 720-turn
seasons to evaluate profit.

### Other Kaggle Environments Print Missing-Package Messages

Problem: importing `kaggle_environments` reports that Halite, Kore, Lux,
OpenSpiel, and Reinforce Tactics cannot load because optional packages such as
NumPy are absent.

Fix: no code change is needed. Kaggriculture loads and completes games. The
messages describe other environments that we intentionally did not install.

Lesson: distinguish a relevant runtime failure from noise produced by unrelated
plugins.

### Long Benchmarks Appeared To Stop Before Completion

Problem: the terminal tool returned an output snapshot after only a few games,
even though the Python process continued in its persistent terminal. The first
benchmark implementation wrote JSON only after all games, so there was no
durable evidence while the process was still running and a true interruption
would lose completed games.

Fix: `benchmark.py` now rewrites a checkpoint report after every completed game
and includes a `complete` boolean. A partial report contains all finished game
records and an up-to-date summary; the flag becomes `true` only when the
expected game count is reached.

Verification: a focused test writes a one-game checkpoint for a two-game suite,
then confirms `complete` is false and the saved result and summary are intact.

Lesson: long experiments should persist incremental evidence instead of relying
on one final write or on how a terminal UI presents live output.

## Benchmark Protocol

The current v9 baseline command is:

```powershell
./.conda/python.exe benchmark.py --opponent starter `
  --seed-start 0 --seed-count 10 --steps 720 `
  --output artifacts/benchmarks/v1327-v9-vs-starter-seeds-0-9.json
```

Protocol rules:

1. Do not modify `main.py` during a benchmark run.
2. Use the same seeds for every policy comparison.
3. Test both player positions unless diagnosing a specific issue.
4. Treat any non-`DONE` status as an error, not a loss.
5. Compare win rate first because Kaggle ranking uses wins and losses.
6. Use coins, margins, and action counts to explain why results changed.
7. Keep a candidate only after it beats the baseline over repeated games.

Score rate awards 1 point for a win, 0.5 for a tie, and 0 for a loss. It is a
compact summary, but the raw win/loss/tie counts remain the primary evidence.

### How To Read The Metrics

- **Reward / final coins** is money already in the bank. This determines the
  winner.
- **Market order count** says how many turns contained an order. One sell order
  may contain one unit or many units.
- **Market units** sums the quantities requested inside those orders, such as
  `SELL:WHEAT` or `BUY_SEED:WHEAT`.
- **Final shed inventory** is produce stored but not sold. It has no reward
  value at season end.
- **Final carried inventory** is produce still held by the farmer or hands. It
  also has no reward value at season end.
- **Final seeds** are paid inputs that can no longer return money once there is
  insufficient growing time.
- **Pass share** estimates unused action capacity, while **movement share**
  measures travel overhead. Neither is good or bad alone; the question is
  whether actions eventually create banked profit.

## Current Rules Audit: Simulator 1.32.7

On August 16, we compared the live Kaggle How to Play page with the installed
engine and found the workspace was still on 1.32.3 while PyPI had released
1.32.7. The existing project-local `.conda` was upgraded in place; no second
environment was created.

The current wheat pipeline is:

1. `BUY_SEED` is a market order. It can run in the same turn as one farmer
  action, but market processing happens after farmer actions, so a seed bought
  this turn cannot be planted until a later turn.
2. Moving one cell costs one farmer turn.
3. `PLANT WHEAT` costs one farmer turn on an empty unlocked tile.
4. A new plant must be watered later on its planting day. It starts with one
  missed day already recorded and becomes a weed if the day ends unwatered.
5. Wheat needs no digging on an empty tile, no structure, no pasture, and no
  crop `CARE` action.
6. Daily watering keeps it alive. Watering at ages 2, 3, and 4 raises an
  unfertilized crop from its base 1 unit to 4 units.
7. Fertilizer is optional. Buying it puts it in the shed; the farmer must use
  `PICKUP`, travel to a crop, and spend a `FERTILIZE` action, while watering is
  still required. It can raise wheat to 6 units, but paying 100 coins to gain
  at most two wheat units is not automatically profitable.
8. `HARVEST` costs one farmer turn and puts wheat in carried inventory.
9. Carried inventory drops to the shed at end of day. `SELL` can sell only from
  the shed, and only banked coins count at the end.

Pastures are only for cows and sheep; geese use coops. `CARE` is animal-only
and banks an animal yield bonus. These operations are not part of wheat setup.

There are no spring/summer planting restrictions. “Season” means the single
30-day episode. Crop scheduling comes from time-to-yield, decay, daily care,
market demand, and the remaining days, not from a crop calendar prohibition.

### Why Six Concurrent Wheat Plots

The plot target is constrained by service capacity, not only by four-day growth:

- On an ordinary care day, six crops need 6 water actions plus roughly 5 moves
  along the current one-way sweep.
- On the first harvest day, the current two-pass route uses 6 waters + 5 moves
  outward + 6 harvests + 5 moves back + 1 replant + 1 immediate water = 24
  turns, exactly one day.
- Seven plots cannot fit that same schedule: 7 + 6 + 7 + 6 already equals 26
  before replanting.

Earlier 1.32.3 experiments also measured six as better than four, seven, or
eight, but those cash values must now be reproduced on 1.32.7.

### Route Instrumentation Findings

The current analyzer records task coordinates, travel before each task, daily
routes, crop cycles, planting-day water, weeds, harvest yield, inferred shed
arrival, and FIFO harvest-to-sale delay.

For seed 0, player 0 on 1.32.7:

- score: 7,663 versus starter's 3,596;
- movement: 212 turns;
- crop tasks: 260;
- mean travel before a task: 0.81 turns, maximum 5;
- planted cycles: 38;
- harvested cycles: 37;
- weeded cycles: 1;
- planting-day watering: 37 of 38;
- every successful unfertilized harvest: 4 units;
- harvested and sold: 148 units; and
- mean harvest-to-sale delay: 10.05 turns.

The first six tiles were `(4,4)`, `(4,3)`, `(4,2)`, `(4,1)`, `(4,0)`, and
`(3,0)`. That is already a minimum five-move path through six adjacent tiles.
The agent eventually touched nine coordinates because the failed planting
became a permanent weed and nearest-empty placement shifted later cycles.

The failed cycle was planted at `(4,2)` on day 9, hour 23. No watering turn
remained, so it became a weed at day 10, hour 0.

### 1.32.7 v5 Control Baseline

The same policy completed seeds 0-9 in both player positions:

| Metric | Frozen v5 control |
| --- | ---: |
| Games | 20 / 20 completed |
| Wins / losses / ties / errors | 20 / 0 / 0 / 0 |
| Mean coins | 7,501.1 |
| Minimum coins | 6,760 |
| Maximum coins | 8,253 |
| Mean opponent coins | 3,642.9 |
| Mean margin | 3,858.2 |
| Movement turns | 4,240 |
| Crop task visits | 5,200 |
| Planted / harvested / weeded cycles | 760 / 740 / 20 |
| Harvested and matched-sold wheat | 2,960 / 2,960 |
| Mean harvest-to-sale delay | 10.05 turns |

The action and lifecycle pattern was stable: every game lost exactly one
hour-23 planting but sold every successfully harvested unit. Cash varied because
town shop draws and market demand varied by seed.

### Rejected Current-Version Route Candidates

**Block hour-23 planting:** removed the weed and produced a fixed six-tile
layout, but seed-0 cash fell from 7,663 to 7,538 despite selling the same 148
units. The changed synchronization altered dynamic market timing. Rejected at
the gate rather than promoted from intuition alone.

**Harvest a watered mature current tile before moving:** intended to merge the
watering and harvest sweeps. It instead changed the remaining schedule enough
to create 9 late unwatered plantings across two games, increased movement to 586
turns, sold only 288 units versus the baseline pair's 296, and scored 7,491 as
player 0 and 7,824 as player 1. Mean 7,657.5 was below the 7,663 baseline, so the
candidate was rejected.

### Day-9 Macro Selection And Compact Kaggle Submission

Day-5 tree and KNN selectors failed promotion at 23-7 and 22-8 versus a 24-6
fixed baseline. Day-9 recollection produced 54 fresh four-arm training contexts
and a separate 30-game validation set. The day-9 tree went 26-4, grouped-CV KNN
went 27-3, and fixed compact went 28-2. The oracle also went 28-2, so the
validation features contained no recoverable win beyond the compact policy.

The learned candidates were rejected. A fixed day-9 compact agent advanced on
direct evidence: 20-0 versus the submitted adaptive agent and 44-6 over fresh
center-out, lifecycle, scale, investment, and starter games. It remained 0-4
against the exact current-top and rank-two replay controls.

The first Kaggle upload, `55778248`, failed at the first action because the
standalone package retained a workspace-only import. A red structural test now
rejects all `experimental_*` imports. The corrected package passed Kaggle's
path loader (`DONE/DONE`), 1,438-decision equivalence, and all 213 tests.

Corrected submission `55778351` is `COMPLETE`. Validation episode `99509927`
finished 70,494-71,744. Its initial 600.0 is not ladder evidence. Kaggle tracks
it alongside adaptive submission `55770236`, currently rated 654.0.

The first public sequence was loss/win/loss: 71,293-104,910 against
zulfikar.khalwaniev, 59,107-28,908 against Marc Dakuginow, and 57,916-86,410
against Kshitiz2002. Compact is therefore 1-2 at 542.3. The sample is small,
but the direction is clear enough to keep adaptive as the measured incumbent.

### Full Capacity, Learned Templates, And Deadline Taper

Replay feedback identified two explicit limits in compact: it hardcoded one
extra land, and crop admission stopped melons after day 7, strawberries after
day 11, and wheat after day 22. Two wheat slots also had an impossible day
23-through-22 admission window. Full-capacity v1 exposed a rotation bug that
oscillated PLANT and DIG; after fixing active-crop identity, v3 bought both land
expansions and beat compact 16-4 on development and 60-0 across a fresh
six-policy league.

The day-level replay showed why workers appeared idle: PASS rose from 11% on
day 20 to 32-79% on days 21-29 while the policy continued hiring 12 hands.
Blindly releasing every idle crop reserve reduced PASS slightly but lost 2,853
coins per game through route churn. A deadline-aligned workforce taper instead
kept ten hands through day 26, then used 8/4/3 on days 27-29. It preserved the
last wheat cohort and improved development mean from 76,129 to 76,981 coins.

A real day-4 contextual bandit was trained over paired terminal outcomes. It
selected crop rotation and crop-service reserve templates above deterministic
safety. KNN reached 24-0 on untouched counterfactual contexts, but direct
rollout versus fixed wheat was 5-5 with exactly symmetric rewards: it selected
wheat every time. The learned policy is implemented but rejected; this is not
claimed as an RL improvement.

Deadline taper validation:

- fresh six-policy league, seeds 169-173, both positions: **60-0**;
- current-top replay control: 0-2, own mean 50,463.5;
- rank-two replay control: 0-2, own mean 68,335.0;
- package SHA-256:
  `d76bd22843350319b44c9543e72ab261abb42a6c4077a0a6dd0c92735305f0d7`;
- source/package/replay equivalence: 0 mismatches over 1,438 decisions; and
- Kaggle submission `55795843`, validation episode `100091628`, `COMPLETE`.

Before the learned upload, the tracked pair was deadline `55795843` plus
compact `55778351`. Deadline's current verified snapshot is 12-13 over 25
games at 604.1882; its three newest ladder games were losses. Compact is still
displayed at 631.6 but is no longer one of the latest two tracked submissions.

### Post-Submission Learning And Service-Capacity Gates

The broader economic contextual portfolio did not beat its fixed controls on
untouched validation: the tree finished 21-5, KNN 19-7, and fixed wheat and
fixed melon each 24-2. A daily state-cloned seed-admission collector found
decisive examples in both directions, including one extra seed flipping a win
to a loss and another flipping a loss to a win. The first frozen tree lost
11.547 win-first utility versus baseline on holdout. After augmentation and
hard worst-seed/worst-opponent constraints, model selection correctly chose
the always-baseline fallback. This is real counterfactual learning evidence,
but not an RL promotion.

The next deterministic experiments isolated serviceable occupancy:

- per-quadrant seed reservation: 3-7, with 89.1 plantings and 34 weeds/game;
- crop-first reservation: 0-10, with 93.2 plantings and 42 weeds/game;
- critical cross-quadrant rescue: 5-5, position-symmetric and neutral;
- crop-before-CARE plus reservation: 8-2 on seeds 159-163, then 6-14 on the
  broader spent-seed 140-149 gate;
- crop-before-CARE without reservation: 7-3, then 9-11 on the broader gate;
- admission before CARE and due-work reserve scaling: each 0-10;
- replay-grounded 13th hands on days 19, 21, and 26: 4-6;
- routine cross-quadrant assistance using only otherwise-idle workers: 4-6;
  and
- carried-only strawberry fertilization: 1-9.

These failures sharpened the constraint. Animal CARE and collection are not
incidental overhead: reducing them also raises the opponent's milk/wool market
value. More crops, more worker actions, or fewer PASS actions are not promotion
metrics unless terminal wins improve.

### Learned Service Selector Promotion

The simulator executes farmer and hand actions sequentially. Two workers on an
animal tile can therefore FEED and CARE in the same transition. The deadline
scheduler previously waited for a later observation before assigning CARE. A
strict optimization now pairs FEED+CARE only when two free workers are already
co-located and one carries wheat, so it adds no travel and does not consume the
protected crop pair. Fixed pairing improved the first direct gate to 7-3 but
was mixed at 9-11 on broader seeds, proving that context mattered.

A real contextual bandit now selects between frozen deadline service and
co-located pairing. Both arms share the opening through day 0. At day 1, the
collector clones the exact simulator state and rolls both safe arms to terminal
reward. Opponent identity is not a feature. The frozen depth-2 tree uses public
position and opponent crop state, locks one arm for the episode, and falls back
to baseline outside the observed day-1 opponent-bank range.

Promotion evidence:

- training: 80 cloned contexts, 68 wins learned versus 67 for either fixed arm;
- separate validation: 37-3 learned, 35-5 baseline, 36-4 fixed pairing, and
  37-3 oracle;
- direct spent-seed league: 37-3 across deadline, compact, adaptive, and scale;
- untouched seeds 184-185: **23-1** across deadline, compact, adaptive,
  center-out, lifecycle, and scale;
- untouched direct deadline matchup: **3-1**, mean margin +1,391;
- captured elite scripts: still 0-4, with exact deadline fallback in unsupported
  opening states;
- Kaggle path loader: `DONE/DONE`, rewards 82,365-82,229;
- source/package/replay equivalence: zero mismatches over 1,438 decisions; and
- package SHA-256:
  `684693161aebb51bd6293a497033d630218af5eabf92870899efabef69d158b2`.

Fresh seeds 184-185 are now spent. The exact package was uploaded as Kaggle
submission `55803952` (133,479 bytes). Validation episode `100394606`
completed 60,004-57,984, status `COMPLETE`, and initialized the agent at 600.0.
The tracked pair is now learned service `55803952` plus deadline `55795843`.

### Overnight Routing, Demand, And Workspace Pass

The workspace is now organized into `agents/`, `core/`, `policies/`,
`research/`, `tests/`, `tools/`, `models/`, `submissions/`, and `docs/`.
Generated datasets, replays, diagnostics, and benchmark matrices remain local
under ignored `artifacts/`; promoted models and exact packages are versioned.

Routing diagnosis showed that the farm grid has no blocked movement tiles, so
Manhattan distance is the exact Dijkstra/A* path length. The one-step movement
code was already shortest-path optimal. The visible outer-layer behavior came
from target valuation and static cohort order. Globally choosing the nearest
equal-priority planting slot lost 6-14 against the submitted package, so it was
rejected. Exact shortest-path primitives now live in `core/routing.py`, while
urgency and economic value continue to choose targets.

Shop demand is modeled explicitly in `core/economics.py`. Every shop instance
consumes its products six times per day; duplicate and single-product shops
compound demand. This explains the melon case: melon has high nominal value but
no specialist shop, only one guaranteed town-center unit per day, a long cash
delay, and a severe nonlinear glut curve.

A bounded demand-aware candidate keeps the proven wheat crop schedule but waits
until day 6, after two shop draws, to choose expansion livestock. It replaces at
most one sheep in each new quadrant with cows or geese and locks the choice.
Unsupported low-bank openings fall back to the balanced herd.

Evidence against exact learned-service package
`684693161aebb51bd6293a497033d630218af5eabf92870899efabef69d158b2`:

- development seeds 140-149: 13-7, mean margin +1,057.45;
- validation seeds 159-163: 7-3, mean margin +2,628;
- five-policy validation league: 47-3;
- untouched seeds 186-187 across six policy styles: **23-1**;
- untouched direct submitted-agent gate: 3-1, mean margin +1,399;
- elite scripts: 0-4, with exact submitted-baseline rewards through fallback;
- standalone loader: `DONE/DONE`, 74,624-71,607;
- source/package/simulator equivalence: zero mismatches over 1,438 decisions;
- package SHA-256:
  `53cbab96eaf7eba10a55adac2208b273636ba45274b5cac34967bedae335f5ac`.

A three-arm contextual bandit was trained on 80 cloned day-6 contexts and
evaluated on 40 separate contexts. Its validation curve was 35, 34, 35, 33,
33, and 35 wins as training grew. Fixed cows scored 35 and the oracle 37. The
tree is rejected; the curve is versioned at
`docs/experiments/demand-animal-learning-curve.svg` rather than claiming an RL
gain that did not generalize.

Seeds 186-187 are now spent. The demand-animal heuristic is the clean candidate
for live measurement; its learned sibling is research-only.

### Overnight Shadow Gate And Live Submission

The deterministic seeds 188-197 suite ran five variants against learned
service, compact, adaptive, lifecycle, and scale in both player positions: 500
full 720-turn games. Every game completed `DONE/DONE` with zero errors.

| Variant | W-L | Mean margin | Decision |
| --- | ---: | ---: | --- |
| Exact submitted learned-service control | 89-11 | +11,185.60 | Control |
| Demand-animal heuristic | **92-8** | +11,234.75 | Promote |
| Rejected shadow tree | 91-9 | +11,741.24 | Research-only |
| Fixed cows | 85-15 | +11,012.25 | Reject |
| Fixed geese | 79-21 | +8,847.82 | Reject |

Demand improved the direct control matchup from 10-10 to 13-7 and did not
regress any opponent-level win count. The shadow tree remains rejected because
its held-out learning curve did not improve with more training contexts; this
single matrix does not retroactively make that training result generalize.

The exact frozen package was uploaded as Kaggle submission `55817911`.
Validation episode `100869093` completed 58,100-59,301, status `COMPLETE`, and
initialized at 600.0. Its SHA-256 remains
`53cbab96eaf7eba10a55adac2208b273636ba45274b5cac34967bedae335f5ac`.
The tracked pair is now demand animal `55817911` plus learned service
`55803952`.

### Opponent-Aware Future Labor

Three live demand-animal losses exposed a capacity gap rather than a pathfinding
bug. Our peak crop footprint was 35-41 versus 50-55, plantings were 79-83 versus
84-194, and PASS load was 1,378-1,567 versus 213 for the 115k opponent. The
board remains obstacle-free and every movement step is an exact shortest step.

Worker-relative nearest-vacancy planting lost 0-2 at -5,426.5 margin with seven
weeds because targets changed during travel. Stable center ordering went 1-1 at
-1,020. Dynamic crop slots, demand-gated fertilizer, and larger crop-worker
reserves also failed direct gates. Those axes were removed from production
interfaces rather than retained as misleading options.

A fixed 13-hand peak schedule beat the exact package 6-0 on seeds 206-208 but
hurt an all-wheat scale matchup. The final day-6 rule adds that hand only when
the demand-selected herd replaces sheep with cheaper cows/geese and the
opponent has more non-wheat crops than wheat. It otherwise falls back to the
submitted schedule for the full episode.

Untouched broad gates across eight opponent families and both positions:

| Gate | Future labor | Exact control | Margin delta | Decision |
| --- | ---: | ---: | ---: | --- |
| Seed 212 | **12-4** | 10-6 | +227.81 | Promote |
| Seed 213 | **10-6** | 9-7 | +598.74 | Promote |
| Combined | **22-10** | 19-13 | +413.27 | Package |

Both gates completed without errors or opponent-level win regression. Direct
incumbent games improved from 2-2 to 3-1 and learned-service games from 2-2 to
4-0. Both policies remain 0-8 against the elite replay schedules.

The standalone package is `submissions/future-labor/main.py`, SHA-256
`200fef67c5a8e8b001b4a54986bb853d22b80f869af7460b67ec8eda169c70e3`.
Kaggle path-loader self-play completed 92,478-90,174 and all 1,438 compared
decisions matched source and replay. The exact file was uploaded as submission
`55821334`; validation episode `100974134` completed 52,718-52,990.

At 24 ladder games the submission is 13-11 at Score 674.8 with mean reward
68,738.58. At the same 23-game count, demand animal was 12-11 at Score
658.9609 with mean reward 67,795.91; it now displays 655.8. Future labor is the
stronger tracked submission, but it is not a 1000-level result.

Branch-level replay inspection explains the limited gain. The 13-hand branch
activated six times and went 5-1; the fallback branch went 7-10. Episode
`100978351` reproduced exactly at 73,394-79,127 and showed the fallback's
capacity gap: 39 versus 48 peak crops, 572 versus 877 crop tile-days, zero
versus 32 fertilizer actions, and 12 versus 13 hands.

We compacted all 11 live-loss opponent schedules and verified that the frozen
package reproduces every original reward before counterfactual evaluation.
Pressure labor, lean herd, late strawberries, pressure plus late strawberries,
and fertilizer holding are rejected on own-reward deltas of -3,040, -4,105.73,
-2,822.73, -2,924.18, and -1,902.64. Replay wins caused only by changing the
fixed opponent's market return are explicitly not promotion evidence.

A zero-travel strawberry service bundle improved seven of the 11 loss contexts
and tied four, for +217.82 mean own reward with no negative context. It performs
ordered `HARVEST`/`FERTILIZE`/`WATER` only when all workers and carried
fertilizer are already on the tile. The unconditional version had one -14,602
own-reward cascade on the win set. A frozen fertilizer-price guard removed that
case: across 24 ladder contexts it improved 15, tied nine, regressed none, and
preserved every incumbent win. Broad seeds 215-216 stayed 23-9 for both
candidate and control, though candidate margin improved by 178.28. It was
rejected because wins did not improve.

Full-capacity, center-out, pressure-aware investment, and dynamic-replacement
arms were then screened over the 11 losses. Their own-reward deltas were
-6,623.27, -24,771.00, -33,160.64, and -10,944.36. Richer day-6 own workload
and herd features did not help leave-one-episode-out selection; always-control
still won validation.

A bounded carried-fertilizer arm created the first real replay conversion.
Episode `100989827` changed from 91,939-93,752 to 95,691-94,332, with 23 more
harvested units, the same one weed, zero animal losses, and no sellable terminal
inventory. Unconditional routing still regressed five of 11 losses. A frozen
contextual guard routes only with normalized wheat price above 1.30, no wool
shop, at most three opponent wheat crops, and the existing low fertilizer-price
guard. It otherwise uses guarded zero-travel service.

The contextual arm improved eight losses, tied three, regressed none, and
gained 1,303.09 mean own reward. The separate 12-win set remained 12-0 with
seven improvements, five ties, and +364.17 mean reward; the next live win also
improved by 395. Untouched seeds 217-218 were 22-10 for both candidate and
control. Candidate mean margin improved by 226.72, with zero errors and no
opponent-level regression, but no extra broad-gate win. It is research-only and
was not packaged or submitted.

### Late Workload-Aware Value Fertilizer

The replay league expanded to all 33 then-visible ladder games: 16 losses and
17 wins. The collector now resolves our player index from replay agent names,
supports conflict-checked append/refresh, and captures day 9-12 worker,
fertilizer, premium-crop, and animal-service state at hours 8 and 12.

Fertilizer ROI now estimates extra units over the three-day effect and compares
their conservative sale value with selling fertilizer. A separate economic
wheat reserve retains one to three feed days only when animal-product value
beats wheat sale value. Combined fertilizer plus economic feed was rejected:
it produced four fixed-replay wins but regressed seven of 16 own rewards, with
a -23,649 minimum delta.

The first routed strawberry policy improved 12 of 16 losses but had a -12,921
outlier. A day-12 harvest-backlog guard made the loss set monotonic, then failed
the independent win set at -13,289. A four-application budget converted two
captured losses and averaged +2,759.31 there, but still had a -11,538 win-set
outlier. Risk-constrained shallow trees also failed held-out zero-regression
validation.

The root cause was mechanism-level opportunity cost and market timing. The
safe implementation runs after all productive assignments and may use only an
otherwise-idle carrier on a strawberry already assigned water or already
watered. A frozen day-12 price tier permits up to two staging steps above 1.30
normalized strawberry price and requires co-location otherwise. Four total
applications are allowed; each must model at least 50 coins of marginal value.

Across 33 exact replay contexts, the audited tiered arm improved 30, tied
three, regressed none, converted two captured losses, and preserved all 17
captured wins. Mean own delta was +1,220.21. Colocated-only broad seeds 219-220 tied
control at 21-11 while improving mean margin by 567.19. Tiered seed 221 tied
control at 10-6 with +537.38 margin improvement. No gate added a win, so no
package or upload was created. A five-application seed-221 probe narrowed a
loss to 440 coins; six applications worsened it to 513 with no additional
yield. Seed 222 remains untouched.

The final audit put fertilizer and wheat opportunity costs on the same 75%
sale-realization basis and separated melon versus strawberry proximity and
fertilization features. The corrected source remained monotonic at 14/2/0 on
losses (+1,266.38 mean) and 16/1/0 on wins (+1,176.76 mean). A combined rerun
of spent broad seeds 219-221 stayed 31-17 for both candidate and control while
improving candidate mean margin by 768.02. It remains rejected for no extra
wins.

## What Comes Next

1. Keep submission `55821334` frozen while matchmaking accumulates.
2. Add genuinely new ladder losses beyond the current 33-game replay league.
3. Require a fresh broad-gate win, not only positive reward or margin.
4. Keep seed 222 untouched until a mechanism can close the remaining narrow
  direct-match gap without increasing the fertilizer budget.

## Experiment Log

| Version | Change | Evaluation | Result | Decision |
| --- | --- | --- | --- | --- |
| Baseline v1 (1.32.3) | Four wheat plots | Seed 7 vs `pass` | 6,854-3,000 | Historical |
| Baseline v1 (1.32.3) | Four wheat plots | Seed 7 vs `starter` | 6,485-3,503 | Historical |
| Baseline v1 (1.32.3) | Four wheat plots | Seeds 0-9, both positions | 20-0-0, mean 6,647.6 | Historical control |
| Candidate v2 | Eight wheat plots only | Seed 0, both positions | Mean 6,273; -360 vs control | Rejected at gate |
| Candidate v3 | Six wheat plots only | Seed 0, both positions | 8,111 both; +1,478 | Gate passed |
| Candidate v3 | Six wheat plots only | Seeds 0-9, both positions | 20-0-0; mean 7,824.1 | Promoted |
| Promoted v3 (1.32.3) | Six-plot `main.py`, no override | Seed 0, both positions | 8,111 both, 2-0-0 | Historical baseline |
| Candidate v4 | Seven wheat plots only | Seed 0, both positions | 7,518 both; -593 | Rejected at gate |
| Candidate v5 | Six plots plus day-24 cutoff | Seed 0, both positions | 8,181 both; +70 | Gate passed |
| Candidate v5 | Six plots plus day-24 cutoff | Seeds 0-9, both positions | 20-0-0; mean 7,894.1 | Promoted |
| Promoted v5 (1.32.3) | `main.py`, no override | Seed 0, both positions | 8,181 both, 2-0-0 | Historical baseline |
| Candidate v6 | Seven plots plus day-24 cutoff | Seed 0, both positions | 7,588 both; -593 | Rejected at gate |
| Baseline v5 (1.32.7) | Existing `main.py` | Seed 0, both positions | 7,663 both, 2-0-0 | Current gate |
| Baseline v5 (1.32.7) | Existing `main.py` | Seeds 0-9, both positions | 20-0-0; mean 7,501.1 | Current control |
| Candidate v7 (1.32.7) | Block hour-23 planting | Seed 0, player 0 | 7,538; -125 | Rejected at gate |
| Candidate v8 (1.32.7) | Finish mature current tile | Seed 0, both positions | Mean 7,657.5; -5.5 | Rejected at gate |
| Candidate v9 (1.32.7) | Sell at 35, cap at 72, liquidate day 25 | Seed 0, both positions | 7,992 both; +329 | Gate passed |
| Candidate v9 (1.32.7) | Same price-aware policy | Seeds 0-9, both positions | 20-0-0; mean 7,849.9; +348.8 | Promoted |
| Promoted v9 (1.32.7) | File-loaded `main.py`, no override | Seed 0, both positions | 7,992 both, 2-0-0 | Current baseline |
| Promoted v9 (1.32.7) | Full audited replay | Seed 11, player 0 | 8,161-3,677; cash difference 0 | Captioned evidence |
| Promoted v9 vs v5 control | Seeds 10-19, both positions | V9 mean 7,705.95; +255.5; 10/10 seeds improved | Generalization passed |
| Candidate threshold 34 | Seeds 30-39, both positions | Mean 8,066.4; -27.4; 0/10 seeds improved | Rejected |
| Candidate threshold 36 | Seeds 30-39, both positions | Mean 8,149.9; +56.1; 10/10 seeds improved | Advanced to holdout |
| Candidate threshold 36 | Untouched seeds 20-29, both positions | Mean 7,999.3; +41.7; 8/10 seeds improved | Rejected by consistency gate |
| Promoted v9 threshold 35 | Untouched seeds 20-29, both positions | Mean 7,957.6; 20 wins | Current baseline retained |
| Counterfactual pilot | Seed 30, prices 34-36 | HOLD/SELL/TIE each represented | Branching validated |
| Counterfactual dataset | Seeds 30-39, one position | 28 states: 7 HOLD, 8 SELL, 13 ties | Development evidence |
| Depth-2 value tree | Leave-one-seed-out | Regret 91 vs v9 62 | Rejected |
| Depth-0 value baseline | Leave-one-seed-out | Regret 33 vs v9 62 | Research baseline only; not conditional |
| Broad counterfactual data | Seeds 30-39, prices 28-40 | 120 states: 71 HOLD, 13 SELL, 36 ties | Development evidence |
| Guarded ridge rollout | Seeds 30-39, both positions | Mean 8,250.2; +156.4; 10/10 seeds improved | Development passed |
| Guarded ridge rollout | Fresh seeds 40-49, both positions | Mean 8,088.4; +116.0; 9/10 seeds improved | Not promoted |
