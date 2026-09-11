"""Sweep one constant against many contested opponents.

This replaces the three-route harnesses that produced every unsound
measurement in this project. Those ran sixty games against *three*
strategies, which cannot distinguish a real gain from one that happens to
suit three opponents -- a COMPACT value was committed on 42 of 60 paired
wins there and turned out to lose against thirty-six opponents, taking
the win count from four to nought.

Every sweep here goes through the same contested panel the agent is
judged on. It is roughly five times slower. That is the price of the
numbers meaning anything.

    python -m tools.eval.refit COMPACT 0.15 0.25 0.35
    python -m tools.eval.refit HAND_CAP 12 13 --opponents 24
"""

from __future__ import annotations

import argparse
import statistics
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("values", nargs="+")
    parser.add_argument("--spec", default="rl.candidate_g:agent")
    parser.add_argument("--opponents", type=int, default=30)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--min-rating", type=float, default=2800.0)
    parser.add_argument("--contested", type=float, default=15000.0)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    from tools.eval.wide_panel import best_tape_per_opponent, one

    def parse(raw: str):
        if raw.lower() in ("true", "false"):
            return raw.lower() == "true"
        return float(raw) if ("." in raw or "e" in raw.lower()) else int(raw)

    values = [parse(v) for v in args.values]
    field = best_tape_per_opponent(args.opponents, args.min_rating,
                                   args.contested)
    seeds = list(range(11, 11 + args.seeds))
    if not field:
        raise SystemExit("no contested tapes held; fetch some first")

    print(f"{args.name}: {len(field)} contested opponents x {len(seeds)} "
          f"seeds x 2 seats = {len(field) * len(seeds) * 2} games each",
          flush=True)

    results: dict[object, list[tuple[float, float]]] = {}
    for value in values:
        jobs = [(args.spec, {args.name: value}, tape, seed, seat)
                for _, tape, _ in field
                for seed in seeds
                for seat in (0, 1)]
        with Pool(args.workers) as pool:
            rows = pool.map(one, jobs)
        results[value] = rows
        mine = [a for a, _ in rows]
        wins = sum(1 for a, b in rows if a > b)
        margin = statistics.mean(a - b for a, b in rows)
        print(f"  {args.name}={value!r:>10}  mean {statistics.mean(mine):9,.0f}"
              f"  median {statistics.median(mine):9,.0f}"
              f"  floor {min(mine):8,.0f}"
              f"  wins {wins:3d}/{len(mine)}"
              f"  margin {margin:+9,.0f}", flush=True)

    base = values[0]
    for value in values[1:]:
        better = sum(1 for (a, _), (b, _) in zip(results[base], results[value])
                     if b > a)
        n = len(results[base])
        print(f"  {value!r} beats {base!r} on {better}/{n} paired games",
              flush=True)


if __name__ == "__main__":
    main()
