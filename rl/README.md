# Kaggriculture RL Workspace

This folder contains the implementation foundation for a state-adaptive agent.
It is isolated from the frozen submission and keeps the strongest known calendar
as a safe baseline.

## Objective

The current agent executes one complete elite calendar. It is strong, but it
keeps the same intent when prices, shops, purchases, workers, or the opponent
diverge from the source game.

The learning objective is:

> Observe the live state, compare it with the calendar intent, and choose when a
> bounded correction is better than staying on plan.

This is residual RL. The model will eventually select high-level corrections;
deterministic executors will handle legal primitive actions and logistics.

## Code Map

| Path | Purpose |
| --- | --- |
| `action_space.py` | Factored labor, land, crop, service, market, and recovery decisions. |
| `features.py` | Stable named vector from legal observations and calendar intent. |
| `policy.py` | Policy protocol and exact `KEEP_CALENDAR` baseline. |
| `runtime.py` | Fail-closed bridge from policy output to Kaggle actions. |
| `replay_dataset.py` | Strict replay validation and decision alignment. |
| `rewards.py` | Win-first terminal reward with a bounded margin bonus. |
| `rollout.py` | Same-seed, both-seat official-simulator evaluation. |
| `tests/` | Contract tests for state, actions, replay data, rewards, and rollout. |

## Current Safety Boundary

No neural framework is required or installed. The runtime currently permits
only `KEEP_CALENDAR`; every unimplemented residual raises an error before it can
reach the simulator. This makes phase zero behaviorally identical to the frozen
calendar.

Each residual must add its own mechanic tests, no-op equivalence checks, paired
evaluations, and temporal holdout before it becomes executable.

## Commands

Run focused tests:

```powershell
.\.conda\python.exe -m unittest discover -s rl\tests -v
```

Create a private replay dataset:

```powershell
.\.conda\python.exe -m rl.replay_dataset `
  artifacts\top-replays\episode-99058164-rank1-vs-rank2-replay.json `
  --team-name "Crop Dusta" `
  --split train `
  --output rl\data\episode-99058164-crop-dusta.jsonl
```

Run paired evaluation:

```powershell
.\.conda\python.exe -m rl.rollout `
  submissions\distilled-calendar\main.py `
  submissions\gated-late-strawberry\main.py `
  --seed 50000
```

Without `--player`, rollout uses the same seed with the candidate in both seats.
Use `--player 0` or `--player 1` only for a deliberate one-seat diagnostic.

## Reading Order

1. `features.py`
2. `action_space.py`
3. `runtime.py`
4. `replay_dataset.py`
5. `rollout.py`

Detailed strategy audits and experiment plans remain local. The implementation
and tests are the tracked source of truth.

## Data Rule

Public episode replays are Kaggle Competition Data. Raw replays, derived
datasets, checkpoints, and run outputs stay local and ignored. Keep this
repository private during the competition.