# COPY-PASTE AGENT HANDOFF PROMPT

You are taking over the Kaggriculture agent project at `C:\Users\Oyash\Desktop\Kaggriculture` on Windows. Work autonomously through implementation, validation, packaging, GitHub push, and carefully justified Kaggle submission. Do not stop at plans. The ultimate competitive objective is a robust 2500-2800-class agent, but never claim a score before local gates and real ladder games support it.

## 1. Repository and environment

- Branch: `overnight/routing-demand-workspace`.
- Current HEAD / `origin/main` / active remote branch: `6f05c36` (`Keep RL research notes local`).
- Simulator: project-local `.conda`, Python 3.12, `kaggle-environments==1.32.7`.
- Run Python with `.\.conda\python.exe`.
- Existing full suite before Candidate A: 470 tests passed.
- Do not install WSL/Linux or large toolchains without explicit approval.
- The repo may be dirty. Never revert user work. `.vscode/tasks.json` was restored to HEAD before this handoff; temporary tasks must not be committed.
- Use `apply_patch` for edits. Run a focused executable check immediately after each substantive edit.
- Keep detailed research notes local, not on GitHub. Only `rl/README.md` is tracked. Local-only files exist at `rl/ARCHITECTURE.md`, `rl/FAST_TRACK.md`, `rl/PUBLIC_META_AUDIT.md`, `rl/ROADMAP.md`, and this file. They are hidden by `.git/info/exclude`.
- `rl/data/`, `rl/checkpoints/`, `rl/runs/`, and generated `artifacts/` are ignored. They may contain Competition Data and must remain private.

## 2. Current deployed parent

- Agent source: `agents/experimental_distilled_calendar_agent.py`.
- Frozen package: `submissions/distilled-calendar/main.py`.
- SHA-256: `43d24a73c346c7687e574de69b8ffaf0ef959b34649e4e333a70f3f6c44b0976`.
- Kaggle submission: `55910432`.
- Validation episode: `103922332`, rewards `47243-44975`, COMPLETE.
- Live snapshot on 2026-09-01: about Score `981.2`, rank `2911/7190`; prior peak `1024.6`. Refresh this before any new upload.
- This is a fixed open-loop Crop Dusta episode-99058164 action calendar. It roughly doubled planting versus the old tiered agent and locally scored 72-8 versus 55-25 on the broad gate, but it ignores live divergence.
- Never modify or regenerate the frozen package. Build every challenger separately.

## 2b. Candidate A is live on Kaggle (correction to prior handoff drafts)

An earlier draft of this file said Candidate A was validated/packaged but
never uploaded, reasoning from the absence of a "Freeze ... Kaggle
submission" commit. That was wrong: the user confirmed Candidate A
(`submissions/candidate-a(calendar recovery first attempt)/main.py`) is
live on Kaggle with a score around 1160-1200. Do not re-derive submission
status from commit history alone going forward -- ask, or trust an
explicit user statement over an absence-of-evidence inference. As of the
Candidate B work in this file, `rl/candidate_a.py`,
`agents/experimental_calendar_recovery_agent.py`, and
`submissions/candidate-a(calendar recovery first attempt)/main.py` were
not modified, so no Candidate A reupload is needed for that work
specifically. That submission folder was originally named
`calendar-recovery/`; it was renamed for clarity after this file was
first written, and this file's references were updated to match.

## 3. Ultimate architecture and truthful score expectations

Use a two-speed hybrid architecture:

1. Candidate A: deterministic recovery and terminal commitments.
2. Candidate B: A plus order-safe premium market residuals.
3. Candidate C: A+B plus a public-state portfolio of complete route experts.
4. Candidate D: a learned residual/Option selector over the proven A/B/C executors.

Planning bands only, not guarantees:

- Parent: ~981.
- Candidate A: current evidence says roughly parent-level; target only `1025-1150` after terminal conversions are validated. Do not call it “well above” yet.
- Candidate B cumulative target: `1150-1450`.
- Candidate C cumulative target: `1500-2100`; this is the first architecture specifically intended to cross 1500.
- Candidate D target: `1800-2500`; ultimate 2500-2800 is a stretch goal requiring better route experts, meta adaptation, and real ladder proof.

