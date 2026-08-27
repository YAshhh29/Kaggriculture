# Repository Map

The repository is organized around the decisions a competition agent makes,
not around the chronology in which experiments were created.

## Intended Layout

```text
agents/                 runnable deterministic and learned agents
core/                   game mechanics, routing, scheduling, economics
policies/               small strategy interfaces and learned selectors
research/
  analysis/             replay and benchmark analysis
  collection/           counterfactual and trajectory collection
  evaluation/           fixed-arm and learned-policy evaluation
  training/             model fitting and learning-curve generation
tools/
  packaging/            standalone Kaggle package builders
  validation/           loader and source/package equivalence checks
tests/                  unit and integration tests
  fixtures/             compact versioned replay/state fixtures only
models/                 promoted, versioned model files
submissions/            exact validated standalone submissions and manifests
docs/
  experiments/          durable conclusions, not raw generated output
artifacts/               ignored local benchmark/replay/dataset output
```

## Active Modules

| Decision | Owning module today | Planned home |
| --- | --- | --- |
| Crop and animal plan | `experimental_premium_throughput_agent.py` | `core/scheduling.py` |
| Shortest movement step | `core/routing.py` | implemented |
| Market affordability | `experimental_throughput_agent.py` | `core/economics.py` |
| Safe service arms | `service_policy.py` | `policies/service.py` |
| Learned selection | `experimental_learned_service_agent.py` | `agents/learned_service.py` |
| Replay measurement | `research/analysis/analyze_public_replay.py`, `benchmark.py` | `research/analysis/` |

## Experiment Contract

Every experiment must state:

1. one behavioral hypothesis;
2. one incumbent and exact package hash;
3. development seeds and opponents;
4. untouched promotion seeds;
5. both-position wins, losses, errors, and mean margin;
6. secondary mechanism metrics such as movement, weeds, CARE, and sold units;
7. decision: reject, research-only, or package candidate.

Activity metrics are diagnostic only. More crops, workers, land, or actions are
not improvements unless terminal wins generalize.

## Git Policy

- Commit source, tests, promoted models, compact fixtures, manifests, and
  experiment conclusions.
- Keep generated datasets, replays, HTML renderings, diagnostics, and broad
  benchmark matrices under ignored `artifacts/`.
- Keep each commit independently understandable and testable.
- Never combine a submitted package hash change with unrelated refactoring.