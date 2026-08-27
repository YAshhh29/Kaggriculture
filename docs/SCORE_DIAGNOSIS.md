# Kaggriculture Score Diagnosis (Snapshot: 2026-08-25)

## Scope and evidence

This diagnosis uses only local repository evidence plus the explicit live snapshot values supplied in this conversation.

Primary local sources:

- [RULEBOOK.md](RULEBOOK.md)
- [progress.md](progress.md)
- [strategy.json](strategy.json)
- [artifacts/top-replays/episode-99058164-rank1-vs-rank2-strategy.json](artifacts/top-replays/episode-99058164-rank1-vs-rank2-strategy.json)
- [artifacts/top-replays/episode-99003467-rank3-recent-win-strategy.json](artifacts/top-replays/episode-99003467-rank3-recent-win-strategy.json)
- [artifacts/top-replays/episode-99071613-ours-recent-loss-strategy.json](artifacts/top-replays/episode-99071613-ours-recent-loss-strategy.json)
- [artifacts/benchmarks/v1327-throughput-wheat21-gate-seed30.json](artifacts/benchmarks/v1327-throughput-wheat21-gate-seed30.json)
- [artifacts/benchmarks/v1327-throughput-globalcritical-gate-seed30.json](artifacts/benchmarks/v1327-throughput-globalcritical-gate-seed30.json)
- [artifacts/benchmarks/v1327-premium-cashflow-gate-seed30.json](artifacts/benchmarks/v1327-premium-cashflow-gate-seed30.json)
- [artifacts/benchmarks/v1327-premium-nw-rotation-swdelay-gate-seed30.json](artifacts/benchmarks/v1327-premium-nw-rotation-swdelay-gate-seed30.json)
- [artifacts/benchmarks/v1327-premium-nw-rotation-swdelay-development-seeds30-34.json](artifacts/benchmarks/v1327-premium-nw-rotation-swdelay-development-seeds30-34.json)
- [artifacts/benchmarks/v1327-premium-rotation-vs-center-out-seeds30-34.json](artifacts/benchmarks/v1327-premium-rotation-vs-center-out-seeds30-34.json)
- [artifacts/benchmarks/v1327-center-out-diversified-development-seeds30-34.json](artifacts/benchmarks/v1327-center-out-diversified-development-seeds30-34.json)
- [artifacts/benchmarks/v1327-center-out-vs-lifecycle-seeds30-34.json](artifacts/benchmarks/v1327-center-out-vs-lifecycle-seeds30-34.json)

## Kaggle Score vs episode reward

This distinction is critical:

- Episode reward is in-match banked coins at day 30. The simulator objective is final bank, per [RULEBOOK.md](RULEBOOK.md).
- Kaggle Score is an aggregate ladder rating across episodes and opponents, not a single episode reward. Local project notes explicitly record that score moves as episodes accumulate and is driven by wins/losses rather than margin against starter in isolation, per [progress.md](progress.md) and [strategy.json](strategy.json).

Observed local evidence:

- New submissions initialize at 600.0 and then move as more episodes complete (examples logged in [progress.md](progress.md) and [strategy.json](strategy.json)).
- Therefore a strong local episode reward and a much lower live Kaggle Score can coexist.

## Live score snapshot from conversation context (2026-08-25)

This is a point-in-time snapshot provided in the conversation and should not be treated as durable beyond 2026-08-25.

- Center-out: 573.7 (rank 4056)
- Other user scores: 556.0, 555.1, 550.3, 321.6, 299.8
- Leaders: Crop Dusta 3061.2, Ryo 3056.2, Subramanya 2956.5

## Episode distribution snapshot from conversation context

Also from the same date snapshot:

- Rank 1: 100-17, reward range 67,009-167,126
- Rank 2: 178-66, reward range 52,432-168,259
- Rank 3: 172-111, reward range 53,524-170,964
- Center-out: 28-36, reward range 10,080-89,295