If measurements disagree with these bands, trust measurements and update the plan.

## 4. Exact uncommitted worktree state

Expected dirty files after `.vscode/tasks.json` cleanup:

- Modified: `research/evaluation/evaluate_live_macro_arms.py`.
- New: `agents/experimental_calendar_recovery_agent.py`.
- New: `rl/candidate_a.py`.
- New: `tests/test_experimental_calendar_recovery_agent.py`.

No Candidate A package or manifest exists. Nothing is submitted. Do not commit until the post-terminal full gates complete.

Known diagnostics to fix before commit:

- `rl/candidate_a.py`: missing final newline.
- `agents/experimental_calendar_recovery_agent.py`: missing final newline.
- `tests/test_experimental_calendar_recovery_agent.py`: two method declarations exceed 79 columns and file lacks final newline.

Focused tests currently pass despite those style diagnostics:

```powershell
.\.conda\python.exe -m unittest \
  tests.test_experimental_calendar_recovery_agent \
  tests.test_evaluate_live_macro_arms -v
```

Last verified focused result: 14 tests passed.

## 5. Candidate A implementation already completed

`rl/candidate_a.py` implements a residual policy and executor around the frozen calendar.

### Implemented recovery

- Live hand actions are aligned to the actual live hand count.
- A calendar `PLANT`, `BUILD_COOP`, or `BUILD_PASTURE` blocked by a weed may become `DIG` followed by a pending retry.
- A repaired plant receives `WATER` after planting.
- Recovery is synchronization-safe: `PLANT -> WATER` repair is allowed only if the same worker’s next two calendar actions are `WATER -> PASS`; other setup repair requires the next action to be `PASS`.
- This rule exists because the original broad repair displaced scheduled movement and permanently shifted open-loop routes.

### Implemented terminal liquidation

- From terminal planning, actual carried/shed inventory is used rather than calendar assumptions.
- Workers with sellable carried inventory route to a shed tile and `DROP` when time permits.
- Harvestable current tiles may be harvested only when there is enough time to return/drop.
- Same-transition `DROP` and shed-directed `PLACE` are projected into shed inventory.
- At terminal sell steps, all actual sellable products are sold, respecting shed capacity and the nine product domains.

### Implemented terminal commitment

- From step 700, inspect the same worker’s future calendar.
- Find a future calendar `HARVEST` of an already valuable crop.
- Require all displaced pre-harvest actions to be only movement, `PASS`, `DROP`, or required `WATER` on that target.
- Trigger only if the baseline harvest would be stranded, the advanced route can harvest and return/drop, and this is the last feasible window.
- Persist target -> optional water -> harvest -> shed -> drop phases per worker.
- This is generic; it does not use episode ID, rank, team identity, or seed.

### Evaluator integration

`research/evaluation/evaluate_live_macro_arms.py` exposes:

- `calendar_recovery`: combined Candidate A.
- `calendar_recovery_only`.
- `calendar_liquidation_only`.

`agents/experimental_calendar_recovery_agent.py` is the standalone research entrypoint using all Candidate A Options.

## 6. Candidate A evidence already completed

Private local datasets:

- `artifacts/datasets/v1327-distilled-live-losses-13.json`.
- `artifacts/datasets/v1327-distilled-live-wins-20.json`.

The frozen control reproduced all Kaggle rewards exactly before counterfactual conclusions.

### Important failed version

The first broad recovery implementation was REJECTED:

- 13 live losses: 5 improved, 6 tied, 2 worse.
- Mean own delta about `-403`.
- Worst regression `-32690`.
- Cause: `DIG -> PLANT -> WATER` displaced `WEST`/`EAST`, desynchronizing the route.

Do not restore broad multi-step recovery.

### Safe recovery / liquidation before terminal commitment

Completed reports:

- `artifacts/benchmarks/v1327-candidate-a-causal-ablation-live-losses-13.json`.
- `artifacts/benchmarks/v1327-safe-recovery-regressions.json`.
- `artifacts/benchmarks/v1327-calendar-liquidation-live-wins-20.json`.
- `artifacts/benchmarks/v1327-calendar-recovery-live-losses-13.json`.
- `artifacts/benchmarks/v1327-calendar-recovery-live-wins-20.json`.

