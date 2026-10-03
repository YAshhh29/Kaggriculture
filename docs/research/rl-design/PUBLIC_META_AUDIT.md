# Public Kaggriculture Meta Audit

**Audit date:** 2026-09-01 03:38 UTC

**Question:** What are 1800-2800-score public agents actually doing, and what
should we independently implement before committing compute to RL?

## Evidence Rules

- **Verified** means stated in the public notebook, visible in its Apache-2.0
  source, or shown by Kaggle's first-party notebook metadata.
- **Inferred** means a likely architectural consequence, not a claim by the
  author.
- Scores are snapshots and can move. Best score and current public score are
  kept distinct when Kaggle exposes both.
- This report describes mechanisms. It does not copy another participant's
  implementation.

## Executive Finding

The strongest public notebook agents are not end-to-end RL policies. They are
usually:

1. one or more complete 719-transition expert programmes;
2. visible-state guards around those programmes;
3. local recovery that keeps the programme synchronized;
4. order-safe market timing and storage accounting;
5. live terminal liquidation;
6. sparse route or component selection from public state.

This independently validates the residual architecture in this folder, but it
changes the order of work. We should first implement the most universal
deterministic residuals and ship a guarded-portfolio challenger. Later imitation
and RL should select routes, commitments, and residuals rather than emit every
primitive worker action.

## The Ten Requested Notebooks

