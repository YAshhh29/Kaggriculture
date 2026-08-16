# Kaggriculture Progress Journal

Last updated: August 17, 2026

This file is the durable record of what we are doing, why we are doing it,
how we verify it, what went wrong, how we fixed it, and what comes next. Update
it whenever we complete an experiment or learn something that changes our
approach.

## Current Objective

Explain and reduce the learned policy's rare timing regressions while keeping
promoted v9 frozen as the deterministic submission control.

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
`http://127.0.0.1:8765/captioned_replay.html`. It places the official Kaggle
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
- synchronized explanation wrapper: `captioned_replay.html`.

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
| `captioned_replay.html` | Explains each official visualizer step in plain language. |
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

## What Comes Next

1. Keep v9 threshold 35 frozen; do not retune against spent seeds 20-29.
2. Investigate sequence-aware market labels: one-step interventions can change
  future inventory and make individually good-looking sales interact badly.
3. Keep model validation grouped by seed, never by individual row or player
  position.
4. Require the next candidate to beat v9 on seed-grouped regret and on every
  development seed before any full policy rollout.
5. Retain deterministic legality, capacity, liquidation, and v9 fallback rules.
6. Treat seeds 40-49 as spent; reserve seeds 50-59 for the next truly frozen
  candidate only.

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