Interpretation: the current top population sustains high reward across many episodes, while center-out is both lower and less consistent.

## Replay-backed throughput and utilization gap

The `episode-99071613` comparison below is the older center-out submission,
which peaked at 16 crops and 11 hands. It is useful historical evidence for
the original underuse diagnosis, but it is not a replay of deadline submission
`55795843`; the deadline policy later reached three owned quadrants, 12 hands,
and roughly 35-43 simultaneous crops in verified public wins.

From the requested replay analyses in [artifacts/top-replays/episode-99058164-rank1-vs-rank2-strategy.json](artifacts/top-replays/episode-99058164-rank1-vs-rank2-strategy.json), [artifacts/top-replays/episode-99003467-rank3-recent-win-strategy.json](artifacts/top-replays/episode-99003467-rank3-recent-win-strategy.json), and [artifacts/top-replays/episode-99071613-ours-recent-loss-strategy.json](artifacts/top-replays/episode-99071613-ours-recent-loss-strategy.json):

- Seasonal productive-capacity utilization:
  - Rank1: 81.36%
  - Rank2: 87.04%
  - Rank3: 78.67%
  - Center-out (ours): 29.54%
- Productive-tile peaks (productive tiles / owned tiles):
  - Rank1: 75/75
  - Rank2: 75/75
  - Rank3: 66/75
  - Center-out: 28/75
- Actual planting throughput (all-worker PLANT):
  - Rank1: 164
  - Rank2: 179
  - Rank3: 172
  - Center-out: 39
- Pass load (all-worker PASS):
  - Rank1: 274
  - Rank2: 272
  - Rank3: 343
  - Center-out: 3837
- Crop tile-days:
  - Rank1: 1168.5
  - Rank2: 1256.92
  - Rank3: 949.83
  - Center-out: 241.75

Diagnosis from those numbers: the main gap is not a small pricing tweak. It is a large system-level throughput/utilization deficit under opponent pressure.

## Market-order bug and starvation evidence (submitted center-out replay)

In [artifacts/top-replays/episode-99071613-ours-recent-loss-strategy.json](artifacts/top-replays/episode-99071613-ours-recent-loss-strategy.json):

- BUY_ANIMAL:SHEEP requested: 52
- Successful sheep placements: 6
- HIRE requests on day 8: 55
- Maximum market order entries in a turn: 10

The combination is consistent with order-cap starvation: oversized same-turn order bursts crowd out execution of intended purchases/hires.

## Land timing and underuse

Top replay cadence (same source files):

- NW saturated by days 2-5.
- NE expansion actively loaded around days 5-6.
- SW brought into productive use around days 8-10.
- 12-hand scale reached around days 9-11.

By contrast, our center-out case expands land but leaves much of it underused (29.54% seasonal productive utilization, 28/75 peak), so paid land and labor are not converted into output at top-echelon rates.

## Failure tolerance vs strict zero-loss safety

Conversation snapshot values to include:

- Rank1 tolerated 12 actual crop deaths plus 3 animal losses.
- Rank2 tolerated 5 plus 1.
- Rank3 tolerated 27 crop deaths, 13 planting misses, and zero animal loss.
- User policy remains constrained to zero-loss safety.

Local replay evidence aligns with the broader pattern that top teams preserve very high output while operating near capacity, while current center-out is far from capacity and still loses direct opponent games.

## Local prototype results and rejected paths

Evidence from benchmark artifacts:

