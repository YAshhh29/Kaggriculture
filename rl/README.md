# Kaggriculture RL Workspace

This folder is a learning-first workspace for building a state-adaptive agent
without modifying the frozen submission or discarding the strongest known
calendar.

## Start Here

The current agent is strong because it executes one complete elite action
calendar. Its weakness is that it executes the same intent after prices, shops,
cash, purchases, or the opponent diverge from the source game.

The RL objective is therefore not "learn Kaggriculture from random actions."
It is:

> Observe the real state, compare it with the trusted calendar intent, and
> learn when a bounded correction is worth more than staying on plan.

This is **residual RL**. The calendar is the baseline; the learned model emits
small macro corrections. In phase zero, the runtime only clones the trusted
calendar and rejects every non-keep residual. Later deterministic executors must
earn responsibility for legality, routing, affordability, planting-day water,
feed safety, and liquidation one tested residual at a time.

## Folder Map

| Path | Purpose |
| --- | --- |
| `action_space.py` | Factored macro decisions the learner may eventually choose. |
| `features.py` | Stable named vector built from legal observations and calendar intent. |
| `policy.py` | Minimal policy interface and exact `KEEP_CALENDAR` baseline. |
| `runtime.py` | Fail-closed bridge from policy output to Kaggle actions. |
| `replay_dataset.py` | Correctly aligns observation record `n-1` with action record `n`. |
| `rewards.py` | Win-first terminal reward with a bounded margin bonus. |
| `rollout.py` | Thin adapter around the official simulator for paired evaluation. |
| `ARCHITECTURE.md` | Why the learner is hierarchical, recurrent, and residual. |
| `ROADMAP.md` | Staged experiments and promotion gates. |
| `data/` | Local replay-derived datasets. Ignored by Git. |
| `checkpoints/` | Local learned parameters. Ignored by Git. |
| `runs/` | Local metrics and experiment outputs. Ignored by Git. |
| `tests/` | Fast contract tests for this workspace. |

## Phase-Zero Guarantees

No neural framework is required or installed yet. The current executor permits
only `KEEP_CALENDAR`; every other residual action raises an error before it can
reach the simulator. This makes the first checkpoint behaviorally identical to
the frozen calendar.

Run the focused tests:

```powershell
.\.conda\python.exe -m unittest discover -s rl\tests -v
```

Create a private JSONL imitation dataset from a local replay:

```powershell
.\.conda\python.exe -m rl.replay_dataset `
  artifacts\top-replays\episode-99058164-rank1-vs-rank2-replay.json `
  --team-name "Crop Dusta" `
  --split train `
  --output rl\data\episode-99058164-crop-dusta.jsonl
```

Run one paired simulator episode from two local agent files:

```powershell
.\.conda\python.exe -m rl.rollout `
  submissions\distilled-calendar\main.py `
  submissions\gated-late-strawberry\main.py `
  --seed 50000
```

Without `--player`, the rollout command runs the same seed twice with the
candidate in both seats and prints paired totals. Pass `--player 0` or
`--player 1` only for a deliberate one-seat diagnostic.

## Learning Order

1. Read this file.
2. Read `features.py` and inspect the named state vector.
3. Read `action_space.py` and understand why actions are factored.
4. Read `runtime.py` and note the fail-closed executor boundary.
5. Read `replay_dataset.py` to understand replay time alignment.
6. Read `ARCHITECTURE.md` for the eventual actor, critic, and league.
7. Follow `ROADMAP.md`; do not jump directly to million-game self-play.

## Data Rule

Public episode replays are Kaggle Competition Data. Their use is permitted for
the competition under Apache-2.0, but the competition rules restrict
redistribution to non-participants. Raw replays, derived datasets, checkpoints,
and run outputs stay local and ignored. Keep this repository private during the
competition.

## Current Compute Baseline

One official 720-step game with the lightweight calendar took about 3.80 seconds
on this machine. Serial estimates are therefore approximately:

| Games | Serial wall time |
| ---: | ---: |
| 10,000 | 10.6 hours |
| 100,000 | 4.4 days |
| 1,000,000 | 44 days |

Parallel workers can reduce wall time, but neural inference and CPU contention
make ideal scaling unrealistic. Each larger budget must be earned by a rising
held-out learning curve.