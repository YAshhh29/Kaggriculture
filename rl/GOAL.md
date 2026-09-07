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
section 13's own discipline (state a hypothesis, run the narrow test
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
leakage. This clears GOAL.md section 11's 200-episode minimum (245 usable,
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
are JS-rendered and this is the same limitation section 12's audit
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
route -- simulator counterfactual branching (section 11's prescribed
method) scores best against the observed opening. This is genuinely
different work from Candidate C, not a rename of it, which is why it
belongs in Candidate D rather than a Candidate C3.

**Status.** Today's concrete progress is the corpus pipeline, the
land-quadrant answer, the notebook-research honesty pass, and the
route-selection mechanism decision above. No Option-labeling harness,
no model, and no trained selector exist yet -- see section 11 for the
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
selecting among frozen tapes, which is what section 11 always specified
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
anything; section 11 says the opposite -- *"Do not train a
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

### 9q. Why cloning is capped, and what Agent E must actually fix
(2026-09-05)

**The clone ceiling, stated plainly.** We cloned "fog flower" at public
score 2882 and the resulting agent settled at **2094.7** live. A frozen
tape discards whatever reactivity earned the source its score, and
section 9m measured the size of that loss from the other direction: tapes
are roughly forty points weaker than the agents they came from, and the
world #1's tape wins 6 of 24 locally. Every tape-panel number in sections
9n-9p, including Candidate D's 64.1%, is measured against *tapes* and so
does **not** establish that D beats live top-500 agents.

The consequence is arithmetic. To reach the top ten by cloning we would
need a source around 3700, and the ladder's best is 3021. **Cloning cannot
pass ~2100 for us, which is exactly where C1 and D both sit.** Candidate D
is a lateral move from C1, not a climb, and this file should not be read
as claiming otherwise. Cloning is also commodity: anyone can pull the same
replays, and three tapes in the 9p re-screen turned out to be one shared
public agent running under two team names.

**So Agent E must be our own policy.** Not a copy of one player, but a
strategy specification distilled from what *many* winners do, executed by
our own agent.

**The blocker is execution, not strategy.** Profiled the tape route
against the best reactive engine configuration, identical seeds and
opponent, three games each:

| metric | tape | reactive engine | gap |
| --- | ---: | ---: | ---: |
| reward | 113,550 | 45,101 | -68,449 |
| task turns | 3,494 | 1,956 | -1,538 |
| move turns | 3,272 | 4,522 | +1,250 |
| idle turns | 322 | 985 | +663 |
| water | 1,231 | 590 | -640 |
| care | 415 | 179 | -236 |
| harvest | 450 | 238 | -212 |
| units sold | 2,140 | 720 | -1,420 |
| **revenue per unit sold** | **91.1** | **88.5** | **~equal** |
| **task share of turns** | **0.493** | **0.262** | — |

The engine realises essentially the same price per unit as the tape, so
its market policy and product mix are not the problem -- consistent with
sections 9j-9o, where every market-side intervention measured neutral or
negative. What it does is **44% less work**: it burns 1,250 more turns
walking and 663 more idling, and ends with 14 tiles in use against 21.

**Therefore Agent E's core problem is task assignment and routing**, not
strategy discovery. Raising task share from 0.262 toward 0.49 is worth
roughly a doubling of output on its own, and it is a well-posed
engineering problem rather than an open-ended search. The strategy
specification to execute is already measured and recorded: sections 9l
(market absorption per product, and the scarce tomato/carrot/egg markets),
9m (live-validated winner traits: more task turns, grow your own feed
rather than round-tripping wheat, sheep over cows), and 9o (three
quadrants, weeds already solved, watering already saturated in a good
route).

**Planned order for E**, so it is falsifiable at each step rather than a
single large bet:

1. Localise the lost turns precisely -- travel distance per completed
   task, and the reason each idle turn had no assignment.
2. Fix assignment/routing until task share approaches the tape's, scored
   on own final reward across fixed seeds.
3. Only then apply the 9l/9m strategy specification on top.
4. Gate against live-like opposition, and never again quote a tape-panel
   win rate as evidence of live strength.

### 9r. What actually separates winners, learned from 120 paired games
(2026-09-05)

Agent E needs a real edge, not a copied route. This section looks for one
in the games of the strong players themselves, contrasting winner against
loser **inside the same game** so seed, market and opponent are held
fixed. Three findings, one of them the first significant behavioural
differentiator this project has found.

**1. The marginal-value model does not discriminate. (Falsified.)**
`rl/economics.py` prices each action in coins from the simulator's own
constants. Scoring every action both players actually took, across 70
paired games:

| metric | winner | loser | winner higher | p |
| --- | ---: | ---: | ---: | ---: |
| modelled action value | 90,918 | 92,186 | 54.3% | 0.47 |
| value per action | 37.3 | 39.1 | 52.9% | 0.63 |
| productive actions taken | 2,440 | 2,438 | 55.1% | 0.40 |

Losers' actions score marginally *higher*. The model is not wrong as a
description of what an action is worth -- it is simply not what separates
these players. Recorded as a falsification so it is not silently reused
as a ranking signal.

**2. Throughput separates us from the field, not winners from losers.**
Winners and losers perform 2,440 against 2,438 productive actions -- a
dead heat. Section 9q measured our reactive engine at 1,956 against a
tape's 3,494, so throughput is what stands between *our* agent and real
players, and it remains worth fixing. But it will not win games once we
get there, and section 9q should be read with that qualification.

**3. Winners get paid more for identical output. (Significant.)**
Across 90 paired games:

| metric | winner | loser | winner higher | p |
| --- | ---: | ---: | ---: | ---: |
| units sold | 1,755 | 1,760 | 51.7% | 0.75 |
| **mean price per unit** | **68.52** | **64.21** | **61.1%** | **0.035** |
| MILK price realised | 58.8 | 55.1 | 61/89 | **0.0005** |
| wheat units sold | 373 | 404 | winners sell less | **0.031** |

Same production, same volume, better price. The wheat result independently
reproduces section 9m's live-game finding that winners grow their own feed
rather than round-tripping it.

**The mechanism, and it checks out quantitatively.** Milk sale *timing*
explains nothing -- across 120 paired games the volume-weighted sale step
is identical (494.7 against 494.7), as are first-sale step, spread and
burstiness. What differs is the state of the shared market at the moment
of sale:

| MILK, 120 paired games | winner | loser | p |
| --- | ---: | ---: | ---: |
| price realised | 60.9 | 55.1 | **0.0045** |
| **market inventory when selling** | **10,047.6** | **10,050.2** | **0.0004** |
| units sold | 271.5 | 275.0 | 0.71 |

Winners sell milk into a **less saturated market**. The inventory gap is
only ~2.6 units, but milk's price moves 2.098 coins per unit of deviation
from equilibrium (base 160, T 122, linear glut response, target 1.60), so
2.6 x 2.098 = 5.5 coins per unit -- against an observed price gap of 5.8.
Mechanism and magnitude agree from independent directions, which is the
strongest evidence in this file that the effect is real rather than a
coincidence of the sample.

It is also milk-specific: wool (p=0.16) and strawberry (p=0.78) show
nothing, exactly as expected, because milk has the steepest price
sensitivity of the high-volume goods.

**What this gives Agent E.** A concrete, cheap, market-side rule --
condition milk sales on `observation["market"]["inventory"]["MILK"]`
rather than selling blind. It costs no worker turns, so it cannot harm
throughput, and it targets the one behaviour that measurably separates
winners from losers among strong players.

Two cautions carried forward. Section 9j's price-floor throttle, which
withheld sales on a *price* threshold with cash and shed guards, cost
12-16k coins -- withholding must never starve the logistics that clear
the shed and fund feed. And that experiment was scored against frozen
tape opponents, which cannot compete for market space the way a live
opponent does, so it does not settle the inventory-conditioned rule
proposed here.

### 9s. The price edge scales with rank, but resists being turned into a
rule (2026-09-05)

Section 9r found winners are paid more for identical output. This asks
whether that skill also describes *climbing*, and then tries to build it.

**It is the single largest behavioural gap between rank bands.** Forty
teams with five or more games each, 851 games, leaderboard 2029-3021,
aggregated per team:

| feature | corr with LB | top (>=2850) | mid (2300-2600) | delta |
| --- | ---: | ---: | ---: | ---: |
| price_WOOL | -0.04 | **73.1** | **26.5** | **+46.5** |
| price_MILK | **+0.184** | **53.5** | **41.9** | **+11.6** |
| invsale_WOOL | +0.08 | **10,041.5** | **10,053.9** | **-12.4** |
| invsale_MILK | **-0.184** | 10,050.9 | 10,056.3 | **-5.5** |
| units_WOOL / units_MILK | ~0.00 | — | — | unchanged |
| reward | +0.06 | 88,397 | 78,424 | +9,973 |
| hires | +0.318 | 290 | 287 | +3 |
| cow | -0.154 | 8 | 9 | -1 |

