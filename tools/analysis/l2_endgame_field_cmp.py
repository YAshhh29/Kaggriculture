"""Game-by-game comparison of two paired-harness runs (same opponents, seeds,
seats): e.g. the endgame candidate's field run against L's baseline field run.

    python -m tools.analysis.l2_endgame_field_cmp L-baseline-field endgame-mirror40-field
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAIRED = ROOT / "rl" / "data" / "l2" / "paired"


def main() -> None:
    base, cand = sys.argv[1], sys.argv[2]
    a = {(r["opponent"], r["seed"], r["seat"]): r for r in
         json.loads((PAIRED / f"{base}.json").read_text(encoding="utf-8")) if "margin" in r}
    b = {(r["opponent"], r["seed"], r["seat"]): r for r in
         json.loads((PAIRED / f"{cand}.json").read_text(encoding="utf-8")) if "margin" in r}
    keys = sorted(set(a) & set(b))
    print(f"{cand} vs {base}: {len(keys)} shared games")
    for opp in sorted({k[0] for k in keys}) + ["ALL"]:
        ks = [k for k in keys if opp == "ALL" or k[0] == opp]
        dm = [b[k]["margin"] - a[k]["margin"] for k in ks]
        own = [b[k]["ours"] - a[k]["ours"] for k in ks]
        print(f"  {opp:26s} n={len(ks):2d} wins {sum(a[k]['won'] for k in ks):2d} -> "
              f"{sum(b[k]['won'] for k in ks):2d}  margin change {statistics.mean(dm):+6.0f} "
              f"(median {statistics.median(dm):+5.0f}, better {sum(x > 0 for x in dm)}, "
              f"worse {sum(x < 0 for x in dm)})  own {statistics.mean(own):+6.0f}")


if __name__ == "__main__":
    main()
