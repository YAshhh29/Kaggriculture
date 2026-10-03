# Agent Handoff: J2 and K2

Written for whoever picks this up next, including a future session of
this same project. Everything here is measured, not asserted — where a
number appears, it came from a real run against a real opponent, and the
command to reproduce it is given.

## What J2 and K2 actually are

**J** (`rl/candidate_j.py`) is our bespoke, from-scratch agent: a per-turn
auction that prices every (worker, job) pair on the board in coins per
turn including the walk, and books the highest-rate pairs first. No
third-party code anywhere in it.

**K** (`rl/candidate_k.py`) is H2's recorded opening (days 0–12, the
public Apache-2.0-derived lineage H2 was always built on, licence notices
retained) handed off to J's reactive engine at day 12 (`SPLICE = 288`).
This is not a tuning choice made blind — an independent study of the
top-200 corpus found that what actually separates 3000-rated play from
2800-rated play is that the top *re-decides every turn* rather than
replaying a script: teams rated 3000+ repeat only 40.5% of their own
farmer actions across their own games and diverge from their own past
play by step 40; the 2800 band repeats 95.7% and doesn't diverge until
step 258. K's architecture is built to match the winning shape, not just
to average two agents together.

"J2" and "K2" are not new files. They are these same two agents after
today's round of fixes — the packaging bug that made both of them
un-submittable, and the two candidate mechanisms (wind-down, race-aware
truncation) pulled from public notebooks and awaiting clean measurement.
There was never a structural rewrite that earned a new filename; the
version bump is in the fixes, not the architecture.

## The packaging bug — read this before touching either packager again

Both J and K failed Kaggle's validation episode after their first
submission. The actual cause, from the user's own error log:

```
from agents.experimental_distilled_calendar_agent import decide as calendar
```

`rl/runtime.py` is a bridge to an abandoned reinforcement-learning
"residual policy" experiment from earlier in this project. J's own code
uses exactly one thing from it — the `AgentAction` type alias, which is
just `dict[str, Any]` — but the packager was inlining the **whole file**
as one of its `PARTS`, and that file does the import above, reaching into
an `agents/` folder that exists in this repo and is never part of a
submission.

It worked in every local test because every local test script starts
with `sys.path.insert(0, ROOT)`. The repo is never actually absent in
development. Kaggle's server has only `main.py` — nothing else. Eight
separate local hypotheses were tested and disproven before the real cause
was found from the user's own error screenshot: entry-point resolution,
load time, per-turn time at the engine's *actual* default `actTimeout` of
one second (not the 60s used in every local test all session), Python
syntax compatibility, self-play, leftover unresolved imports, name
collisions across inlined files, and byte-level file integrity. All
clean, none of them the cause, because none of them removed the repo from
`sys.path`.

**Fixed two ways**, both in `tools/packaging/prepare_candidate_j_submission.py`:

1. `rl/runtime.py` is no longer inlined. `PARTS` drops it; `AgentAction`
   is defined directly in the packager's own header instead.
2. `check_only_stdlib_imports(path)` walks the finished file's AST and
   refuses to write it if anything outside `sys.stdlib_module_names`
   appears in a top-level import, anywhere in the file. Confirmed to fire
   by testing it directly against a reconstruction of the exact line that
   shipped.

**The lesson for anyone adding a new module to either packager's `PARTS`
list**: inlining a whole file inlines everything that file imports too,
even things the calling code never actually uses. Check what a new part
imports, not just what it's needed for.

**K also had its own separate packaging problem**, since fixed
separately. Its first version embedded H2 and J as base64 blobs and ran
`exec(compile(...))` on them at import time on the grading server — the
one thing in either file structurally unlike every one of the seven
public notebooks read tonight, all of which decode and verify a blob like
that at *build* time in their own notebook and ship the plain, decoded
source. Replaced with `tools/packaging/namespace_merge.py`: an AST-level
rename of every top-level name H2 and J each define, behind a unique
prefix (`_H2_`, `_J_`), producing one flat, ordinary, linearly-compiled
file. This surfaced a real bug of its own before it shipped — H2's file
layers many historical versions of `agent` by doing `agent =
globals().pop("agent")` sixteen times through the file, a string-keyed
reflective lookup a plain identifier rename cannot see. Fixed by teaching
the renamer to recognise `globals().pop(...)`/`globals()[...]`
specifically and rewrite the string argument to match. Reverified the
same way: the renamed H2 matches the original action for action, 719 of
719 steps, same for the full packaged K against its own source across the
splice.

**Both packagers now**:
```
python -m tools.packaging.prepare_candidate_j_submission
python -m tools.packaging.prepare_candidate_k_submission
```
Each writes `submissions/candidate-{j,k}/main.py` and refuses to finish
if `agent` is not the last callable, if the packaged file's decisions
diverge from the source across a full game, if the file does not play
cleanly when loaded the way Kaggle loads it, or now, if anything outside
the standard library is imported anywhere in the file. Re-run either
after any change to the corresponding source module or its dependencies
— a stale packaged file is worse than an obviously broken one.

