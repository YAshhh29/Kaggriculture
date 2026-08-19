# Kaggriculture Agent

This repository is our learning lab and competition submission for
Kaggriculture.

See `progress.md` for the detailed experiment journal, decisions, failures,
fixes, current work, and next steps.

`strategy.json` is the machine-readable current policy, verified baseline,
replay findings, hands and livestock experiments, learning roadmap, and
promotion guardrails.

## What The Competition Is

Kaggriculture is a two-player, turn-based resource-management game. The
environment calls your `agent` function once per turn with an observation of
the farm and market. Your function returns actions for the farmer, hired hands,
and market. After 720 turns, the player with more banked coins wins.

This is an agent-programming competition before it is a machine-learning
competition. A deterministic policy with good scheduling, accounting, and
market logic is the best place to learn the environment. We can consider
search or learning methods only after we have a measured baseline.

Kaggle labels the displayed submission metric `Score`. It is distinct from
in-game coins: episode performances are aggregated into this competition Score,
so it changes as more episodes are played. The frozen scale submission started
at 600.0 and later moved to 567.0 and 539.3 while its local seed-70 farm score
remained 55,138 coins. Reliability across many opponents therefore matters more
than one unusually profitable game against `starter`.

## Current Status

There are four deliberately separate policy states:

- `main.py` is the frozen v9 submission control: six wheat plots and guarded
  price-aware selling.
- `submission-goose/main.py` is the second active Kaggle submission.
- `experimental_cow_agent.py` is the superseded plain-cow research control.
- `experimental_scale_agent.py` is the strongest frozen candidate: eight daily
  hands, sixteen wheat plots, four cows, four sheep, daily feed, CARE, staged
  expansion, and no land. Its package is `submission-scale/main.py`; it has not
  been uploaded.

No third Kaggle agent should be submitted without an explicit decision. Local
profit against `starter` is diagnostic evidence, not proof of ladder strength.

## Submitted Baseline

`main.py` is already in the single-file format Kaggle accepts. It:

- maintains a target of six wheat plots;
- waters every planted plot each day;
- waits until wheat's maximum-yield age before harvesting;
- stops buying and planting after day 24 so late inputs can still return cash;
- holds wheat below 35 coins unless shed stock reaches 72 units;
- sells at 35 coins or better and liquidates all remaining wheat from day 25;
  and
- uses deterministic shortest-path movement.

It intentionally does not use farm hands, animals, fertilizer, land expansion,
or a learned policy. Those features remain isolated development experiments so
the promoted submission control does not move silently.

Kaggle's file loader executes a submission and selects its last callable.
Therefore, `agent` must remain the final function defined in `main.py`. A unit
test protects this packaging rule.

## Run The Unit Tests

The decision tests do not need the Kaggle simulator:

```powershell
./.conda/python.exe -m unittest -v
```

These tests answer narrow questions such as "does watering take priority over
harvesting?" They make policy changes faster and safer. The command currently
runs the agent, benchmark-metric, and episode-audit tests.

## Simulator Setup On Windows

This workspace uses a project-local Conda environment with Python 3.12. The
official `kaggle-environments` package declares dependencies for every game it
ships, including an Orbax fixture whose path is too deep for this Windows
installation. Kaggriculture does not import that stack.

Create the environment:

```powershell
conda create --prefix .conda python=3.12 pip -y
```

Install the shared runner dependencies and the pinned Kaggle package without
the unrelated game extras:

```powershell
./.conda/python.exe -m pip install -r requirements-simulator.txt
./.conda/python.exe -m pip install --no-deps kaggle-environments==1.32.7
```

This exact minimal installation was verified in a fresh environment by running
a file-based Kaggriculture episode. Messages saying that other environments
failed to load are expected when their optional packages are absent.

Then run the cheapest integration check:

```powershell
./.conda/python.exe run_match.py --steps 48 --opponent pass --seed 7
```

For a full repeatable season against the stronger built-in baseline:

```powershell
./.conda/python.exe run_match.py --steps 720 --opponent starter --seed 7 `
  --replay artifacts/starter-seed-7.json `
  --html artifacts/starter-seed-7.html
```

