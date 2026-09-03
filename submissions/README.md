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
  liquidation, and stranded harvest commitments. Uploaded to Kaggle; live
  score has been observed in the `1160-1200` range. Locally gated at
  `21-12` on 33 captured live episodes and `107-13` on a fresh 120-game,
  6-opponent-family gate (both alone, before Candidate B).
- `candidate-b/` (Candidate A + sequential affordability) contains
  Candidate A plus a market residual that moves a SELL order ahead
  of a same-turn HIRE/BUY_PRODUCT purchase it can fund, verified per-turn
  against a local market replay. Locally gated at `22-11` on the same 33
  captured live episodes and `108-12` on the same fresh family gate (both
  combined with Candidate A). Not yet uploaded to Kaggle.

After a package is uploaded, its exact `main.py` is immutable. Each package's
`manifest.json` records its hashes and supporting evidence.

## Legacy packages

`legacy/` contains generated packages retained for local historical review.
These packages are ignored by Git and can be recreated with the corresponding
scripts in `tools/packaging/`. They are not active submission candidates.