## Where J and K stand, measured

**Against live opponents** (`tools/eval/strong_panel.py` — aurax7, v34,
our own H2, our own route-replay I; the only opponents in this whole
project that can actually react to what we do, not replay a fixed tape):

| | wins | margin |
|---|---:|---:|
| J | 0/64 | large negative against every one, including our own H2 by −67,202 |
| K (before today's mechanisms) | 2/48 | margin still deeply negative |

**On the breadth panel** (`tools/eval/broad_panel.py`, replayed top-200
tapes, both seats) — this measures *breadth of opponent* well but each
individual game is an open-loop recording that cannot react, so treat any
single-panel win-rate number as directional, not final:

| | wins | median | margin |
|---|---:|---:|---:|
| J (current, all today's fixes) | 6/60 | 66,559–82,295 (has varied run to run — see caveat below) | consistently −40,000 to −43,000 |
| K (day-12 splice, current J) | 4/60 | 78,834 | −23,553 |
| H2 alone (reference, unmodified) | 34/60 | 101,020–106,851 | **the only one with a positive margin, +514 to +3,466** |

**Read this caveat before trusting any panel number in this repo**: the
breadth panel's own tape corpus has been refetched multiple times this
session, and running the panel *while* a fetch is in progress silently
draws a different, growing set of tapes for each sequential arm of a
comparison, invalidating it. Check `their score ... (they really scored
X)` is IDENTICAL across every arm of a comparison before trusting it. A
whole afternoon's wind-down comparison was thrown out for exactly this
reason. **`strong_panel` does not have this problem** — it plays live
opponent code, not tapes — and should be preferred for any single
head-to-head question when time allows.

**Sample size**: this project has now seen a 30-tape (60-game) result
reverse on a 60-tape (120-game) confirmation *six separate times* today.
The ongoing-yield fix claimed +4,523 on 30 tapes and delivered +1,679 on
60. The pen-distance reservation looked like the best result of the
session on 30 tapes and lost its entire margin advantage on 120. Treat
anything measured on fewer than 60 tapes as a direction, not a number.

## Mechanisms: adopted, rejected, and pending

All in `rl/candidate_j.py` unless noted, all guarded by a module-level
constant so they can be toggled via `J_SET='{"CONST": value}'` against
`rl.j_variant:agent` without editing the source.

**Adopted, all re-validated on the honest (non-per-agent-filtered) fixed
panel after the panel itself was found to be biased**:
- Watering an ongoing crop on its production night (`WATER_ONGOING`) —
  the engine only pays the manure bonus on a day the tile was also
  watered; this was priced at zero. +3,294.
- Pricing a meal at what it actually cashes on a production night, not a
  flat guess (`FEED_PRODUCTION_SHARE = 0.5` — full value overshoots and
  loses, see below). +11,047, the largest single fix of the project.
- Not buying the third land quadrant — the farm never had labour to work
  it (`LAND_DAYS = (5, 9, 99)`).
- `crop_units` was undervaluing ongoing crops (strawberry) at half their
  real yield, because it counted one unit per production event when the
  engine pays two on a fertilized-and-watered day (`ONGOING_YIELD = 1.5`).
  +1,679 (60-game figure; a 30-game sample overstated this at +4,523).
- Melon hard-capped while other crops' book cap is soft
  (`SOFT_CAP_EXCEPT = ("MELON",)`) — melon is in no shop basket at all, so
  a soft cap let it flood a book the town barely drains.
- Seed queue at 3 crops deep, not 4 — a fourth slot was adopted earlier on
  a biased panel and reversed on honest re-measurement; the real effect
  was spreading the same purse thinner, not letting strawberry through as
  originally (wrongly) reasoned.
- The book cap is soft (`CAP_IS_SOFT = True`, `OVER_CAP_RATE = 0.6`) — a
  crop at its book's nominal cap competes at a reduced rate instead of
  being struck from the plan outright.
- Same-day watering guarantee tightened: `PLANT_CUTOFF = 3` hours before
  day's end rather than 2, so a late sowing has time to win its own
  rescue-watering auction. Reduced same-day plant-to-weed events from 4 a
  game to 1 (not fully zero — a residual edge case, not chased further).

**Rejected, each cost real money when measured** (list is not
exhaustive — see `rl/candidate_j.py`'s own inline comments next to each
constant for the full reasoning and numbers): a fourth seed-queue slot,
the hard book cap, buying grain to raid the wheat market (denial cannot
be bought — 32,590 lost to take 3,953 off the rival), a wheat "float"
(round-trip loses on the buy/sell spread by construction), selling
through the pre-town-tick quiet turn, pricing pens by shed-distance
alone, reserving ground near the shed for pens (matched the elite's
spatial pattern almost exactly and still lost money at 120-game
confirmation — see `docs/public_meta_study.md` for the full story),
an explicit job-queue/commitment mechanism for the auction (fired on 84%
of eligible turns and moved nothing, because the auction's own
distance-weighted pricing was already finding the same jobs), giving K
extra hires beyond H2's own plan, and letting K fill H2's idle hands
directly (this one desyncs H2's whole route, since it's a frozen
programme that assumes where its hands are standing — moving one drops
the score from 184,922 to 90,409).

**Pending, built tonight, not yet cleanly measured** (the panel that was
running them was contaminated by a concurrent tape fetch; re-run before
trusting either):
- `WIND_DOWN_DAYS` (currently 0, off) — a public notebook studying the
  top of this ladder independently found every strong route it mapped
  switches to a liquidation plan at day 27 of 30, seventy steps before
  this agent's own trigger, which was the literal last turn. Implemented
  as a gradual loosening of the fragile-book floor and per-turn sell
  allowance across the last `WIND_DOWN_DAYS` days, not a hard switch.
- `RACE_AWARE_TRUNCATE` (currently False) — `sale_lots` already ranks
  sales by loss-if-outraced against `ctx["rival_batch"]`, independently
  arriving at close to what a public notebook calls "Layer D" (an exact
  market-list order-book simulation, worth +124 to +133 coins/game in its
  own measurement against seven strong published agents). Found that this
  ranking was being **thrown away** — re-sorted by raw dollar value —
  whenever a turn's sells didn't fit the remaining order slots, exactly
  when the ordering matters most. This flag keeps the original ranking
  instead of discarding it.

**Test command for both, once the tape corpus is stable** (check fetch
has actually finished — `ls kaggle_cache/top200_tapes/*.json | wc -l`
should stop growing between two checks a minute apart):
```
J_SET='{"WIND_DOWN_DAYS": 3}' python -m tools.eval.broad_panel rl.j_variant:agent --tapes 30
J_SET='{"RACE_AWARE_TRUNCATE": true}' python -m tools.eval.broad_panel rl.j_variant:agent --tapes 30
```
Confirm any positive result on 60 tapes before adopting, given today's
six-for-six record of 30-tape results overstating themselves.

## What public code taught us (full detail in `docs/public_meta_study.md`)

Seven notebooks read by explicit user request: ahmedberatozer's v39 and
v34, leoprovorov's reverse-engineering writeup, two of dmitriigluzdov's
agents, shiiin9's order-book notebook, lynnsakurai's invariant-checked
wrapper. Headline findings:

1. **The whole strong field is one converging lineage** — Hayashi's
   ShopRouter → Tschinkel's Metav4 → ahmedberatozer's v25–v56 series →
   shiiin9's order-book layer → dmitriigluzdov's further additions.
   ahmedberatozer's own v39 measures 95.83% against a "top field" of 120
   games. This is very likely most of what the 2700–2900 bracket the user
   is targeting is actually running.
2. **Two independent confirmations** of mechanisms found in this project
   the same day, from the opposite direction: v39's changelog lists
   "production-calendar feeding" (our biggest fix, +11,047) and "bounded
   wheat replenishment" (matches our own wheat-float rejection) as its
   headline additions.
3. **Layer D** (shiiin9): an exact slot-by-slot order-book simulation for
   market-sell ordering. We already had most of the underlying idea; see
   `RACE_AWARE_TRUNCATE` above for the gap that was found and closed.
4. **The tomato gate** (dmitriigluzdov via v55): a scripted late
   investment gated on a market-inventory projection rather than a coarse
   shop count. Not yet checked against our own numbers.
5. **Trajectory-matched sale prediction** (dmitriigluzdov, "More Wheat,
   Smarter Sales"): match the live opponent's observed behaviour against
   a library of recorded games to predict its next sale, then pre-empt it
   by 1–2 turns. Directly buildable now — we have 2,300+ recorded tapes,
   which is exactly the library this needs. **Not started.**
6. **The safety-invariant wrapper pattern** (lynnsakurai): check whether
   the live game still matches what a frozen route's plan assumed before
   substituting anything into it; fall back to the route's own action
   otherwise. This is the real, structurally different way to build on
   H2 without desyncing it — everything tried tonight that touched H2
   directly (extra hires, idle-hand filling) broke it, because none of it
   checked first. **Not started; the primary open research direction for
   K.**
7. Even the strongest agents studied have real, unsolved weaknesses —
   goose escapes in 16 of 64 games for one team's own selected best
   controller. Do not assume 100% is reachable on every axis.

## Honest assessment

Neither J nor K beats H2 as of this writing, on any panel. J beats
nothing live (0/64 on `strong_panel`). K is meaningfully better than J
(the splice carries real value — H2's opening is a genuinely strong
farm) but still loses to H2 unmodified on every measurement taken. The
target set by the user is not H2 — it is the live 2700–2900 bracket,
which the public-notebook study suggests is dominated by the converged
lineage above. The two most promising open threads for actually closing
that gap are items 5 and 6 in the previous section: neither has been
started, and both are aimed at something this project has not yet built
at all — reacting to a *specific* opponent's behaviour, rather than
playing the same way regardless of who is across the board.
