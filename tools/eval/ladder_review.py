"""Every agent this project has shipped, over one identical set of games.

The point is the shared game set. A panel that drops games per agent -- when
a replayed tape collapses, say -- judges each one against different
opponents, and the agent that breaks fewer tapes looks better for it. Here
every agent plays the same tapes, both seats, and the columns are
comparable by construction.

Each opponent is a recorded top-of-ladder team, and the tape reproduces its
own game to the coin when both sides are replayed, so `theirs` is close to
what that team really did -- `real` is printed beside it to show how close.

    python -m tools.eval.ladder_review --tapes 15
    python -m tools.eval.ladder_review --tapes 15 --only g h2 j k
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

# name -> spec. The packaged submissions are loaded as the ladder loads
# them; J and K are the live source modules under development.
AGENTS = [
    ("a", "rl.submitted:a"),
    ("b", "rl.submitted:b"),
    ("c", "rl.submitted:c"),
    ("c2", "rl.submitted:c2"),
    ("d", "rl.submitted:d"),
    ("e", "rl.submitted:e"),
    ("f", "rl.submitted:f"),
    ("g", "rl.submitted:g"),
    ("h", "rl.submitted:h"),
    ("hd", "rl.submitted:hd"),
    ("h2", "rl.submitted:h2"),
    ("i", "rl.submitted:i"),
    ("J", "rl.candidate_j:agent"),
    ("K", "rl.candidate_k:agent"),
]


def play(job):
    name, spec, path, seat = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent
    from tools.eval.measure_panel import resolve

    record = json.loads(Path(path).read_text(encoding="utf-8"))
    tape = json.loads(zlib.decompress(
        base64.b64decode(record["actions_zlib_b64"])).decode())
    try:
        mine = resolve(spec)
    except Exception:
        return None
    theirs = build_replay_agent(tuple(tape))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    try:
        env.run([mine, theirs] if seat == 0 else [theirs, mine])
    except Exception:
        return None
    ours = float(env.state[seat].reward or 0)
    rival = float(env.state[1 - seat].reward or 0)
    return {"name": name, "ours": ours, "theirs": rival,
            "won": ours > rival, "rank": record.get("team_rank") or 200,
            "recorded": float(record["rewards"]["them"]),
            "status": str(env.state[seat].status)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tapes", type=int, default=15)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()

    paths = sorted(str(p) for p in TAPES.glob("ep*.json"))
    random.Random(args.seed).shuffle(paths)
    paths = paths[: args.tapes]

    chosen = [(n, s) for n, s in AGENTS
              if not args.only or n.lower() in {o.lower() for o in args.only}]
    jobs = [(n, s, p, seat) for n, s in chosen for p in paths
            for seat in (0, 1)]
    with Pool(args.workers) as pool:
        rows = [r for r in pool.map(play, jobs) if r]

    print(f"\nEvery agent over the same {len(paths)} teams, both seats "
          f"({2 * len(paths)} games each)\n")
    print(f"  {'agent':6s} {'wins':>9s} {'median':>9s} {'mean':>9s} "
          f"{'theirs':>9s} {'margin':>10s} {'best':>9s} {'worst':>9s}")
    table = []
    for name, _spec in chosen:
        mine = [r for r in rows if r["name"] == name]
        if not mine:
            print(f"  {name:6s} {'did not run':>9s}")
            continue
        wins = sum(r["won"] for r in mine)
        ours = statistics.median(r["ours"] for r in mine)
        table.append((ours, name, mine, wins))
        print(f"  {name:6s} {wins:4d}/{len(mine):<4d} {ours:9,.0f} "
              f"{statistics.mean(r['ours'] for r in mine):9,.0f} "
              f"{statistics.median(r['theirs'] for r in mine):9,.0f} "
              f"{statistics.median(r['ours'] - r['theirs'] for r in mine):+10,.0f} "
              f"{max(r['ours'] for r in mine):9,.0f} "
              f"{min(r['ours'] for r in mine):9,.0f}")

    print("\n  ranked by median score\n")
    for place, (ours, name, mine, wins) in enumerate(
            sorted(table, reverse=True), 1):
        bar = "#" * int(ours / 4000)
        print(f"  {place:2d}. {name:5s} {ours:9,.0f}  {wins:3d} wins  {bar}")

    bad = [r for r in rows if r["status"] != "DONE"]
    if bad:
        names = {}
        for r in bad:
            names[r["name"]] = names.get(r["name"], 0) + 1
        print(f"\n  games that did not finish cleanly: "
              + ", ".join(f"{k} {v}" for k, v in names.items()))


if __name__ == "__main__":
    main()
