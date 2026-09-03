# Submission Packages

## Active packages

The tracked standalone Kaggle packages are:

- `deadline/` contains the frozen deadline-taper policy uploaded as submission
  `55795843`.
- `learned-service/` contains the promoted learned service policy uploaded as
  submission `55803952`.
- `demand-animal/` contains the demand-aware animal policy uploaded as
  submission `55817911`.
- `future-labor/` contains opponent-aware labor submission `55821334`, frozen
  at its manifest SHA-256.
- `tiered-fertilizer/` contains four-application, price-tiered fertilizer
  submission `55858409`, recorded at `649.3`.
- `gated-late-strawberry/` contains the validated live-measurement candidate
  uploaded as submission `55887535`, selected at the current `655.2` snapshot.
- `distilled-calendar/` contains public-calendar behavior clone submission
  `55910432`. Its exact package is `72-8` on the 80-game broad gate and is
  frozen after successful validation.
- `candidate-a(calendar recovery first attempt)/` (Candidate A) contains
  `distilled-calendar` plus guarded weed/setup recovery, live terminal
  liquidation, stranded harvest commitments, and (as of the locked-quadrant
  fix below) a guard against acting on land the calendar assumes is
  purchased but isn't. Uploaded to Kaggle; live score has been observed in
  the `1160-1200` range, but that score predates the locked-quadrant fix --
  see below. Locally gated at `21-12` on 33 captured live episodes and
  `107-13` on a fresh 120-game, 6-opponent-family gate (both alone, before
  Candidate B, and before this fix).
- `candidate-b/` (Candidate A + market-timing residuals) contains
  Candidate A plus two market residuals: sequential affordability (moves a
  SELL order ahead of a same-turn HIRE/BUY_PRODUCT purchase it can fund)
  and land priority (moves a BUY_LAND order ahead of a same-turn spend that
  would otherwise starve it -- see below). Locally gated at `22-11` on the
  same 33 captured live episodes and `108-12` on the same fresh family gate
  (both combined with Candidate A, before the land-purchase fix). Not yet
  uploaded to Kaggle.

### 2026-09-03: locked-quadrant fix (both packages above)

Two live episodes (105061000, 105062726 -- both real Kaggle games played by
the live Candidate A submission) showed the same calendar turn (record 200,
same step in both games, both seats) spend past the money a same-turn
`BUY_LAND` needed: the batch was `[BUY_PRODUCT WHEAT 16, BUY_LAND]`, and the
product purchase drained the funds the land purchase needed. The calendar
only ever attempts `BUY_LAND` twice in its entire 720-step script; once this
one failed, it was never retried, and the third quadrant stayed locked for
the rest of both episodes. Every later scheduled `PLANT`/`WATER`/`HARVEST`/
`BUILD_PASTURE` the calendar sent to that quadrant reported the tile as the
literal string `"LOCKED"` and executed as a no-op -- 471 wasted actions in
each replay.

Two fixes, at two different layers:

- `rl/candidate_a.py` now guards every tile-task operation (not just the
  existing weed guard's three) against a `"LOCKED"` target tile, substituting
  `PASS`. This benefits both packages, since Candidate B wraps Candidate A.
  Verified against the real captured observation from both episodes: the
  guard swaps exactly the calls that were previously silent no-ops, and
  leaves every other worker's action byte-for-byte unchanged.
- `rl/candidate_b.py` adds `_land_priority_ordering`, a second market
  residual that moves a starved `BUY_LAND` order ahead of a same-turn
  `HIRE`/`BUY_PRODUCT`/`BUY_SEED`/`BUY_ANIMAL`, but never across a `SELL`
  (a SELL's position stays entirely the existing affordability pass's
  decision). Unlike that existing pass, this is a deliberate value
  judgment, not a strict-fulfillment-dominance proof: a whole quadrant is
  judged to dominate a partial WHEAT restock. Verified against the real
  observation from episode 105061000: the fix trades 11 of 16 requested
  WHEAT units for the land purchase actually succeeding. This fix does
  *not* help the currently-live Candidate A package on its own -- only
  Candidate B's market-timing layer carries it.

Both fixes: full test suite green (489/489), package/source/simulator
equivalence 1438/1438 decisions with 0 mismatches (seed 230). The land
fix's fresh live-opponent gate (120 games, 3 opponent families, seeds
400-409) came back inconclusive rather than passed: the starvation
condition it targets never occurred against these opponents/seeds, so it
neither confirms nor refutes live-opponent risk the way that gate did for
the existing sell-reordering pass. See `rl/GOAL.md` section 8c for the
structural argument for why it should still be safe, and the reasoning
for trusting the guard fix and the reorder fix at different confidence
levels in the meantime.

After a package is uploaded, its exact `main.py` is immutable. Each package's
`manifest.json` records its hashes and supporting evidence.

## Legacy packages

`legacy/` contains generated packages retained for local historical review.
These packages are ignored by Git and can be recreated with the corresponding
scripts in `tools/packaging/`. They are not active submission candidates.