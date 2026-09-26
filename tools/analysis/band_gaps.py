"""Where an agent falls behind 2600-2900 teams, day by day.

Reads a band_panel result file, replays the agent's clean games from the
arena records (exact: at step t the action stored at t+1), and prints the
median gap (agent minus team) in cash, planted tiles, animals and quadrants
per day -- separately for games the agent won and lost -- plus the losses
worth watching.

    python -m tools.analysis.band_gaps A --results rl/data/band_panel/band_2600_2900.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.arena.arena import CONFIG, GAMES, _unpack  # noqa: E402

DAYS = (2, 5, 8, 10, 12, 15, 18, 21, 24, 27, 29)


def _count(farm: dict) -> tuple[int, int]:
    plants = animals = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict):
                if "animal" in t:
                    animals += 1
                elif t.get("kind") == "PLANT":
                    plants += 1
    return plants, animals


def trace(job) -> dict:
    game_id, ours = job
    from kaggle_environments import make

    record = json.loads((GAMES / f"{game_id}.json").read_text(encoding="utf-8"))
    tapes = [_unpack(t) for t in record["tapes"]]
    env = make("kaggriculture", configuration={**CONFIG, "seed": record["seed"]},
               debug=False)
    env.reset()
    out = {}
    for t in range(719):
        env.step([tapes[0][t + 1], tapes[1][t + 1]])
        if t % 24 == 12 and t // 24 in DAYS:
            farms = env.state[0].observation["farms"]
            a, b = farms[ours], farms[1 - ours]
            (pa, aa), (pb, ab) = _count(a), _count(b)
            out[t // 24] = {"cash": float(a["money"]) - float(b["money"]),
                            "plants": pa - pb, "animals": aa - ab,
                            "quads": (len(a["unlocked_quadrants"]),
                                      len(b["unlocked_quadrants"])),
                            "hands": (len(a["hands"]), len(b["hands"]))}
    return {"game_id": game_id, "days": out}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agent")
    ap.add_argument("--results", default="rl/data/band_panel/band_2600_2900.json")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--low", type=int, default=2600)
    ap.add_argument("--high", type=int, default=2900)
    ap.add_argument("--min-fidelity", type=float, default=0.9,
                    help="replayed team score / its real recorded score")
    args = ap.parse_args()

    rows = [r for r in json.loads((ROOT / args.results).read_text(encoding="utf-8"))
            if r.get("agent") == args.agent and "ours" in r
            and args.low <= r["score"] < args.high
            and r["theirs"] >= args.min_fidelity * r["recorded"]]
    jobs = [(r["game_id"], 1 - r["seat"]) for r in rows]
    with Pool(args.workers, maxtasksperchild=2) as pool:
        traces = {t["game_id"]: t["days"] for t in pool.imap_unordered(trace, jobs)}

    for label, keep in (("WON", True), ("LOST", False)):
        group = [r for r in rows if r["won"] == keep]
        if not group:
            continue
        print(f"\n{args.agent} {label} {len(group)} faithful games vs {args.low}-{args.high} teams "
              f"(median final margin {statistics.median(r['ours'] - r['theirs'] for r in group):+,.0f})")
        print(f"  {'day':>3} {'cash gap':>9} {'plant gap':>10} {'animal gap':>11} "
              f"{'quadrants us/them':>18} {'hands us/them':>14}")
        for d in DAYS:
            cells = [traces[r["game_id"]][d] for r in group if d in traces.get(r["game_id"], {})]
            if not cells:
                continue
            med = lambda k: statistics.median(c[k] for c in cells)  # noqa: E731
            q = [statistics.median(c["quads"][i] for c in cells) for i in (0, 1)]
            h = [statistics.median(c["hands"][i] for c in cells) for i in (0, 1)]
            print(f"  {d:3d} {med('cash'):+9,.0f} {med('plants'):+10.0f} {med('animals'):+11.0f} "
                  f"{q[0]:>9.0f} / {q[1]:<6.0f} {h[0]:>6.0f} / {h[1]:<6.0f}")
    losses = sorted((r for r in rows if not r["won"]), key=lambda r: r["ours"] - r["theirs"])
    print("\n  biggest losses (python -m tools.arena.arena render <game_id> --open):")
    for r in losses[:8]:
        print(f"    {r['ours'] - r['theirs']:+9,.0f}  vs {r['team'][:22]:22s} ({r['score']:.0f})  {r['game_id']}")


if __name__ == "__main__":
    main()