Combined Candidate A over 33 captured public games before the new terminal commitment:

- All 13 controls and all 20 controls reproduced exactly.
- Loss cohort: 4 improved / 9 tied / 0 worse; mean own delta `+1537.85`; still 0-13.
- Win cohort: 13 improved / 7 tied / 0 worse; all 20 wins preserved; mean own delta `+2492.10`.
- Combined: 17 improved / 16 tied / 0 worse, but record remained 20-13.

Fresh paired gate before terminal commitment:

- Report: `artifacts/benchmarks/v1327-candidate-a-fresh-gate-235-239.json`.
- Seeds 235-239, both seats, six distinct opponent paths, 60 games per variant.
- Parent: 49-9-2, mean margin `38138.67`.
- Candidate: 49-9-2, mean margin `38205.15`.
- 31 improved / 29 tied / 0 worse own reward; mean own delta `+66.38`; no conversions; zero errors.
- Formal promotion: REJECT because wins did not increase.

### New terminal-commitment evidence

- Report: `artifacts/benchmarks/v1327-terminal-close-loss-conversion.json`.
- Episode `104027148` control: `63205-63319` loss, margin `-114`.
- Candidate: `63720-63329` win, margin `+391`.
- Own delta `+515`; margin swing `+505`; one real loss converted.
- This was the latest completed evidence.

The second close loss still needs a targeted run:

- Episode `104085256` control was `103859-104736`, margin `-877`.
- No completed post-terminal report exists for it.

## 7. Immediate next actions: finish Candidate A

Do these in order. Do not start Candidate B until Candidate A is frozen or explicitly rejected.

### A1. Run the second close-loss check

```powershell
.\.conda\python.exe -m research.evaluation.evaluate_live_macro_arms \
  artifacts\datasets\v1327-distilled-live-losses-13.json \
  --control submissions\distilled-calendar\main.py \
  --arm calendar_recovery \
  --episode 104085256 \
  --output artifacts\benchmarks\v1327-terminal-second-close-loss.json
```

Interpretation:

- Conversion is valuable.
- Tie/small nonnegative delta is acceptable.
- Any own-reward regression requires tracing and narrowing the planner.

### A2. Rerun all 33 captured live schedules with the new terminal planner

Use new output names; do not overwrite pre-terminal evidence.

```powershell
.\.conda\python.exe -m research.evaluation.evaluate_live_macro_arms \
  artifacts\datasets\v1327-distilled-live-losses-13.json \
  --control submissions\distilled-calendar\main.py \
  --arm calendar_recovery \
  --output artifacts\benchmarks\v1327-candidate-a-terminal-live-losses-13.json

.\.conda\python.exe -m research.evaluation.evaluate_live_macro_arms \
  artifacts\datasets\v1327-distilled-live-wins-20.json \
  --control submissions\distilled-calendar\main.py \
  --arm calendar_recovery \
  --output artifacts\benchmarks\v1327-candidate-a-terminal-live-wins-20.json
```

Required gate:

- 20/20 parent wins preserved.
- No own-reward regression in any of 33 games.
- At least the `104027148` loss remains converted.
- Zero control reproduction errors and zero candidate errors.
- Record must improve from 20-13 to at least 21-12.

### A3. Rerun fresh paired family gate after terminal commitments

```powershell
.\.conda\python.exe -m research.evaluation.evaluate_future_labor \
  --seed-start 240 --seed-count 10 \
  --opponent submissions\distilled-calendar\main.py \
  --opponent agents\current_rank2_replay_agent.py \
  --opponent submissions\gated-late-strawberry\main.py \
  --opponent agents\experimental_scale_agent.py \
  --opponent agents\experimental_lifecycle_agent.py \
  --opponent submissions\learned-service\main.py \
  --control submissions\distilled-calendar\main.py \
  --candidate agents\experimental_calendar_recovery_agent.py \
  --output artifacts\benchmarks\v1327-candidate-a-terminal-fresh-gate-240-249.json
```

