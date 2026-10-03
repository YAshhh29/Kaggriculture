# Submissions

Every folder holds the exact single-file `main.py` that was uploaded to
Kaggle (and, for the early packages, a `manifest.json` with its hashes and
the evidence it was promoted on). These files are never edited after upload:
the source they were built from is in `stack/`, `candidates/` and `agents/`,
and the builders are in `tools/packaging/`.

## Final submissions (30 September 2026)

Kaggle ranks a team on its two latest submissions.

| Folder | Agent | Submission | What it is |
|---|---|---|---|
| [`candidate-n11/`](candidate-n11/) | **N11** | 56720031 | N10 plus corrected bookkeeping of our own sales (`stack/own_book.py`) |
| [`candidate-n10/`](candidate-n10/) | **N10** | 56709381 | N9 plus the shed guard (`stack/shed_guard.py`) |

Result: **448th of 10,246 teams, silver medal.**
Rebuild either with `python -m tools.packaging.build_final N11` (or `N10`).

## Index

| Folders | Period | Lineage |
|---|---|---|
| `candidate-n` … `candidate-n12`, `candidate-n3w`, `candidate-n9h` | 28–30 Sep | The layered stack on the public 2965 Master Hybrid Engine (`stack/`). N3w and N9h are rejected variants; N12 was built but not submitted |
| `candidate-l` … `candidate-l5`, `candidate-l4e`, `candidate-m`, `candidate-m2`, `agent-a` | 26–28 Sep | The layered stack on a public clone (Agent A); M adds an in-game seller |
| `candidate-g` … `candidate-k`, `candidate-hd` | 9–23 Sep | Candidates G to K (`candidates/`) |
| `candidate-a` … `candidate-f` | 2–8 Sep | Candidates A to F (`candidates/`) |
| `deadline`, `learned-service`, `demand-animal`, `future-labor`, `tiered-fertilizer`, `gated-late-strawberry`, `distilled-calendar` | August | The first agents (`agents/`, `policies/`) |

Packages from L onwards embed verbatim copies of public Apache-2.0 programs
(the parent and the opponent library), with their licence notices retained
inside each copy.

## Notes on the August and early-September packages

### Packages up to Candidate D

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
- `candidate-a/` (Candidate A) contains
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
  (both combined with Candidate A, before the land-purchase fix). An
  earlier version of this package (sequential affordability only, before
  the land-priority fix below) was previously uploaded and live -- see the
  correction below.
- `candidate-c/` (public-state route portfolio) contains a real elite
  player's strategy ("fog flower", public leaderboard score 2882.6,
  pulled from the Kaggle leaderboard via API, episode 105144807 where
  they beat the leaderboard's #2 team) wrapped in Candidate A's guards
  and Candidate B's market-timing residuals, currently the sole
  effectively-selected route (Candidate B is kept as a second, documented
  route; the selector cannot yet legally choose between them -- see
  `docs/research/GOAL.md` section 9c). Beat Candidate B 20-0 and Candidate A 8-0 on
  fresh seeds neither was recorded on, both seats -- the first of five
  route candidates tried to win instead of losing. This is a strong
  initial signal, not the full 1000-game/panel gate `docs/research/GOAL.md` section
  9 specifies for a real promotion decision. Not yet uploaded to Kaggle.

#### 2026-09-03: locked-quadrant fix (both packages above)

Two live episodes (105061000, 105062726) showed the same calendar turn
(record 200, same step in both games, both seats) spend past the money a
same-turn `BUY_LAND` needed. Correction: these were played by the
*previously-uploaded* Candidate B (sequential affordability only), not
Candidate A alone as first written here -- it makes no difference to the
diagnosis, since that turn's batch (`[BUY_PRODUCT WHEAT 16, BUY_LAND]`)
contains no `SELL`, so the sequential-affordability pass was a guaranteed
no-op on it; previously-live Candidate B behaved identically to Candidate
A alone for this specific bug. The product purchase drained the funds the
land purchase needed. The calendar
only ever attempts `BUY_LAND` twice in its entire 720-step script; once this
one failed, it was never retried, and the third quadrant stayed locked for
the rest of both episodes. Every later scheduled `PLANT`/`WATER`/`HARVEST`/
`BUILD_PASTURE` the calendar sent to that quadrant reported the tile as the
literal string `"LOCKED"` and executed as a no-op -- 471 wasted actions in
each replay.

Two fixes, at two different layers:

- `candidates/candidate_a.py` now guards every tile-task operation (not just the
  existing weed guard's three) against a `"LOCKED"` target tile, substituting
  `PASS`. This benefits both packages, since Candidate B wraps Candidate A.
  Verified against the real captured observation from both episodes: the
  guard swaps exactly the calls that were previously silent no-ops, and
  leaves every other worker's action byte-for-byte unchanged.
- `candidates/candidate_b.py` adds `_land_priority_ordering`, a second market
  residual that moves a starved `BUY_LAND` order ahead of a same-turn
  `HIRE`/`BUY_PRODUCT`/`BUY_SEED`/`BUY_ANIMAL`, but never across a `SELL`
  (a SELL's position stays entirely the existing affordability pass's
  decision). Unlike that existing pass, this is a deliberate value
  judgment, not a strict-fulfillment-dominance proof: a whole quadrant is
  judged to dominate a partial WHEAT restock. Verified against the real
  observation from episode 105061000: the fix trades 11 of 16 requested
  WHEAT units for the land purchase actually succeeding. This fix does
  *not* help a Candidate A upload on its own -- only Candidate B's
  market-timing layer carries it, so the new `candidate-b/` package (not
  a plain Candidate A reupload) is what should replace whatever is
  currently live.

Both fixes: full test suite green (489/489), package/source/simulator
equivalence 1438/1438 decisions with 0 mismatches (seed 230). The land
fix's fresh live-opponent gate (120 games, 3 opponent families, seeds
400-409) came back inconclusive rather than passed: the starvation
condition it targets never occurred against these opponents/seeds, so it
neither confirms nor refutes live-opponent risk the way that gate did for
the existing sell-reordering pass. See `docs/research/GOAL.md` section 8c for the
structural argument for why it should still be safe, and the reasoning
for trusting the guard fix and the reorder fix at different confidence
levels in the meantime.

After a package is uploaded, its exact `main.py` is immutable. Each package's
`manifest.json` records its hashes and supporting evidence.

## Legacy packages

`legacy/` contains generated packages retained for local historical review.
These packages are ignored by Git and can be recreated with the corresponding
scripts in `tools/packaging/`. They are not active submission candidates.