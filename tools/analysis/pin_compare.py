"""Compare two pinned-night replay runs split into chunks (l2_land_pin labels
<prefix>-c1..cN), game by game: wins, flips, margin change, by opponent band.

    python -m tools.analysis.pin_compare all-n3twfa all-n4d9
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "rl" / "data" / "l2" / "land" / "replays"


def load(prefix: str) -> dict:
    rows = {}
    for p in sorted(OUT.glob(f"{prefix}-c*.json")) + ([OUT / f"{prefix}.json"] if (OUT / f"{prefix}.json").exists() else []):
        for r in json.loads(p.read_text(encoding="utf-8")):
            if "skip" not in r and "us" in r:
                rows[r["episode_id"]] = r
    return rows


def band(r) -> str:
    x = r.get("opponent_rating") or 0
    if x >= 2600:
        return "2700+" if x >= 2700 else "2600-2700"
    return "<2300" if x < 2300 else "2300-2400" if x < 2400 else "2400-2600"


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("cand")
    ap.add_argument("--max-drift", type=float, default=None,
                    help="only games where both arms' opponent drift is at most this")
    args = ap.parse_args()
    sys.argv[1:3] = [args.base, args.cand]
    base, cand = load(args.base), load(args.cand)
    shared = sorted(set(base) & set(cand))
    if args.max_drift is not None:
        before = len(shared)
        shared = [e for e in shared if base[e].get("drift", 0) <= args.max_drift
                  and cand[e].get("drift", 0) <= args.max_drift]
        print(f"(drift <= {args.max_drift}: {len(shared)} of {before} games)")
    m = {e: (base[e]["us"] - base[e]["them"], cand[e]["us"] - cand[e]["them"]) for e in shared}
    wa = sum(a > 0 for a, _ in m.values())
    wb = sum(b > 0 for _, b in m.values())
    up = [e for e, (a, b) in m.items() if a <= 0 < b]
    down = [e for e, (a, b) in m.items() if b <= 0 < a]
    d = [b - a for a, b in m.values()]
    print(f"{sys.argv[2]} vs {sys.argv[1]}: {len(shared)} games | wins {wa} -> {wb} (+{len(up)} -{len(down)}) | "
          f"margin change mean {statistics.mean(d):+,.0f} median {statistics.median(d):+,.0f} "
          f"(better {sum(x > 0 for x in d)}, worse {sum(x < 0 for x in d)})")
    for b_ in ("<2300", "2300-2400", "2400-2600", "2600-2700", "2700+"):
        es = [e for e in shared if band(base[e]) == b_]
        if es:
            print(f"  {b_:9}: {len(es):3} games, wins {sum(m[e][0] > 0 for e in es)} -> {sum(m[e][1] > 0 for e in es)}, "
                  f"margin {sum(m[e][1] - m[e][0] for e in es):+,.0f}")
    for tag, es in (("to wins", up), ("to losses", down)):
        for e in es:
            print(f"  flip {tag}: {e} {base[e].get('opponent')} {m[e][0]:+,.0f} -> {m[e][1]:+,.0f}")
    worst = sorted(shared, key=lambda e: m[e][1] - m[e][0])[:5]
    print("  worst: " + ", ".join(f"{e} {base[e].get('opponent', '')[:12]} {m[e][1] - m[e][0]:+,.0f}" for e in worst))


if __name__ == "__main__":
    main()