Top teams get **2.8x the price per wool unit and 28% more per milk unit
for the same volume sold**, and they sell at systematically lower market
inventory. The direction matches 9r exactly, on a different question and
a different slice of the data.

**A real calibration bug, found here.** Section 9j's glut-deferral used a
threshold of **10,500**. Actual market inventory only moves through
roughly **10,040-10,060**, so that rule could never fire -- which is
exactly what its 0/80 result showed, and the reason was a mis-scaled
constant rather than an absent mechanism. `rl/sell_gate.py` now carries a
test asserting the thresholds sit inside the measured band so this cannot
regress.

**But the rebuilt, correctly-calibrated gate still does not pay.** Holding
gated sales while inventory is above the measured band, with cash, shed,
terminal and patience guards, over 24 games against three opponents:

| configuration | mean coins | floor | wins |
| --- | ---: | ---: | ---: |
| Candidate D, no gate | **128,970** | **96,086** | 16/24 |
| gate WOOL>10046 + MILK>10052 | 121,950 | 86,846 | 16/24 |
| gate WOOL only | 122,594 | 86,908 | 16/24 |
| gate MILK only | **128,064** | 95,984 | 16/24 |
| tighter thresholds | 121,985 | 86,843 | 16/24 |

Wool gating is the damage (-6,376 on its own); milk gating is roughly
neutral (-906). No configuration changed the win count at all.

**Two honest readings, and I cannot yet separate them.**

1. *The local benchmark cannot test this mechanism.* Frozen tape opponents
   sell on a fixed script and never compete for market space, so waiting
   for a quieter market cannot pay against them by construction. Section
   9m established these panels mislead about live strength; this is
   plausibly another instance.
2. *The winners were never waiting.* Their milk may simply arrive at
   quieter moments as a by-product of when animals were placed. Testing
   that over 140 paired games: winners place cows earlier on median
   (p=0.041) and their first sheep later (p=0.010), with cow and sheep
   counts unchanged. Both are modest, and with seven comparisons in that
   family neither clearly survives a multiple-comparison correction, so
   this is a lead rather than a finding.

**Standing conclusion.** The price-realisation edge is the best-evidenced
thing this project has found about strong play -- it replicates across
winner-versus-loser pairs, across rank bands, and its magnitude is
independently predicted by the simulator's own pricing constants. It has
so far resisted every attempt to convert it into a sell-side rule. The
next test should be production-side (animal placement schedule) rather
than sale-side, and it needs an evaluation that reactive opponents can
participate in, because the tape panel cannot decide this question.

`rl/sell_gate.py` is kept, tested and **not wired into any candidate**.

### 9t. Games are decided late, and by very little (2026-09-06)

Money is observable every step, so the winner's lead can simply be
watched rather than reconstructed from prices and costs. Across 140
paired games, tracking `farms[player].money` for winner and loser:

| step | median winner lead | share of final margin | eventual winner ahead |
| ---: | ---: | ---: | ---: |
| 72 | 0 | 0.0% | **40.0%** |
| 144 | 0 | 0.0% | 41.4% |
| 216 | 12 | 0.2% | 56.4% |
| 360 | 120 | **2.5%** | 56.4% |
| 432 | 1,224 | 25.3% | 63.6% |
| 504 | 1,986 | 41.0% | 72.1% |
| 576 | 2,657 | 54.8% | 75.7% |
| 648 | 3,978 | **82.1%** | 87.9% |
| 719 | 4,845 | 100% | 100% |

**Two facts that should govern where effort goes.**

*The game is decided in its second half.* At the halfway mark the eventual
winner is ahead by 2.5% of the margin they will finish with, and in the
opening they are behind more often than not -- at step 72 the eventual
winner leads in only 40% of games. About 97.5% of the final margin forms
after halfway and roughly three quarters of it in the final third. Opening
and setup optimisation therefore has very little leverage, which
retrospectively explains why the animal-placement leads in 9s were so
weak: they are early-game decisions in a late-game contest.

*The margin is small.* The median winning margin is **4,845 coins against
rewards near 85,000** -- games are decided by about 5.7% of final money.

**This recalibrates every result in sections 9j-9s.** An edge worth ~1,500
coins is not marginal here, it is about a third of a typical winning
margin: the milk price effect in 9r (5.8 coins/unit across ~271 units,
~1,570 coins) is materially sized after all. Equally, the sell gate's
-7,000 in 9s was not a small regression but roughly 1.4 entire winning
margins of self-inflicted damage, which is why it read as so decisively
bad.

**Consequences for Agent E.**

1. Spend effort on steps ~430-719. That window contains three quarters of
   the decided margin, and it is wider than Candidate A's terminal
   liquidation window (700+), so most of it is currently unmanaged.
2. Judge candidate mechanisms against the 4,845-coin yardstick rather than
   against total reward. A change worth 1,000-2,000 coins is a real
   contender; one costing 7,000 is disqualifying.
3. Stop investing in opening/setup tuning until something specific
   justifies it.

### 9u. Town demand is random per game, observable, and barely exploited
(2026-09-06)

Every earlier section treated the market as a price curve. It is not --
there is a demand engine underneath it that this project had never
opened, and it is the largest unexploited edge found so far.

**How demand actually works** (`_town_consume`, `kaggriculture.py`):

* Every `townShopSellInterval` (4) steps, **each unlocked shop instance**
  removes one unit of each product it sells. Shops selling a single
  product remove **two** -- that is `YARN_STORE` (WOOL) and `PET_CAFE`
  (CARROT).
* Every `townCenterSellInterval` (24) steps the town centre removes one
  unit of every product **except FERTILIZER**.
* A shop unlocks every few days, **drawn at random with replacement**
  from the eight types, capped at `MAX_SHOP_INSTANCES` = 8. Observed
  unlock days: 3, 6, 9, 12, 15, 18, 21, 24.

Two consequences follow immediately. Demand is **fully determined by
`observation["town"]["unlocked_shops"]`**, so it can be computed exactly
rather than estimated. And because the draw is random with replacement,
**every game has a different demand profile** -- a game may unlock
`YARN_STORE` twice and consume 4 wool per event, or never unlock it and
consume wool only from the town centre.

**The model reproduces reality.** Predicted total drain against measured
drain over 60 games:

| item | predicted | actual | ratio |
| --- | ---: | ---: | ---: |
| MELON | 30 | 30 | **1.00** |
| WOOL | 390 | 384 | **0.99** |
| MILK | 570 | 520 | 0.91 |
| STRAWBERRY | 750 | 584 | 0.78 |
| WHEAT | 930 | 570 | 0.61 |
| FERTILIZER | 0 | 74 | — |

It is exact where supply meets demand and predicted-above-actual where
players simply do not grow enough to satisfy the town, which is the
correct reading: predicted is demand *capacity*, actual is
min(demand, supply). MELON matching at 1.00 is the sharpest confirmation
-- melon appears in **no shop at all**, so its only demand is the town
centre's 30 units, and that is exactly what drains. FERTILIZER is in no
shop and not a town-centre product, so it has **zero** natural demand;
every unit sold sits in the market permanently depressing its price.

**The price consequences are enormous.** Splitting games by whether an
item's shop demand is above or below median, and comparing its
end-of-game price:

| item | low-demand games | high-demand games | swing |
| --- | ---: | ---: | ---: |
| **WOOL** | 24.0 | **242.5** | **10x** |
| **MILK** | 3.0 | **122.0** | **40x** |
| STRAWBERRY | 41.0 | 192.0 | 4.7x |
| TOMATO | 79.0 | 216.0 | 2.7x |
| CARROT | 43.5 | 63.5 | 1.5x |
| EGG | 59.0 | 69.0 | 1.2x |
| WHEAT | 34.0 | 43.0 | 1.3x |

Whether wool is worth 24 or 242 a unit is decided by a random draw the
agent can *see*, from day 3 onward.

**And the field barely responds.** Correlation between a game's demand
for a product and how much of it that player produced, across 180
player-games:

| adaptation | correlation |
| --- | ---: |
| wool demand -> sheep bought | +0.388 |
| milk demand -> cows bought | +0.194 |
| **strawberry demand -> strawberry planted** | **+0.065** |

Partial at best, and essentially absent for strawberry. Winners adapt
harder than losers -- wool demand to sheep is **+0.497 for winners
against +0.276 for losers** -- which is the first evidence in this file
that *adapting to demand is itself a winning behaviour* rather than a
theory. Milk demand alone correlates +0.322 with reward.

