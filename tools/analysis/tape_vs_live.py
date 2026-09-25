"""Does a top team's recorded plan beat a live agent on the same seed?

Each corpus tape is replayed exactly -- that team's actions, that game's seed,
the same seat -- against a LIVE agent in place of the opponent it really met.
The tape cannot react: if the live agent's play moves prices, the tape's
recorded buys and sales can fail. So a tape that still wins is strong evidence
its plan is better, and a tape that loses is inconclusive; "fidelity" (the
replayed score over the score the team really recorded) says which.

    python -m tools.analysis.tape_vs_live --teams "DECEM" "Smackaveli" --live nb_tschinkel_2945
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CORPUS = ROOT / "kaggle_cache" / "corpus_v2"


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def one(job):
    path, live_name = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make
    from rl.replay_agent import build_replay_agent
    from tools.arena.arena import load

    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    seat = int(rec["seat"])
    live = load(live_name)
    players = [None, None]
    players[seat] = build_replay_agent(_unpack(rec["actions_zlib_b64"]))
    players[1 - seat] = live
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": rec["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run(players)
    final = env.steps[-1]
    tape_score = float(final[seat].get("reward") or 0.0)
    live_score = float(final[1 - seat].get("reward") or 0.0)
    recorded = float((rec.get("rewards") or {}).get("them") or 0.0)
    return {"team": rec.get("source_team"), "rank": rec.get("team_rank"),
            "episode": rec.get("episode_id"), "tape": tape_score,
            "live": live_score, "recorded": recorded,
            "fidelity": tape_score / recorded if recorded else 0.0,
            "status": [final[0].get("status"), final[1].get("status")]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--teams", nargs="+", required=True)
    ap.add_argument("--live", default="nb_tschinkel_2945")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    wanted = set(args.teams)
    paths = []
    for path in sorted(CORPUS.glob("ep*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if rec.get("source_team") in wanted:
            paths.append(str(path))
    jobs = [(p, args.live) for p in paths]
    print(f"{len(jobs)} tapes from {len(wanted)} teams against live "
          f"{args.live}", flush=True)
    with Pool(args.workers, maxtasksperchild=1) as pool:
        rows = list(pool.imap_unordered(one, jobs))

    by_team: dict[str, list[dict]] = {}
    for r in rows:
        by_team.setdefault(r["team"], []).append(r)
    print(f"\n  {'team':24s} {'games':>5} {'tape wins':>9} {'mean tape':>10} "
          f"{'mean live':>10} {'fidelity':>9}")
    total_w = total_g = 0
    for team, rs in sorted(by_team.items(), key=lambda kv: kv[1][0]["rank"]):
        wins = sum(r["tape"] > r["live"] for r in rs)
        total_w += wins
        total_g += len(rs)
        print(f"  #{rs[0]['rank']:<3} {team[:20]:20s} {len(rs):5d} "
              f"{wins:5d}/{len(rs):<3d} {statistics.mean(r['tape'] for r in rs):10,.0f} "
              f"{statistics.mean(r['live'] for r in rs):10,.0f} "
              f"{statistics.median(r['fidelity'] for r in rs):8.0%}")
    print(f"\n  all: recorded plans beat live {args.live} in {total_w} of "
          f"{total_g} games")


if __name__ == "__main__":
    main()