- Wheat-dense gate: about 75.8k (75,836) but 8 crop losses (cycles_weeded = 8), from [artifacts/benchmarks/v1327-throughput-wheat21-gate-seed30.json](artifacts/benchmarks/v1327-throughput-wheat21-gate-seed30.json).
- Global dispatcher target churn variant: [artifacts/benchmarks/v1327-throughput-globalcritical-gate-seed30.json](artifacts/benchmarks/v1327-throughput-globalcritical-gate-seed30.json) shows high instability signals (for example 27 crop losses/cycles_weeded and reduced harvested cycles vs planted cycles).
- Premium cash-flow safe: 64,208 from [artifacts/benchmarks/v1327-premium-cashflow-gate-seed30.json](artifacts/benchmarks/v1327-premium-cashflow-gate-seed30.json).
- NW rotation plus SW delay: 72,827 on seed 30 from [artifacts/benchmarks/v1327-premium-nw-rotation-swdelay-gate-seed30.json](artifacts/benchmarks/v1327-premium-nw-rotation-swdelay-gate-seed30.json).
- Ten-game starter run completed 10/10 with mean 65,536.4 and floor 60,311, zero crop losses and zero animal losses, from [artifacts/benchmarks/v1327-premium-nw-rotation-swdelay-development-seeds30-34.json](artifacts/benchmarks/v1327-premium-nw-rotation-swdelay-development-seeds30-34.json).
- Direct center-out suite: 0-10 across both positions, 46,984.9 mean agent coins versus 56,600.0, with one crop loss, from [artifacts/benchmarks/v1327-premium-rotation-vs-center-out-seeds30-34.json](artifacts/benchmarks/v1327-premium-rotation-vs-center-out-seeds30-34.json).

Conclusion from these prototypes: strong starter means and high single-seed gates are not sufficient evidence for ladder promotion.

## Why current scores cluster near 550-574 while leaders are near 2956-3061

Primary drivers:

- Capacity conversion gap: far fewer productive tile-days and planting actions.
- Idle/action-allocation gap: very high PASS count in center-out relative to top replays.
- Market execution reliability gap: order-cap starvation and bursty request patterns.
- Expansion efficiency gap: land/labor spending without matching service capacity.
- Selection-pressure gap: local starter success does not model high-level opponent economies.

## Recommendation now

The new local candidate is [experimental_adaptive_counter_agent.py](experimental_adaptive_counter_agent.py). It observes the opponent's public crop footprint before the first possible land purchase:

- All-wheat opponent: one extra quadrant and the eight-animal NW/NE core.
- Diversified opponent: two extra quadrants and the twelve-animal NW/NE/SW core.
- Both branches retain paired planting, stable quadrant crews, affordability filtering, final ongoing-crop cleanup, and no late wheat admission on unsafe slots.

Final simulator evidence on seeds 30-34 in both positions:

- Starter: 10-0, mean 76,372.4, floor 58,580 ([report](artifacts/benchmarks/v1327-adaptive-final-vs-starter-seeds30-34.json)).
- Submitted center-out: 6-4, mean 51,011.6 vs 50,035.1, mean margin +976.5 ([report](artifacts/benchmarks/v1327-adaptive-final-vs-centerout-seeds30-34.json)).
- Lifecycle: 5-5, mean 54,018.5 vs 56,216.5, mean margin -2,198.0 ([report](artifacts/benchmarks/v1327-adaptive-final-vs-lifecycle-seeds30-34.json)).
- Combined local incumbents: 11-9. The submitted center-out had gone 0-10 against lifecycle.
- Current rank-one replay schedule at its source seed: 0-2, mean 40,812.5 vs 82,083.0 ([report](artifacts/benchmarks/v1327-adaptive-final-vs-current-top-script.json)).

Across all four final reports: zero crop deaths, zero unfinished crops, zero planting-day water misses, zero animal losses, and no terminal shed/carried inventory. The remaining seeds are paid inputs, not reward-bearing inventory.

This is materially better than the submitted center-out on the tested local opponent set, but no Kaggle submission is recommended yet because it still loses decisively to the current top replay schedule.

## Exploratory Kaggle submission

At the user's explicit request, the adaptive policy was packaged and uploaded as exploratory submission **55770236** on 2026-08-25.

