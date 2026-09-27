"""Which programs our live opponents play, from shadow-sync runs.

    python -m tools.analysis.sync_presence new80_56613410 new80_56609589

Per program: games it matched the opponent for all 719 turns, and games it
matched past day 16. Programs already in the L5/M shadow library are marked.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main(labels: list[str]) -> None:
    from rl.l2_combo import M_LIBRARY_EXTRA, NEW_LIBRARY
    from rl.l2_shadow import SH_LIBRARY
    library = set(SH_LIBRARY) | set(NEW_LIBRARY) | set(M_LIBRARY_EXTRA)
    presence = defaultdict(lambda: [0, 0])
    games = 0
    best_by_game = []
    for label in labels:
        rows = json.loads((ROOT / "rl" / "data" / "l2" / "shadow" / f"sync_{label}.json").read_text(encoding="utf-8"))
        for r in rows:
            games += 1
            best = None
            for name, c in r["candidates"].items():
                if "error" in c:
                    continue
                fm = c.get("first_miss")
                if fm is None:
                    presence[name][0] += 1
                    best = best or name
                elif fm >= 384:
                    presence[name][1] += 1
            best_by_game.append(best)
    covered = sum(1 for b in best_by_game if b)
    print(f"{games} games; an exact public program all game in {covered}")
    print(f"  {'program':60s} {'all game':>8s} {'> day 16':>8s}  in library")
    for name, (a, b) in sorted(presence.items(), key=lambda kv: -(3 * kv[1][0] + kv[1][1])):
        if a or b:
            print(f"  {name:60s} {a:8d} {b:8d}  {'yes' if name in library else ''}")


if __name__ == "__main__":
    main(sys.argv[1:])
