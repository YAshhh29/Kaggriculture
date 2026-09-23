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
    # Two arms are only comparable if they played the SAME tapes. Drawing
    # them by shuffling a glob does not guarantee that: any fetch running
    # against kaggle_cache/top200_tapes changes what the glob returns, the
    # shuffle then lands differently, and the arms silently diverge. It
    # has happened twice in this project, most recently while measuring
    # J2 and K2 -- the corpus grew from 561 tapes to 898 mid-comparison
    # and the "they really scored" baseline moved from 95,048 to 100,728,
    # which is the only reason it was caught. Pin the list with
    # --tapes-from and every arm plays the same games whatever else is
    # happening to the directory.
    parser.add_argument("--tapes-from", type=Path, default=None,
                        help="file of tape paths, one per line; pins the "
                             "sample so a growing corpus cannot change it")
    parser.add_argument("--freeze-to", type=Path, default=None,
                        help="write the drawn tape list here, to pin later "
                             "arms of the same comparison to it")
    args = parser.parse_args()

    if args.tapes_from:
        paths = [line.strip() for line
                 in args.tapes_from.read_text(encoding="utf-8").splitlines()
                 if line.strip()]
        missing = [p for p in paths if not Path(p).is_file()]
        if missing:
            raise SystemExit(
                f"{len(missing)} pinned tapes are missing, so this arm "
                f"cannot match the others:\n  " + "\n  ".join(missing[:5]))
        paths = paths[: args.tapes]
    else:
        paths = sorted(str(p) for p in TAPES.glob("ep*.json"))
        random.Random(args.seed).shuffle(paths)
        paths = paths[: args.tapes]
    if args.freeze_to:
        args.freeze_to.write_text("\n".join(paths), encoding="utf-8")
        print(f"  pinned {len(paths)} tapes to {args.freeze_to}")
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

    # Fidelity is NOT a property of the tape. Replayed with both recorded
    # sides on its own seed, a tape reproduces its game to the coin -- 149
    # of 149 checked. It degrades only because WE replace one side, so the
    # degradation is a property of the matchup, and filtering on it judges
    # each agent on a different set of opponents: H2 on 64 games and J on
    # 47, which is not a comparison at all. The fixed set of games is the
    # comparison; fidelity is reported beside it as a diagnostic.
    for row in games:
        row["fidelity"] = (row["theirs"] / row["recorded"]
                           if row["recorded"] else 0.0)
    broken = [g for g in games if g["fidelity"] < FIDELITY]

    print(f"\n{args.spec}: {len(games)} games against {len(paths)} "
          f"different ladder teams, both seats")
    print(f"  tape fidelity: median "
          f"{statistics.median(g['fidelity'] for g in games):.0%}; "
          f"{len(broken)} of {len(games)} games fell below {FIDELITY:.0%} "
          f"(diagnostic only -- every agent is scored on all {len(games)})")
    report(games, "ALL GAMES (the comparison)")


if __name__ == "__main__":
    main()