Open the generated HTML file to inspect the game in Kaggle's official replay
visualizer. In a notebook, `env.play()` provides the interactive human action
UI; replay HTML is preferred for repeatable agent comparisons.

Create a concise but complete turn-by-turn audit from a saved replay:

```powershell
./.conda/python.exe audit_episode.py artifacts/full-replay.json `
  --player 0 --agent main.py --output artifacts/full-audit.json
```

The audit preserves all replay records and records actions, positions, task
validity, board changes, money, inventory, market state, realized sale revenue,
seed spending, daily summaries, and exact final-score reconciliation.

To watch the promoted seed-11 game with a plain-language explanation of every
step, serve the repository root and open the captioned wrapper:

```powershell
./.conda/python.exe -m http.server 8765 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8765/captioned_replay.html`. The left side is
Kaggle's official visualizer. The right side follows its slider and reports the
farmer action, destination, market order, cash change, inventory, and board
change for the same replay record.

## Run A Multi-Seed Benchmark

One game can be unusually favorable. The benchmark runs the same unchanged
agent over ten seeds and places it in both player positions, producing 20 full
seasons:

```powershell
./.conda/python.exe benchmark.py --opponent starter `
  --seed-start 0 --seed-count 10 --steps 720 `
  --output artifacts/benchmarks/baseline-v1-vs-starter-seeds-0-9.json
```

The report records wins, losses, ties, errors, coins, margins, action counts,
player-position splits, simulator version, and a hash of the exact agent file.
Use the same seeds and positions when comparing a candidate policy with the
baseline. The report is checkpointed after every game; `"complete": true`
means the entire requested suite finished.

To evaluate a workload without changing the submission default, pass a local
experiment parameter:

```powershell
./.conda/python.exe benchmark.py --opponent starter `
  --seed-start 0 --seed-count 10 --steps 720 `
  --target-wheat-tiles 6 `
  --output artifacts/benchmarks/candidate-wheat-6.json
```

For reproducible paired analysis, use `compare_benchmarks.py`. Market-learning
data are handled separately: `collect_market_dataset.py` records compact
observed trajectories, while `collect_market_counterfactuals.py` clones a live
state and evaluates one forced HOLD and SELL choice before returning both
branches to v9. The latter explicitly restores Kaggriculture's resolved seed in
each clone; the generic environment `clone()` does not preserve that metadata.

## Analyze A Public Leader Replay

Kaggle's Episode Player fetches complete public episode data from:

```text
https://www.kaggle.com/competitions/episodes/<episode-id>/replay.json
```

After saving a replay, produce a compact strategy report with:

```powershell
./.conda/python.exe analyze_public_replay.py `
  artifacts/top-replays/episode-94173913-replay.json `
  --output artifacts/top-replays/episode-94173913-strategy.json
```

The report counts farmer and hand actions, hires by day, maximum workforce,
land timing, animal purchases and placements, structures, crop transitions,
product sales, bank trajectory, and terminal inventory for both players.

The captured 111,082-coin rank-one episode used 277 hires, up to 12 simultaneous
hands, 18 pastures, 6 cows, 12 sheep, and all four quadrants. A captured loss
kept the same 277-hire backbone but shifted to 10 cows and 4 sheep and bought
only two extra quadrants. These replays motivate controlled labor and capital
experiments; they do not make the local opponent representative.

## Current Baseline Results

On simulator 1.32.7, promoted v9 combines the six-plot, day-24 crop policy with
price-aware selling. It was measured against `starter` over seeds 0-9 in both
player positions:

| Metric | Result |
| --- | ---: |
| Completed games | 20 / 20 |
| Wins / losses / ties / errors | 20 / 0 / 0 / 0 |
| Mean coins | 7,849.9 |
| Minimum coins | 7,150 |
| Maximum coins | 8,450 |
| Mean opponent coins | 3,642.9 |

The frozen v5 immediate-sale control averaged 7,501.1 on the identical games,
so v9 gained 348.8 coins on average without changing production. Route
instrumentation still found 760 plantings, 740 harvests, and 20 weeds, and all
2,960 successfully harvested wheat units were sold. Holding increased mean
harvest-to-sale delay from 10.05 to 63.05 turns by design, while terminal shed,
carried, and seed inventories remained empty.

