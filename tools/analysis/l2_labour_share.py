"""Share of idle/no-op hand-turns with any in-place option, and with a valued one.

Reads rl/data/l2/labour/audit_<label>.json (tools.analysis.l2_labour_audit).

    python -m tools.analysis.l2_labour_share L A
"""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for label in sys.argv[1:] or ["L"]:
    games = json.loads((ROOT / "rl/data/l2/labour" / f"audit_{label}.json").read_text(encoding="utf-8"))
    per = []
    for g in games:
        idle = len(g["idle_detail"])
        anyc = sum(1 for o in g["idle_detail"] if o["cands"])
        valued = {(r["step"], r["idx"]) for r in g["opps"] if r["gain"] > 0}
        per.append((idle, anyc, len(valued),
                    sum(r["gain"] for r in g["opps"] if r["first"]),
                    g["turns"].get("pass/hand", 0) + g["turns"].get("absent/hand", 0),
                    g["turns"].get("noop/hand", 0),
                    g["turns"].get("pass/farmer", 0), g["turns"].get("noop/farmer", 0)))
    n = len(per)
    col = lambda i: [p[i] for p in per]
    print(f"{label}: {n} games")
    print(f"  idle+no-op unit-turns/game median {statistics.median(col(0)):.0f} "
          f"(hand PASS {statistics.median(col(4)):.0f}, hand no-op {statistics.median(col(5)):.0f}, "
          f"farmer PASS {statistics.median(col(6)):.0f}, farmer no-op {statistics.median(col(7)):.0f})")
    print(f"  with any in-place option: median {statistics.median(col(1)):.0f} "
          f"({sum(col(1)) / sum(col(0)):.0%} of idle turns)")
    print(f"  with a valued option (gain > 0 against the tape's own future): median "
          f"{statistics.median(col(2)):.0f}, mean {statistics.mean(col(2)):.1f} "
          f"({sum(col(2)) / sum(col(0)):.2%})")
    print(f"  valued coins/game: mean {statistics.mean(col(3)):.0f}, median {statistics.median(col(3)):.0f}, "
          f"max {max(col(3)):.0f}")
    top = Counter()
    for g in games:
        for o in g["idle_detail"]:
            top[(o["kind"], tuple(o["cands"]))] += 1
    print("  most common (tile, in-place options) at idle turns, per game:")
    for (k, c), v in top.most_common(8):
        print(f"    {v / n:6.1f}  {k}: {list(c)}")
