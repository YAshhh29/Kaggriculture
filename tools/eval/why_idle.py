"""Why is a worker idle? Ask the board, do not guess.

Candidate G passes on roughly a fifth of its worker turns. Four changes
have been made on guesses about why -- more land, a bigger herd, more
kinds of job, a second shed errand -- and all four lost. This measures it
instead.

A worker ends up idle for exactly one of two reasons:

* **starved** -- the board offered jobs, but other workers claimed every
  tile first, so there were more hands than jobs;
* **barren** -- no tile on the board offered this worker any job at all,
  whatever the other workers did.

The distinction decides everything. Starved means the farm needs more
work on the ground and the earlier experiments were right in kind and
wrong in detail. Barren means the crew is too large for the farm, or the
job list itself refuses to offer anything, and no amount of extra land or
livestock will help.

    python -m tools.eval.why_idle --seeds 3
"""

from __future__ import annotations

import argparse
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE = "kaggle_cache/live_clones/live_106683123.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=3)
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    import candidates.candidate_g as G
    from tools.eval.measure_panel import resolve

    opponent = resolve("clone:" + ROUTE)

    for seed in range(11, 11 + args.seeds):
        reason: Counter[str] = Counter()
        by_day: dict[int, list[int]] = {}
        tiles_offering: list[int] = []
        crew: list[int] = []

        original = G.job_value

        def decide_and_watch(observation, *rest):
            farm = G._farm(observation)
            board = farm.get("tiles") or []
            if not board:
                return G.agent(observation)

            day = int(observation.get("day", 0))
            positions = G._positions(farm)
            shed = G._shed(observation)
            seeds_held = G._seeds(observation)
            counts = G.census(board)
            closing = day >= G.LAST_DAY - 1

            # Which tiles offer *any* worker a job, ignoring contention.
            offering = 0
            per_worker_has_job = [False] * len(positions)
            for y in range(len(board)):
                for x in range(len(board[y])):
                    if not G._owned(board, x, y):
                        continue
                    tile_offers = False
                    for worker in range(len(positions)):
                        jobs = original(
                            observation, board[y][x], x, y,
                            G._inventory(observation, worker), day,
                            shed, seeds_held, counts, closing,
                        )
                        if jobs:
                            tile_offers = True
                            per_worker_has_job[worker] = True
                    if tile_offers:
                        offering += 1

            action = G.agent(observation)
            units = [action.get("farmer"), *(action.get("hands") or [])]
            idle = [i for i, u in enumerate(units)
                    if isinstance(u, list) and u and u[0] == "PASS"]
            for worker in idle:
                if worker < len(per_worker_has_job) and per_worker_has_job[worker]:
                    reason["starved (jobs existed, tiles taken)"] += 1
                    by_day.setdefault(day, [0, 0])[0] += 1
                else:
                    reason["barren (no job anywhere for them)"] += 1
                    by_day.setdefault(day, [0, 0])[1] += 1
            tiles_offering.append(offering)
            crew.append(len(positions))
            return action

        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": seed},
                   debug=False)
        env.run([decide_and_watch, opponent])

        total_idle = sum(reason.values())
        print(f"\n=== seed {seed}   final {env.state[0].reward:,.0f} ===")
        print(f"  idle worker-turns: {total_idle}")
        for label, count in reason.most_common():
            print(f"    {label:38s} {count:6d}  {count / max(1, total_idle):6.1%}")
        print(f"  tiles offering work, mean {statistics.mean(tiles_offering):.1f}"
              f"   crew mean {statistics.mean(crew):.1f}")
        print(f"  {'day':>4} {'starved':>9} {'barren':>8}")
        for day in sorted(by_day):
            if day % 5 == 0 or day >= 27:
                starved, barren = by_day[day]
                print(f"  {day:>4} {starved:>9} {barren:>8}")


if __name__ == "__main__":
    main()
