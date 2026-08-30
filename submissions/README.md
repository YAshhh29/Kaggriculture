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
  submission `55858409`, currently selected at `649.3`.
- `gated-late-strawberry/` contains the validated live-measurement candidate
  uploaded as submission `55887535`, frozen after validation at `600.0`.

After a package is uploaded, its exact `main.py` is immutable. Each package's
`manifest.json` records its hashes and supporting evidence.

## Legacy packages

`legacy/` contains generated packages retained for local historical review.
These packages are ignored by Git and can be recreated with the corresponding
scripts in `tools/packaging/`. They are not active submission candidates.