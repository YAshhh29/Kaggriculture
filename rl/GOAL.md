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
against different real opponents, YASH JAIN on different seats in each),
not from a gate. **Correction**, per the user: these were played by the
*previously-uploaded* Candidate B (sequential affordability only, before
the fix below existed), not Candidate A alone as this section first
claimed. This changes nothing about the diagnosis or the fix: the failing
turn's batch (`[BUY_PRODUCT WHEAT 16, BUY_LAND]`) contains no `SELL`, so
`_sequential_affordability_ordering` -- the only residual the previously-live
package had beyond Candidate A -- was structurally a no-op on it (its own
`_has_reorder_opportunity` gate requires a `SELL` present at all). The
previously-live Candidate B was therefore byte-identical to Candidate A
alone on this exact turn. Lesson (same shape as 2b): don't infer which
package is actually live/current from this file's own "not yet uploaded"
notes -- ask, the way 2b already established for Candidate A itself. In
both games, at the identical calendar record (200), the calendar's *only*
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
above.

A fresh live-opponent gate for the reorder fix specifically (the same
class of test that actually caught the `BUY_SEED` regression in 8, which
captured-replay and single-player simulation both missed) was run against
future-labor/gated-late-strawberry/tiered-fertilizer, seeds 400-409, both
seats -- 120 games. Result: **inconclusive, not passed**. The starvation
condition this fix targets (a same-turn spend draining `BUY_LAND` below
its cost at calendar record 200) never occurred against any of these three
opponents at these ten seeds -- every one of the 60 old/new pairs produced
byte-identical rewards, meaning `_land_priority_ordering` never fired once.
That is a real limitation of random sampling against a rare, opponent-
trajectory-dependent trigger, not a pass: it neither confirms nor refutes
live-opponent risk for this rule the way the fresh gate did for the sell
pass in 8. Widening the seed/opponent sweep further is unlikely to be
efficient (2200s for zero firings), so the stronger remaining argument is
structural, not empirical: `BUY_LAND`'s cost depends only on
`unlocked_quadrant_count`, never on the shared `market_inventory` a live
opponent also trades against, so the specific mechanism that broke the
`BUY_SEED` rescue (reordering shifts the price a live opponent's own
concurrent trade lands on) cannot touch `BUY_LAND` itself. The one order
this rule displaces that *does* read shared market state is `BUY_PRODUCT`
(when present) -- moving it one queue position later could shift the price
it pays, but only on the partial quantity already being deliberately
sacrificed, not on whether `BUY_LAND` succeeds. Treat this rule as
verified-by-construction-and-real-replay, not yet live-gate-confirmed;
revisit if a future live episode shows it firing with a worse outcome.

The guard fix carries no comparable live-opponent risk (it never touches a
market order, only a worker's tile-task action on a tile no policy has
ever had reason to plant on), so it does not need the same gate to be
trusted.

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

### 9a. Status: selector scaffold built, no second route yet (2026-09-03)

Before writing any selector code, surveyed the ~77 files under
`agents/experimental_*.py` for genuinely different, already-competitive
route experts to reuse (avoiding exactly the "ten forks of one route"
trap this section warns about). Finding: only 3 genuinely distinct
execution mechanisms exist in this repo's history (the parametric wheat
engine behind `experimental_premium_throughput_agent.py`; the frozen
elite-replay clone behind Candidate A/B; and the older scale/investment/
zoned/lifecycle/center-out expansion lineage), plus one narrow,
toy-scale market-timing seed (`experimental_ridge_agent.py`). None of
the four suggested new families above (cow-heavy, carrot/tomato
scarcity, wool/dairy shop-sensitive, market-front-running) exist as a
complete route today; real scaffolding exists for two of them in
`core/economics.py` (`crop_opportunity`, `animal_opportunity`,
`SHOP_PRODUCTS`) but nobody has assembled a dedicated route from it.

Tested the two best candidates for reuse directly, per section 3's rule
to trust measurements over the plan:

- `experimental_center_out_agent.py`, the one genuinely diversified
  5-crop layout in the whole catalog: lost 0-10, 0-4, and 0-4 in existing
  benchmark artifacts against agents (`experimental_deadline_tapered_
  wheat_agent.py`, `experimental_learned_service_agent.py`,
  `experimental_demand_animal_agent.py`) that are themselves weaker than
  Candidate B.
- The most evolved homegrown lineage, tested fresh against Candidate B
  directly: `submissions/gated-late-strawberry/main.py` and
  `submissions/tiered-fertilizer/main.py` each lost 0-8 (seeds 500-501,
  both seats), by roughly 2x margin every game.

Two independent hand-built strategies losing decisively to the calendar
clone is now real evidence, not a one-off: the calendar clone (itself a
behavior-clone of a real elite player, not a hand-built heuristic)
appears to structurally dominate this project's own hand-built
alternatives. Building a third hand-rolled route from `core/economics.py`
now, under time pressure and with no iteration budget remotely close to
what the other lineages received (dozens of ablation files, hundreds of
benchmark runs each), would very likely repeat this exact failure. The
user was asked and chose: source new route experts the same way the
current parent was built -- by behavior-cloning a genuinely different
real elite replay -- rather than a third hand-built attempt.

