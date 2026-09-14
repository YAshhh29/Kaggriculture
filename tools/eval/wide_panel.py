"""Measure an agent against many distinct opponents, not three.

Every constant in Candidate G was fitted against three tapes at ten
seeds. That is sixty games against *three* strategies, and it cannot tell
a real improvement from one that happens to suit those three. The cache
holds 404 tapes from 67 distinct opponents; this uses them.

One tape per opponent, highest-rated first, so the panel is 67 different
strategies rather than 67 samples of a handful. Both seats, so a seat
advantage cannot flatter the result.

    python -m tools.eval.wide_panel rl.candidate_g:agent --opponents 40
    python -m tools.eval.wide_panel rl.candidate_g:agent --set WHEAT_TILES=20

Reports the mean, the median, the floor, and the win rate -- the win rate
being the one number that matters on a ladder and the one a three-tape
panel cannot estimate at all.
"""

from __future__ import annotations

import argparse
import json
import statistics
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def best_tape_per_opponent(limit: int, min_rating: float,
                           contested: float = 0.0) -> list[tuple[str, str, float]]:
    """(name, tape path, rating), one tape each, strongest opponents first.

    `contested` keeps only tapes from games the winner won by less than
    that margin against an opponent also above `min_rating`. It matters:
    across 2,348 games between top-45 teams the winner banks a median
    98,994 and the loser 93,765, a margin of 3,906. A tape chosen for its
    owner's rating alone is usually a blowout against somebody weak, and
    measuring against those flatters nobody -- it tells us how a strong
    farm performs when unopposed, which is not the game we play.
    """
    from tools.data.profile_tapes import INDEX, TAPES

    # Only games played by a submission that is on the board *now*. The
    # match snapshot is rebuilt from each top team's current submission, so
    # an episode missing from it belongs to an agent that has since been
    # replaced or has fallen away. Four days after one refresh, 24 of 30
    # panel tapes were in that state and the panel was measuring G against
    # opponents nobody plays any more.
    matches = ROOT / "rl" / "data" / "top_matches.jsonl"
    current = {int(json.loads(line)["episode_id"])
               for line in matches.read_text(encoding="utf-8").splitlines()}

    best: dict[str, tuple[str, float]] = {}
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if int(row["episode_id"]) not in current:
            continue
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists():
            continue
        rating = float(row.get("rating") or 0)
        if rating < min_rating:
            continue
        if contested:
            if float(row.get("beat_rating") or 0) < min_rating:
                continue
            if abs(float(row.get("margin") or 0)) > contested:
                continue
        name = str(row.get("name") or "?")
        # Newest tape for each opponent at their best rating: an agent's
        # play from weeks ago is not what it plays now.
        key = (rating, int(row["episode_id"]))
        if name not in best or key > best[name][1]:
            best[name] = (str(path), key)
    ranked = sorted(best.items(), key=lambda kv: (-kv[1][1][0], -kv[1][1][1]))
    return [(n, p, r[0]) for n, (p, r) in ranked[:limit]]


def one(job):
    spec, overrides, tape, seed, seat = job
    from kaggle_environments import make

    from tools.eval.measure_panel import resolve

    module_name, attr = spec.split(":")
    import importlib

    module = importlib.import_module(module_name)
    for key, value in (overrides or {}).items():
        setattr(module, key, value)
    mine = getattr(module, attr)
    opponent = resolve("clone:" + tape)
    agents = [mine, opponent] if seat == 0 else [opponent, mine]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(agents)
    return (env.state[seat].reward or 0, env.state[1 - seat].reward or 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--opponents", type=int, default=40)
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--min-rating", type=float, default=2700.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--contested", type=float, default=0.0,
                        help="only tapes won by less than this margin "
                             "against an opponent also above --min-rating")
    parser.add_argument("--set", action="append", default=[],
                        help="NAME=VALUE override, repeatable")
    args = parser.parse_args()

    overrides = {}
    for item in args.set:
        name, _, raw = item.partition("=")
        overrides[name] = (float(raw) if ("." in raw or "-" in raw)
                           else int(raw))

    field = best_tape_per_opponent(args.opponents, args.min_rating,
                                   args.contested)
    seeds = list(range(11, 11 + args.seeds))
    jobs = [(args.spec, overrides, tape, seed, seat)
            for _, tape, _ in field
            for seed in seeds
            for seat in (0, 1)]

    print(f"{len(field)} distinct opponents x {len(seeds)} seeds x 2 seats "
          f"= {len(jobs)} games", flush=True)
    if overrides:
        print(f"overrides: {overrides}", flush=True)

    with Pool(args.workers) as pool:
        results = pool.map(one, jobs)

    mine = [a for a, _ in results]
    wins = sum(1 for a, b in results if a > b)
    print(f"\n  mean   {statistics.mean(mine):9,.0f}")
    print(f"  median {statistics.median(mine):9,.0f}")
    print(f"  floor  {min(mine):9,.0f}")
    print(f"  WINS   {wins}/{len(mine)}  ({wins / len(mine):.1%})")

    # Where we lose worst, which is where the strategy is wrong.
    per: dict[str, list[float]] = {}
    for (name, _, _), idx in zip(field, range(0, len(results), len(seeds) * 2)):
        chunk = results[idx:idx + len(seeds) * 2]
        per[name] = [a - b for a, b in chunk]
    worst = sorted(per.items(), key=lambda kv: statistics.mean(kv[1]))[:8]
    print("\n  worst matchups (mean margin):")
    for name, margins in worst:
        print(f"    {name[:26]:28s} {statistics.mean(margins):+10,.0f}")


if __name__ == "__main__":
    main()