**Why this matters more than anything in 9j-9t.** Every candidate this
project has shipped -- A, B, C1, C2, D -- is a frozen tape or a fixed
schedule. None of them can read `unlocked_shops`, so none can respond to
a 10x swing in what their produce is worth. That is not a tuning gap, it
is a structural one, and it is exactly the kind of edge a clone can never
capture no matter which replay is cloned.

**This is Agent E's core mechanism.** Read the unlocked shops, compute
exact per-product demand, and steer production and sale priority toward
what this particular town actually wants. The signal arrives by day 3 and
is largely complete by day 15; wheat cycles in ~5 days and animals yield
4-8 days after placement, so there is real time to act. Strawberry is the
most attractive first target: its price swings 4.7x, and the field's
adaptation to it is +0.065 -- effectively uncontested.

### 9v. Adapting to demand is what the top does -- and a tape cannot do it
(2026-09-06)

Section 9u showed town demand is random per game, observable, and swings
prices up to 40x. This section asks who exploits it, what it is worth,
and whether our existing architecture can be made to.

**Adaptation is the cleanest correlate of rank in this whole file.**
Correlation between a game's demand for a product and how much of it the
player produced, split by leaderboard band, 300 player-games:

| band | wool -> sheep bought | milk -> cows bought | strawberry -> planted |
| --- | ---: | ---: | ---: |
| **TOP (>=2850)** | **+0.672** | **+0.339** | **+0.309** |
| MID (2400-2849) | +0.323 | +0.319 | +0.123 |
| **LOW (<2400)** | **+0.000** | **-0.046** | **-0.086** |

A clean monotonic gradient. The top of the ladder steers production at
the demand draw; the middle does it weakly; below 2400 there is no
response at all. This is the first measurement in this file that explains
the ladder rather than describing it -- and it says the demand engine is
not undiscovered, it is *what being good at this game consists of*.

**What adaptation is worth, ranked properly.** Section 9u picked
strawberry because it was uncontested, which is the wrong criterion.
Ranking by expected value -- the price gap between high- and low-demand
games times the volume actually achievable:

| target | low-demand price | high-demand price | typical units | EV |
| --- | ---: | ---: | ---: | ---: |
| STRAWBERRY | 37 | 178 | 270 | **38,070** |
| WOOL | 1 | 239 | 154 | **36,652** |
| MILK | 5 | 110 | 271 | 28,455 |
| TOMATO | 77 | 202 | 144 | 18,135 |
| EGG | 59 | 70 | 64 | 704 |
| CARROT | 45 | 66 | 18 | 387 |

Strawberry and wool are effectively tied at the top; carrot and egg are
near-worthless targets despite carrot's scarcity premium, because the
volumes are tiny. For scale, section 9t measured the median winning
margin at 4,845, so the leading targets are several margins wide.

**A frozen tape cannot be retrofitted to do this. Demonstrated, not
asserted.** COW and SHEEP looked like the ideal substitution: both occupy
a PASTURE tile, both are placed with PLACE, both accept FEED and CARE,
both are collected with HARVEST. Rewriting `BUY_ANIMAL COW` to SHEEP and
the matching placements should therefore change *what the farm produces*
while leaving geometry, routing and service schedule untouched.

It failed, three times, each for a different structural reason:

1. **Per-worker inventory.** The first version checked whether *any*
   worker held the animal and rewrote placements globally, so it
   redirected a PLACE for a worker who was not carrying it. Result: 9 of
   17 animals placed, 7 pastures permanently empty, reward 117,133 ->
   63,035 and wins 40/48 -> 4/48.
2. **Animals live in the shed.** `BUY_ANIMAL` deposits into
   `private["shed"]`, so the real route is buy -> **PICKUP** -> PLACE.
   Rewriting the purchase without the PICKUP left workers asking for an
   animal that was no longer there. Fixing that recovered 2 of the 7 lost
   pastures.
3. **Cash coupling, which is fatal.** Sheep cost 500 against a cow's 400.
   The tape's purchase schedule is tuned to its own cash trajectory with
   no slack: tracing a swapped game shows money at **39** at step 185 and
   **1** at step 204, where a `BUY SHEEP x2` needing 1,000 simply fails.
   Five pastures stay empty for the rest of the game.

So the tape's actions are coupled through cash, shed capacity and pickup
timing, not just through tile geometry. Even the most surgical
substitution available in this game breaks it. **This closes off the
tempting shortcut of bolting adaptation onto a clone**, and it explains
mechanically why every candidate we have shipped scores +0.000 on the
adaptation gradient above.

**Conclusion for Agent E.** E has to generate its own actions. Adaptation
cannot be a layer over a recorded route, because the recorded route's
affordability is part of what was recorded. The demand model itself is
built and tested (`rl/demand.py`, 15 tests) and is the piece worth
keeping; `rl/herd_swap.py` is retained as the evidence for this section
and is wired into nothing.

### 9w. Candidate E, first build: a working skeleton, not a contender
(2026-09-06)

Section 9v concluded E must generate its own actions. This is that build,
reported honestly: it plays complete legal games and it adapts to demand,
but it earns **1,153 coins against Candidate D's 107,115** on the same
seeds and opponent. It is a foundation, not a submission, and D remains
the agent to ship.

**What is built and works.**

* `rl/economics.py` (27 tests) prices any job in coins from the
  simulator's own constants.
* `rl/demand.py` (15 tests) computes exact per-product town demand from
  `unlocked_shops`, and picks the herd this town actually rewards.
* `rl/candidate_e.py` schedules every worker each turn by coins per turn
  including travel, and generates its own market orders. It completes
  720-step games with zero errors in both seats, buys land, hires, plants,
  waters, harvests and banks goods.

**What does not work, and why it is instructive.** A pure greedy
marginal-value scheduler turned out to be unstable, collapsing into a
different degenerate mode after each fix:

| version | behaviour | reward |
| --- | --- | ---: |
| first build | goods harvested but never banked -- `DROP` was only a fallback, so nothing reached the shed to be sold | 1,685 |
| after adding DROP/PICKUP as scored jobs | 327 pickups against 323 drops -- a worker banked fertilizer, then immediately valued picking it back up | 208 |
| after excluding working stock from bankable value | ran out of seeds, 1,559 idle turns | 4,058 |
| after buying seeds wide | built 14 pastures it could not stock, spending the purse that should have bought land and animals | 395 |
| after gating pens on affordability | stable, but the herd never starts | 1,153 |
| after pricing a rescue watering at the plant's whole remaining crop | watered all game, banked nothing | **0** |

The last one is the general lesson and is now a comment in
`rl/economics.py`: **job values in a greedy scheduler have to stay
commensurable.** A rescue priced at "the entire remaining plant" dwarfs
every harvest priced at "the units currently in hand", so the agent
becomes monomaniacal and stops finishing the loop that turns crops into
money. Greedy value maximisation needs either normalised values or an
explicit planner that reserves capacity per job class; that is the next
architectural step, not more constant-tuning.

**Why this was still worth doing.** The two libraries are the durable
part and both are measured, not guessed. And the failure modes above are
exactly the couplings section 9v predicted -- cash, shed capacity, working
stock, and pen-versus-animal ordering -- now demonstrated from the inside
of an agent that owns its actions rather than from outside a tape.

**Status: E is not a candidate.** It is committed, tested and wired into
no submission. Candidate D (episode 105520725) is live and unchanged, and
its seven pre-flight gates still pass.

## 10. AGENT E -- ENGINEERING HANDOFF

**Read this section before touching Agent E.** It is written for someone
picking the work up cold. It states what exists, what every number is,
what was tried and failed, and what to do next. Nothing here needs to be
re-derived; where a claim came from a measurement, the measurement is
named.

### 10.1 One-paragraph summary

Agent E is a from-scratch agent that generates its own actions instead of
replaying a recorded game, and prices every decision against the
simulator's own market curve. It plays complete legal 720-step games in
both seats with zero errors.

**On 72 held-out games -- three opponents, twelve seeds, both seats,
none of them used for any tuning -- E earns 64,407 mean with a 35,261
floor and wins 4, against Candidate D's 87,730 / 48,748 / 55.** It sits
at 73% of D, up from 33% at the start of the 2026-09-06 session. On the tuning seeds
(0-5) it earns 57,827 against D's 89,401; the gap between the two is
honest overfit and the held-out number is the one to quote.

E still wins no games against elite opposition where D wins 37 of 48, so
**Candidate D (episode 105520725) remains the live agent** and must stay
that way until E beats it on measured evidence.

The 2026-09-06 session took E from 28,763 to 50,437 on held-out games
(+61%) by finding real defects, not by tuning: see 10.5 phase three,
10.11 for the simulator mechanics that drive them, and 10.12 for the
market model that reframed the whole strategy.