A post-promotion file-loaded gate scored 7,992 in both player positions on
seed 0. The audited seed-11 game scored 8,161 versus 3,677 and reconciled
exactly: 3,000 starting coins + 5,541 sale revenue - 380 seed spending = 8,161.

V9 also passed a separate generalization comparison on seeds 10-19 in both
positions. It averaged 7,705.95 versus 7,450.45 for the immediate-sale control,
improved all 10 independent seeds, preserved every win, and harvested and sold
the same 2,956 wheat units. The paired report is
`artifacts/benchmarks/v1327-v9-vs-v5-paired-seeds10-19.json`.

A neighboring threshold of 36 improved the tuning suite but lost by 1-2 coins
on two independent holdout seeds. It was therefore not promoted; the submitted
default remains 35. This is intentional conservatism, not an unfinished edit.

## Hands And Plain Cow Results

Two daily hands around the one-goose control raised development performance on
seeds 30-39, both positions, from 9,884.5 to 12,333.3 mean coins. The paired
result was 20 improved, 0 tied, and 0 worse games, for a +2,448.8 mean gain.

Adding only one plain cow and a protected pasture raised the same development
suite to 16,634.3 mean coins. The exact candidate was frozen at SHA-256
`aec06f1da0dd046a98af9e57d391ec779cb7fd690e0fb8e34d4044f9057cd9b5` before
using untouched seeds 60-69.

| Metric | Two-hand control | Frozen cow candidate |
| --- | ---: | ---: |
| Holdout games won | 20 / 20 | 20 / 20 |
| Mean coins | 11,768.3 | 16,694.75 |
| Mean paired gain | - | +4,926.45 |
| Minimum paired game gain | - | +3,536 |
| Improved / tied / worse | - | 20 / 0 / 0 |

Every cow game sold exactly 25 eggs, 11 milk, and 56 fertilizer, used no CARE,
and ended with no sellable shed or carried inventory. The candidate is now the
frozen local control for the next scale experiment, but its roughly 16.7k score
is still far below the 78k-111k public replay economies.

## Frozen Scale Candidate

The replay-inspired overnight ladder changed one axis at a time: workforce,
crop capacity, animal count and mix, CARE, feed cadence, market priority, then
land. The selected policy uses eight hands, sixteen wheat, four cows, and four
sheep. It feeds and cares for animals daily, stages purchases over days 0, 3,
5, and 7, and protects required feed from wheat sales.

The exact source hash is
`acfc19dd312dcd281428e62ff8d4c2919150b1aed0776d093e14470a0380cfb5`.

| Metric | Plain cow | Frozen scale |
| --- | ---: | ---: |
| Development mean, seeds 30-39 | 16,634.3 | 58,853.4 |
| Development paired result | - | 20 / 0 / 0 |
| Untouched holdout mean, seeds 70-79 | 17,052.3 | 57,231.45 |
| Holdout paired gain | - | +40,179.15 |
| Holdout minimum / maximum | 16,102 / 18,346 | 43,745 / 65,110 |
| Holdout animal losses | 0 | 0 |

It also won all 40 direct local matches against the two active policies: 20/20
against v9 and 20/20 against goose, testing both player positions. Against the
captured rank-one action script on its original seed, however, it lost 41,702
to 113,032 in both positions. That script is a fixed stress test, not an
adaptive clone, but it usefully shows that the candidate is a large upgrade,
not a solved leaderboard strategy.

Build and validate the single-file candidate with:

```powershell
./.conda/python.exe prepare_scale_submission.py
./.conda/python.exe validate_submission.py submission-scale/main.py --seed 70
```

The packaged SHA-256 is
`a478741d32205b1ec772aced6879796c718249b695b0a8b5d85bb65ad893dac2`.
Kaggle's file loader completed full self-play with both statuses `DONE`.
Source and package each score 55,138 against `starter` on seed 70, confirming
packaging equivalence. This package is now live on Kaggle as the safer control.

