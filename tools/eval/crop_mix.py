"""Compare whole crop mixes against the contested panel.

`refit` sweeps a scalar; CROP_TILES is a tuple of (crop, cap) pairs and
needs its own comparison. Named mixes are defined below and measured on
the same panel and the same margin metric as everything else.

    python -m tools.eval.crop_mix --opponents 30
"""

from __future__ import annotations

import argparse
import statistics
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIXES: dict[str, dict] = {
    "now (no tomato)": {},
    "tomato 12": {
        "CROP_TILES": (("TOMATO", 12), ("MELON", 12), ("CARROT", 16),
                       ("STRAWBERRY", 8)),
    },
    "tomato 20, no straw": {
        "CROP_TILES": (("TOMATO", 20), ("MELON", 12), ("CARROT", 16)),
    },
    "tomato first 20": {
        "CROP_TILES": (("TOMATO", 20), ("MELON", 12), ("CARROT", 16),
                       ("STRAWBERRY", 8)),
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponents", type=int, default=30)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--min-rating", type=float, default=2800.0)
    parser.add_argument("--contested", type=float, default=15000.0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--only", action="append", default=[])
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    from tools.eval.wide_panel import best_tape_per_opponent, one

    field = best_tape_per_opponent(args.opponents, args.min_rating,
                                   args.contested)
    if not field:
        raise SystemExit("no contested tapes held")
    seeds = list(range(11, 11 + args.seeds))
    names = args.only or list(MIXES)
    print(f"{len(field)} contested opponents x {len(seeds)} seeds x 2 seats "
          f"= {len(field) * len(seeds) * 2} games each", flush=True)

    out: dict[str, list] = {}
    for name in names:
        jobs = [("rl.candidate_g:agent", MIXES[name], tape, seed, seat)
                for _, tape, _ in field
                for seed in seeds
                for seat in (0, 1)]
        with Pool(args.workers) as pool:
            rows = pool.map(one, jobs)
        out[name] = rows
        mine = [a for a, _ in rows]
        wins = sum(1 for a, b in rows if a > b)
        margin = statistics.mean(a - b for a, b in rows)
        print(f"  {name:22s} mean {statistics.mean(mine):9,.0f}"
              f"  median {statistics.median(mine):9,.0f}"
              f"  wins {wins:3d}/{len(mine)}"
              f"  margin {margin:+9,.0f}", flush=True)

    base = names[0]
    for name in names[1:]:
        better = sum(1 for (a, _), (b, _) in zip(out[base], out[name]) if b > a)
        print(f"  {name} beats {base} on {better}/{len(out[base])}", flush=True)


if __name__ == "__main__":
    main()