### 10.2 Why E exists at all

Cloning is capped, and the cap is measured, not assumed:

* We cloned "fog flower" at public score 2882 and the resulting agent
  settled at **2094.7** live. A frozen tape discards the reactivity that
  earned the source its score (section 9m).
* Reaching the top ten by cloning would need a source near 3700; the
  ladder's best is 3021. **Cloning cannot pass ~2100 for us**, which is
  where C1 and D both sit.
* The behaviour that separates the ladder is adapting production to the
  town's random demand draw. Correlation of demand-to-production, by rank
  band, 300 player-games (section 9v): **+0.672** for teams at 2850+,
  **+0.323** for 2400-2849, **+0.000** below 2400. A frozen tape scores
  structurally zero, which is why every candidate we have shipped sits in
  the bottom band behaviourally.
* Retrofitting adaptation onto a tape was tried and is impossible: a
  tape's actions are coupled through cash, shed space and pickup timing.
  Swapping a cow for a sheep (identical tile, identical PLACE/FEED/CARE/
  HARVEST) still broke it, because sheep cost 500 against a cow's 400 and
  the tape's purchase schedule has no cash slack -- a trace showed money
  at 39 by step 185 and 1 by step 204, and five pastures stayed empty for
  the rest of the game (section 9v).

So E must own its actions. That conclusion is demonstrated, not
preferred.

### 10.3 The measured facts E is built on

Do not re-litigate these; they are the load-bearing results.

| fact | value | source |
| --- | --- | --- |
| Town demand is deterministic and observable | every 4 steps each unlocked shop removes 1 unit of each product it sells (2 if the shop sells only one), every 24 steps the town centre removes 1 of everything except FERTILIZER | 9u |
| Shops unlock at random with replacement | one every ~3 days, capped at 8, visible in `observation["town"]["unlocked_shops"]` | 9u |
| Demand swings prices enormously | WOOL ends at 24 or 242, MILK at 3 or 122, STRAWBERRY at 41 or 192 depending on the draw | 9u |
| The demand model is exact | predicted vs actual drain: MELON 30/30, WOOL 390/384, MILK 570/520 | 9u |
| MELON is in no shop | its only demand is the town centre's ~30 a game, so melon is capped however much is grown | 9u |
| FERTILIZER has zero natural demand | in no shop, not a town-centre product; every unit sold permanently depresses its price | 9u |
| EV of steering toward a product | STRAWBERRY 38,070, WOOL 36,652, MILK 28,455, TOMATO 18,135, EGG 704, CARROT 387 | 9v |
| Games are decided late | ~97.5% of the winning margin forms after halfway, ~75% in the final third | 9t |
| Winning margins are small | median **4,845** coins on rewards near 85,000 | 9t |
| Local tape panels mislead | they overstate live win rate by roughly 40 points | 9m |
| Three quadrants, never four | 4-quadrant players win 8.3% against 51.2%; the top 500 use three essentially always | 9i |
| Winners grow feed rather than trade it | they sell less wheat and buy less of it (p=0.031) | 9m |

**The 4,845-coin yardstick is the one to judge changes against.** A
mechanism worth 1,000-2,000 coins is a genuine contender; one costing
7,000 is disqualifying.

### 10.4 What is built, file by file

**`rl/market.py` -- what a unit will actually fetch (18 tests,
`tests/test_market.py`)**

The simulator's own price curve, transcribed. `price_at`, `sale_revenue`
(which walks the price down unit by unit, and takes a `sold_already`
offset so production can be valued at the margin), `marginal_price` and
`headroom`. This is the module that reframed E's whole strategy; read
10.12 before using it.

**`rl/economics.py` -- job pricing (27 tests, `tests/test_economics.py`)**

Prices any farm action in coins using constants transcribed from the
installed simulator. This is the piece to trust and reuse.

* `water_value` -- one yield unit inside the crop's window, two if
  fertilized; zero once the tile is full or the crop cannot mature.
* `fertilize_value` -- the extra units its three-day window can still
  boost, **minus** what the unit would have fetched if sold.
* `harvest_value` -- units on the tile at the live price, for crops and
  animals alike.
* `feed_value` -- the whole remaining production stream when an animal is
  one day from bolting, a fraction otherwise.
* `care_value`, `collect_fertilizer_value`, `plant_value`.
* `crop_can_mature` -- the strawberry question: a crop whose first yield
  lands after day 29 is worth nothing, so no effort spent on it is
  justified.

**`rl/demand.py` -- town demand (15 tests, `tests/test_demand.py`)**

* `SHOPS` -- the eight shop types and what each consumes.
* `shop_demand_per_event`, `demand_rate`, `remaining_demand` -- exact
  per-product demand from the live observation.
* `preferred_animal` -- which pasture animal this town rewards, requiring
  a margin so a near-tie changes nothing.

**`rl/candidate_e.py` -- the agent**

Per turn: parse the farm, choose the herd (`preferred_herd`) and a crop
ranking weighted by remaining demand (`crop_ranking`), enumerate every
job every worker could do on every owned tile, score each as
`value / (travel + 1)`, assign greedily with a `claimed` set so two
workers do not target one tile, then emit market orders (hire toward 11
hands, buy land to three quadrants, buy seeds wide, buy the preferred
animal, reserve wheat for feed, sell the rest).

**Not wired into anything, kept as evidence:**

* `rl/sell_gate.py` (12 tests) -- gating sales on market saturation. Cost
  6-7k coins; wool gating alone -6,376 (9s).
* `rl/herd_swap.py` -- demand-driven cow/sheep substitution over a tape.
  Broke the tape three ways (9v).
* `rl/idle_work.py` (10 tests) -- converting idle turns to fertilize or
  water. Worth +265 coins, +0.27% (9o).

### 10.5 Every result E produced, in order

**Phase one -- getting it to run at all** (single opponent, three seeds):

| build | change | reward | what broke |
| --- | --- | ---: | --- |
| 1 | first working version | 1,685 | goods harvested but never banked; `DROP` was only a fallback |
| 2 | DROP/PICKUP added as scored jobs | 208 | **327 pickups against 323 drops** -- banked fertilizer, then instantly re-valued picking it up |
| 3 | working stock excluded from bankable value | 4,058 | ran out of seeds; **1,559 idle turns** |
| 4 | buy seeds for the top three crops | 395 | built **14 pastures it could not stock** |
| 5 | pens gated on affordability | 1,153 | stable, but the herd never started |
| 6 | rescue watering priced at the whole remaining crop | **0** | watered all game, banked nothing |

**Phase two -- making the economy work.** Every one of these was found by
watching the money curve or the action mix, never by guessing:

| fix | reward | the defect |
| --- | ---: | --- |
| lower the seed threshold | 35 | seeds gated behind 300 coins, so E never planted, never earned, never reached 300 -- money frozen at 236 from step 24 to 288 |
| rank crops by coins per **tile-day** | 12 | gross value bought strawberry and melon seeds at 100 and 80, spending 2,967 of the 3,000 opening in three steps |
| **rewrite the market as one ordered budget** | 1,330 | independent per-line thresholds deadlocked repeatedly; priority order over a shared running balance fixed it |
| **sell first, not last** | **5,930** | selling ran last under a ten-order cap and was crowded out: **1,506 harvests produced 76 units sold**, the shed overflowing its 100 cap and discarding the rest |
| **capacity-reserving planner** | **19,470** | rescue work cannot win a value auction without turning monomaniacal; reserved capacity (45% cap) fixed both failure modes at once. Task share 0.513, idle turns 9 |
| **reprice early harvest** | 24,229 | the simulator destroys a non-ongoing plant on harvest, so picking wheat at 1 unit when it could reach 6 throws 5 away. E harvested 1,714 times for 0.2 units each against the tape's 450 for 4.75 |
| **price fetching feed at what feeding preserves** | 37,324 | a flat 45 lost every auction, so nobody carried wheat; animals fed 84 times against the tape's 384, the herd bolted, and **zero milk or wool sold all game** |
| **weight time-to-first-cash while cash is thin** | **38,099** | melon tops the per-tile-day ranking at ~118 but first yields on day 10; planting it holding 30 coins froze the purse for ten days. Herd went from 3-6 animals to 9-15 |
| reserve 70% of labour for watering | 31,555 | **rejected** -- over-reserving starves harvesting and logistics; 45% stays |

Those single-opponent figures are optimistic. On the fair 18-game panel
that configuration measured **29,161 against D's 136,074**.

**Phase three -- 2026-09-06.** Measured on a fair panel of 36 games
(3 opponents x 6 seeds x both seats) unless stated. Every one of these
was a defect found by instrumenting the agent or reading the simulator,
not a constant that was tuned:

| fix | mean | the defect |
| --- | ---: | --- |
| baseline at session start | 28,763 | -- |
| feed priced at the escape loss, not the product's spot price | 31,242 | milk and wool bottom out at 1 coin, so feeding looked worthless; E fed its herd 188 times where it needed 450, bought 31 animals and finished with 18 |
| **harvest prices the growth it forfeits, exactly** | 35,904 | on the last day of a crop's window HARVEST and WATER were priced identically, an exact tie, and the scheduler took the harvest -- so **every carrot in a game was picked holding one unit of a possible four** |
| seed reserved across workers within a turn | +4,200 | the seed store is shared, so all twelve workers independently planned to plant the same single seed: **215 PLANT actions for one crop**, all but a handful no-ops costing a worker-turn each |
| HARVEST blocked before `first_yield_day` | -- | the simulator refuses it and still charges the turn; melon accrues units from age 6 but cannot be picked until age 10, so workers parked on melons harvesting nothing -- **659 wasted worker-turns in one game** |
| **herd capped at what the standing wheat can feed** | 37,756 | on one seed E sold its melon crop on day 11, spent every coin of it on eleven cows inside two turns, then had neither wheat nor money: herd 11 to 0 by day 15, all 34 plants weeded, **game ended on 485 coins** |
| **travel discounted by the square of distance** | 45,934 | `value / distance` rates a 600-coin job eight tiles away above a 100-coin job next door; E walked 2.0 steps per task against a good route's 0.94. Floor went from 673 to 14,417 |
| crew re-hired on the closing day too | 48,704 | hands are wiped every night, and the early-return that skipped last-day purchases skipped the hire with them, leaving the farmer to work day 29 alone |
| seed spend capped at 15% of the purse, crew at 9 | **57,827** | see 10.13 |

**Held-out check.** The same configuration on seeds 6-13, 48 games never
used for tuning: **50,437 mean, 21,393 floor, against 31,336 / 12,719 for
the session's starting version.** D scores 88,863 / 48,748 there.

### 10.6 The central lesson, and the reason for the next step

Build 6 is the important one. Pricing a rescue watering the way a
starving animal is priced -- at everything it would still produce -- took
reward to exactly zero. The rescue value then dwarfed every harvest
priced at "units currently in hand", so workers watered constantly and
never completed the loop that turns crops into money.

**Job values in a greedy scheduler must stay commensurable.** A pure
greedy argmax over heterogeneous job types is unstable here: whichever
class is priced highest absorbs all labour, and the agent becomes
monomaniacal. Every one of the six builds above is a version of that
failure. More constant-tuning will keep producing new degenerate modes.

### 10.7 The plan -- what to build next, in order

**Step 1. DONE -- the capacity-reserving planner is built.** Rescue work
(at-risk plants, starving animals) gets reserved labour up front, capped
at `RESCUE_SHARE = 0.45` of the crew; everything else competes on
`value / (travel + 1)`. This took reward from 5,930 to 19,470 and solved
the throughput problem outright. **Do not raise the share to 0.70** --
that was tried and cost about 6,500 coins by starving harvesting.

**Step 2. DONE -- the opening no longer deadlocks.** E reaches three
quadrants and 9-15 animals on every seed.

**Step 2b (do this next). Grow the herd and the planted area.** This is
now the largest revenue gap. E peaks near 47 plants against the tape's 58
and 9-15 animals against 17, and the tape sells 389 wool and 347 milk
where E sells a fraction. Start by asking why pasture building stops:
`TARGET_PASTURES` is 14 but E builds 6-8, and the `pastures <=
animals_now + 1` guard may be too conservative once cash is healthy.
Historical note kept because it explains the guard: E used to stall at one
quadrant and no animals because it never accumulated cash. Instrument the first 150 steps
against Candidate D's money curve and fix the opening explicitly: hire
early (hands are priced by a fibonacci with multiplier 1, so early hands
are nearly free), plant wheat immediately (2-day first yield, replantable
about every 5 days, 6 units when fertilized), and get to three quadrants.
Do not build a pasture before the animal for it is affordable -- that was
build 4.

**Step 3. DONE -- the throughput gap is closed.** E's task share is
**0.513** against the reference tape's 0.493, with 9 idle turns against
322; the old reactive engine sat at 0.26. Do not spend more effort here.
Historical note: a tape spends 49% of worker-turns on tasks and the old
engine 26%, burning 1,250 more turns walking and 663 more idling (9q). The probe used for this lives in the session scratchpad as
`exec_gap.py` (task/move/idle counts, coins per task-turn) and is worth
re-creating as a committed tool.

**Step 4. Only then turn on demand steering.** The libraries are ready.
Expect the gain to be real but second-order compared with steps 1-3: a
correct product mix on a farm that produces nothing is worth nothing.
Targets ranked by EV are in 10.3; strawberry and wool lead and are
effectively tied.

**Step 5. Build an evaluation reactive opponents can participate in.**
This is the missing instrument. Frozen tapes sell on a fixed script and
never compete for market space, so they cannot settle any market-timing
question -- that is why the sell gate's result is uninterpretable. Until
this exists, treat every sell-side result as unproven.

### 10.8 Dead ends -- do not repeat these

* **Sale gating on market saturation** -- -6,376 to -7,020 coins; wool
  gating is the damage, milk roughly neutral (9s).
* **Withholding sales on a price floor** -- -12,466 to -16,570; those
  cheap sales are logistics, clearing the 100-unit shed and funding feed
  (9k).
* **Deferring sales to await a price recovery** -- dips do not
  mean-revert: 0.1% of MELON dips recovered within 10 steps, mean drift
  negative (9j).
* **Eager or accelerated selling** -- -448 to -585 (9k).
* **A C1/C2 route selector** -- a perfect selector is worth **+2 games in
  80** (9k).
* **Buying the fourth quadrant** -- 8.3% win rate against 51.2% (9i).
* **Retrofitting adaptation onto a tape** -- broken by cash, shed and
  pickup coupling (9v).
* **Configuration search over the old reactive engine** -- its fertilizer
  and feed flags are inert in the high-utilisation config, producing
  byte-identical output, and holding fertilizer collapses it to 2,642
  (9v).

### 10.8b Dead ends from 2026-09-06 -- measured, do not repeat

Each of these was a reasonable idea, tested on the same 36-game panel,
and lost. They are recorded with their numbers so nobody spends another
session on them.

| idea | result | why it fails |
| --- | ---: | --- |
| **A herd of geese only** | 16,551 against 26,049 | eggs are the only product whose price never collapses, and every real game ends 150-300 units *below* equilibrium on egg at 59-68 coins, so this looked like the strongest idea of the session. It only pays for an agent that can keep a large herd fed and cared for every day; E cannot yet, and an under-tended goose yields one egg where a cow yields a premium product. Revisit **only** once feeding is reliable |
| Hold fertilizer back to spread on the fields | 14,200 against 26,300 | correct on paper -- a unit fetches 36-53 sold against roughly 129 as extra wheat -- but E is capital-starved for three weeks and the cash the held stock did not raise is cash it cannot spend on animals. The herd fell from 11.4 head to 3.8 |
| Rank crops by true marginal revenue | 22,021 against 30,067 | the more correct model, and it loses. It is right about the season; a hand-to-mouth agent needs a model that is right about tomorrow. The `payback` ranking stays default, `marginal` is kept behind `RANKING_MODE` for when E has working capital |
| Stop rescue-watering plants with no yield left | 26,890 against 31,242 | a spent plant left to die becomes a weed that holds the tile and costs a DIG to clear; keeping it alive is cheaper than that |
| Buy land on crew capacity rather than spare ground | 22,171-25,568 against 31,242 | buying the second quadrant early starves seed and livestock; land has to come out of surplus |
| Crews of 13, 15, 17 | 41,926 / 1,309 / 1,022 | hands are re-hired **every day**, so the 10th through 14th cost 55+89+144+233+377 coins *daily*. A crew of 9 beat 11 and 13 |
| Travel priced as `value - cost * distance` | 32,863 at best | too blunt; the square-of-distance discount is much better (10.11) |

### 10.8c The demand engine does not pay on a strong route (2026-09-07)

This is the most important negative result in the file, because the whole
plan for Agent E after section 9v rested on the opposite. Four independent
forms of demand steering were built and measured on **48 held-out games**
-- three opponents, seeds 6-13, both seats -- against Candidate D:

| layer | mean | vs D |
| --- | ---: | ---: |
| **D, unchanged** | **88,863** | -- |
| D + herd swap (`rl/herd_swap.py`) | 88,756 | -107 |
| D + demand-driven herd *ratio* tilt | 88,996 | +133 |
| D + sell gate (`rl/sell_gate.py`) | 83,609 | **-5,254** |
| D forced to an all-sheep herd | 73,153 | **-15,710** |
| D forced to an all-cow herd | 63,992 | **-24,871** |

**Why, and this is the part worth keeping.** The tape's recorded herd is
already *six cows and eleven sheep*. Wool falls to a single coin once
about 59 units have been sold into it and milk once about 76 have, so a
seventeen-head herd pouring everything into one product destroys that
product's price. Two half-sized streams sell into two separate curves and
both stay near the top of theirs. **Diversification, not demand-matching,
is what this market rewards** -- and the elite human whose game the tape
records already diversifies.

That reframes 9v. The correlation it measured between a top team's herd
and the town's demand is real, but it is not a lever: strong players
diversify, and diversification correlates with demand-matching without
being caused by it. Steering the herd toward the demanded product gains
+133 coins over 48 games, which is a fortieth of the 4,845-coin median
winning margin -- indistinguishable from nothing.

The herd swap fires in only **3 of 48 games** even when unblocked, and the
sell gate fails for the reason its own docstring predicts: withholding
sales starves the purchases the sales were funding.

**Do not spend another session on demand steering as a bolt-on.** If it
has value anywhere it is inside an agent that chooses its own production
from scratch, where the herd size and the crop mix are still free
variables -- which is Agent E, not a wrapper on a tape.

### 10.8d Four more measured dead ends on E (2026-09-07)

All on the same 48 held-out games, against E's 50,437 baseline.

| idea | result | why it fails |
| --- | ---: | --- |
| **Per-worker zones** (contiguous row-major bands, one per hand) | 37,192 | the clear loser of the day. Bands cut across the shed and trap a worker in a strip with nothing to do; the herd collapsed from 12.3 head to 5.2. A better zoning might still work, but not this one |
| Gentler travel discount for herd work (exponent 1.0 instead of 2.5) | 41,447 | E visits each animal ~10 times in 25 days against a good route's daily, so this looked certain. Pulling workers to distant pens starves the watering, and a weeded plant costs more than a missed collection |
| Two-tier ranking: idle workers re-rank with distance barely discounted | 49,815 | E idles 4,709 worker-turns a game, so converting them looked free. It is not -- those turns are idle precisely because everything reachable is far, and walking five tiles does not pay. The idleness is a symptom of a thin farm, not a scheduling bug |
| Liquidity floor at 0 / 400 / 3000 (controls how much slow crops are penalised while cash is short) | 51,549 / 52,708 / 49,250 | all inside noise; the heuristic is not what keeps E off strawberry |

**What the same measurement did establish.** E realises far better prices
than D on every shared product -- wool 243 a unit against 34, milk 197
against 92, strawberry 144 against 69 -- because it sells smaller
quantities earlier into an uncrowded market. Its entire deficit is
**volume: 1,957 units a game against D's 6,414**. Throughput, not pricing,
is the whole remaining gap, and throughput is routing: E walks 1.55 steps
per task where D walks 0.94.

### 10.8e The volume round: 50,437 to 61,644, and nine more dead ends

All on 48 held-out games (three opponents, seeds 6-13, both seats).
Candidate D scores 88,863 on the same panel.

**What worked.**

| change | mean | floor |
| --- | ---: | ---: |
| starting point | 50,437 | 21,393 |
| **buy the second quadrant out of the opening capital** | 56,946 | 32,779 |
| **crew back up to 11 hands** (reverses the earlier finding) | 58,535 | 37,303 |
| **travel exponent 2.5 -> 3.0** | **61,644** | 32,075 |

The opening-land change is the one to understand. A day-by-day trace
showed E working nineteen crop tiles with no animals for the first eleven
days -- a third of the season -- idling 95 to 144 worker-turns a day
because the ground it owned had no work left on it. A quadrant is 25
tiles, the pens take six, and the second quadrant costs 1,000 of a 3,000
opening. The old rule waited for 2,500 clear surplus, which never arrived,
because the farm that would have earned it was the farm being bought.

Two settings **reversed** once the board doubled: 11 hands now beat 9
(they lost by 8,000 on the small farm), and the travel discount wants to
be steeper, not gentler. Retune after any change that alters farm size.

Also fixed: five geese sat in the shed from day 21 to the end of a game,
1,500 coins and a season of production wasted, because the herd plan
changed its mind after the pens were built. Anything in the shed now gets
a pen of its own kind before anything else is raised.

**What did not work.** Nine attempts, every one measured:

| idea | result | why |
| --- | ---: | --- |
| dedicated herd crew, 2-5 hands taken off the auction | 53,110 | tried twice, before and after the farm doubled. The herd is under-served -- 230 CARE against a good route's 413 with an identical seventeen animals -- but taking hands off the fields costs more than the herd gains |
| **pen clustering**, build pens adjacent to existing pens | 54,961 | the best hypothesis of the day and it failed. Seventeen scattered pens are seventeen journeys; one block is a round. But forcing the block puts pens on ground the crops needed |
| opportunity-cost travel, `(value - cost*d) / (d+1)` | 53,837 | the principled model: a full animal is worth ~1,000 coins and a cubic discount scores it below a 28-coin watering two tiles nearer. Measured worse anyway -- **locality beats value-weighted travel**, because leaving the neighbourhood weeds the plants behind you |
| gentler travel for herd work only (exponent 1.0) | 41,447 | same lesson, larger loss |
| two-tier ranking so idle workers walk to distant work | 49,815 | E's idle turns are idle *because* everything reachable is far |
| per-worker zones (row-major bands) | 37,192 | worst of the day; bands cut across the shed |
| hold fertilizer to spread on the fields | 48,148 | re-tested in the new regime; still loses |
| marginal crop ranking / liquidity floor 0 or 500 | 53,629 / 55,380 / 55,238 | re-tested with capital available; `payback` at floor 1500 still wins |
| melon cap 6 or 20 | 52,082 / 52,830 | 12 is right |

**The remaining gap, precisely.** E's task count now nearly matches D
(3,065 a game against 3,488) and its farm matches exactly (17 animals, 18
pens, 3 quadrants, 11 hands). Two things separate them:

* **crop yield per planting: 2.3 units against 4.2.** E loses 35 plants a
  game to weeds against D's 18, and its plants do not reach full yield.
* **animal service: 230 CARE, 229 FEED, 220 COLLECT against 413, 384,
  373** -- with the same herd. A fed and cared cow yields 1.5 units a day
  and an ignored one 0.5, which is exactly the 3.2x gap in animal product
  (233 units a game against 736).

E realises *better prices than D on every shared product* -- wool 170 a
unit against 34, milk 103 against 92, strawberry 112 against 69 -- because
it sells less into an uncrowded market. Volume is the entire remaining
difference and those two numbers are where it lives.

### 10.8f Agent E is at a local optimum: 64,407, and 21 measured failures

**Where E stands.** On 72 held-out games -- three opponents, twelve
seeds, both seats, none used for tuning -- E earns **64,407 mean with a
35,261 floor and wins 4**, against Candidate D's 87,730 / 48,748 / 55.
That is up from 28,763 at the start of 2026-09-06.

Only one change landed in this round: **do not sell a unit while its
price is under 15 coins** (62,273 -> 64,407 on the wide panel, floor
32,075 -> 35,261), guarded so it never holds when cash is short, when the
shed is filling toward the 100-unit cap that discards overflow, or on the
final day. It works because selling is the one thing E already does
better than any tape -- 170 coins a unit on wool where a good route gets
34 -- and the town keeps draining the shared market all game, so a unit
held while its price is on the floor is worth more a few days later.

**Twenty-one other interventions were measured and failed.** They are
listed so the next person does not repeat them. Against the 61,644-62,273
baseline of the time:

| intervention | result |
| --- | ---: |
| dedicated herd crew (2-5 hands), tried before *and* after the farm doubled | 50,202-53,110 |
| per-worker zones (row-major bands) | 37,192 |
| pen clustering (build pens adjacent to pens) | 52,246-54,961 |
| pens near the shed, where the crew respawns each morning | 55,064-61,494 |
| gentler travel discount for herd work only | 41,447 |
| opportunity-cost travel, `(value - cost*d)/(d+1)` | 31,874-53,837 |
| two-tier ranking so idle workers walk to distant work | 49,476-49,815 |
| hold fertilizer to spread on fields (re-tested in the new regime) | 48,036-48,500 |
| the **fourth quadrant**, with and without extra hands and pens | 42,863-57,084 |
| earlier opening herd -- pen gate only, then **both** gates | 51,069-58,713 |
| goose-first opening herd (cheapest animal, fastest first yield) | 51,697-52,940 |
| fast-paying crops only in the opening (four windows) | 55,408-58,017 |
| marginal crop ranking, liquidity floors 0/500, melon caps 6/20 | 52,082-55,380 |
| crews of 13, four quadrants plus 13 hands | 42,863-49,029 |