A second pressure-aware investment package is also submitted and currently has
a live Score of 491.3. It uses up to ten hands, twelve wheat, all land, six cows, and twelve
sheep when opponent market pressure permits; it scales down when the opponent
already operates many animals. Its untouched seed-80-89 mean is 56,501.8 with
an 88,136 maximum, and it wins 16/20 direct games against the scale control.

The separate `experimental_zoned_agent.py` fixes a confirmed row-major planting
bias by selecting center-near crop tiles and assigning persistent near/far
planting crews. It is intentionally unsubmitted. Center-first/no-land routing
scores 64,424 on the seed-30 gate and averages 60,100.45 on development seeds;
adding the right quadrant with the same labor reduces performance because animal
service leaves too few crop actions to maintain two zones.

## Historical Baseline Results

The six-plot policy with a day-24 planting cutoff was measured on simulator
1.32.3 against `starter` over seeds 0-9 in both player positions:

| Metric | Result |
| --- | ---: |
| Completed games | 20 / 20 |
| Wins / losses / ties / errors | 20 / 0 / 0 / 0 |
| Mean coins | 7,894.1 |
| Minimum coins | 7,473 |
| Maximum coins | 8,367 |
| Mean opponent coins | 3,503.2 |

The previous four-plot policy averaged 6,647.6 coins on the identical suite.
The six-plot workload contributed a 1,176.5-coin mean improvement, and the
endgame cutoff added another 70 coins by avoiding seven late seed purchases per
game. Both changes preserved every win.
The promoted `main.py` was also loaded by file with no experiment override and
scored 8,181 in both positions on seed 0. See `progress.md` for the full
comparison and rejected eight-plot experiment.

These scores are historical because the live competition and this workspace
now use simulator 1.32.7. Do not compare new candidates with 1.32.3 scores.

## How We Will Improve It

For each version, we will change one strategic idea and compare it over the
same set of seeds and opponents:

1. Validate that every episode finishes without agent errors.
2. Record final cash, wins, action counts, idle turns, and lost crops.
3. Establish crop-profit and labor-cost baselines.
4. Add hands only when extra revenue exceeds daily hiring cost.
5. Test fertilizer, livestock, land, and sale timing independently.
6. Keep a change only when repeated matches beat the prior version.

We are not choosing between heuristics and learning as mutually exclusive
approaches. V9 remains the deterministic safety and control layer. A
checkpointed v9 dataset now contains 4,154 hold/sell decisions from seeds 30-39,
but it records only the action v9 took. Training on it immediately would clone
v9 rather than prove a better choice. Deterministic state branching has now
produced 28 true one-step counterfactual labels across prices 34-36: 7 prefer
HOLD, 8 prefer SELL, and 13 tie. A shallow value tree was evaluated by leaving
one seed out at a time, but its 91-coin regret was worse than v9's 62, so it was
not promoted. That led to broader counterfactual coverage and the guarded ridge
experiment described next. Offline RL or self-play remains later work, after a
state-dependent value model can pass the full consistency gate.

An earlier research run broadened true counterfactual coverage to 120 states over
prices 28-40 and produced a guarded ridge policy. It improved every development
seed by 156.4 coins on average. On fresh seeds 40-49 it preserved all 20 wins,
all production, and gained 116 coins on average, but seed 48 lost 25 coins.
Therefore the learned policy remains in `experimental_ridge_agent.py`; the
submission in `main.py` is still v9. Seeds 20-29, 40-49, 50-59, 60-69, and
70-79 are spent holdouts.

The next research question is no longer raw labor capacity. Blindly copying the
leader's 12-hand, 18-animal, all-land topology scored only 52,536.5 because
service and crop churn prevented most expansion animals from coming online.
The next candidate should make high-level capital choices adaptively: hire,
buy land, add a cow or sheep, change crop mix, or hold cash. Selection must use
head-to-head and replay-script pressure as well as `starter`, with deterministic
legality, feeding, market-order, and endgame safeguards retained.

Before submitting, accept the competition rules in the browser. API credentials
are useful later for automation but are not needed to understand or test the
agent.
