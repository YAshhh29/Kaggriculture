"""Play candidates against a live-validated agent, not against recordings.

The frozen-tape panel is disqualified as a selection instrument. It scored
Candidate F 18.7 points above Candidate D on identical games; live, D
holds an internal rating near 1744 and F near 1687, displayed 1356. It did
not merely mis-scale, it **inverted the ordering it was being used to
make**, and a route chosen on it went to the ladder and lost 350 points.

The reason is structural. A recording cannot respond to anything we do, so
a strategy that exploits an opponent's inability to react scores far above
its worth, and the panel rewards exactly that. Both sides of a head to
head can react.

Candidate D is the only agent we have with a settled live rating, so it is
the reference here: a change that cannot beat D on identical seeds has no
claim on a submission slot, whatever a panel says.

    python -m tools.eval.head_to_head rl.candidate_e:agent \\
        --reference rl.candidate_d:agent --seeds 24
"""

from __future__ import annotations

import argparse
import statistics
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.eval.measure_panel import resolve  # noqa: E402

SEEDS = (11, 29, 53, 97, 131, 173, 211, 257, 307, 353, 401, 449,
         503, 557, 601, 647, 701, 757, 809, 853, 907, 953, 1009, 1051,
         1103, 1151, 1201, 1259, 1301, 1361, 1409, 1459)


def play(job) -> dict[str, Any]:
    spec, reference, seed, seat = job
    from kaggle_environments import make

    mine = resolve(spec)
    theirs = resolve(reference)
    players = [mine, theirs] if seat == 0 else [theirs, mine]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(players)
    final = env.steps[-1]
    ours = float(final[seat].get("reward") or 0.0)
    rival = float(final[1 - seat].get("reward") or 0.0)
    return {"spec": spec, "seed": seed, "seat": seat, "ours": ours,
            "theirs": rival, "won": ours > rival,
            "status": str(final[seat].get("status"))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specs", nargs="+")
    parser.add_argument("--reference", action="append", default=None)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--workers", type=int, default=11)
    parser.add_argument("--label", action="append", default=None)
    args = parser.parse_args()

    seeds = SEEDS[: args.seeds]
    labels = list(args.label or [])
    labels += [s for s in args.specs[len(labels):]]
    references = args.reference or ["rl.candidate_d:agent"]
    print("field: " + ", ".join(references))
    print(f"{len(seeds)} seeds x 2 seats x {len(references)} opponents = "
          f"{len(seeds) * 2 * len(references)} games each\n", flush=True)
    print(f"  {'candidate':34s} {'wins':>10s} {'ours':>10s} "
          f"{'theirs':>10s} {'median margin':>14s}")
    for spec, label in zip(args.specs, labels):
        jobs = [(spec, ref, s, seat)
                for ref in references for s in seeds for seat in (0, 1)]
        with Pool(min(args.workers, len(jobs))) as pool:
            out = pool.map(play, jobs)
        wins = sum(1 for g in out if g["won"])
        margins = [g["ours"] - g["theirs"] for g in out]
        errors = sum(1 for g in out if g["status"] != "DONE")
        print(f"  {label:34s} {wins:4d}/{len(out)} "
              f"{wins / len(out):5.1%} "
              f"{statistics.mean(g['ours'] for g in out):10,.0f} "
              f"{statistics.mean(g['theirs'] for g in out):10,.0f} "
              f"{statistics.median(margins):+14,.0f}"
              + (f"  ERR {errors}" if errors else ""), flush=True)


if __name__ == "__main__":
    main()