- Package: [submissions/legacy/adaptive/main.py](../submissions/legacy/adaptive/main.py)
- Package SHA-256: `782bbeb87222cf0c4b9d1febdf96e7f92f08069b6627df5bf1a5399c34368bf9`
- Kaggle file-loader self-play: `DONE/DONE`, rewards 63,186 and 63,305.
- Source/package/recorded action equivalence: 0 mismatches across 1,438 decisions (seed 30, both positions).
- Kaggle status: `COMPLETE`; displayed score 600.0.
- Validation episode 99245275: self-play rewards 69,638 and 69,024, both completed.
- Public matchmaking episodes at this check: zero. The displayed 600.0 is therefore the unchanged initialization rating, not measured ladder strength.
- Kaggle set submission 55770236 as the team's active public-leaderboard submission.

This upload is an experiment, not evidence that the top-agent gap is closed.

## Learning path beyond fixed rules

Do not start with end-to-end reinforcement learning over raw movement and market lists. A turn can contain a farmer action, a variable number of hand actions, and ten market orders; the 720-turn credit assignment is too sparse and the valid-action surface changes with inventory, workers, land, and tile state.

Use a hierarchical policy instead:

1. Keep deterministic safety and execution below the learning boundary: same-turn plant/water, emergency crop rescue, animal feeding, inventory return, and final liquidation.
2. Learn one macro decision per day: hand target, land commitment, crop mix/admission, animal species expansion, crop-vs-animal service budget, and sell/hold mode.
3. Build behavior-cloning labels from several current top-agent public replays. This provides a competent initial policy instead of random exploration.
4. Fine-tune the macro policy with self-play against a league: center-out, lifecycle, current adaptive checkpoints, and captured top schedules.
5. Optimize a win-first reward: win/loss as the dominant term, bounded bank margin as shaping, and hard penalties for crop deaths, escapes, unfinished cycles, and terminal inventory.
6. Promote only on unseen seeds, both positions, direct opponent pools, and rating simulations. Starter reward remains a safety/throughput check, not the objective.

A practical first learner is a small discrete macro policy trained with behavior cloning followed by cross-entropy policy search. It requires no large ML toolchain and produces interpretable policies. PPO can be considered later after this constrained action interface and opponent league are stable.

Do not promote from starter mean or from initial 600.0 score behavior alone.

## Day-9 macro experiment and compact promotion

The first learned macro decision was made on day 5. On its fresh 30-game gate,
the shallow tree went 23-7 and KNN went 22-8, below the 24-6 fixed baseline;
the counterfactual oracle reached 26-4. Moving feature capture and selection to
day 9 tested whether three additional shop unlocks and visible opponent
development made that gap learnable.

The day-9 training set contains 54 paired contexts and all four safe macro
arms. On untouched seeds 106-108, both positions and five opponents:

| Selector | W-L | Decision |
| --- | ---: | --- |
| Day-9 shallow tree | 26-4 | Rejected |
| Day-9 grouped-CV KNN | 27-3 | Rejected |
| Handwritten selector | 27-3 | Control |
| Fixed compact animal | **28-2** | Promoted |
| Fixed compact crop | **28-2** | Tied control |
| Counterfactual oracle | **28-2** | No recoverable win beyond compact |

The learner was therefore rejected rather than uploaded. The evidence-backed
agent in [experimental_compact_macro_agent.py](experimental_compact_macro_agent.py)
uses the common safe policy through day 8, then commits to one extra land and
the protected one-land animal plan. Fresh direct gates were:

- adaptive incumbent, seeds 120-129: **20-0**, mean margin +6,757.6;
- center-out, seeds 130-134: **9-1**;
- lifecycle: **7-3**;
- scale: **10-0**;
- investment: **8-2**;
- starter: **10-0**; and
- current top and rank-two replay controls: **0-4**.

The five-opponent suite is 44-6. This is a clear incumbent upgrade, but the
0-4 replay result means the top-agent throughput gap remains open.

The first upload, submission `55778248`, failed validation because the AST
packager retained `from experimental_adaptive_counter_agent import ...`.
Local module import and action-equivalence checks could resolve that workspace
module, while Kaggle's single-file sandbox could not. The regression test now
rejects every `experimental_*` import, and the required pre-upload gate runs
Kaggle's path-based file loader in self-play.