This is 120 games per variant. Require zero errors, no family win regression, and preferably more total wins. A tie in wins means Candidate A remains a reliability layer, not a score-jump submission.

### A4. Instrument residuals before larger gates

Add structured counters to benchmark output, not prints in the deployable agent:

- guard type;
- worker;
- step;
- original and replacement action;
- pending repair/commitment completion or cancellation;
- recovered units and sold value;
- invalid/no-op actions prevented;
- terminal inventory before/after.

Do not let instrumentation alter agent actions.

### A5. Fill Candidate A gaps only with evidence

Candidate A still lacks several originally planned safeguards:

- explicit carried-animal placement repair;
- projected pickup/feed reservations outside terminal closeout;
- sequential affordability repair after market changes;
- a formal no-guard equivalence run across full episodes;
- tests for multiple workers competing for the same seed/target/shed capacity;
- full package builder, manifest, loader, and 1438-decision equivalence.

Implement only a gap tied to an observed failure. Ablate each residual separately.

### A6. Candidate A promotion decision

Candidate A may be packaged only if all are true:

- post-terminal captured record improves and has no regression;
- fresh family gate has zero errors/no family regression;
- guard-firing states show >=50% reduction in invalid or stranded actions;
- no-guard behavior is exact;
- full suite passes;
- source/package/simulator equivalence passes in both seats.

If fresh wins remain tied, do not upload A alone. Keep it as the foundation for A+B.

Before commit, fix current line-length/newline diagnostics, restore `.vscode/tasks.json`, review the diff, run full tests, then commit/push only reproducible source/tests/evidence summaries. Never commit raw replay data or generated reports.

## 8. Candidate B: what was actually built (supersedes the original 8-item plan below)

