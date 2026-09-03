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
