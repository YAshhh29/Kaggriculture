"""A pass/fail battery an agent must clear before it is uploaded.

`measure_panel` produces numbers and `diagnose_agent` explains them.
Neither answers the question that actually gates a release: is this thing
safe to send, and is it better than what is already live, by enough that
the difference is not seed noise?

So this runs a fixed battery against the incumbent on identical games and
reports each check as PASS or FAIL:

1.  **completion** -- every game reaches DONE. A crash or a timeout on
    Kaggle scores zero, so this is a hard gate rather than a metric.
2.  **ladder win rate** -- beats the incumbent against the field we are
    drawn from.
3.  **elite win rate** -- beats the incumbent against 2700+ opposition,
    which is the bracket a rating is actually decided in (10.8x).
4.  **head to head** -- plays the incumbent directly. A panel of
    recordings can flatter both; this cannot.
5.  **seed stability** -- the win rate does not swing wildly with the
    seed. Candidate D moves 40.6% to 62.5% on identical games between two
    seeds (10.8u), so a one-seed result is not a result.
6.  **seat balance** -- wins from both seats. The market is one shared
    inventory and seat order decides who sells into a glut first, so an
    agent that only works from seat 0 will lose half its real games.
7.  **no dominant nemesis** -- no single opponent takes more than half
    its games. Concentrated losses are survivable; an opponent that beats
    us every time is a hole the ladder will find.

    python -m tools.eval.bulletproof rl.candidate_f:agent \\
        --incumbent rl.candidate_d:agent --seeds 11,29,53,97
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.eval.measure_panel import panel, resolve  # noqa: E402


def play(job) -> dict[str, Any]:
    """One game. `opponent` is a tape path, or a spec for head to head."""
    spec, opponent, seed, seat, tape = job
    from kaggle_environments import make

    from rl.replay_agent import load_replay_agent

    mine = resolve(spec)
    theirs = (
        load_replay_agent(Path(opponent)) if tape else resolve(opponent)
    )
    players = [mine, theirs] if seat == 0 else [theirs, mine]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(players)
    final = env.steps[-1]
    ours = float(final[seat].get("reward") or 0.0)
    rival = float(final[1 - seat].get("reward") or 0.0)
    return {
        "ours": ours,
        "theirs": rival,
        "won": ours > rival,
        "seed": seed,
        "seat": seat,
        "status": str(final[seat].get("status")),
        "opponent": Path(opponent).stem if tape else opponent,
    }


def run(spec: str, rows: list[dict[str, Any]], seeds: tuple[int, ...],
        workers: int) -> list[dict[str, Any]]:
    jobs = [(spec, r["path"], s, seat, True)
            for r in rows for s in seeds for seat in (0, 1)]
    with Pool(workers) as pool:
        return pool.map(play, jobs)


def rate(games: list[dict[str, Any]]) -> float:
    return sum(1 for g in games if g["won"]) / max(1, len(games))


def line(name: str, ok: bool, detail: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}", flush=True)
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--incumbent", default="rl.candidate_d:agent")
    parser.add_argument("--seeds", default="11,29,53,97")
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--skip", type=int, default=8)
    parser.add_argument("--workers", type=int, default=11)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    seeds = tuple(int(s) for s in args.seeds.split(","))
    ladder = panel("ladder", args.limit, args.skip)
    elite = panel("elite", args.limit, 0)
    results: dict[str, Any] = {}
    checks: list[bool] = []

    print(f"\ncandidate  {args.spec}")
    print(f"incumbent  {args.incumbent}")
    print(f"seeds {seeds}   ladder {len(ladder)} tapes   "
          f"elite {len(elite)} tapes   "
          f"{len(seeds) * 2 * (len(ladder) + len(elite))} games each\n")

    for label, rows in (("ladder", ladder), ("elite", elite)):
        mine = run(args.spec, rows, seeds, args.workers)
        theirs = run(args.incumbent, rows, seeds, args.workers)
        results[label] = {"mine": mine, "theirs": theirs}
        a, b = rate(mine), rate(theirs)
        print(f"=== {label} panel ===")
        print(f"  candidate {sum(1 for g in mine if g['won']):4d}/{len(mine)} "
              f"= {a:6.1%}   mean coins "
              f"{statistics.mean(g['ours'] for g in mine):9,.0f}   "
              f"median margin "
              f"{statistics.median(g['ours'] - g['theirs'] for g in mine):+9,.0f}")
        print(f"  incumbent {sum(1 for g in theirs if g['won']):4d}/{len(theirs)} "
              f"= {b:6.1%}   mean coins "
              f"{statistics.mean(g['ours'] for g in theirs):9,.0f}   "
              f"median margin "
              f"{statistics.median(g['ours'] - g['theirs'] for g in theirs):+9,.0f}")
        checks.append(line(f"{label} beats incumbent", a > b,
                           f"{a:.1%} vs {b:.1%}"))
        bad = [g for g in mine if g["status"] != "DONE"]
        checks.append(line(f"{label} all games DONE", not bad,
                           f"{len(mine) - len(bad)}/{len(mine)} finished"))
        by_seed = {s: rate([g for g in mine if g["seed"] == s]) for s in seeds}
        spread = max(by_seed.values()) - min(by_seed.values())
        checks.append(line(
            f"{label} seed stability", spread <= 0.25,
            "spread " + f"{spread:.1%} across " +
            " ".join(f"{s}:{v:.0%}" for s, v in by_seed.items())))
        seat0 = rate([g for g in mine if g["seat"] == 0])
        seat1 = rate([g for g in mine if g["seat"] == 1])
        checks.append(line(f"{label} seat balance",
                           min(seat0, seat1) > 0.4,
                           f"seat0 {seat0:.1%}  seat1 {seat1:.1%}"))
        beaten: dict[str, list[bool]] = defaultdict(list)
        for g in mine:
            beaten[g["opponent"]].append(g["won"])
        worst = min(
            ((sum(v) / len(v), k) for k, v in beaten.items() if len(v) >= 2),
            default=(1.0, "-"),
        )
        checks.append(line(f"{label} no dominant nemesis", worst[0] >= 0.5,
                           f"worst opponent {worst[1][:24]} at {worst[0]:.0%}"))
        print()

    print("=== head to head ===")
    jobs = [(args.spec, args.incumbent, s, seat, False)
            for s in seeds for seat in (0, 1)]
    with Pool(min(args.workers, len(jobs))) as pool:
        h2h = pool.map(play, jobs)
    results["head_to_head"] = h2h
    won = sum(1 for g in h2h if g["won"])
    print(f"  candidate {statistics.mean(g['ours'] for g in h2h):9,.0f}   "
          f"incumbent {statistics.mean(g['theirs'] for g in h2h):9,.0f}")
    checks.append(line("beats incumbent directly", won > len(h2h) / 2,
                       f"{won}/{len(h2h)} games"))

    print(f"\n{sum(checks)}/{len(checks)} checks passed")
    if args.out:
        Path(args.out).write_text(json.dumps(results, default=str),
                                  encoding="utf-8")
    raise SystemExit(0 if all(checks) else 1)


if __name__ == "__main__":
    main()
