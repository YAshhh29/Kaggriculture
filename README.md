# Kaggriculture Agent

This repository is our learning lab and competition submission for
Kaggriculture.

See `progress.md` for the detailed experiment journal, decisions, failures,
fixes, current work, and next steps.

`strategy.json` is the machine-readable current policy, verified baseline,
next experiment, learning roadmap, one-goose experiment design, and promotion
guardrails.

## What The Competition Is

Kaggriculture is a two-player, turn-based resource-management game. The
environment calls your `agent` function once per turn with an observation of
the farm and market. Your function returns actions for the farmer, hired hands,
and market. After 720 turns, the player with more banked coins wins.

This is an agent-programming competition before it is a machine-learning
competition. A deterministic policy with good scheduling, accounting, and
market logic is the best place to learn the environment. We can consider
search or learning methods only after we have a measured baseline.

The leaderboard rating depends on wins and losses, not the margin of victory.
That makes reliability across many opponents more valuable than one unusually
profitable game.

## Current Baseline

`main.py` is already in the single-file format Kaggle accepts. It:

- maintains a target of six wheat plots;
- waters every planted plot each day;
- waits until wheat's maximum-yield age before harvesting;
- stops buying and planting after day 24 so late inputs can still return cash;
- holds wheat below 35 coins unless shed stock reaches 72 units;
- sells at 35 coins or better and liquidates all remaining wheat from day 25;
  and
- uses deterministic shortest-path movement.

It intentionally does not yet use farm hands, animals, fertilizer, land
expansion, or a learned policy. Those are experiments, not missing mystery
code.

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
not promoted. The next step is broader counterfactual coverage before another
model fit; fresh seeds 40-49 remain reserved for one final selected candidate.
Offline RL or self-play remains later work, after a state-dependent value model
can first beat v9 under seed-grouped validation.

Before submitting, accept the competition rules in the browser. API credentials
are useful later for automation but are not needed to understand or test the
agent.