**What the diagnostics ruled out, with numbers.** These are the reason the
list above is not worth re-running:

* **Crops are at parity.** E harvests 2.97 units per pick against a good
  route's 3.05, and takes *more* picks a game (245 against 207). An
  earlier claim of "2.3 against 4.2" was wrong -- it divided units sold by
  PLANT *actions*, which counts actions the simulator refused.
* **Animals are full only 3% of animal-days**, so "a full animal stops
  producing" is not the bottleneck.
* **Escapes are 1.5 a game** against 19 bought, and **shed overflow
  discards 1.5 units a game**. Neither is a leak.
* **Idle turns are idle because everything reachable is far**, not
  because the scheduler is confused -- which is why every re-weighting
  failed and why adding hands loses money.

**The one real gap left is animal-days: 271 a game against 396.** E has
no animals on day two where a good route has four, and nine by day twelve
where it has seventeen. Every animal-day is worth roughly 1.5 units of
produce plus a unit of manure, and that arithmetic accounts for almost
exactly the remaining difference.

**And it is not a scheduling problem -- it is capital.** Every direct
attempt to buy the herd earlier loses money, because the same coins
compound faster in land and seed first. That was tested three ways
(pen-gate floor, both-gate floor, and a cheap fast-yielding goose herd)
and all three lost. E's herd timing is the *correct* consequence of its
opening; a recorded human route reaches four animals on day two because
it is replaying a season somebody else already financed.

**So the next gain is not a constant.** A per-turn greedy auction cannot
plan an opening -- it cannot decide to under-plant on day two so that a
cow can be bought on day three. Closing the last 23,000 coins needs a
scheduler that plans a day or a week at a time, or an explicit opening
book for the first ten days. Do not spend another session on weights.

### 10.8g What the whole field actually does in its first ten days

Extracted from the cached corpus with `tools/data/extract_opening_book.py`
-- 245 real Kaggle episodes, **490 sides**, both players of each.

| by day | 1 | 4 | 8 | 10 | 2nd quadrant | 3rd |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **top 20 sides** (mean reward 141,731) | 4 animals | 5 | 10 | 12 | day 6 | day 9 |
| **middle 20 sides** (mean 77,772) | 4 | 5 | 9 | 12 | day 6 | day 10 |
| **Agent E** | **0** | **0** | **3** | **9** | day 1 | -- |

Seeds bought by day 10 are the same for both groups too: about 40 wheat,
27 strawberry, 14 melon, 2 carrot; and about 34 wheat, 24 strawberry and
12 melon actually planted, with 68 hire orders.

**The finding is that the opening does not separate strong from weak.**
The top sides and the median sides open almost identically -- it is a
solved problem the entire field has solved -- so rank is won somewhere
later. But E was behind *all* of them, standing no animals at all on day
one where every real side stands four, which is the whole of its
271-against-396 animal-day deficit.

They pay for it by spending the entire 3,000 opening on day one -- their
money drops to 46 by the end of it -- and it goes on **animals first**.
Land comes on day six, out of what the farm has earned by then.

**Transplanting that book into E cost 11,500 coins** (50,762 against
62,273). The reason is precise and worth keeping: four animals on day one
consume exactly the cash E needs for its day-one second quadrant, and that
quadrant is worth +8,000 on its own. E cannot afford both, and for E the
land is worth more.

**So an opening is not portable between architectures.** It pays only
alongside the rest of the play it was recorded with -- the field's herd-
first opening works because their labour routes feed and tend those
animals from day one, and E's does not. This is the same lesson as 10.8c
in a different place: what correlates with strength in a corpus of
recorded games is not automatically a lever you can pull.

### 10.8h The animal gap, decomposed exactly -- and five more failures

E's shortfall against a strong route is entirely in its herd, and it
factors cleanly into two independent numbers. Measured by diffing every
animal tile's `yield_units` turn by turn, over three seeds:

| | animal-days | fed **and** cared | units per animal-day | units produced | units harvested |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Agent E** | 283 | **69.7%** | 0.82 | 231 | 229 |
| **elite route** | 412 | **90.5%** | 1.13 | 467 | 467 |

0.69 x 0.73 = 0.50, which is exactly E's 231 against 467. So:

* **Harvesting is not the problem.** E collects essentially everything its
  animals produce (229 of 231).
* **Half the gap is animal-days** -- the herd arrives late, and 10.8f
  established that is a capital constraint, not a scheduling one.
* **Half is the feed-and-care coincidence.** The care bonus is only paid
  out on a day the animal was *also* fed, so the two must land together.
  E manages both on 69.7% of animal-days against 90.5%; it feeds on ~80%
  and cares on ~79%, and those two 80%s multiply out to 70%.

**Five more interventions were measured against this and all failed:**

| intervention | result vs 63,270 |
| --- | ---: |
| weight animal jobs 1.6x to 8x over crop jobs | 55,630-58,227 |
| carry a full feed round per shed trip (4 -> 8, 14, 20 wheat) | 53,816-59,554 |
| **sticky assignments** -- a worker keeps walking to its target across turns instead of re-auctioning every turn | **53,150** |
| demand-paced selling at 12 and 96 steps (24 is right) | 60,164-62,150 |
| the opening book from 490 real sides (10.8g) | 50,762 |

The feed-round result is worth a note because the mechanism looked
certain: worker inventories have **no capacity limit at all** in the
simulator -- `_inv_add` simply adds -- so fetching four wheat at a time
for a seventeen-head herd is five shed trips a day where one would do.
Raising it still lost, because the threshold that triggers the trip pulls
workers off other work more often than the bigger load saves.

The sticky-assignment result is the one that closes the routing question.
E reverses direction on 5.8% of its moves against an elite route's 0.6%
and walks 1.37 steps per task against 0.94, so committing a worker to its
target looked like the obvious repair. It costs 10,000 coins, because a
commitment made on stale information is worse than re-deciding: the job a
worker was sent to do is frequently done by someone nearer, or stops being
worth doing, before it arrives.

**Taken with 10.8d, 10.8e and 10.8f, that is roughly thirty measured
interventions on this scheduler since its last real gain.** Every one of
labour allocation, job weighting, travel pricing, spatial assignment,
commitment, herd composition, herd timing and opening crop choice has been
tried and lost. The remaining gap is not reachable by editing how a
per-turn auction scores its options.

### 10.8i Against the real ladder, not three elite tapes (2026-09-07)

Every measurement in 10.5 through 10.8h used the same three elite tapes as
opponents. That is a hard panel and it was never checked against the field
E will actually meet. The cached corpus holds **245 real Kaggle opponents**
as replayable clones (`kaggle_cache/clones/`), spanning the whole ladder --
their own rewards run from 146,514 down to 2,645, median 74,812.

Forty of them, sampled at random, both seats, 80 games each:

| agent | mean | floor | wins |
| --- | ---: | ---: | ---: |
| **D** (live) | **101,535** | 48,455 | **74/80 (92%)** |
| F (clone + demand pacing) | 97,098 | 48,299 | 70/80 (88%) |
| **E** (bespoke) | 70,930 | 19,482 | **4/80 (5%)** |

**E is not stronger against weaker opponents.** The hope that its price
advantage would widen against a less crowded market does not survive
contact with the data: it wins 5% here against 6% on the elite panel. Its
deficit is production volume, and volume does not depend on who it is
playing.

**D wins 92% of games against real cached opponents.** Whatever its live
rating says, on this measure it is a strong agent and the right thing to
have deployed. Note the standing caveat from 9m: these opponents are
frozen tapes of games their authors played live, and a tape is weaker than
the player it was recorded from, so 92% here is an upper bound on the live
figure.

**Use `tools/viewer/render_match.py` to watch any of this.** It plays one
match and writes a self-contained HTML replay:

    python tools/viewer/render_match.py --agent rl.candidate_e:agent         --opponent agents/experimental_distilled_elite_andrey_agent.py         --seed 6 --out artifacts/replays/e_seed6.html

Open it in VS Code with Ctrl+Shift+P -> "Simple Browser: Show". The files
are about 47 MB each and `artifacts/replays/` is git-ignored.

### 10.9 How to test

* `python -m tools.validation.preflight_candidate_d` -- seven gates for
  the live agent; non-zero exit on failure. Includes the loader-order
  check that the section 9h upload failure would have tripped.
* `python -m unittest discover -s tests -q` -- **583 tests** currently
  passing.
