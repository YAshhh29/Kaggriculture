"""Day-by-day cash for a candidate against a strong live opponent.

The final score is a noisy way to judge a change: on twelve games it cannot
resolve anything smaller than about five thousand coins. The money held on
days 9 to 15 is the leading indicator -- every strong agent triples its purse
in that window, and a candidate that is still poor on day 15 has already lost
whatever it does afterwards.

    python -m tools.eval.early_curve candidates.candidate_j:agent --seeds 4
"""

from __future__ import annotations

import argparse
import statistics
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.eval.measure_panel import resolve  # noqa: E402

DAYS = (3, 6, 9, 12, 15, 18, 22, 26, 29)


def play(job):
    spec, reference, seed, seat = job
    from kaggle_environments import make

    mine, theirs = resolve(spec), resolve(reference)
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run([mine, theirs] if seat == 0 else [theirs, mine])
    rows = {}
    for day in DAYS:
        i = min(day * 24 + 23, len(env.steps) - 1)
        farms = env.steps[i][0]["observation"]["farms"]
        mine_f = farms[seat]
        animals = sum(1 for r in mine_f["tiles"] for t in r
                      if isinstance(t, dict) and "animal" in t)
        plants = sum(1 for r in mine_f["tiles"] for t in r
                     if isinstance(t, dict) and t.get("kind") == "PLANT")
        rows[day] = (float(mine_f["money"]), float(farms[1 - seat]["money"]),
                     animals, plants)
    return {"rows": rows, "final": float(env.state[seat].reward or 0),
            "theirs": float(env.state[1 - seat].reward or 0)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--against", default="stack.public_agents:aurax7")
    parser.add_argument("--seeds", type=int, default=4)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    seeds = (11, 29, 53, 97, 131, 173)[: max(1, args.seeds)]
    jobs = [(args.spec, args.against, s, seat) for s in seeds for seat in (0, 1)]
    with Pool(args.workers) as pool:
        games = pool.map(play, jobs)

    print(f"\n{args.spec} vs {args.against}, {len(games)} games")
    print(f"{'day':>4} {'ours':>10} {'theirs':>10} {'% of theirs':>12} "
          f"{'animals':>8} {'plants':>7}")
    for day in DAYS:
        ours = statistics.median(g["rows"][day][0] for g in games)
        theirs = statistics.median(g["rows"][day][1] for g in games)
        an = statistics.median(g["rows"][day][2] for g in games)
        pl = statistics.median(g["rows"][day][3] for g in games)
        pct = f"{100 * ours / theirs:.0f}%" if theirs > 0 else "-"
        print(f"{day:>4} {ours:>10,.0f} {theirs:>10,.0f} {pct:>12} "
              f"{an:>8.0f} {pl:>7.0f}")
    final = statistics.median(g["final"] for g in games)
    rival = statistics.median(g["theirs"] for g in games)
    wins = sum(g["final"] > g["theirs"] for g in games)
    print(f"\n  final {final:,.0f} vs {rival:,.0f} | wins {wins}/{len(games)}")


if __name__ == "__main__":
    main()
