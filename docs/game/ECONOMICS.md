# Demand And Profit

## What Open Shops Change

Every open shop consumes its listed products every four turns, or six times per
day. Duplicate shops consume independently. A single-product shop consumes two
units per event, so one Pet Cafe or Yarn Store creates twelve units of daily
carrot or wool demand. The town center adds one daily unit of demand for every
product except fertilizer.

Demand removes units from shared market inventory. Lower inventory raises the
quoted price; selling adds inventory and usually lowers it. Both players affect
the same market.

## Why Melon Can Lose

Melon has a high base price and strong theoretical crop margin, but no dedicated
shop. Its only guaranteed demand is one town-center unit per day. Several melon
plots can therefore produce faster than demand removes supply, pushing the
nonlinear melon price toward one coin. Melon also ties up a tile and workers for
ten days before cash arrives.

The correct question is not "which crop has the highest base price?" It is:

```text
expected sale value
- seed and feed cost
- delayed cash cost
- worker-action opportunity cost
- shared-market saturation risk
```

## Inspecting A Replay

Use a replay record captured before the decision you want to understand:

```powershell
.\.conda\python.exe -m research.analysis.explain_economics `
  artifacts\some-replay.json --record 216 --player 0
```

The report includes:

- exact daily demand implied by current shops;
- current market quote;
- opponent public crop or animal count;
- final cashable planting day;
- expected net at the current quote;
- labor-, horizon-, demand-, and saturation-adjusted opportunity score.

The score is a comparison signal, not a profit guarantee. Promotion still
requires terminal head-to-head wins on separate seeds.