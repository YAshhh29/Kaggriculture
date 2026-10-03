# Shadow Controller

The final demand-animal tree is retained as a research-only shadow policy. It
chooses among balanced, cow-biased, and goose-biased expansion plans at day 6,
then executes the same deterministic scheduler as every other arm.

It is not promoted because held-out validation tied fixed cows on wins and
trailed fixed cows on mean margin. The shadow comparison exists to answer a
future question with direct games: does the learned recommendation improve as
opponents and shop contexts change?

Run the deterministic suite:

```powershell
.\.conda\python.exe -m research.analysis.run_overnight_shadow `
  --seed-start 188 --seed-count 10 `
  --output artifacts\benchmarks\overnight-shadow.json
```

The report compares:

- exact submitted learned-service control;
- promoted demand heuristic;
- frozen shadow tree;
- fixed cow expansion;
- fixed goose expansion.

Promotion is conservative: zero errors, more total wins than control, positive
aggregate margin delta, and no opponent-level win regression. The classifier
cannot upload or change the live agent.

## Overnight Result

The seeds 188-197 suite completed 500 full games: five variants, five
opponents, and both player positions. All games completed without errors.

| Variant | Wins-Losses | Mean margin | Decision |
| --- | ---: | ---: | --- |
| Submitted learned-service control | 89-11 | +11,185.60 | Control |
| Demand heuristic | **92-8** | +11,234.75 | Promoted |
| Shadow tree | 91-9 | +11,741.24 | Research-only |
| Fixed cows | 85-15 | +11,012.25 | Rejected |
| Fixed geese | 79-21 | +8,847.82 | Rejected |

Demand improved the direct submitted-control matchup from 10-10 to 13-7 and
matched every other control win count: 20-0 against compact, adaptive, and
scale, plus 19-1 against lifecycle. The frozen tree remains rejected because
this result does not repair its non-improving held-out learning curve.