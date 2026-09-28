"""Where a candidate loses money to the top of the ladder.

Reads a corpus_pin run (<label>-c*.json, with the per-item trade log) and sums,
per good and per 5-day block, our net trade minus the top team's, split by
result and by the top team's rating band. Games whose top-team recording
drifted past --max-drift are left out.

    python -m tools.analysis.corpus_gaps top-n4 --max-drift 0.05
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.pin_compare import load  # noqa: E402


def band(x: float) -> str:
    return "2800+" if x >= 2800 else "2600-2800" if x >= 2600 else "2450-2600" if x >= 2450 else "<2450"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("--max-drift", type=float, default=0.05)
    args = ap.parse_args()
    rows = [r for r in load(args.label).values() if r.get("drift", 0) <= args.max_drift and "trade" in r]
    if not rows:
        print("no rows")
        return
    won = [r for r in rows if r["won"]]
    print(f"{args.label}: {len(rows)} games with drift <= {args.max_drift}: won {len(won)} "
          f"({100 * len(won) / len(rows):.0f}%), margin median "
          f"{statistics.median(r['us'] - r['them'] for r in rows):+,.0f}")
    by_band = defaultdict(list)
    for r in rows:
        by_band[band(r.get("opponent_rating") or 0)].append(r)
    for b in ("2800+", "2600-2800", "2450-2600", "<2450"):
        rs = by_band.get(b, [])
        if rs:
            print(f"  vs {b:9}: {len(rs):4} games, won {sum(r['won'] for r in rs):4} "
                  f"({100 * sum(r['won'] for r in rs) / len(rs):3.0f}%), margin median "
                  f"{statistics.median(r['us'] - r['them'] for r in rs):+8,.0f}")

    def gaps(rs):
        item, block = defaultdict(float), defaultdict(float)
        for r in rs:
            for who, sign in (("us", 1), ("them", -1)):
                for k, v in r["trade"].get(who, {}).items():
                    it, blk = k.split(":")
                    item[it] += sign * v / len(rs)
                    block[int(blk)] += sign * v / len(rs)
        return item, block

    for name, rs in (("lost games", [r for r in rows if not r["won"]]), ("won games", won)):
        if not rs:
            continue
        item, block = gaps(rs)
        print(f"\n{name} ({len(rs)}): trade gap per game, us minus them "
              f"(the rest of the money gap is spending: seeds, animals, hires, land)")
        for it, v in sorted(item.items(), key=lambda kv: kv[1]):
            print(f"  {it:11} {v:+9,.0f}")
        print("  by days:    " + "  ".join(f"{5 * b}-{5 * b + 4}: {v:+,.0f}" for b, v in sorted(block.items())))
        spend = statistics.mean((r["us"] - r["them"]) - sum(
            sign * v for who, sign in (("us", 1), ("them", -1)) for v in r["trade"].get(who, {}).values())
            for r in rs)
        print(f"  spending gap (money gap minus trade gap), per game: {spend:+,.0f}")


if __name__ == "__main__":
    main()
