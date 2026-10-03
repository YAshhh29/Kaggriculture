# RL Experiment Roadmap

## Two-Speed Strategy

The public meta audit changed sequencing, not the core architecture.

- **Fast track:** implement guarded recovery, inventory, liquidation, market,
  and route-portfolio residuals around the current calendar. See
  `FAST_TRACK.md`.
- **Learning track:** use those same bounded residuals as supervised/RL Options.

We do not wait for neural training before testing deterministic residuals, and
we do not let fast-track rules expand into an untestable second strategic
policy. Every intervention remains isolated and ablated.

## Phase 0: Contracts

Status: implemented.

- stable state vector;
- factored residual action;
- exact keep-calendar policy;
- fail-closed executor;
- replay alignment and JSONL format;
- win-first reward;
- official-simulator rollout adapter.

Exit gate: focused tests pass and the keep policy matches the calendar exactly.

## Phase 1: Replay Corpus

Collect a stratified private corpus:

- current top 10;
- top 50 and top 500;
- agents around scores 1500, 1250, and 1000;
- our wins and losses;
- multiple games per team and both player positions.

Deduplicate by episode ID and SHA-256. The JSONL metadata header records team,
optional submission and score snapshot, replay and collection dates, result,
seed, player, simulator, and schema versions. Split train/validation by team and
use later dates as a final temporal holdout. Corpus assembly must reject missing
provenance fields before Phase 2 training.

Exit gate: at least 200 complete episodes, no train/holdout team overlap, and
reproducible feature statistics.

## Phase 2: Behavior-Cloning Baseline

Start with supervised heads for interpretable macro targets rather than raw
worker actions. Compare:

- logistic/linear heads;
- a shallow tree;
- a small MLP;
- a small GRU over decision checkpoints.

Metrics:

- held-out action accuracy by head;
- calibration and keep-calendar rate;
- invalid masked-action rate;
- direct simulator record against the calendar and teacher league.

Exit gate: held-out teams improve direct simulation without increasing runtime
errors or bottom-decile losses.

## Phase 3: Counterfactual Residual Learning

Implement one executor head at a time. Suggested order:

1. recovery after calendar state drift;
2. preserve-cash versus keep;
3. add-one-hand versus keep;
4. shop-conditioned crop choice;
5. sale pacing;
6. service mode and abandonment.

At each checkpoint, clone state and run every currently legal residual against
the same opponent continuation. Train on win-first utility differences.

Exit gate: each enabled head independently beats `KEEP_CALENDAR` on untouched
states and has a tested deterministic executor.

## Phase 4: Online League RL

Begin with 10,000 games, not one million. Use recurrent PPO/MAPPO only after the
offline policy is stronger than the calendar.

Promotion to 100,000 games requires:

- rising held-out win rate;
- stable entropy and value loss;
- no opponent-family regression;
- no increase in state-drift failures;
- useful CPU scaling measured on this machine.

Promotion to one million games requires continued gains between 10,000 and
100,000. A flat curve ends the experiment.

## Final Promotion Gate

A learned submission must satisfy all of the following:

- at least 55% over 1,000 paired games against the frozen calendar;
- both player positions and untouched seeds;
- stronger than the current hard elite holdout result;
- no opponent-family win regression;
- lower bottom-decile loss severity;
- zero simulator errors;
- negligible invalid or masked action attempts;
- held-out teams and later replay dates;
- package/source/simulator equivalence;
- standalone inference within Kaggle limits.

Live rating is the final test. Local gates justify a challenger; they never
guarantee a leaderboard score.