The corrected package is submission **55778351**:

- package: [submissions/legacy/compact/main.py](../submissions/legacy/compact/main.py);
- SHA-256: `7782c6c35870411960014fe5154bafe904c69f539c75ee8d5c2277d73f79e367`;
- uploaded bytes: 108,480;
- source/package/recorded equality: 0 mismatches over 1,438 decisions;
- Kaggle validation episode: `99509927`, completed 70,494-71,744; and
- status: `COMPLETE`, initial score 600.0.

The first three public games produced one win and two losses:

| Episode | Opponent | Result | Coins | Rating after game |
| --- | --- | --- | ---: | ---: |
| `99514128` | zulfikar.khalwaniev | Loss | 71,293-104,910 | 514.3 |
| `99516420` | Marc Dakuginow | Win | 59,107-28,908 | 602.1 |
| `99518695` | Kshitiz2002 | Loss | 57,916-86,410 | **542.3** |

This is early and noisy, but it is the first genuine ladder evidence. Compact
is not replacing adaptive as the measured incumbent: adaptive's comparison
snapshot remains 654.0. The local 20-0 head-to-head exposed a weakness in that
specific policy matchup, not universal ladder superiority.

Kaggle confirms the tracked pair is compact `55778351` and adaptive
`55770236`. Adaptive remains the measured 654.0 incumbent while compact
continues as the 542.3 challenger.

## Full-capacity response to replay feedback

Compact's underuse was caused by policy constants, not simulator limits:

- `target_extra_land=1` made SW impossible to buy;
- premium planting deadlines stopped new melon/strawberry/wheat admission on
  days 7/11/22;
- two configured wheat slots had an impossible day 23-through-22 window; and
- 12 hands were retained through day 27 even after planting closed.

The corrected deadline-taper policy buys SW, safely backfills cleared slots
with wheat, prioritizes mature finite-crop harvests, and tapers hiring only
after the final wheat cohort is serviceable. Fresh seeds 169-173 produced 60-0
across compact, adaptive, center-out, lifecycle, scale, and investment.

The hierarchical learning experiment was genuine but rejected. A day-4 KNN
contextual bandit selected among paired crop-rotation/service templates using
terminal win-first reward. It reached 24-0 offline, but direct fresh rollout
against fixed wheat was 5-5 with identical rewards because it chose wheat in
every episode. No RL gain is claimed.

Submission **55795843** packages the stronger fixed deadline taper:

- SHA-256: `d76bd22843350319b44c9543e72ab261abb42a6c4077a0a6dd0c92735305f0d7`;
- uploaded bytes: 112,839;
- validation episode `100091628`: 41,908-39,495;
- source/package/recorded equality: 0 mismatches over 1,438 decisions; and
- status: `COMPLETE`, initial 600.0 with no public games yet.

Elite controls remain the blocker: deadline taper loses 0-4, although own mean
output improved to 50,463.5 against current top and 68,335 against rank two.
The next gain must roughly double planting throughput toward the elite
164-179 plantings, not merely keep workers visibly busy.

## Next design and promotion gates

Design requirements for the next agent iteration:

- Dynamic workload-based admission (do not admit work beyond service capacity).
- Stable quadrant ownership (minimize cross-quadrant retarget churn).
- Day-based crop rotation policy (explicit opening, midgame, and liquidation calendars).
- Affordability budgeting (reserve-aware ordering, no order-burst starvation).
- Staged land unlock only when projected service capacity and payback thresholds pass.

Promotion gates before any submission:

- Both positions.
- At least 10 unseen seeds.
- If zero-loss safety remains a hard requirement: zero crop and animal losses must hold.
- Direct wins versus current center-out and lifecycle controls.
- Captured-strategy stress tests must pass (not only starter).
- No submission based only on starter mean or on initial 600.0 ladder initialization.
