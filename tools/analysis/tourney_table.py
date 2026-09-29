"""Win table of several agents on the same corpus games (corpus_pin labels).

    python -m tools.analysis.tourney_table N=top-n2m N6=top-n6 N2=t710-n2 ...
Games are those every listed agent played, with each agent's top-team
recording within --max-drift (default 0.15).
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.pin_compare import load  # noqa: E402


def band(x):
    return "2700+" if x >= 2700 else "2600-2700" if x >= 2600 else "2450-2600" if x >= 2450 else "<2450"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agents", nargs="+", help="NAME=label")
    ap.add_argument("--max-drift", type=float, default=0.15)
    ap.add_argument("--episodes", default=None, help="file of episode ids to restrict to")
    args = ap.parse_args()
    runs = {}
    for a in args.agents:
        name, label = a.split("=", 1)
        runs[name] = load(label)
    games = set.intersection(*(set(r) for r in runs.values()))
    if args.episodes:
        games &= {int(x) for x in Path(args.episodes).read_text().split()}
    games = sorted(e for e in games if all(r[e].get("drift", 0) <= args.max_drift for r in runs.values()))
    ref = next(iter(runs.values()))
    bands = ("<2450", "2450-2600", "2600-2700", "2700+")
    print(f"{len(games)} games (every agent, drift <= {args.max_drift}); by the top team's rating:")
    print(f"{'agent':8} {'won':>5} {'win%':>6} {'margin med':>11} " + " ".join(f"{b:>11}" for b in bands))
    rows = []
    for name, r in runs.items():
        won = sum(r[e]["us"] > r[e]["them"] for e in games)
        med = statistics.median(r[e]["us"] - r[e]["them"] for e in games)
        per = []
        for b in bands:
            es = [e for e in games if band(ref[e].get("opponent_rating") or 0) == b]
            per.append(f"{sum(r[e]['us'] > r[e]['them'] for e in es):>4}/{len(es):<4}")
        rows.append((won, name, med, per))
    for won, name, med, per in sorted(rows, reverse=True):
        print(f"{name:8} {won:5} {100 * won / len(games):5.1f}% {med:+11,.0f} " + " ".join(f"{p:>11}" for p in per))


if __name__ == "__main__":
    main()
