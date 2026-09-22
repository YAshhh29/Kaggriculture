"""Win rate against a wide sample of real ladder opponents.

The four live agents in `strong_panel` measure depth; this measures breadth,
by replaying the recorded play of many different top-200 teams. The opponent
is an open-loop recording and cannot react, so a game where it refuses many
of its own moves has drifted and is reported separately.

    python -m tools.eval.broad_panel rl.candidate_j:agent --tapes 40
"""

from __future__ import annotations

import argparse
import base64
import json
import random
import statistics
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TAPES = ROOT / "kaggle_cache" / "top200_tapes"
# A replay must reach this share of the score its team really
# recorded for the game to count as that team still playing.
FIDELITY = 0.70


def play(job):
    spec, path, seat = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent
    from tools.eval.measure_panel import resolve

    record = json.loads(Path(path).read_text(encoding="utf-8"))
    tape = json.loads(zlib.decompress(
        base64.b64decode(record["actions_zlib_b64"])).decode())
    mine = resolve(spec)
    theirs = build_replay_agent(tuple(tape))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run([mine, theirs] if seat == 0 else [theirs, mine])
    ours = float(env.state[seat].reward or 0)
    theirs_score = float(env.state[1 - seat].reward or 0)
    return {"team": record.get("source_team"), "rank": record.get("team_rank"),
            "ours": ours, "theirs": theirs_score, "won": ours > theirs_score,
            "recorded": float(record["rewards"]["them"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--tapes", type=int, default=40)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    paths = sorted(str(p) for p in TAPES.glob("ep*.json"))
    random.Random(args.seed).shuffle(paths)
    paths = paths[: args.tapes]
    jobs = [(args.spec, p, seat) for p in paths for seat in (0, 1)]
    with Pool(args.workers) as pool:
        games = pool.map(play, jobs)

    def report(rows, label):
        if not rows:
            print(f"\n  {label}: no games")
            return
        wins = sum(r["won"] for r in rows)
        print(f"\n  {label}: {len(rows)} games, wins {wins}/{len(rows)} "
              f"({100 * wins / len(rows):.0f}%)")
        print(f"    our score   median "
              f"{statistics.median(r['ours'] for r in rows):,.0f}  mean "
              f"{statistics.mean(r['ours'] for r in rows):,.0f}")
        print(f"    their score median "
              f"{statistics.median(r['theirs'] for r in rows):,.0f}  "
              f"(they really scored "
              f"{statistics.median(r['recorded'] for r in rows):,.0f})")
        bands = {"1-50": [], "51-120": [], "121-200": []}
        for r in rows:
            rank = int(r["rank"] or 200)
            key = ("1-50" if rank <= 50 else
                   "51-120" if rank <= 120 else "121-200")
            bands[key].append(r)
        for key, band in bands.items():
            if band:
                w = sum(b["won"] for b in band)
                print(f"    ranked {key:8s}: {w:3d}/{len(band):3d} wins, "
                      f"median ours "
                      f"{statistics.median(b['ours'] for b in band):,.0f}")

    # A replayed tape is an open-loop recording. When our play diverges from
    # the game it was taken from, its orders stop fitting the farm it now
    # has, and it collapses -- a team that really scored 130,000 finishes on
    # 50,000. Beating that is not beating the team. So every game is scored
    # for fidelity, `theirs / what they really scored`, and the honest
    # number is the one over the games where the tape still played its own
    # game. This was in the docstring from the first commit and never
    # implemented, and it is why this panel has been flattering us: the
    # same teams that score 115,000 here score 125,000 to 130,000 live.
    for row in games:
        row["fidelity"] = (row["theirs"] / row["recorded"]
                           if row["recorded"] else 0.0)
    clean = [g for g in games if g["fidelity"] >= FIDELITY]
    collapsed = [g for g in games if g["fidelity"] < FIDELITY]

    print(f"\n{args.spec}: {len(games)} games against {len(paths)} "
          f"different ladder teams, both seats")
    print(f"  tape fidelity: median "
          f"{statistics.median(g['fidelity'] for g in games):.0%}, "
          f"{len(collapsed)} of {len(games)} games below {FIDELITY:.0%} "
          f"and discarded")
    report(clean, "CLEAN GAMES (the honest number)")
    report(games, "all games, including collapsed tapes")


if __name__ == "__main__":
    main()
