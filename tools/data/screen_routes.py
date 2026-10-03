"""Screen every cached route by WIN RATE, the objective the ladder uses.

Each cached opponent side is replayed as a candidate route under the same
Candidate A + B guard stack, against a fixed panel of real opponents drawn
from the same corpus, both seats.

Why win rate: Kaggle's simulation ladder rates on match outcomes, so a
game won by one coin counts as much as one won by fifty thousand. Every
earlier route search in this project ranked on mean coins instead, and
section 10.8j measured that the two orderings genuinely disagree.

Why screen all of them: a side's own recorded reward does not predict its
strength as a route -- fan yanbing scored 137,331 in its own game and
screens at 48% -- so restricting the search to the highest scorers, as the
earlier passes did, is not a shortcut but a bias.

Results are appended to the output JSONL as they land, so the run is
resumable.
"""

from __future__ import annotations

import argparse
import json
import random
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLONES = ROOT / "kaggle_cache" / "clones"
INDEX = ROOT / "rl" / "data" / "candidate_d_corpus_index.jsonl"


def corpus() -> list[dict]:
    rows = []
    for line in INDEX.read_text().splitlines():
        entry = json.loads(line)
        if entry.get("type") != "episode":
            continue
        path = CLONES / f"opp_{entry['episode_id']}.json"
        if path.exists():
            rows.append({
                "episode": str(entry["episode_id"]),
                "name": entry["opponent_name"],
                "path": str(path),
                "seed": int(entry["seed"]),
                "own_reward": float(entry["opponent_reward"]),
            })
    return rows


def _one(job):
    route_path, opponent_path, seed, seat = job
    from kaggle_environments import make
    from candidates.candidate_a import build_candidate_a_agent
    from candidates.candidate_b import build_candidate_b_agent
    from rl.replay_agent import load_replay_agent

    route = load_replay_agent(Path(route_path))
    mine = build_candidate_b_agent(
        baseline=build_candidate_a_agent(baseline=route)
    )
    theirs = load_replay_agent(Path(opponent_path))
    players = [mine, theirs] if seat == 0 else [theirs, mine]
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    environment.run(players)
    final = environment.toJSON()["steps"][-1]
    return (
        final[seat].get("reward") or 0.0,
        final[1 - seat].get("reward") or 0.0,
        str(final[seat].get("status")),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponents", type=int, default=12)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--panel-seed", type=int, default=11)
    parser.add_argument(
        "--out", default=str(ROOT / "rl" / "data" / "route_screen.jsonl")
    )
    args = parser.parse_args()

    rows = corpus()
    random.seed(args.panel_seed)
    panel = random.sample(rows, args.opponents)
    out_path = Path(args.out)
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            done.add(json.loads(line)["episode"])
    print(f"{len(rows)} routes | panel of {len(panel)} opponents x 2 seats "
          f"= {2 * len(panel)} games each | {len(done)} already screened",
          flush=True)

    with out_path.open("a", encoding="utf-8") as handle:
        for index, route in enumerate(rows, 1):
            if route["episode"] in done:
                continue
            jobs = [
                (route["path"], o["path"], o["seed"], seat)
                for o in panel for seat in (0, 1)
            ]
            with Pool(args.workers) as pool:
                results = pool.map(_one, jobs)
            mine = [r[0] for r in results]
            wins = sum(1 for a, b, s in results if s == "DONE" and a > b)
            errors = sum(1 for _, _, s in results if s != "DONE")
            record = {
                "episode": route["episode"],
                "name": route["name"],
                "own_reward": route["own_reward"],
                "mean": sum(mine) / len(mine),
                "floor": min(mine),
                "wins": wins,
                "games": len(results),
                "errors": errors,
            }
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            # Team names carry non-cp1252 characters and Windows consoles
            # cannot encode them; the record keeps the real name.
            safe = route["name"][:24].encode("ascii", "replace").decode("ascii")
            print(f"  [{index:3d}/{len(rows)}] {safe:24s} "
                  f"ep{route['episode']}  W={wins:2d}/{len(results)} "
                  f"({wins/len(results):3.0%})  mean={record['mean']:9,.0f}",
                  flush=True)


if __name__ == "__main__":
    main()
