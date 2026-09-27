"""Game-by-game difference between two live-replay runs of the same games.

    python -m tools.analysis.replay_diff l4-on-l3-live l4c-on-l3-live

Prints wins for each, flips, the margin change per game (median, best, worst),
and the games whose replay drifted from the live opponent (desync) separately,
since a drifted tape no longer shows what the real opponent would have done.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "rl" / "data" / "live_replays"


def load(slug: str) -> dict:
    d = json.loads((RUNS / f"{slug}.json").read_text(encoding="utf-8"))
    return {g["episode_id"]: g for g in d["games"] if "reward" in g}


def margin(g: dict) -> float:
    return g["reward"]["us"] - g["reward"]["them"]


def main(a: str, b: str, drift_max: float = 0.02) -> None:
    A, B = load(a), load(b)
    common = sorted(set(A) & set(B))
    clean = [e for e in common
             if A[e].get("opponent_drift", 0) <= drift_max and B[e].get("opponent_drift", 0) <= drift_max]
    for label, eps in (("all", common), (f"clean (drift <= {drift_max})", clean)):
        if not eps:
            continue
        diffs = [margin(B[e]) - margin(A[e]) for e in eps]
        wa = sum(margin(A[e]) > 0 for e in eps)
        wb = sum(margin(B[e]) > 0 for e in eps)
        up = sum(margin(A[e]) <= 0 < margin(B[e]) for e in eps)
        down = sum(margin(B[e]) <= 0 < margin(A[e]) for e in eps)
        print(f"{label}: {len(eps)} games | {a} won {wa} | {b} won {wb} | flips +{up} -{down} | "
              f"{b} better in {sum(d > 0 for d in diffs)}, worse in {sum(d < 0 for d in diffs)}, "
              f"median {statistics.median(diffs):+.0f}, total {sum(diffs):+.0f}")
    worst = sorted(common, key=lambda e: margin(B[e]) - margin(A[e]))
    print("worst for", b)
    for e in worst[:6]:
        print(f"  ep {e} {str(A[e].get('opponent'))[:16]:16s} {margin(A[e]):+9.0f} -> {margin(B[e]):+9.0f}"
              f"  drift {A[e].get('opponent_drift', 0):.3f}/{B[e].get('opponent_drift', 0):.3f}")
    print("best for", b)
    for e in worst[-4:]:
        print(f"  ep {e} {str(A[e].get('opponent'))[:16]:16s} {margin(A[e]):+9.0f} -> {margin(B[e]):+9.0f}"
              f"  drift {A[e].get('opponent_drift', 0):.3f}/{B[e].get('opponent_drift', 0):.3f}")


if __name__ == "__main__":
    main(*sys.argv[1:3], *(float(x) for x in sys.argv[3:4]))
