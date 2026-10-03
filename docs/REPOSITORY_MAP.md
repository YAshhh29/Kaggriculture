# Repository Map

```text
stack/            the final agent: thirteen layers around a public route follower (agents L to N12)
candidates/       agents A to K and the components they were built from
rl/               the reinforcement-learning contracts: features, action space, rewards, rollout, replay
agents/           the August agents: a deterministic baseline grown into about 90 experimental policies
policies/         small strategy interfaces and learned selectors used by agents/
core/             shared game mechanics: routing and economics
research/         analysis, counterfactual collection, evaluation and training scripts from August
tools/            everything that measures, packages and validates
  analysis/         replay analysis: pinned replays of our ladder games, corpus replays, studies
  arena/            local tournaments (round robin, Bradley-Terry scorecards), live-game health checks
  data/             Kaggle fetchers: leaderboard, our games, replays, public notebooks and their programs
  eval/             paired tests, robustness checks, turn budgets
  packaging/        single-file Kaggle package builders (build_final.py rebuilds N10, N11, N12)
  validation/       loader and source/package equivalence checks
  viewer/           replay rendering
tests/            684 unit and integration tests
models/           small versioned model files used by agents/ and policies/
submissions/      the exact files uploaded to Kaggle, one folder per agent
docs/             rules, research, journal, figures (see docs/README.md)
main.py           the first baseline agent (a wheat farmer); later agents still import it
run_match.py      play one local game, optionally saving a replay
benchmark.py      play many seeds in both seats and write a report
```

## Not in the repository

| Path | Why |
|---|---|
| `rl/public/nb_*.py` | Other people's public programs, extracted from their notebooks for local evaluation (`tools/data/extract_notebook_agents.py`) |
| `rl/data/` (except its README and `macro_plan.json`) | Replay-derived datasets and ladder tapes, which can contain Kaggle Competition Data |
| `kaggle_cache/` | Raw Kaggle downloads |
| `artifacts/`, `arena/`, `build/` | Generated output: benchmarks, rendered replays, local tournaments, package builds |

## Experiment contract

Every experiment states one behavioural hypothesis, the incumbent and its exact
package hash, the games it was developed on and separate games it is confirmed
on, wins and losses in both seats, errors, mean margin, and a decision: reject,
research-only, or package candidate. Activity metrics (more crops, workers or
land) are diagnostic only; an agent improves only when it wins more games it
was not tuned on.