The original plan (preserved unedited in 8a below) specified 8 mechanisms.
Only item 1 ("premium ordering") was ever implemented as a standalone
experiment, and it turned out to be inert: this game's pricing model prices
each product only off that product's own running inventory, so permuting
already-fixed SELL quantities across products can never change total
revenue -- proven by direct permutation enumeration (24 permutations of a
4-product batch, 1 distinct value) and confirmed empirically (264 real
eligible firings across 33 captured episodes, 0 changed anything). Worse,
the permutation search was a live timeout risk: a 10-order batch (the
code's own stated cap) took 174 seconds. That implementation was deleted
entirely, not patched.

`rl/candidate_b.py` was rebuilt around item 3 (sequential affordability),
which the evidence supported: live replay of Candidate A's real games found
858 WHEAT and 825 FERTILIZER sells trailing an unrelated spend order in the
same turn's batch (0 premium sells in that position) -- a real, measurable
inefficiency, unlike item 1. The mechanism moves eligible SELL orders ahead
of a spend they could fund in the same turn, verified per-turn by replaying
both orderings through a local single-player market simulation (money,
shed, and all 9 products' exact 1.32.7 price curves) and only applying the
reorder when no order's fulfilled quantity ever decreases.

Two failure modes were found and fixed before shipping, both by evidence,
not by design review alone:

- Rescuing a `BUY_ANIMAL` purchase: the fixed calendar never schedules
  care/feed for an animal it didn't plan for, and the rescue can also fill
  the pasture/coop slot the calendar's own later, already-planned animal
  purchase needed. Cost -37129 relative to Candidate A on a captured replay
  episode (103937628) before being walled off.
- Rescuing a `BUY_SEED` purchase, even with `BUY_ANIMAL` already walled
  off: cost -15302 and flipped a win into a loss against a *live*
  mirror-match opponent (seed 300 vs distilled-calendar family gate,
  seeds 300-309) -- invisible to captured-replay testing, since a replayed
  opponent's actions are fixed regardless of our timing, but a live
  opponent's realized prices are not. Reordering our own trades shifts the
  price a live opponent's own concurrent trades land on; the isolated
  single-player safety simulation cannot see that by construction.

Given two of four spend types tested this way caused real, large harm, the
shipped scope is deliberately narrow: only `HIRE` and `BUY_PRODUCT` are
rescue-eligible; `BUY_ANIMAL`, `BUY_SEED`, and `BUY_LAND` are hard barriers
a SELL may never cross. `BUY_LAND` has no direct evidence either way and is
walled off on the same "implement only a gap tied to an observed failure"
principle the rest of this file already prescribes.

Validated results (final code, `rl/candidate_b.py` as committed):

- Captured-live gate, 33 episodes (13 losses + 20 wins from the parent):
  A+B record `22-11` vs Candidate A's own `21-12`, one additional loss
  converted (episode 103977950, +20922 own-reward vs Candidate A alone),
  zero regressions to a worse result category, zero errors.
- Fresh family gate, 120 games, 6 opponent families, seeds 300-309: A+B
  `108-12` vs Candidate A's `107-13`, zero per-family win regressions,
  margin improved in every family, zero errors.
- Full suite 494/494. Package/source/simulator equivalence 1438/1438
  decisions, 0 mismatches, seed 230.

Items 2, 4, 5 (as originally scoped to premium products), 6, 7, and 8 from
the original plan were not implemented and remain open for a future B
iteration -- in particular the shift/repay ledger (item 6) and live
terminal order-slot allocation (item 8) were never attempted. If picking
those up: gate each individually against a *live* paired-opponent family,
not just captured replay -- that is the concrete lesson from this round,
not a repeat of the same review.

### 8a. Original plan (historical; superseded above, not deleted for context)

Build B on a frozen Candidate A. Do not change physical production or route in the first B experiment.

Implement independently from public descriptions:

1. Exact marginal revenue under the 1.32.7 market curves.
2. Same-transition projected shed inventory, reserved pickups/feed, existing sells, shed capacity, and ten-order cap.
3. Sequential affordability: preserve lower-index sells that fund later purchases; never reorder blindly.
4. Town-demand timing at hours 0/4/8/12/16/20; town acts after player market orders.
5. Premium candidate products: melon, milk, wool, strawberry first; evaluate tomato/carrot/egg only under current 1.32.7 scarcity/demand.
6. One-turn shift/repay ledger: moving quantity earlier creates equal per-product future debt; never invent net quantity.
7. Do not shift wheat needed for feed or protected production.
8. Live terminal order-slot allocation by exact sellable value.

B experiments must isolate:

- premium ordering only;
- shift/repay only;
- sequential affordability only;
- combined A+B.

B gate:

- 100 paired games per independent route family.
- Retain parent wins in every family and convert >=1 parent loss.
- Zero errors.
- Exact quantity conservation for shifted units.
- No purchase fails because B consumed/reordered its financing slots.
- No guard states remain action-equivalent.

Likely planning range if measured gates improve wins: 1150-1450. Do not state this as achieved.

### 8b. Suggestions for C/D from the B round (non-binding; do not change the C/D plan below on these alone)

These are offered as things to watch for, not a mandate to alter section 9
or 10's architecture or gates:

- Gate every economically-active residual against a live paired-opponent
  family, not only captured replay, before trusting a "safe" verdict.
  Captured replay cannot show an effect that depends on a live opponent
  reacting to shared state (market prices here; conceivably shop/plot
  contention for a route selector in C). The -15302 BUY_SEED regression in
  this round was invisible to 33 replay episodes and only showed up in the
  first live family gate.
- A locally-provable-safe change to one turn's actions is not automatically
  safe for the rest of the game if it changes a persistent resource the
  rest of the (fixed or selected) policy has baked-in assumptions about --
  workforce count was fine because Candidate A already re-aligns to it;
  animal count and seed inventory were not, because nothing downstream
  re-aligns to them. For C's route-switching specifically, that suggests
  checking whether a route's assumptions about owned land/animals/workers
  still hold after a switch, not just whether the switch itself is legal.
- Ablating one mechanism at a time and killing it outright on disproof
  (rather than patching around a proven-inert idea) kept this round's
  scope small enough to actually find and fix the two real regressions
  above. Worth preserving as C/D grow more mechanisms.

### 8c. Post-deployment fix: land-purchase starvation (2026-09-03)

Found from two real live Kaggle episodes (105061000, 105062726 -- both
played by the live Candidate A submission, both against different real
opponents, YASH JAIN on different seats in each), not from a gate. In both
games, at the identical calendar record (200), the calendar's *only*
scripted `BUY_LAND` attempt for the third quadrant (SW) sat behind a
`BUY_PRODUCT WHEAT 16` in the same turn's batch (`[BUY_PRODUCT WHEAT 16,
BUY_LAND]`), which drained the money the land purchase needed
(money=2192/2156, land cost=2000). The purchase failed silently. Because
the calendar is a fixed 720-step replay with no adaptive retry, and because
this is the *only* record in the whole script that attempts that quadrant,
it never got a second chance -- the third quadrant stayed locked for the
rest of both 720-step episodes. Every later scheduled `PLANT`/`WATER`/
`HARVEST`/`BUILD_PASTURE` the calendar sent there reported the tile as the
literal string `"LOCKED"` (confirmed by direct inspection of both replays)
and executed as a no-op: 471 such wasted actions in each game.

Two fixes, at the two layers already established by this file's own
architecture:

- **Guard fix, `rl/candidate_a.py`.** The existing weed guard already
  substitutes a safe action when a scheduled tile-task's target is a
  `WEED` tile it didn't expect; it never checked for a `LOCKED` tile
  (unpurchased quadrant), because until this discovery no evidence existed
  that the calendar could ever schedule a task onto one. Extended the same
  guard's tile-kind check to cover `LOCKED` across all tile-task operations
  (not just the weed guard's three), substituting `PASS`. Structurally
  simpler and safer than the weed guard: no retry state is needed (a locked
  quadrant doesn't clear itself the way a dug weed does), and since none of
  these operations move the worker, swapping the guaranteed-no-op action
  for `PASS` cannot desync any later scheduled movement either way -- unlike
  the weed guard, this one carries none of the synchronization-safety risk
  documented in section 6. Benefits both Candidate A and Candidate B (B
  wraps A). Verified directly against the real captured observation from
  replay 105061000, record 210: the guard swaps exactly the calls that were
  live no-ops (farmer and two hands, all sitting on `"LOCKED"` tiles) and
  leaves every other worker's action, including ones on real WEED/PLANT/
  PASTURE tiles in the same turn, byte-for-byte unchanged.
- **Reorder fix, `rl/candidate_b.py`.** Fixing the wasted turns alone
  doesn't get the quadrant purchased -- the underlying complaint. Added
  `_land_priority_ordering`, a second, separate market-timing residual
  alongside the existing sequential-affordability one: it moves a starved
  `BUY_LAND` order ahead of a same-turn `HIRE`/`BUY_PRODUCT`/`BUY_SEED`/
  `BUY_ANIMAL`, gated on local simulation actually flipping that `BUY_LAND`
  from failing to succeeding (same `_simulate_orders` primitive the
  affordability pass already uses and was validated against). It never
  moves a `SELL` in either direction -- a `SELL`'s position is left
  entirely to the existing, already-gated affordability pass, so this fix
  cannot reproduce the live-opponent shared-market-timing risk documented
  in 8's `BUY_SEED` regression (that risk comes specifically from moving
  *when a SELL executes*, and this rule never does). What it does **not**
  inherit from the affordability pass is that pass's core safety property:
  strict fulfilled-count dominance. Rescuing land is expected to (and, in
  both real episodes, does) reduce a same-turn purchase's fulfilled count,
  sometimes to a small fraction of what was requested. That is accepted
  as a deliberate value judgment -- an entire quadrant (`LAND_PRICES[1] =
  2000`, on the order of 500 remaining steps of extra planting/harvesting
  surface) is judged to dominate a partial WHEAT restock or a skipped
  hire -- not proven the way the rest of Candidate B's logic is. Verified
  against the real observation from episode 105061000, record 199: the fix
  reorders to `[BUY_LAND, BUY_PRODUCT WHEAT 16]`, which local simulation
  confirms lets the land purchase succeed at the cost of 11 of the 16
  requested WHEAT units (5 fulfilled instead of 16). This fix does **not**
  help the currently-live Candidate A package by itself -- only Candidate
  B's market-timing layer carries it, so shipping just the guard fix to
  Candidate A alone would stop the wasted turns but not get the quadrant
  bought.

Validation completed before this section was written: full suite 489/489
(8 new tests: 3 for the guard, 5 for the reorder, including one that
replays the exact real failing turn end-to-end through
`build_candidate_b_agent`), package/source/simulator equivalence 1438/1438
decisions with 0 mismatches (seed 230), both fixes hand-verified against
the real captured observations from both failing episodes as described
above. Not yet completed as of this writing: a fresh live-opponent family
gate for the reorder fix specifically, the same class of test that is what
actually caught the `BUY_SEED` regression in 8 (captured-replay and
single-player simulation both missed that one). A gate against
future-labor/gated-late-strawberry/tiered-fertilizer, seeds 400-409, both
seats, was started and is running in the background; update this section
with the result once it completes rather than treating the reorder fix as
validated to the same bar as the rest of Candidate B until then. The guard
fix carries no comparable live-opponent risk (it never touches a market
order, only a worker's tile-task action on a tile no policy has ever had
reason to plant on), so it does not need the same gate to be trusted.

## 9. Candidate C: public-state route portfolio

C is the first intended 1500-crossing architecture. Build only after A+B are stable.

### Route experts

Collect/reconstruct several genuinely different complete public replay programmes locally. Use distinct economic families, not ten forks of one route. Suggested families:

- current Crop Dusta backbone;
- cow-heavy recovery/storage route;
- carrot/tomato scarcity route for 1.32.7;
- wool/dairy shop-sensitive route;
- market-front-running route.

Use public Kaggle Competition Data legally and keep raw data private. Independently write selectors/executors; do not paste public notebook code.

### Selector

Use only visible/deployable state:

- duplicate shop sequence and counts;
- opponent money, hires, hands, land, crops, animals, structures, weeds;
- own live farm and inventory;
- current prices and market inventory;
- route signature distance;
- first meaningful expert divergence.

Rules:

- Execute shared prefix before selecting where possible.
- Latch physical route with hysteresis; do not oscillate.
- Keep physical-route selection separate from market-overlay selection.
- Keep every stateful expert synchronized from episode start.
- Fall back to Candidate A+B when distance/uncertainty is high.
- Never select by team name, rank, submission ID, replay ID, or seed.

C gate:

- >=55% head-to-head over 1000 paired games versus parent.
- >=50% against every independent target family around scores 1500, 1800, 2200, and 2500.
- <=2 percentage-point regression in any 100+ game family unless a preregistered hedge justifies the second active slot.
- Improved bottom-decile margin and hard elite holdout.
- Zero errors; <0.1% masked/invalid attempts.
- Temporal holdout collected after selector freeze.

Planning range if gates pass: 1500-2100. Ultimate public analogues reach 2300-2800, but correlated forks and stale ratings are not proof our C will.

## 10. Candidate D: learned residual/Option selector

Do not train a primitive-action PPO policy. Public evidence shows full-action PPO/BC often stalls around 40k-80k terminal cash and fails to generalize.

Use the proven A/B/C executors as complete Options. The model owns preference and persistence; the executor owns legality/logistics.

### Data

- At least 200 complete episodes before first serious BC model.
- Stratify top 10/top 50/top 500/score 1500/1250/1000/our wins and losses.
- Multiple games per team and both seats.
- Deduplicate by episode ID and SHA-256.
- Split by team; reserve later dates as temporal holdout.
- Record source team/submission/date/score snapshot/seed/player/version/result.
- Strictly reject malformed/failed actions; no teacher action, future label, or opponent-private state may enter the forward pass.

### Labels and model

- Generate state-valid candidate Options from deterministic executors.
- Use simulator counterfactual branches to label win-first utility of KEEP/PATCH/REBUILD, route expert, shift/repay, expansion commitment, and terminal portfolio.
- Start with interpretable baselines (tree/logistic), then small MLP/GRU.
- Use a recurrent model only if history materially improves team-held-out free-running results.
- Measure event recall and model-to-action conversion, not aggregate accuracy dominated by KEEP/PASS.
- Freeze executor and compare the learned selector against a constant selector to prove causal influence.

### Online RL

Only after free-running BC beats the deterministic selector:

- residual PPO/MAPPO over Options;
- league: parent, A+B+C, historical agents, distinct public families, recent checkpoints, market-aggressive stress agents;
- win-first terminal reward with bounded margin bonus;
- 10k games first; 100k only on improving held-out curve; 1m only if 10k->100k gains continue;
- snapshot league / PFSP to limit cycles;
- persistent commitments for financing -> land -> workforce -> production -> sell-through;
- explicit terminal portfolio.

D gate must exceed C on the same 1000-game and temporal holdouts before packaging. Planning range if genuinely stronger: 1800-2500. The 2500-2800 goal is a stretch target requiring both a strong route portfolio and learned meta adaptation.

## 11. Public research that informs implementation

The detailed local audit is at `rl/PUBLIC_META_AUDIT.md`. Key requested public notebooks:

1. https://www.kaggle.com/code/lynnsakurai/farming-score-v3-replay-revised
2. https://www.kaggle.com/code/tetsutani/shape-the-shop-work-the-pasture-kaggriculture
3. https://www.kaggle.com/code/indarkarhana/shape-the-shop-work-the-pasture-top-10
4. https://www.kaggle.com/code/boatlee/v21-r1-public-state-route-portfolio
5. https://www.kaggle.com/code/lynnsakurai/farming-score-a-mathematical-approach
6. https://www.kaggle.com/code/stevenleehans/kaggriculture-x544-nah-i-d-win
7. https://www.kaggle.com/code/reyhanksatria/kaggriculture-adaptive-shop-guard
8. https://www.kaggle.com/code/yamakawanin/kaggriculture-adaptive-public-state-multi-route
9. https://www.kaggle.com/code/ameythakur20/kaggriculture-premium-first-market-agent
10. https://www.kaggle.com/code/boatlee/v20-adaptive-r1-multi-route-agent

Additional high-score patterns came from Zero to Top Meta, V16 Recovery, V14 Clone Preemption, Conditional Memory, V17 Market/Storage, and V13 Order-Safe Premium Control.

Verified recurring ideas:

- complete programme + narrow visible-state guards;
- actor-local weed/hand/placement recovery;
- projected shed and sequential affordability;
- premium sale ordering and shift/repay debt;
- live liquidation;
- sparse route portfolios and public-state signatures.

Do not count correlated forks as independent evidence. Public score is noisy/stale. Optimize per-family win probability, not mean coins.

## 12. Validation and release discipline

For every candidate:

1. State one local falsifiable hypothesis.
2. Add a focused test first or immediately with the edit.
3. Run the narrow test before more patching.
4. Run paired seeds in both seats.
5. Compare exact same game sets.
6. Track wins/losses/ties/errors, own reward, margin, bottom decile, invalid/no-op actions, guard firings, stranded/terminal inventory, and per-family results.
7. Preserve parent behavior where no guard/selector fires.
8. Keep frozen submissions immutable.
9. Run full suite before commit.
10. Build a standalone package, use Kaggle path loader, then require source/package/simulator equivalence across 1438 decisions.
11. Commit and push only after review; keep artifacts and detailed local notes out of GitHub.
12. Upload only genuine win-rate improvements; keep the best current agent in the other active slot.
13. Freeze an accepted package by full SHA-256, bytes, submission ID, validation episode, and rewards.
14. Never guarantee a leaderboard score from local tests.

## 13. Definition of done

The project is not done when code exists. It is done when:

- A is either safely frozen as infrastructure or rejected;
- A+B produces a measurable win-rate gain and is submitted if justified;
- C crosses the preregistered 1500-ready gates and receives real ladder evidence;
- D beats C causally and out of sample, not just offline;
- the two final active submissions are complementary, error-free, and robust to current meta families;
- score 2500-2800 is treated as the ultimate measured objective, not a promise.

Start now with Candidate A step A1. Preserve the current uncommitted work and do not broaden scope until the second close-loss result and post-terminal 33-game reruns are complete.