| Notebook | Kaggle score evidence | Verified architecture | RL? |
| --- | ---: | --- | --- |
| [Farming Score V3: Replay Revised](https://www.kaggle.com/code/lynnsakurai/farming-score-v3-replay-revised) | Public 2273.6 | Complete replay programme plus hand alignment, weed repair, projected shed, sequential funding, livestock substitution, latent-pasture activation, and exact terminal frontier | No |
| [Shape the Shop Work the Pasture](https://www.kaggle.com/code/tetsutani/shape-the-shop-work-the-pasture-kaggriculture) | Public 2371.1 | Preserved parent programme with registered livestock bundles, visible demand corrections, guarded pasture activation, and fertilizer closeout | No |
| [Shape the Shop Work the Pasture TOP 10](https://www.kaggle.com/code/indarkarhana/shape-the-shop-work-the-pasture-top-10) | Public 2689.6 | Close relative of Shape: guarded programme, demand-based cow/sheep relabeling, projected inventory, and one guarded animal-hand bundle | No |
| [V21-R1 Public-State Route Portfolio](https://www.kaggle.com/code/boatlee/v21-r1-public-state-route-portfolio) | Public 2467.9 | Moon/Mutoy/Munib expert portfolio; early public-state route latch; separate market-delta overlay | No |
| [Farming Score: A Mathematical Approach](https://www.kaggle.com/code/lynnsakurai/farming-score-a-mathematical-approach) | Public 2083.9; best 2733.3 | Shared-prefix route switch plus public inventory-residual detector and conserved six-turn sale front-running | No |
| [Kaggriculture X544 - Nah, I'd Win](https://www.kaggle.com/code/stevenleehans/kaggriculture-x544-nah-i-d-win) | Best 2096.7 | Frozen route with one narrowly guarded milk-sale timing intervention; embedded prose identifies a later X567/X562 lineage | No visible evidence |
| [Adaptive Shop Guard](https://www.kaggle.com/code/reyhanksatria/kaggriculture-adaptive-shop-guard) | Public 2528.2 | Agent payload is opaque in the visible notebook; title alone is insufficient to infer its shop logic | Unknown, no visible evidence |
| [Adaptive Public-State Multi-Route](https://www.kaggle.com/code/yamakawanin/kaggriculture-adaptive-public-state-multi-route) | Public 2061.9 | Moon/Mutoy/Munib route commitment, public-regime market components, weed repair, and tape resynchronization | Explicitly non-neural |
| [Premium-First Market Agent](https://www.kaggle.com/code/ameythakur20/kaggriculture-premium-first-market-agent) | Best 1796.7 | Fixed 8-cow/4-sheep programme, sparse shop routing, hand/weed repair, and premium-first market ordering | No visible evidence |
| [V20 Adaptive R1 Multi-Route](https://www.kaggle.com/code/boatlee/v20-adaptive-r1-multi-route-agent) | Best 2578.2 | Frozen compressed multi-route submission; policy internals are not documented enough for independent conclusions | Unknown, no visible evidence |

### Replay Revised

The executed policy is explicitly described as a complete programme passed
through a visible-state guard network. Guards align the live hand count, repair
weeds, project same-transition shed deposits, cap sales by executable inventory,
order contested sales, and fund purchases sequentially. Failed preconditions
suppress only the infeasible transaction.

Livestock adaptation is deliberately conserved: a complete cow or sheep
transaction bundle may be relabeled while pasture geometry, animal count, and
service route remain fixed. The endgame allocates scarce market slots by exact
liquidation value at the final executable frontier.

**Independent lesson:** do not mutate isolated primitive actions. Change a
complete transaction bundle or leave the programme intact.

### Shape And TOP 10

The two notebooks share a programme-and-guards family. Their interventions are
sparse and reversible: visible dairy/wool pressure can substitute livestock at
registered checkpoints, and a latent pasture activates only when geometry,
inventory, cash, capacity, and service feasibility agree.

**Independent lesson:** preserve validated geometry and routes while adapting
the economic payload that travels through them.

### Public-State Route Portfolios

V21 and Adaptive Public-State Multi-Route maintain several complete experts.
They select a route from early opponent spending/hiring, initial shop sequences,
or the first meaningful divergence between experts. Physical-route selection
and market overlays are separate. One expert's market delta can be applied to
another expert only while physical actions remain compatible.

The stronger public-state notebook additionally describes weed `DIG`/retry and
actor catch-up so a local obstruction does not permanently desynchronize the
tape.

**Independent lesson:** route choice, market policy, and recovery are separate
heads with different evidence and commitment timescales.

### Mathematical Market Residual

This notebook estimates opponent sales from public market inventory after
subtracting known town demand. Under farm-similarity and timing guards, it moves
equal premium-sale volume forward and records an equal future debt. Total
planned quantity is conserved.

**Independent lesson:** market adaptation should shift timing with a repayment
ledger before it attempts to invent new production.

### Premium-First

The visible notebook combines sparse shop routing with closed-loop hand and weed
repair. It prioritizes melon, milk, wool, and strawberry entries within the
market list and reports a large experimental terminal-cash increase from order
priority. That cash result is notebook-local evidence, not a causal guarantee.

**Independent lesson:** market-list ordering is part of the action, not a
post-processing detail.

## Additional High-Score Public Architectures

Kaggle's Code tab sorted by Public Score exposed these distinct mechanisms:

| Notebook | Kaggle score evidence at audit time | Distinct contribution |
| --- | ---: | --- |
| [Findings from Zero to Top Meta](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta) | Public 2837.0; best 2945.5 | Public-farm similarity, inferred opponent sale horizon, debt-conserved front-running, self-impact sale ordering, protected near-shed liquidity |
| [V16 Recovery](https://www.kaggle.com/code/boatlee/v16-rc5-r5a-high-score-8c-4s-recovery) | Code-tab 2834.7 | Hand alignment, actor-local weed recovery, cow-placement repair, one-turn premium shift/repay |
| [V14 Clone Preemption](https://www.kaggle.com/code/boatlee/84-84-base-public-holdout-v14-clone-preemption) | Public/best 2844.1 | Public clone distance, projected shed, nonlinear price impact, conserved premium preemption, live liquidation |
| [Conditional Memory](https://www.kaggle.com/code/kaitofukami/177-180-fresh-top-30-v21-1-conditional-memory) | Public/best 2665.8 | Thirty route medoids and 1-nearest-neighbor public-state matching; only colliding SELL blocks are shifted |
| [V17 Market & Storage](https://www.kaggle.com/code/boatlee/v17-r1-rc2-high-score-10c-4s-market-storage) | Best 2587.6 | Pickup reservations, late near-shed returns, projected overflow, live liquidation from step 716 |
| [V13 Order-Safe Premium Control](https://www.kaggle.com/code/boatlee/v13-r3-top-meta-order-safe-premium-control) | Code-tab 2359.8 | Order-safe shift/repay controller and static top-route hazard prior |

These are not six independent proofs. V14, V16, V17, V20, and V21 share a
development lineage; several Conditional Memory notebooks are copies or
variants. The repeated mechanism is still meaningful, but correlated public
agents must not be counted as independent validation opponents.

## What The Current Calendar Lacks

The deployed calendar returns the planned action for `step + 1` verbatim. It
does not currently have:

1. **state-drift recovery** for weeds, hand-count mismatch, or animal placement;
2. **projected-shed safety** for same-transition deposits and reserved pickups;
3. **sequential affordability repair** after a failed or displaced purchase;
4. **live terminal liquidation** from actual inventory and remaining order slots;
5. **premium sale ordering** by exact marginal revenue and demand timing;
6. **shift/repay market debt** that conserves planned quantity;
7. **storage protection** and late high-value return-to-shed diversions;
8. **route or expert selection** from shop sequence and public opponent state.

The first four are correctness and recovery residuals. They are the safest
immediate implementation surface. The next three are market residuals. Route
selection has the largest upside and the largest overfitting risk.

## RL And Behavior-Cloning Evidence

### What Has Actually Worked

The strongest detailed RL report is [Learnings from PPO to 80k terminal
cash](https://www.kaggle.com/competitions/kaggriculture/discussion/738619).
It reports a JAX rewrite at roughly 10,000 simulator steps/second, heuristic
warm-up, classic PPO, self-play plus active/banked opponents, shaped rewards,
history features, and future value-horizon features. It reached roughly 80k
terminal cash, then hit saturated logits and an exploration/collapse wall. That
author is now testing an intent policy over a deterministic executor.

The detailed behavior-cloning report [If I'm Going to Write Rules Anyway, Why
Train a Model?](https://www.kaggle.com/competitions/kaggriculture/discussion/738079)
found:

- high offline accuracy can hide PASS/STOP class imbalance;
- label leakage produced almost-perfect offline metrics and a free-running
  always-PASS policy;
- state-generated complete Options worked better than independent primitive
  heads;
- reliable execution still did not create profitable expansion;
- 99.84% land accuracy produced only seven confirmed expansions in 300 branches;
- long-horizon decisions need persistent financing, workforce, production, and
  sell-through commitments;
- model causal influence must be measured by replacing the model with a
  constant policy while freezing the executor.

### What Has Not Been Demonstrated

The discussion [End-to-End RL Is Harder Than It
Looks](https://www.kaggle.com/competitions/kaggriculture/discussion/736567)
reports extra-land harvest success of only 20-40%, followed by a policy that
learned not to buy land. One participant reports BC+RL around 75k in self-play,
while several others report poor competitive generalization without the same
numeric result. A former fourth-place participant states that all of their
high-scoring agents were rule-based despite ongoing RL experiments.

[Determinism is an argument against RL
here](https://www.kaggle.com/competitions/kaggriculture/discussion/737937)
highlights three concrete issues: 719-step compounding, a combinatorial and
order-coupled action space, and terminal credit assignment. A participant near
the top reports moderate success only with heuristic+RL and uses learning mainly
for opponent modeling; their end-to-end PPO/transformer reached about 40k.

There is anecdotal suspicion that at least one private top agent was built with
RL, but no public source or result verifies that claim.

## Competition And Evaluation Constraints

- Engine `1.32.7` makes carrot, tomato, and egg scarcity situationally valuable;
  public field measurements show carrot adoption rose sharply while tomato was
  barely adopted. Shop-aware policy is therefore important, but raw expected
  value can increase variance without increasing win probability.
- The rating uses wins and losses, not coin margin. The former-rank-one
  [submission strategy post](https://www.kaggle.com/competitions/kaggriculture/discussion/736219)
  recommends judging after roughly 60 games, comparing equal-age submissions,
  and optimizing per-opponent win probability.
- Public agents and the meta are copied and replaced quickly. [Leaderboard is
  by nature obsolete](https://www.kaggle.com/competitions/kaggriculture/discussion/737955)
  warns that a current high score may represent an older strategy and that most
  agents remain static with only marginal reactions.
- A Kaggle staff reply in [the public-agent rules clarification](https://www.kaggle.com/competitions/kaggriculture/discussion/737788)
  informally states that freely and publicly available work is fair use. The
  binding rules still require sufficient rights, original-work warranties,
  compatible open-source licensing, and the ability to grant the winner
  license. We will write our own implementation, preserve attribution, and use
  public agents primarily as research evidence and benchmark opponents.

## Decision

### Immediate Track: Guarded Portfolio

Build a new challenger without waiting for neural training:

1. retain the current high-utilization calendar as the physical backbone;
2. add actor-local weed/hand/placement recovery;
3. compute projected same-transition inventory and sequential affordability;
4. replace fixed closeout with live order-slot-constrained liquidation;
5. add exact premium sale ordering;
6. add a conservative one-turn shift/repay ledger;
7. add one or more independently reconstructed route experts only after the
   residual-only version clears gates;
8. select routes at shared-prefix divergence points with hysteresis, never by
   rank, team identity, replay ID, or hidden state.

### Learning Track: Residual Decisions

Use the same deterministic executors as the RL action space. The model should
learn:

- whether to keep, patch, or rebuild the current commitment;
- which route expert best matches the visible state;
- whether a premium sale should stay, shift, or repay debt;
- when recovery cost is lower than abandoning the programme;
- which persistent expansion/terminal portfolio to commit to.

The model should not emit arbitrary worker and market lists.

## Can This Cross 1500?

The untrained phase-zero RL policy adds no new mechanism or evidence for crossing
1500 because it is exactly the current calendar. The guarded-portfolio
architecture has a credible path because public agents in the same architectural
family score from roughly 1800 to 2800. That is evidence of attainability, not a
forecast for our implementation.

We will call a candidate **1500-ready** only if it:

1. beats the current calendar over at least 1,000 paired games;
2. exceeds 50% against an independently sourced panel around score 1500;
3. does not regress against any major route family;
4. improves the current hard elite holdout;
5. has zero execution errors and materially fewer state-drift no-ops;
6. clears a temporal holdout collected after implementation is frozen.

The bold target for the next shipped deterministic challenger is 1500-2000,
but no score will be promised before those gates and real ladder evidence.