Built in the meantime, so a validated route can be added without a
redesign: `rl/candidate_c.py` (`RouteExpert`, `CandidateCExecutor`,
`build_candidate_c_agent`) and `tests/test_candidate_c.py` (9 tests,
all passing; full suite 498/498). The executor commits to exactly one
route per episode with unconditional hysteresis (never reconsiders once
committed, even if the injected selector's signal would change), and
hard-enforces that a non-reentrant route (the calendar's own step-indexed
baseline is the only one so far) can only ever be selected at step 0 --
raises otherwise. `ROUTES` ships with only the validated fallback
(Candidate B) today, so `rl.candidate_c.agent` is currently
behavior-identical to `rl.candidate_b.agent` (tested directly) and is
not yet a submission candidate distinct from Candidate B.

Blocked on: a real episode replay of a genuinely different, competitive
elite strategy to clone (candidate leads from `rl/PUBLIC_META_AUDIT.md`:
teams playing like `tetsutani`/`indarkarhana`'s "Shape the Shop Work the
Pasture" cow/sheep-pasture family, scored 2371-2689 there). This
environment has no Kaggle API credentials and cannot browse Kaggle's
JS-rendered pages for episode data, so this needs either a user-supplied
replay JSON or a user-supplied Kaggle API token.

### 9b. Two real-replay clone attempts also failed (2026-09-03)

The user supplied 24 real replays from Candidate A/B's own recent match
history (`failing_replays/`). Surveying them found the same signature
(COW~8, SHEEP~6, 3 land quadrants) in 15-18 of 24 games across entirely
different team names -- not 20 independent opponents, one widely-copied
public strategy that is the current dominant meta archetype, and it beat
Candidate A/B in 12 of the 24 games shown. This looked like the strongest
possible real-replay clone candidate available, so it was tried before
concluding anything further about section 9a's hand-built dead end.

Cloned the archetype's two largest observed wins over Candidate A/B
(episodes 105113156 "Mikhail_Komkin", 105061000 "Mwanza Wambua") the same
way the Crop Dusta parent was built --
`agents/experimental_distilled_pasture_agent.py` plus
`models/v1327-public-pasture-*.json`, zero fidelity mismatches against
the source replay. Both, tested raw and with Candidate A's guard layer
applied, lost 0-6 to the *current* Candidate B on 3 fresh seeds neither
was recorded on, both seats -- guards fired zero times in either case.
Full reasoning and rejection notice kept in
`experimental_distilled_pasture_agent.py`'s docstring rather than deleted,
matching the existing `experimental_shadow_demand_agent.py` precedent for
a documented negative result.

That makes four independently-sourced candidates now rejected by direct
measurement (center_out, the best homegrown lineage, and these two
real-opponent clones) with the same outcome: everything tested so far
loses decisively to the current Candidate B. Read together with section
8c's live-bug fixes, this suggests Candidate B is not obviously weak
locally -- it beat every one of these four candidates, including two real
recordings of the strategy currently winning against this project's own
live agent on Kaggle. Likely explanation for why none of these 24 replays
contained an elite-caliber opponent: Kaggle's ladder pairs similarly-rated
players, so a project's own match history reflects opponents near its own
current rating, not top-of-leaderboard play. The original Crop Dusta
episode was evidently sourced some other way (its exact provenance
predates this file), not from this project's own match history -- the
same gap likely applies to finding a second one now. Real next unlock is
almost certainly a replay involving a top-leaderboard player specifically
(from the leaderboard directly, not this project's own games), or a
Kaggle token so this can be searched for directly.

### 9c. Kaggle API token unlocked real leaderboard data (2026-09-03)

The user supplied a Kaggle API token (`KGAT_...`). It authenticates as a
Bearer token against `api.kaggle.com` (not the `kaggle.json`
username+key scheme the `kaggle` pip package's own client assumes, which
returned 401 with this token) -- raw `requests` calls or the `kaggle` CLI
with `KAGGLE_API_TOKEN` set both work. This gave direct access to the
live leaderboard, any team's public submissions and episodes, and replay
downloads for any completed episode. Token is not committed anywhere;
treat as a live account credential.

**A-vs-B investigation.** The user's own submission history (pulled via
`kaggle competitions submissions kaggriculture`) showed the *previous*
Candidate B (sequential-affordability only, before this file's 8c fixes)
already scored lower than Candidate A (1019.6 vs 1175.0) -- the
underperformance predates the locked-quadrant fix and is not specific to
it. It also showed the same exact Candidate A package file re-uploaded
twice scoring 1175.0 and 1210.8 -- roughly 35 points of pure noise on
identical bytes, before any A-vs-B comparison is even attempted. A larger
recent-episode sample (23 games for Candidate A, 35 for Candidate B, both
pulled live) gave A 65.2% wins vs B's 54.3% -- a real gap, if a smaller
one than the raw scores suggested. But a *controlled* local test --
cloning 6 of those exact real opponents (`Kaggler Albafica`, `Cary Jin`,
`The Grower`, `Stanislav Tsepa`, `SGY2512`, `Shangshang Zhang`) and
running Candidate A and B against each, same seeds, same seats -- found
the opposite: B 13-11, A 9-15. These two methodologies disagree on
direction. Likely reason: the clones are frozen replays of what a real
opponent did against a *different, older* version of this project's
agent, so they cannot reproduce how a genuinely reactive live opponent
would respond differently to A's choices vs B's -- exactly the
"shared-market timing an isolated simulation cannot see" risk section 8
already documents, just now cutting the other way. **No confident verdict
on A vs B**; recorded honestly rather than forcing one.

**Elite route found and validated.** Pulled the live leaderboard
(`kaggle competitions leaderboard kaggriculture -s`) and confirmed Crop
Dusta is still ranked #1 (2979.7) -- direct evidence the original parent
really was elite-sourced. Rather than guessing at other elite teams,
pulled leaderboard #2 (`Giulio Ravasio`, 2965.4)'s most recent episode
(105144807) and found their opponent, `fog flower` (public score 2882.6),
*won* that game 71471-69193. Cloned `fog flower`'s side of that one
episode the same way as every other clone this file describes
(`agents/experimental_distilled_elite_pasture_agent.py`,
`models/v1327-public-elite-fogflower-105144807.json`) and tested it,
wrapped in Candidate A's guards and Candidate B's market-timing residuals
(`build_candidate_b_agent(baseline=build_candidate_a_agent(baseline=...))`),
against both Candidate A and Candidate B on fresh seeds neither this
route nor A/B was ever recorded on, both seats:

- vs Candidate B: 20-0 (seeds 600-602, 700-703, 750-753, 800-803)
- vs Candidate A: 8-0 (seeds 750-753)

Every variant tested (raw, guarded, fully stacked) won every single game.
This is the first candidate, of five tried across sections 9a/9b/9c, to
win decisively instead of losing decisively. The distinguishing factor
was not the strategy family (this is the same cow/sheep-pasture archetype
as the two rejected clones in 9b) but the source: a genuinely elite
leaderboard result, pulled from the leaderboard directly, rather than
from this project's own match history -- confirming the theory in 9b.

**Wired into `rl/candidate_c.py`** as `ELITE_PASTURE`, now the first
(default-selected) route, with `CALENDAR` (Candidate B) kept as the
second, documented route. The selector still cannot legally choose
between them adaptively -- both are step-indexed scripted replays with
no live-opponent signal available at episode start, per this file's own
non-reentrant rule -- so `_select_route_name` remains a placeholder
returning whichever route is listed first. This is "ship the better-
measured single route," not yet a real portfolio; a genuine per-opponent
selector still needs a second *reactive* route or a legal early signal,
neither of which exists yet.

**Packaged**: `submissions/candidate-c/main.py`
(`tools/packaging/prepare_candidate_c_submission.py`), built on top of
the full Candidate B package the same way Candidate B was built on
Candidate A. Package/source/simulator equivalence: 1438/1438 decisions,
0 mismatches (seed 230). Full suite 500/500.

**Not yet done**, per this section's own C-gate requirements above: the
1000-game head-to-head, the panel checks around scores 1500/1800/2200/
2500, the bottom-decile/hard-elite-holdout checks, and a temporal
holdout collected after selector freeze. What exists is a strong initial
signal (28 fresh-seed games, zero losses) two orders of magnitude below
that gate's own stated scale -- treat this as "promising enough to
package and keep validating," not as a promotion decision. `rl/GOAL.md`
section 12's own discipline (state a hypothesis, run the narrow test
first, then paired seeds, then larger gates) has been followed through
the narrow and paired-seed stages; the larger gates are the honest next
step before this should be trusted as much as Candidate A/B's own
promotion evidence.

### 9d. Broad 56-opponent gate (2026-09-03)

Extracted a clone for every unique real opponent already sitting in the
local replay cache from the A-vs-B investigation in 9c (56 distinct
teams; no new Kaggle API calls, per the decision to stop using the
token) and ran Candidate C against all of them: 2 fresh seeds (950, 951)
neither Candidate C nor any of its components was ever recorded on, both
seats -- 224 games.

**Result: 218-6-0, 97.3% win rate.** Only 2 of the 56 opponents beat
Candidate C at all:

- `Cary Jin`: 2-2. The same opponent that beat both Candidate A and
  Candidate B decisively in the 9c controlled comparison -- Candidate C
  is a clear improvement here (2 wins vs 0 for A and B), not a full fix.
- `SGY2512`: 0-4. This is worse than how Candidate A/B did against the
  same real opponent in the 9c comparison (3-1, different seeds though,
  so not a perfectly controlled comparison) -- the one clear case so far
  where the elite-pasture route looks weaker than the calendar route it
  replaced as Candidate C's default. Not yet investigated further.

All 6 losses were by small margins (-1934 to -6944); every one of the
218 wins with a visible margin in the raw results was substantially
larger. Full per-game results kept locally at
`kaggle_cache/candidate_c_broad_gate_results.json` (git-ignored, derived
from Competition Data replays -- not published).

This is a meaningfully larger sample than 9c's 28 games, still two
orders of magnitude below section 9's own 1000-game bar, and it
surfaced a specific, named weakness (`SGY2512`) rather than only
confirming the good news -- exactly what a bigger sample is for. Treat
the headline number as encouraging, and the `SGY2512` result as the
concrete next thing to understand before any promotion claim.

### 9e. The two losses are not a B-layer problem (2026-09-03)

Candidate C's `elite_pasture` route wraps `build_candidate_b_agent`, the
exact code the other concurrent session is auditing for a suspected live
regression -- so a fair question is whether Candidate C's own losses
trace to the same cause, and whether it should be expected to inherit
whatever that investigation finds. Tested three variants of the elite
baseline (raw; wrapped in only Candidate A's guards; wrapped in the full
Candidate A + Candidate B stack, i.e. today's actual route) against both
opponents that had ever beaten Candidate C (`SGY2512`, `Cary Jin`), 3
fresh seeds (960-962), both seats, 36 games:

- All three variants produced the *same* win/loss pattern in every single
  game (identical results down to seat/seed, rewards differing only by
  small guard-triggered corrections). Candidate B's market-timing layer
  is not the cause of either weakness -- whatever the other session finds
  about that code, it does not by itself explain Candidate C's losses.
- `SGY2512`: 6-0 at these seeds -- a complete reversal of 9d's 0-4 at
  seeds 950-951. This was ordinary seed variance, not a persistent
  weakness; retract the "concrete next thing to understand" framing in
  9d.
- `Cary Jin`: 2-1 at these seeds (consistent with 9d's 2-2). This is a
  real, repeatable weak matchup, but it is shared identically across raw/
  guarded/stacked, meaning it is inherent to the elite baseline's actual
  recorded moves against this one opponent's strategy -- not something
  Candidate C's own layers introduced, and not a good target for a
  one-opponent-specific patch (which section 9's own "never select by
  replay ID" spirit argues against extending to hand-tuned counters).

Net effect on confidence: Candidate C's real, replicated weakness is
narrower than 9d suggested (one opponent, not two), and is decoupled
from the current Candidate B investigation.

### 9f. Candidate B corrected, and a second Candidate C (2026-09-03)

**What the land-priority ablation actually showed.** A concurrent session
ran a no-land ablation and concluded land priority was "the source of B's
Kaggle degradation." That conclusion is not supported, and the record is
corrected here so it is not inherited as fact:

- The report
  (`artifacts/benchmarks/v1327-candidate-b-no-land-ablation-300-309.json`)
  labels its arms `submitted_control` and `future_labor`. Those are
  hardcoded legacy names in `research/evaluation/evaluate_future_labor.py`,
  which does not record the agent paths it was actually given. Matching the
  numbers against section 8, the control's 107-13 is Candidate A and the
  candidate's 108-12 is no-land B -- so the run compared **A against
  no-land B**, never land-on against land-off.
- Section 8's original A+B gate scored the *same* 108-12 on the same seeds
  and families **with** the rule enabled. Land priority is a null result
  there, and the +2335 margin delta is the A-to-B delta, not a land effect.
- Direct instrumentation over 8 complete games (5752 decisions, 3408
  non-empty market batches): `_land_priority_ordering` changed the order
  **3** times and `_sequential_affordability_ordering` **8** times. B's
  whole market layer alters ~1.4 decisions per game -- roughly 99.8%
  identical to A. It cannot produce a 200-point rating gap in either
  direction, which points the A-vs-B leaderboard gap at rating dynamics
  (section 9c already measured +/-35 points on byte-identical uploads),
  not at B's logic.

The default stays disabled, on **risk** grounds: it is the one residual
never justified by the fulfilled-count invariant, it deliberately
sacrifices another purchase, and a rule firing ~0.4 times per game with no
measured benefit is not worth an unproven tail. Opt in with
`build_candidate_b_agent(enable_land_priority=True)`.

**Where B's waste actually is.** A no-op audit (every tile-task action
whose target tile was unchanged afterwards) found **205 wasted actions per
3 games (~68/game)**. The largest fixable class was 37 actions doomed by a
weed -- `WATER`/`HARVEST`/`FERTILIZE` on `WEED`, plus `PLANT` the existing
repair declined, because that repair only fires for `RECOVERABLE_SETUP`
work that also passes the schedule-safety check.

`rl/candidate_a.py` now substitutes a bare in-place `DIG` for those. It is
a 1:1 substitution with no queued retry: the worker does not move either
way, so it cannot displace scheduled movement -- the mechanism behind
section 6's -32690 rejection. Measured: waste 205 -> 179 with every
`on WEED` entry eliminated; paired head-to-head over 24 games, 9-15 for
both arms with **zero differing games** and mean margin -12853 -> -12084.
Neutral-to-marginally-positive and safe, not a breakthrough.

`test_weed_repair_does_not_displace_scheduled_movement` was rewritten
rather than deleted: its old assertion assumed the only alternative was
the multi-step repair, so it now asserts the property it actually guards
-- that the calendar's own `WATER` and `WEST` at steps 35/36 still execute
on schedule after the substitution.

**Candidate C2.** `rl/candidate_c2.py` is Candidate C's stack over a
second elite baseline: a clone of "Giulio Ravasio", public leaderboard
rank #2 (2965.4), from the same episode 105144807 whose other side became
Candidate C. Measured on fresh seeds 970-973, both seats, before it was
written to disk: **8-0 against Candidate B, 2-6 against Candidate C1**
(several near-misses: 84515-84243, 107243-110472). So the local ordering
is C1 > C2 > B.

It exists because two variants differing only by a residual flag would
differ by ~1 decision per game -- far below the +/-35 point noise measured
in 9c -- and would settle nothing live. Two different elite programmes
actually diverge, so the comparison can carry information. C2 is a
comparison arm, not a claimed improvement over C1.

Note that Candidate C and C2 both import `rl.candidate_a` and
`rl.candidate_b` directly, so every correction above propagates into both
automatically; C's package bytes changed as a result, and its 9d panel
result predates the weed-clear guard.

**C2 on the same 224-game panel as 9d** (56 unique opponents, seeds
950-951, both seats): **214-10, 95.5%**, against C1's 218-6 / 97.3%.

The 4-loss gap is *entirely one opponent*. Per-opponent losses are Cary
Jin 2-2 and SGY2512 0-4 for **both** variants; the only difference is
Shangshang Zhang, 8-0 for C1 versus 4-4 for C2. 9d already flagged C1's
Shangshang wins as unreliable -- that clone scored literally 0, a
breakdown of the frozen opponent script rather than genuine dominance --
and 9e showed SGY2512's losses are seed-specific (C1 went 6-0 against it
at seeds 960-962). Discount both and the two variants are close to
indistinguishable on this panel.

So do not read 97.3% vs 95.5% as a real 1.8-point quality gap. The
cleanest evidence favouring C1 is the direct head-to-head (6-2, and 2-6
in the concurrent session's independent run at different seeds), not the
panel win rate.

### 9h. Candidate C's first real Kaggle upload failed at "Validation
Episode failed" (2026-09-04)

Every local check this file records for Candidate C -- 518 tests, package
equivalence, 30+ full games through the real simulator, the 224-game
panel -- passed, and the upload still failed immediately with
`AttributeError: 'str' object has no attribute 'name'` inside
`CandidateCExecutor.__init__`. Root cause was in the packaging pipeline,
not in any of the code those checks exercised, which is why nothing
above caught it.

**Mechanism.** `kaggle_environments.agent.get_last_callable` does not
look up a variable literally named `agent`. It execs the whole file into
a fresh namespace and returns
`[v for v in env.values() if callable(v)][-1]` -- the last callable
*value*, by dict insertion order. Candidate C's bundle contained a stray
`agent = build_candidate_b_agent()`, inherited from the embedded
Candidate B package. `_drop_top_level_agent` in
`prepare_candidate_c_submission.py` only filtered `ast.FunctionDef`
nodes named "agent" -- correct for Candidate A's own export (a `def
agent(observation): ...`), but Candidate B moved to `agent =
build_candidate_b_agent()`, an `Assign`, sometime before this file's
section 8. Reassigning an existing dict key does not move its position:
that early assignment pinned `agent`'s slot near the top of the exec
namespace, so this module's own later definitions (`RouteExpert`,
`CandidateCExecutor`, `build_candidate_c_agent`, and the real trailing
`agent = build_candidate_c_agent()`) all landed *after* it in insertion
order. Kaggle's loader therefore picked `build_candidate_c_agent` itself
-- the factory, not the per-turn closure. Calling a factory function
`(routes=ROUTES)` with an observation dict as its first positional
argument binds that dict to `routes`; iterating a dict yields its string
keys, which is exactly `'str' object has no attribute 'name'`.

**Why every existing check missed it.** `test_prepare_candidate_c_submission.py`
called `package_module.agent(...)` directly -- module attribute access
always returns the *current* value of a name regardless of its
insertion-order position, so it cannot see this bug by construction. The
other assertion, `module.body[-1].targets[0].id == "agent"`, checks
*source-order* position of the last statement, not *exec-namespace
insertion-order* position of a possibly-reassigned name -- those are
different things, and only the second one is what Kaggle's loader
actually uses.

**Fix and verification.** Extended `_drop_top_level_agent` to also
filter `ast.Assign` nodes targeting "agent", not just `FunctionDef`.
Verified two ways: replicated `get_last_callable` exactly against the
rebuilt package and confirmed it now returns the real closure and equals
`env['agent']`; then ran 30 full games through the actual simulator
using the callable obtained *that same way* (not `module.agent`) --
30/30 `DONE`, 0 errors. Added a `get_last_callable` helper and two
regression tests (asserts the loader's actual pick behaves correctly;
asserts `agent` is assigned exactly once) to all three packaging test
suites -- B, C, and C2. Reverting the fix and rerunning reproduces the
exact real `AttributeError` in the C and C2 tests, confirming they would
have caught this before the first upload. Checked B and C2 directly
against the same `get_last_callable` replication: B was never affected
(Candidate A's export really is a `FunctionDef`, correctly filtered
already); C2 was never affected (its own filter already checked
`Assign`, independently of this fix).

**Lesson for any future packaging script in this file's pattern**: a
test that calls `module.agent` or checks the literal last source
statement is not a substitute for testing against the actual mechanism
the target platform uses to extract a callable from a file. When
bundling one package's frozen output as a dependency of another,
re-verify what node type its own top-level export uses -- it can change
between the two, and a stale assumption about it is invisible to every
test that only inspects the final state of the name rather than how it
got there.

### 9i. The fourth quadrant, a real 245-episode corpus, and Candidate D
kickoff (2026-09-04)

**Land-quadrant economics, answered with real data.** Deduplicated the
full local cache to 245 genuine `YASH JAIN`-vs-real-opponent episodes
(5 excluded: 1 is the fog-flower/Giulio source game, which has neither
side as us; 4 have `YASH JAIN` on both sides -- self-play probes, not
real opponents) and pooled final-state `unlocked_quadrants` against
final reward for both sides of every game:

| final quadrants | n | mean reward | mean hands |
| --- | ---: | ---: | ---: |
| 2 | 22 | 43,636 | 11.5 |
| 3 | 460 | 83,093 | 10.6 |
| 4 | 7 | 59,916 | 9.3 |

3 quadrants outperforms 4 by ~39% mean reward with *more* labor, not
less. Sharper still: against every one of the 7 opponents who reached 4
quadrants, our win rate is **7-0**, versus 66% against 3-quadrant
opponents. Buying the fourth quadrant is not a missed opportunity we are
leaving on the table -- in this sample it is a tell that an opponent
over-extended. The likely mechanism (consistent with section 9's
existing "worker-time, not land, is the binding constraint" framing):
7000 cumulative coin and, more importantly, the *hand-hours* to farm a
4th quadrant compete directly with hand-hours for premium sale
throughput and livestock service on the first three, and 720 steps is
not enough to recover that trade against a competent opponent. No
candidate in this project buys the 4th quadrant; that default stays.

**Candidate D's data prerequisite is now met.** `tools/data/curate_candidate_d_corpus.py`
(new) scans every cached replay, reuses `rl.replay_dataset._validate_replay`
(simulator version, `DONE`/`DONE`, finite rewards, 720-record shape) so
this pipeline cannot silently ingest a malformed game, deduplicates by
episode ID and SHA-256, and writes one index row per usable episode to
`rl/data/candidate_d_corpus_index.jsonl` (git-ignored, per this repo's
Competition Data handling) with opponent identity, result, and both
sides' final hand/money/quadrant state. Split policy is
`sha256(opponent_name.casefold())[0] % 10` (70/20/10 train/validation/test)
so every game against one opponent stays in one split -- no identity
leakage. This clears GOAL.md section 10's 200-episode minimum (245 usable,
168/43/24 unique opponents across the three splits) and is a curation
pass only: it does not yet call `encode_state` or emit per-step examples,
because that requires the Option-level label design below to be settled
first. True temporal holdout is not yet implemented -- the cached replay
JSON carries no per-episode timestamp, so it would need a fresh
`episodes --csv` pull cross-referenced by episode ID; recorded here as an
open v2 gap, not solved today.

**The four newly-requested public notebooks mostly restate research this
file already has.** WebFetch cannot read any of the four Kaggle notebook
pages the user linked this session (`boatlee/v16-rc5-...`,
`lynnsakurai/farming-score-v3-replay-revised`,
`reyhanksatria/adaptive-route-agent-v2`,
`foysalemonshanto/read-the-market-choose-the-farm`) beyond their
`<title>` -- confirmed for all four, not assumed; Kaggle's notebook pages
are JS-rendered and this is the same limitation section 11's audit
already worked around by using Kaggle's own score/metadata API instead of
page scraping. Of the four, one (`farming-score-v3-replay-revised`) is
already fully audited in `rl/PUBLIC_META_AUDIT.md` ("Replay Revised"),
and `boatlee`'s v16/v20/v21 lineage is already audited there too (V16
Recovery, V20 Adaptive R1, V21-R1 Public-State Route Portfolio) -- the
new `v16-rc5-...` title is almost certainly the same lineage, not
independent evidence. `reyhanksatria/adaptive-route-agent-v2` and
`foysalemonshanto/read-the-market-choose-the-farm` are genuinely new
titles with no prior audit entry and no content beyond the title; their
names are thematically consistent with the audited "route portfolio" and
"market-state-conditioned" families but that is not verified evidence
and is not treated as such.

**The concrete mechanism this unblocks: route selection at shared-prefix
divergence, not at step 0.** Section 9's placeholder selector
(`_select_route_name` always returns `routes[0].name`) exists because
Candidate C1/C2's route experts are two different real players' complete
720-step scripts with no shared opening -- there is no legal opponent
signal at step 0 to select on, and switching mid-script between two
unrelated scripts is not coherent. `PUBLIC_META_AUDIT.md`'s own
independent lesson from the strongest public route-portfolio agents is
exactly the fix: "select routes at shared-prefix divergence points with
hysteresis... from early opponent spending/hiring, initial shop
sequences, or the first meaningful divergence between experts" -- i.e.
run a shared, safe default opening, then *commit* once, once real signal
exists, not before. A quick check of how early that signal actually
appears: across the 244/245 opponents who ever unlock a second quadrant,
the first expansion happens at median step 159 (p10 149, p90 170) --
late, and tightly clustered, meaning quadrant-count timing itself is not
an early discriminator, but it does confirm a shared default opening is
safe to run for well over 100 steps before any commitment is forced.
Early shop/hire sequence (not land timing) is the more promising signal
and is unmeasured -- next step, not done here.

This reframes what Candidate D actually is, versus one more Candidate C
revision: because the elite clones are pure step-indexed lookups
(`actions[step]`, no internal cursor), entering one late at a commit step
`k > 0` is structurally legal, which a step-0-only selector could never
use. Candidate D's first Option is therefore: run `calendar` (the only
reentrant, always-safe route) as the default prefix, gather public
opponent state up to a tunable commit step `k`, then commit once to
whichever executor -- calendar, elite_pasture, elite_giulio, or a future
route -- simulator counterfactual branching (section 10's prescribed
method) scores best against the observed opening. This is genuinely
different work from Candidate C, not a rename of it, which is why it
belongs in Candidate D rather than a Candidate C3.

**Status.** Today's concrete progress is the corpus pipeline, the
land-quadrant answer, the notebook-research honesty pass, and the
route-selection mechanism decision above. No Option-labeling harness,
no model, and no trained selector exist yet -- see section 10 for the
remaining staged plan (counterfactual labeling, interpretable baseline,
causal-influence check against a constant selector, only then online RL).

### 9j. A real, tested, honest null result: glut-aware sell deferral
(2026-09-04)

Extended `kaggle_cache/clones/` from 56 to all 245 corpus opponents
(`tools/data/build_opponent_clones.py`) and built `rl/replay_agent.py`, a
generic factory turning any 720-record action tape into a local
opponent. Building it caught a real indexing bug before it shipped: a
marker-agent probe against the actual simulator proved the action
recorded at replay index k was chosen while observing step k-1, so a
replay agent must look up `step + 1`, not `step` -- confirmed by
reproducing a real recorded game byte-for-byte (rewards 59014.0/123624.0,
exact match) once fixed.

Read the installed simulator source directly
(`kaggle_environments/envs/kaggriculture/kaggriculture.py`) rather than
guess at market mechanics: the market is one pool shared by both players,
priced by `price(inv) = base +/- amp*f(|inv-I0|)`, `I0=10000`. MELON and
WOOL use the quadratic `above_func="sq"` with the highest `above_target`
of any product -- selling into a glut is far more punishing for these two
than for anything else. Candidate C1's frozen elite-clone baseline has no
way to react to this since it just replays fog flower's exact historical
schedule regardless of what the current shared market looks like.

Built `rl/candidate_d.py`: a narrow residual over Candidate C that holds
back a MELON/WOOL sell when the market looks glutted, and flushes the
exact same quantity later (never invents, drops, or resizes an order).
13 focused unit tests first, per this file's own discipline -- one caught
a real bug (a forced flush at the max-hold deadline was being
immediately re-captured and re-deferred by the same call's own
new-deferral scan, if the market was still glutted; fixed by tracking
which items were just force-flushed and excluding them from
reconsideration that turn).

Paired head-to-head against Candidate C1 on the same 80 real opponents,
same seeds, same seats (`kaggle_cache/candidate_d_vs_c1_paired_80.json`):
**0/80 games showed any effect at all.** The guard never fired. Checking
why, against real cached replays rather than guessing again: raw MELON/
WOOL market inventory barely moves (max observed deviation +149 units
against I0=10000), so the 5%-above-I0 threshold this version used was
never reached. Raising sensitivity by checking *price* instead of raw
inventory found real volatility (MELON mean price 161 against a base of
250, WOOL 141 against 200, both frequently near the 1-coin floor) -- but
before rebuilding around that signal, checking the load-bearing
assumption first (does a price dip actually recover?) against 25 real
games directly (no simulation needed) found it does not: of 1,343 MELON
dips more than 20 steps in, only 0.1% recovered above their trailing
median within 10 steps, and the mean price movement over that window was
**negative** (-19.6, price kept falling). WOOL was only marginally
better (6.7%, near-zero mean gain). This market trends on short
horizons; it does not mean-revert. Deferring a sell in the hope the
price comes back is the wrong mechanism for this market, not just an
uncalibrated one -- rebuilding the same residual around a price signal
instead of an inventory signal would not have fixed this.

**This is not shipped as an improvement, and Candidate C1 is unchanged.**
`rl/candidate_d.py` stays in the repo, wired to nothing, as a real,
tested, safe (zero regressions across the full suite; zero effect,
positive or negative, across 80 real paired games), honestly-documented
negative result -- consistent with how this file already records four
earlier rejected route candidates in section 9. The diagnostic pass that
led here also confirms two things worth keeping: Candidate A's existing
terminal liquidation already strands negligible inventory (mean 0.2
units across the same 80 games), so that is not an open gap either; and
C1 held **76/80 (95%)** on this broader, largely non-overlapping opponent
sample, consistent with the original 56-opponent panel's 97.3% -- real
additional evidence, not a repeat of the same numbers.

**What this rules in for next time.** A front-running mechanism (sell
*sooner*, before a trending price falls further, rather than *later*
hoping it recovers) is the mechanism this data actually supports, and is
unexplored -- it is the literal opposite of what this section built.
It was not attempted here for lack of remaining time in this session, not
because the data speaks against it; the persistence finding above is
exactly the evidence that would motivate it.

### 9k. Seven attempts to beat Candidate C1, all measured, all failed
(2026-09-04)

Nothing in this section improved on C1. It is recorded in full because
each result closes a direction that would otherwise be re-attempted, and
two of them close directions this file previously named as the top
priority. `rl/candidate_d.py` and its tests were **deleted** at the end
of this work: both mechanisms it held were refuted, and the second was
actively harmful, so leaving a module exporting a shippable `agent` would
have been a trap. C1 and C2 are unchanged and remain the deployed pair.

**1. The C1/C2 route selector is not worth building.** This is the item
section 9 and the project's own roadmap called the biggest real gap. Ran
C2 across the identical 80 opponents, seeds and seats as C1:

    C1 76/80    C2 69/80    they disagree on only 11/80
    C1 wins where C2 loses:  9
    C2 wins where C1 loses:  2
    ORACLE (a perfect selector): 78/80

The entire upside of a *flawless* selector is **+2 games in 80**, against
nine chances per two to pick wrong. Any realistic selector is
expected-negative. Building it would have been weeks of work for a
ceiling smaller than the noise band section 9c already measured on
byte-identical uploads. It also resolves the live-versus-local
contradiction noted earlier: C1 genuinely beats C2 by 7 games locally, so
C2's higher live score is rating noise, not evidence C2 is better.

**2-4. The market-action surface over this tape is exhausted.** Three
independent interventions, all neutral or negative:

| intervention | result |
| --- | --- |
| glut-aware sell deferral (section 9j) | 0 effect in 80/80 games |
| price-floor throttle (hold sales under 40%/60% of base) | **-12,466 / -16,570** mean coins; 6/10 wins -> 4/10 and 2/10 |
| eager selling (accelerate output goods while price is high) | -448 / -585 mean coins |

The price-floor result is the informative one, because it looked
overwhelming on paper. In one real game C1 sells 333 MILK at a mean of
24.3 coins against a base of 160, and 82% of it goes at 1-6 coins;
the simulator's own numbers say milk's price hits ~4 coins after roughly
74 net units, so the route produces ~4.5x what the market can absorb.
Withholding those "worthless" sales cost 12-16k coins and flipped wins
into losses. The reason is that those cheap sales are not revenue
decisions, they are **logistics**: they clear the 100-unit shed so
harvests can be deposited, and they fund the wheat that feeds the
animals. Starving them breaks the engine. Cheap sales in this game are
load-bearing, and the tape's schedule is close to locally optimal in both
directions.

**5-6. Better source tapes were hunted twice, and neither beat C1.**
On a fixed 24-game screen where **C1 scores 23/24**:

- Six highest-reward opponents from our own cached corpus (their real
  games reached 137k-146k): **7, 11, 14, 14, 15, 19** out of 24. High
  reward in their own game does not transfer; these opponents are
  rating-matched to us, exactly as section 9c warned.
- Six freshly pulled tapes from the *current* top of the leaderboard
  (Crop Dusta #1 at 3029.4, keiz #2 at 2989.1, Jesse Bullard #3 at
  2965.5, in head-to-head games against each other today): **6, 6, 11**
  (Crop Dusta), **14** (keiz), **20, 22** (Jesse Bullard).

The Crop Dusta result is the important one and was verified against a
tape-extraction bug before being believed: replaying both sides of
episode 105502929 reproduces its recorded rewards exactly
(71431.0 / 93533.0). So the #1 agent on the leaderboard, at 3029.4,
produces a route that wins 6 of 24 here. **Leaderboard rank does not
predict tape transferability at all.** The straightforward reading is
that the agents at the top are adaptive, and a frozen replay of one of
their games cannot reproduce behaviour that was conditioned on that
game's opponent and state. Fog flower's tape transferring well (76/80)
looks like a property of that route being unusually self-contained, not
a general property of elite replays.

**7. Jesse Bullard's route, the one screen result close to C1, does not
hold up.** Full 80-opponent panel: **69/80**, identical to C2 and seven
games behind C1, despite slightly higher mean coins (100,720 vs 98,862).
Coins are not the scoring metric. Its 22/24 screen was small-sample luck.
It does cover `opp_105437064`, which both C1 and C2 lose, lifting a
C1+JB oracle to 79/80 -- but with 10 ways to pick wrong against 3 to pick
right, the selector arithmetic is worse than C1/C2's, not better.

**What this means for Candidate D.** Frozen-clone route hunting has
plateaued: two independent searches over twelve candidate tapes, one of
them drawn from the live top of the leaderboard, produced nothing better
than a route captured days ago. Residual tweaks over that route are
exhausted in both directions. And the selector premise -- that we have
two strong routes worth choosing between -- is measurably worth +2
games. If Candidate D is going to beat C1 it has to be **genuinely
adaptive**, i.e. produce actions conditioned on live state rather than
selecting among frozen tapes, which is what section 10 always specified
and what the Crop Dusta evidence now independently argues the top of the
leaderboard is already doing.

One caveat that limits how much any of this says about the live ladder:
all 80 panel opponents come from **our own match history**, so Kaggle
paired them near our own rating. C1's 76/80 is against a field selected
to be our equals, not against the leaderboard's top. Local win rate here
has both little headroom and limited external validity, and no local
number in this section should be read as a live-score prediction.

### 9l. The whole field is farming the wrong products (2026-09-05)

Section 9k exhausted the residual and clone-search surface. This section
stops looking for a better *tape* and asks a different question: what
does a 2900-3000 economy do that ours does not? The answer is a
structural market inefficiency the entire field, us included, is sitting
on -- and it is the first thing found in this project that is worth
roughly a third of our score rather than a couple of games.

**Evidence base.** 51 replays pulled fresh from the current top of the
leaderboard (Crop Dusta 3029.4, keiz 3006.1, Jesse Bullard 2965.5,
AI是我的豆包 2941.3, Andrey Tikhomirov 2919.4, Giulio Ravasio 2913.5,
MtN 2911.6, Syed Asad Ali 2873.5) giving 88 elite player-games, against
253 of our own and 261 mid-field. Profiler:
`tools/data/profile_agents.py`.

**The product mix differs sharply, and the #1 agent is the extreme.**

| team | LB | COW | SHEEP | GOOSE | carrots planted | milk units | milk price |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Crop Dusta | 3029 | 4 | 10 | 3 | 30 | 107 | 65.0 |
| keiz | 3006 | 8 | 6 | 1 | 27 | 188 | 90.1 |
| Jesse Bullard | 2966 | 6 | 11 | 0 | 42 | 165 | 36.6 |
| AI是我的豆包 | 2941 | 7 | 9 | 0 | 41 | 192 | 47.2 |
| **ours (C1/C2)** | ~2100 | **9** | **5** | **0** | **6** | **294** | 45.8 |

Crop Dusta runs 10 sheep to 4 cows -- the inverse of our 5 to 9 -- plants
five times the carrots, keeps geese, and sells a third of the milk.

**Why, from the simulator's own price model.** Price is
`base +/- amp*f(|inv - I0|)` about `I0 = 10000`, and the `above` (glut)
shape is per-product. Units a product absorbs before its price halves:

| product | base | units to half price | price after 200 units |
| --- | ---: | ---: | ---: |
| EGG | 50 | never (log) | 41 |
| WHEAT | 25 | never (log) | 21 |
| FERTILIZER | 100 | 253 | 60 |
| CARROT | 35 | 230 | 19 |
| MELON | 250 | 113 | 1 |
| WOOL | 200 | 42 | 1 |
| MILK | 160 | 39 | 1 |
| STRAWBERRY | 120 | 32 | 1 |

Milk collapses after **39 units**. We sell **294**.

**But absorption is a rate, not a budget.** The town drains inventory
continuously; measured per game across 12 elite replays as
`units sold by both players - net inventory change`: WHEAT 828,
STRAWBERRY 509, WOOL 460, EGG 426, MILK 377, CARROT 354, TOMATO 354,
FERTILIZER 220, MELON 31. Halve those for a per-player sustainable rate.

**The result is that three markets are permanently starved.** Median
price by 90-step bucket across elite games, with end-of-game market
inventory relative to `I0`:

| product | b0 | b2 | b4 | b6 | b7 | final inv - I0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TOMATO | 60 | 62 | 70 | 76 | **80** | **-166** |
| CARROT | 35 | 36 | 39 | 47 | **49** | **-177** |
| EGG | 50 | 51 | 54 | 58 | **59** | **-157** |
| MILK | 172 | 191 | 76 | 19 | 22 | +66 |
| WOOL | 209 | 187 | 172 | 49 | 31 | +54 |
| MELON | 260 | 270 | 94 | 108 | 115 | +129 |

Tomato, carrot and egg prices **rise for the whole game** because demand
outruns supply. **Nobody in the field sells tomato at all** -- not one
team, elite or otherwise -- despite it being the highest-throughput crop
in the game (`ongoing`, `interval 1`, `first_yield_day 8`, `max_yield 4`)
and the town absorbing 354 units of it per game. Meanwhile every agent,
ours included, dumps milk, wool and melon into a collapse.

**What that is worth.** Selling into the observed deficits, priced with
the simulator's own scarcity branch:

| item | deficit | price now | revenue to fill | +100 beyond | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| TOMATO | 166 | 80 | 11,623 | 4,318 | 15,941 |
| CARROT | 177 | 49 | 7,420 | 2,738 | 10,158 |
| EGG | 157 | 59 | 8,595 | 4,371 | 12,966 |
| | | | | | **39,065** |

Against a median reward of 81,508 (ours) and 84,750 (elite). This is
non-degrading revenue in markets with no competition, and it dwarfs
every lever measured in 9j and 9k, all of which were worth hundreds of
coins or less.

**It cannot be bolted onto Candidate C1.** Measured over a full C1 game:
empty unlocked tiles average **0.3 to 3** out of 75 from bucket 2 onward,
and idle worker-turns fall to **2-8%**. The farm is saturated. Capturing
this requires *reallocating* land and labour away from milk-heavy
production, which is a different production plan -- not a residual over a
frozen tape. That is the architectural case for Candidate D being a real
reactive agent, and it is now an evidence-backed case rather than an
aspiration.

**Open question before building.** Where the existing hand-built reactive
agents in `agents/` stand against C1's 23/24 screen is not yet measured
(the run was lost to a session restart). That number decides whether
Candidate D re-targets an existing reactive executor or needs a new one.

### 9l. What actually separates a 3000 economy from ours (2026-09-05)

Section 9k established that clone-hunting and residual tweaks are both
exhausted. This section stops searching over agents and instead asks the
comparative question directly: pulled 51 fresh replays across the top
eight teams (about 100 elite player-games), wrote `tools/data/profile_agents.py`
to profile any replay's economy from public record alone -- units sold and
the live price at each sale, worker action mix, hiring, land, livestock,
crops -- and compared elite, ourselves, and the mid-field on identical
metrics.

**Finding 1: the whole field, us included, competes in collapsing markets
and ignores the ones that pay.** Median price by 90-step bucket across
elite games, with end-of-game market inventory relative to `I0 = 10000`:

| product | b0 | b2 | b4 | b6 | b7 | final inv - I0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TOMATO | 60 | 62 | 70 | 76 | **80** | **-166** |
| CARROT | 35 | 36 | 39 | 47 | **49** | **-177** |
| EGG | 50 | 51 | 54 | 58 | **59** | **-157** |
| MILK | 172 | 191 | 76 | 19 | **22** | +66 |
| WOOL | 209 | 187 | 172 | 49 | **31** | +54 |
| MELON | 260 | 270 | 94 | 108 | 115 | +129 |

Tomato, carrot and egg prices *rise all game* because town demand outruns
supply. Nobody in the field sells tomato at all. Meanwhile everyone dumps
milk, wool and melon into a collapse.

**Finding 2: the market's absorption limits are computable, and we ignore
them.** From the simulator's own `MARKET_PARAMS`, units sellable before
the price halves: EGG and WHEAT **never** (log curves), FERTILIZER 253,
CARROT 230, MELON 113, WOOL **42**, MILK **39**, STRAWBERRY **32**. The
town's measured drain per game (shared across both players) is WHEAT 828,
STRAWBERRY 509, WOOL 460, EGG 426, MILK 377, CARROT 354, TOMATO 354,
FERTILIZER 220, MELON 31. Against that, our median sales are MILK **294**
(roughly 1.6x a sustainable half-share), CARROT **12**, EGG **0**,
TOMATO **0**.

Pricing the three scarce markets from their observed deficits using the
simulator's own scarcity formula gives **~39,000 coins per game of
unclaimed, non-degrading revenue** (TOMATO 15.9k, EGG 13.0k, CARROT
10.2k) against our median reward of 81,508.

**Finding 3: the per-team split explains the top of the leaderboard.**

| team | LB | COW | SHEEP | GOOSE | carrots planted | milk units |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Crop Dusta | 3029 | 4 | **10** | **3** | 30 | 107 |
| keiz | 3006 | 8 | 6 | 1 | 27 | 188 |
| Jesse Bullard | 2966 | 6 | **11** | 0 | 42 | 165 |
| AI是我的豆包 | 2941 | 7 | 9 | 0 | 41 | 192 |
| **ours (C1/C2)** | ~2100 | **9** | 5 | **0** | **6** | **294** |

The number one agent runs the inverse of our livestock mix and five times
our carrots. Note also that the two elite teams with our carrot count (6)
-- Giulio and Andrey -- are the lower-ranked of the elite group, and
Giulio is exactly who Candidate C2 clones.

**Finding 4: our reward variance is market contention, not execution.**
The same C1 build earns MILK at 215/unit in one game and 24.3/unit in
another. Its farm output is near-identical across both (section 9j showed
byte-identical cycle counts across four losses). What changes is whether
the opponent floods the same market. Local rewards ranging 44k-162k are
mostly this.

**Finding 5: our reactive lineage is routing-limited, not strategy-limited.**
Every hand-built reactive agent screened scores **0-1 of 24** where C1
scores 23/24, at roughly half C1's coins. Profiling the best of them
against C1 on an identical game shows why:

| | C1 | best homegrown |
| --- | ---: | ---: |
| utilisation | **0.47** | **0.26** |
| task turns | 3376 | 1955 |
| move turns | 3276 | **4374** |
| pass turns | 540 | **1145** |

Our agents spend their worker-turns walking and idling. The elite tape's
real asset is worker routing, not crop selection. This reframes what is
hard: choosing what to grow is a solved arithmetic problem given the
tables above; routing many workers efficiently over 720 steps is the part
we have never matched, and it is what the tape encodes implicitly.

**Finding 6: there is no spare capacity to bolt new production onto C1.**
Measured across a full game, C1 leaves only 0.3-3 empty tiles of 75
unlocked mid-game and its workers idle only 2-8% of turns. Adding tomato,
carrot or geese on top of C1 is not possible; capturing the 39k requires
*reallocating* land and labour.

**What this implies for Candidate D.** Combining findings 5 and 6: keep
the tape's routing, change what it grows. A crop substitution on the tape
preserves the routing skeleton that makes C1 strong while retargeting its
output at markets whose price is rising rather than collapsing. That is
our own portfolio design applied to a proven execution skeleton, not a
copy of anyone's strategy, and it is the first Candidate D direction that
is both grounded in measurement and cheap enough to falsify quickly.

### 9m. The local benchmark has been lying to us (2026-09-05)

This is the most important measurement in this file, and it invalidates
how every candidate in sections 6-9l was validated.

**The contradiction.** Candidate C1 was measured three ways on the same
day:

| opponent | how measured | C1 win rate |
| --- | --- | ---: |
| ~2100 cached tapes (the standard local panel) | frozen replay | **95%** (76/80) |
| elite tapes, LB 2837-3021 | frozen replay | **78%** (28/36) |
| live agents, LB 2100-2400 | real ladder | **52%** |
| live agents, LB 2400+ | real ladder | **20%** (1/5) |

C1 beats the *tape* of the world #1 (keiz, 3021) 4 games out of 4, and
loses to live 2400-rated agents 4 times out of 5. Both numbers are real.

**The cause: a frozen tape is far weaker than the agent it came from.**
A replay tape reproduces one game's actions against a different opponent
on a different seed, with none of the reactivity that earned the source
its score. Section 9k already saw this without drawing the conclusion:
Crop Dusta, ranked #1 at 3029.4, produces a route that wins 6 of 24 --
and that was verified not to be an extraction bug by reproducing its
source game's rewards exactly. The local panel is not a field of
2100-rated opponents. It is a field of *crippled* 2100-rated opponents,
and it inflates our measured win rate by roughly forty points.

**Our real standing.** 60 live games from submission 56007798 (public
score 2045.1, 136 episodes, well past the ~60-game convergence point):
**33W-27L, 55%**, mean reward 84,770 against 85,412, median opponent LB
2103. By band: 66% against 1800-2100, 52% against 2100-2400, 20%
against 2400+.

**What this explains.**

- Why cloning a 2882-rated player produced a 2045-rated agent. The clone
  keeps the programme and discards the adaptivity that earned the score.
  This is the ceiling on the entire clone strategy, and it is now
  measured rather than suspected.
- Why all seven interventions in section 9k came back neutral. They were
  tuned against a benchmark that does not predict live results.
- Why leaderboard rank fails to predict tape transferability (9k).
- Why C2 scoring above C1 live contradicted C1 beating C2 76-69 locally
  (9k): the local number was never the relevant one.

**Consequences for method, effective immediately.**

1. A tape-panel win rate is not evidence of live strength. Numbers like
   "218/224" and "76/80" elsewhere in this file measure robustness of a
   programme against frozen scripts, nothing more.
2. Real validation requires reactive opponents or live ladder games.
   Live episodes for a submission are pullable via the API and are the
   only unambiguous signal available.
3. Do not spend further effort searching for a better tape to clone.

**Live-validated signals.** Paired winner-versus-loser within the same
live game, 60 games, which controls for seed, market and opponent:

| feature | winner did more | z |
| --- | ---: | ---: |
| sold_WHEAT | 25.0% (median -28.5) | 3.9 |
| task_turns | 72.9% | 3.5 |
| wheat_bought_for_feed | 30.0% | 3.1 |
| plant_WHEAT | 67.4% | 2.3 |
| price_MELON | 68.3% | 2.3 |
| buy_SHEEP | 64.9% | 1.8 |
| utilisation | 62.7% | 2.0 |
| buy_COW | 42.4% | 1.2 |

The clearest actionable defect: winners **plant more wheat, sell less of
it, and buy less of it**. They grow their own feed. We sell 404 wheat and
buy back 157, paying the bid-ask spread on a round-trip we create
ourselves. Throughput (task_turns, utilisation) is again the strongest
non-economic signal, and sheep-over-cows reappears.

**Supporting negative results from the same day.**

- Every hand-built reactive agent in `agents/` and `submissions/` scores
  **1/24 or 0/24** against C1's 23/24, with mean coins near 50,000
  against C1's 98,862. The homegrown lineage is at roughly half of C1's
  economy, so re-targeting one is not a viable base for Candidate D.
- Herd composition does not separate the field. Andrey Tikhomirov sits
  at LB 2920 with the same C9/S5/G0 herd we ran at 2071, and
  `total_animals` correlates -0.016 with leaderboard score across 36
  teams. The product-mix story in 9l is real about market structure but
  is **not** the explanation for the 800-point gap.
- The 9l claim that we run zero geese was drawn from a blend of older
  submissions. Our current live agent runs 7 cows, 5 sheep, **2 geese**
  and sells 229 milk. 9l's "ours" column should not be trusted; this
  section's live profile supersedes it.

### 9n. Candidate D: the route chosen by search, not by rank (2026-09-05)

Sections 9j-9m closed every other door. Residual mechanisms measured
neutral or negative; the C1/C2 selector had a +2/80 ceiling; the
hand-built reactive engine runs at half C1's economy and its fertilizer
and feed knobs are inert in that configuration (measured this session:
41,862 mean coins with the flags on, byte-identical to baseline, and
2,642 when fertilizer sales are withheld -- holding fertilizer starves
the cash the engine needs). What 9m left standing was the route itself,
plus the warning that leaderboard rank does not imply a good tape.

**Method.** Score tapes on *our own final reward*, not tape-panel win
rate, because 9m showed the latter overstates live strength by ~40
points while our own coin production is nearly self-determined. 191
candidates -- every side of every cached replay from a team rated 2400+,
on a game that team won -- ran under the exact Candidate C guard stack on
fixed seeds. The best five then ran 48 games each across six seeds, both
seats and four opponents (two mid-field clones, two elite tapes):

| candidate | wins | mean coins | floor |
| --- | ---: | ---: | ---: |
| Giulio Ravasio ep105531280 | **38/48** | 108,472 | 51,094 |
| Mater Welon ep105545969 | 28/48 | 112,794 | 53,645 |
| peikopon ep105552428 | 32/48 | 107,097 | 49,999 |
| Candidate C1 (fog flower) | 32/48 | 97,043 | 47,364 |
| Andrew Reed ep105554550 | 36/48 | 87,440 | 43,542 |

Coins and wins diverge sharply. Mater Welon's tape earns the most coins
and still loses **0/12** to one opponent -- the failure mode a single
frozen route can least afford. Episode 105531280 won on wins, mean coins
and floor simultaneously, and stayed balanced across all four opponents
(6/12, 12/12, 8/12, 12/12), strongest exactly where C1 is weakest (8/12
against the Jesse Bullard tape against C1's 4/12).

This is **not** the Giulio game Candidate C2 clones. C2 uses episode
105144807; this is 105531280, a day newer. Many Giulio games were scored
and only this one came out on top, which is itself evidence that tape
quality is a property of the individual game, not of the player.

**Where Candidate D stands against C1 -- honestly, it is a wash that
favours D only against strong opposition.**

| measurement | Candidate D | Candidate C1 |
| --- | ---: | ---: |
| finalist panel, incl. elite tapes (48 games) | **38/48** | 32/48 |
| broad panel, 40 mid-field clones x 2 seats | 76/80 | 76/80 |
| broad-panel mean coins | 103,216 | **106,768** |
| broad-panel floor | **42,426** | 36,326 |
| finalist-panel floor | **51,094** | 47,364 |
| head-to-head, 16 games | 6W-10L | **10W-6L** |

D loses the direct matchup with C1 and earns slightly fewer coins on the
weak panel, but wins clearly against elite opposition and has a better
worst case on both panels (+17% and +8%). Against C2 it is unambiguous:
**12W-4L head-to-head, mean margin +5,998**, and ahead on every panel
metric.

**So the justified action is to replace C2, not C1.** D is better than C2
on every measurement taken. It is not established as better than C1, and
this file should not claim it is. Per 9m none of these tape-panel numbers
is a live forecast; the transferable part is the floor improvement and
the elite-panel margin.

**Build and gates.** `rl/candidate_d.py` wraps
`agents/experimental_distilled_elite_giulio2_agent.py` (model
`models/v1327-public-elite-giulio2-105531280.json`, hashes verified by
`tools/data/build_elite_model.py`) in Candidate A's guards and Candidate
B's residuals -- deliberately the same wrapping as C, so the comparison
isolates the route. Packaging is
`tools/packaging/prepare_candidate_d_submission.py`. Gates run:

- source/package/simulator equivalence **1438/1438 decisions, 0
  mismatches**;
- 20 real games driven through Kaggle's actual `get_last_callable`
  extraction path, **20/20 DONE, 0 errors**, mean reward 111,168 -- the
  check that section 9h's upload failure would have tripped;
- full suite **527 tests, OK**;
- 5 packaging tests including the loader-order regression and a new
  assertion that the embedded payload is namespaced.

One real packaging defect was caught and fixed while building: appending
a second distilled clone verbatim rebinds `MODEL_PAYLOAD`,
`CALENDAR_ACTIONS` and `_load_actions`, so the bundled calendar's own
`decide` would silently execute this route's tape. Inert for D, which
never selects that route, but the same class of quiet aliasing as 9h, so
the clone's module-level names are now namespaced.

### 9o. Candidate D validated against the real top 500 (2026-09-05)

Section 9n could not claim D was better than C1: it won the elite-tape
panel but lost their head-to-head 6-10. This section settles it on a
panel that actually matters, and answers four open questions with
measurement.

**Top-500 tournament.** 92 distinct opponents built from cached replays
of teams ranked 1-470 (37 of them top-50), each team's best winning side,
both seats, 184 games per agent -- 552 games total:

| agent | overall | vs top 50 | vs 51-150 | vs 151-500 | mean coins | floor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **D** | **108/184 (58.7%)** | **50/74 (67.6%)** | 18/44 | 40/66 | 86,859 | 47,689 |
| C1 | 103/184 (56.0%) | 38/74 (51.4%) | 19/44 | 46/66 | 85,811 | 35,703 |
| C2 | 81/184 (44.0%) | 36/74 (48.6%) | 17/44 | 28/66 | 85,929 | 50,966 |

D > C1 > C2, and the margin is concentrated exactly where it matters:
**against the strongest fifty teams D wins 67.6% where C1 wins 51.4%**,
twelve more wins in 74. C1 is the better farmer of *weak* opposition
(151-500: 69.7% against D's 60.6%), which is what the old mid-field panel
was measuring and why it scored them equal. D's floor is also 34% higher.
The 9n head-to-head loss does not generalise: one frozen tape against
another is a single matchup, not a ladder.

Note the win rates here (44-59%) sit far closer to our real live 55%
(section 9m) than the 92-95% the mid-field clone panel produced. A panel
built from top-500 opponents is the first local benchmark in this project
whose numbers are in the same range as reality.

**The fourth quadrant, settled.** 1,290 player-games across the whole
ladder:

| rank band | 3 quadrants | 4 quadrants |
| --- | ---: | ---: |
| top 50 | 99.0% | 1.0% |
| 51-150 | 100% | 0% |
| 151-500 | 100% | 0% |
| 501-2000 | 95.7% | 0.6% |

Outcome by quadrant count: 3 quadrants n=1,255, **51.2% win rate**;
4 quadrants n=12, **8.3% win rate**. The only highly-ranked player who
ever buys the fourth is Jesse Bullard (rank 3), who went **1-4** in those
games. The cause is market absorption, not land: milk's price collapses
after 39 units and we already sell past that, so a fourth field produces
goods worth ~1 coin while consuming the hand-hours that grow melon and
wheat. Three quadrants stays, and this is no longer a 7-sample inference.

**The watering and feed-loop claims, implemented and measured.**
`rl/idle_work.py` converts a route's `PASS` turns into FERTILIZE, WATER
or shed PICKUP, firing only where the wrapped route already idled, so it
cannot displace an action or desynchronise a tape. Over six seeds on D:

| variant | mean coins |
| --- | ---: |
| D baseline | 98,827 |
| D + idle water only | **98,827 (exactly zero)** |
| D + idle fertilize + restock | 99,092 (**+265, +0.27%**) |

Watering gains **nothing** -- the route already issues ~1,043 waters a
game and only ~27 idle turns land on a dry in-window plant. The fertilizer
loop is real but tiny: the route collects ~372 fertilizer and applies only
~74, yet capturing the rest needs a worker holding fertilizer *while*
idling on a fertilizable tile, which happens ~13 times a game even with a
shed-restock rule. The mechanics are sound (a fertilized plant gains 2
yield per watering instead of 1) but the tape leaves no room to exercise
them. Kept in the tree, tested, **not wired into Candidate D** -- 0.27% is
not worth the risk surface.

**Weeds are not a problem.** Measured over three seeds per agent: mean
weeds on the board **0.40 tiles (C1) / 0.42 (D)** out of 75, peak 6-8,
handled by ~36-38 DIGs a game. There is nothing to win here.

**Wheat round-trip, quantified.** D sells 397 wheat at a mean of 31.5 and
buys 182 back for feed at a mean of 34.4 -- a real self-inflicted loss of
**~528 coins a game**, and the only lever found that costs zero worker
turns. Worth fixing, worth ~0.5%.

**The public notebooks are not a source of strength.** Kaggle notebook
pages cannot be read by fetching them (JS-rendered), but
`kaggle kernels pull` retrieves their source directly -- a capability
this project wrongly assumed unavailable for several sections. Pulling
six requested notebooks:

| notebook | rank | score | what the code actually is |
| --- | ---: | ---: | --- |
| avioon / apex-v7-god-emperor | 304 | 2379.1 | ctypes shim around a compiled `agent.so`; strategy opaque |
| boatlee / v21 route portfolio | 810 | 1950.7 | 0 functions; a 166KB base64+zlib tape |
| foysalemonshanto | 1201 | 1694.8 | 0 functions; embedded blob |
| llccqq624 | 1380 | 1596.6 | 0 functions; embedded blob |
| dianatofficial | 2263 | 1311.0 | EDA writeup |
| mansiaggarwal88 | 7405 | 147.7 | EDA writeup |

**Five of the six rank below our own 677 / 2071.3.** Cloning them would
move us down. The most-cited "route portfolio" notebook is itself just an
embedded tape, exactly like ours. The genuine top (keiz 3021, Crop Dusta
3011) publish nothing at all -- they expose only replays, which is what
the section 9n search already mines.

**On PPO, accurately.** This file never claimed PPO would settle
anything; section 10 says the opposite -- *"Do not train a
primitive-action PPO policy. Public evidence shows full-action PPO/BC
often stalls around 40k-80k terminal cash and fails to generalize."*
Residual PPO over Options appears only under "Online RL", gated behind
*"Only after free-running BC beats the deterministic selector"*, which
requires an Option-labelling harness and a BC model that do not exist.
Two later measurements make that gate look worse, not better: section 9k
found a perfect route selector is worth **+2 games in 80**, so PPO
optimising Option choice is optimising against an almost-flat ceiling;
and the best public PPO result cited in `PUBLIC_META_AUDIT.md` reached
~80k terminal cash, which is **below** the ~103k our current route
already produces. PPO is not the missing piece here.

### 9p. Candidate D's route re-chosen on a proper panel (2026-09-05)

Section 9n picked Candidate D's route with a screen that used **three
seeds against a single mid-field clone**. That is far too noisy to choose
between tapes whose true win rates sit within a few points of each other,
and section 9o then showed the choice was not settled: D beat C1 on the
elite panel but tied it overall (p=0.50) and lost their head-to-head.

**Re-screen.** Nineteen leading tapes (top twelve by mean coins, top
twelve by floor, deduplicated, plus the incumbent Giulio route as a
control) were re-run on a stratified slice of real top-500 opponents --
12 from the top 50, 6 from 51-150, 12 from 151-500 -- both seats,
identical games for every candidate, 60 paired games each:

| route | wins | mean coins | floor |
| --- | ---: | ---: | ---: |
| **Andrey Tikhomirov ep105520725** | **42/60 (70.0%)** | **92,327** | 49,822 |
| Jesse Bullard ep105487025 | 40/60 (66.7%) | 89,698 | 41,059 |
| Bohannn Wang ep105546785 / 105551379 / 105548688 | 40/60 (66.7%) | 89,698 | 41,059 |
| OceanMix ep105554277 | 38/60 (63.3%) | 87,014 | 49,301 |
| Giulio ep105531280 (incumbent) | 37/60 (61.7%) | 87,830 | 40,872 |
| Ignat / Andrew Reed / sword3522 | 33/60 (55.0%) | 84-91k | 40-49k |
| Mater Welon ep105545969 | 25/60 (41.7%) | 89,894 | 43,905 |
| Andrey Tikhomirov ep105527696 | 24/60 (40.0%) | 90,354 | 56,586 |
| OceanMix ep105550837 | 22/60 (36.7%) | 79,513 | 40,756 |

Two structural facts fall out of that table. **Tape quality belongs to
the game, not the player**: two Andrey tapes recorded the same day score
70.0% and 40.0%, and two OceanMix tapes score 63.3% and 36.7%. And
**public agents are copied wholesale**: three tapes credited to two
different teams (Jesse Bullard, Bohannn Wang twice) return byte-identical
wins, mean and floor, which is what one shared public agent looks like
from the outside.

Section 9n's own ranking metric is also refuted here. Mater Welon's tape
had the highest coin production in the 191-tape search and finishes
**41.7%** on this panel; peikopon, third by coins, finishes 50.0%. Coins
rank routes badly once real opponents are involved.

**Confirmation on the full panel.** The winner was then re-scored on all
92 top-500 opponents using the *same seeds* as section 9o's tournament,
so it pairs game-for-game against the stored results:

| route | wins | mean coins | floor | vs top-50 |
| --- | ---: | ---: | ---: | ---: |
| **Andrey ep105520725** | **118/184 (64.1%)** | **91,199** | 42,858 | 44/74 |
| Giulio ep105531280 | 108/184 (58.7%) | 86,859 | **47,689** | **50/74** |
| C1 fog flower | 103/184 (56.0%) | 85,811 | 35,703 | 38/74 |

**No pair is significant at p < 0.05** (Andrey vs Giulio p=0.19, Andrey
vs C1 p=0.079, Giulio vs C1 p=0.50). This section does not claim
significance, and neither should any later one citing it. The switch
rests on three things instead: Andrey leads **all three independent
evaluations** (the 191-tape search by coins, the 60-game stratified panel,
the 184-game full panel); it wins **+16 games against ranks 51-500**,
which is the band actually faced around our rank of ~677, giving back 6
against the top 50; and it carries the best mean coins of any route
tested, which section 9m argued is the component most likely to transfer
live.

The honest counter-argument, recorded so it is not lost: the Giulio route
has a better floor (47,689 against 42,858) and a better top-50 record
(50/74 against 44/74). If the goal were specifically to beat the top of
the ladder rather than to climb through the middle of it, Giulio would be
the better pick. There is also a winner's-curse risk in selecting the best
of nineteen candidates on one panel; the full-panel confirmation on
different seeds is the partial guard against that, and it held.

**Candidate D now runs episode 105520725.**
`models/v1327-public-elite-andrey-105520725.json`,
`agents/experimental_distilled_elite_andrey_agent.py`, wired through the
unchanged A+B wrapper in `rl/candidate_d.py`. All seven gates in the new
`tools/validation/preflight_candidate_d.py` pass on the rebuilt package:
deterministic rebuild matching disk, manifest hash agreement, embedded
model hash verification, extraction through Kaggle's real
`get_last_callable`, 1438/1438 source/package/simulator equivalence, 12/12
whole games finishing DONE through that loader path in both seats, and the
full test suite.

**Standing recommendation.** Upload Candidate D into the slot vacated by
**C2**, keeping C1. Kaggle keeps only the two most recent submissions
active and does not allow choosing, so the ordering matters: C1 must be
re-submitted *before* D so that D's upload displaces C2 rather than C1.

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
