# Local Experiment Artifacts

This directory contains generated benchmark reports, replay captures, datasets,
diagnostics, and temporary model searches. They are intentionally excluded from
Git because the local archive is large and reproducible.

Versioned assets belong elsewhere:

- promoted model files: `models/`
- compact regression fixtures: `tests/fixtures/`
- submitted standalone agents: `submissions/`
- experiment conclusions: `docs/experiments/`

Do not use one favorable artifact as promotion evidence. Record the command,
seed set, opponent set, both-position result, and package hash in the experiment
journal before promoting an agent.