* Local panels: `kaggle_cache/top500_panel.json` holds 92 distinct
  top-500 opponents built from cached replays. **Remember these are
  tapes** and overstate live win rate by ~40 points (9m); use own-coin
  production as the primary signal, since it is nearly self-determined.
* `kaggle_cache/clones/` holds 245 opponent tapes, and
  `rl/replay_agent.py` turns any of them into an opponent.
* `tools/data/profile_agents.py` and `tools/data/strategy_study.py`
  compute per-game economic profiles and paired winner-versus-loser
  contrasts over cached replays.

### 10.10 Definition of done for E

E replaces Candidate D only when **all** of these hold:

1. own-coin production at or above D's on a shared seed set;
2. a win rate at or above D's on the 92-opponent top-500 panel, both
   seats, with the paired McNemar p-value reported and not hidden;
3. a demand-to-production correlation materially above zero, since that
   is the entire point of the architecture;
4. all seven pre-flight gates green on its own package;
5. zero errors across at least 100 full games in both seats.

Until then D ships and E stays in the tree.

### 10.11 The simulator mechanics that actually decide this game (2026-09-06)

Six mechanics were read out of
`kaggle_environments/envs/kaggriculture/kaggriculture.py` and each one
changed a decision Agent E was getting wrong. They are stated here so
nobody has to find them again.

| mechanic | line | why it matters |
| --- | --- | --- |
| **Reward is final cash and nothing else** | `s.reward = float(obs0.farms[player]["money"])` | assets, herd and standing crops all score zero, so the last day must liquidate the shed completely |
| **The crew is deleted every night** | `farm["hands"] = []; farm["hires_today"] = 0` in the daily refresh | the whole crew is re-hired every morning and the Fibonacci price restarts at 1; hiring a few per turn leaves the farm short-handed through every morning |
| **Structures are free** | `BUILD_COOP` / `BUILD_PASTURE` take no money | a pen costs only its tile and one worker-turn; gating pens on cash was wrong |
| **Every animal drops one fertilizer a day, fed or not** | `tile["fertilizer_available"] = True`, unconditional | 17 animals is ~450 fertilizer a season; this, not milk or wool, is what a herd is actually for |
| **Inventories auto-drop to the shed at every day boundary** | `_drop_inventories_to_shed(private, shed_cap)` | workers never need to walk to the shed to bank produce, only to pick things up |
| **HARVEST is refused before `first_yield_day`** | `if day - tile["planted_day"] < crop_data["first_yield_day"]: return` | melon accrues units from age 6 but cannot be picked until age 10; a scheduler that does not know this parks a worker on it harvesting nothing. Measured: **659 wasted worker-turns in one game** |

### 10.12 The market is one shared pool, and it is the whole economy

`market["inventory"]` is a **single global dictionary for both players**.
Every unit either side sells depresses the price for both, and the town's
consumption lifts it back for both. `rl/market.py` transcribes the
simulator's own curve (18 tests, `tests/test_market.py`) so any unit can
be priced at the margin instead of at spot.

What the curve says, as coins for the first 400 units sold and the price
still on offer at the four-hundredth:

| item | 400 units fetch | price at unit 400 |
| --- | ---: | ---: |
| MELON | 26,727 | 1 |
| FERTILIZER | 24,040 | 20 |
| **EGG** | **16,559** | **40** |
| TOMATO | 10,453 | 9 |
| WOOL | 8,269 | 1 |
| WHEAT | 8,313 | 20 |
| CARROT | 7,853 | 12 |
| MILK | 6,505 | 1 |
| STRAWBERRY | 4,147 | 1 |

And what an elite route **actually realises**, measured by re-pricing
every one of its sell orders against the market inventory at the moment
it placed them:

| product | units sold | coins | coins per unit |
| --- | ---: | ---: | ---: |
| STRAWBERRY | 333 | 19,720 | 59 |
| WHEAT | 459 | 19,548 | **43** |
| FERTILIZER | 455 | 16,198 | 36 |
| MELON | 72 | 12,927 | **180** |
| CARROT | 73 | 5,085 | 70 |
| WOOL | 389 | 4,470 | **11** |
| MILK | 347 | 3,671 | **11** |

**Wool and milk realise eleven coins a unit.** Every recorded route in
this repository builds its herd around them, and 736 units of the two
together are worth 8,141 coins -- half what the same herd's fertilizer
earns. Wheat sells at 43 against a base of 25 all game, because five of
the eight shops buy it and both players are short of it for feed.

Three consequences, all of them now in the code:

* an animal is valued at its **marginal** product plus its manure, so the
  fifth cow is correctly worth 30 coins where the first is worth 3,888;
* wheat is grown, never bought, and the herd is capped at what the
  standing wheat can feed;
* the shed is emptied completely on the last day.

**This also explains Candidate C1's disappointing live rating** better
than section 9m did. A tape's sell prices were set by what *its*
opponent did in the recorded game. Replayed against a different opponent
and a different shop draw, the same orders meet a different inventory
curve: wool that was worth 200 a unit in the source game is worth 1.
Nothing about the route is wrong; the market it was priced against no
longer exists. No amount of better route selection fixes that, which is
the whole argument for E.

### 10.13 Where the constants came from, and how to retune them

Tuned by coordinate descent on seeds 0-5, then validated on seeds 6-13
(10.5). Every one of these is a module-level global in
`rl/candidate_e.py`, so `tools`-free retuning is a matter of setting the
attribute in a worker process; the panel harness does exactly that.

| constant | value | alternatives measured |
| --- | ---: | --- |
| `TRAVEL_EXPONENT` | 2.5 | 1.5 -> 44,943; 2.0 -> 48,704; 3.0 -> 49,296 but a worse floor |
| `SEED_SPEND_SHARE` | 0.15 | 0.25 -> 57,284; 0.40 -> 47,320; 0.60 -> 48,938 |
| `TARGET_HANDS` | 9 | 7 -> 50,442; 11 -> 47,320; 13 -> 41,926 |
| `WHEAT_UNITS_PER_TILE_DAY` | 0.6 | 0.4 -> 53,792; 0.9 -> 49,164 (all within noise of each other) |
| `RESCUE_SHARE` | 0.45 | 0.25 -> 49,944 best mean but floor 11,760; 0.45 has the best floor at 22,546 |

**Two warnings.** These were tuned one at a time and they do **not**
compose additively -- `SEED_SPEND_SHARE=0.25` alone measured 57,284 but
combined with `TARGET_HANDS=9` it fell to 54,154. And 36 games is not
many: differences under about 4,000 coins are inside the noise, which is
the same 4,845-coin yardstick section 10.3 already sets. Re-measure any
change on the held-out seeds before believing it.

### 10.14 What to do next

**Step A. Make feeding reliable, then re-test the goose herd.** This is
the biggest single opportunity on the board and the one thing that would
make E's strategy genuinely unlike anything in the field. Egg is the only
product in the game whose price does not collapse -- it still pays 40
coins at the four-hundredth unit -- and every measured game ends with egg
inventory 150 to 300 units *below* equilibrium at 59 to 68 coins, because
no agent in the top 500 keeps geese. A goose fed and cared for daily
yields two eggs a day; ignored, it yields one. The blocker is feeding, so
fix that first (10.8b) and then re-run the herd comparison.

**Step B. Close the volume gap.** E sells roughly 640 units a game; an
elite route sells 2,140. That ratio, not price realisation, is the whole
remaining difference -- E realises *better* prices than D on every
product, because it sells smaller quantities earlier.

**Step C. Stable per-worker assignments.** The square travel discount was
worth 8,000 coins by keeping workers local. Committing a worker to a
target across turns, or partitioning the board into per-worker zones,
attacks the same waste from the other side; E still reverses direction
mid-journey 5.8% of the time against an elite route's 0.6%.

**Step D. Do not chase task share.** It is not the constraint it was
believed to be. E idled 1,146 worker-turns a game not because the
scheduler was weak but because a 25-tile farm cannot occupy twelve
workers; the fix was capital, not scheduling.

## 11. Candidate D: the original learned residual/Option selector plan

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

## 12. Public research that informs implementation

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

## 13. Validation and release discipline

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

## 14. Definition of done

The project is not done when code exists. It is done when:

- A is either safely frozen as infrastructure or rejected;
- A+B produces a measurable win-rate gain and is submitted if justified;
- C crosses the preregistered 1500-ready gates and receives real ladder evidence;
- D beats C causally and out of sample, not just offline;
- the two final active submissions are complementary, error-free, and robust to current meta families;
- score 2500-2800 is treated as the ultimate measured objective, not a promise.

Start now with Candidate A step A1. Preserve the current uncommitted work and do not broaden scope until the second close-loss result and post-terminal 33-game reruns are complete.
