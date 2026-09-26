"""How a top-30 team beats the public lineage, from real games between them.

Agent A is the lineage's best variant, so above ~2700 it will meet the
original, per-game-planning teams that beat the lineage. The corpus already
holds real ladder games of top-30 teams against opponents whose opening
matches the lineage's. Replaying both sides exactly (index t+1 at step t;
checked against Kaggle's recorded score), this prints, day by day, the median
money and planted-tile gap between the top team and its lineage opponent, and
lists the episodes so the games can be watched:

    python -m tools.arena.arena episode <id> --open

    python -m tools.analysis.top_vs_lineage --top 30
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

from tools.analysis.lineage_fingerprint import (agreement, farmer_seq,  # noqa: E402
                                                references)

CORPUS = ROOT / "kaggle_cache" / "corpus_v2"
DAYS = (2, 5, 8, 11, 14, 17, 20, 23, 26, 29)


def _unpack(blob: str) -> list:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def _tiles(farm: dict) -> tuple[int, int]:
    plants = animals = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict):
                if "animal" in t:
                    animals += 1
                elif t.get("kind") == "PLANT":
                    plants += 1
    return plants, animals


def replay(job) -> dict | None:
    path = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    r = json.loads(Path(path).read_text(encoding="utf-8"))
    seat = int(r["seat"])
    tp = [None, None]
    tp[seat] = _unpack(r["actions_zlib_b64"])
    tp[1 - seat] = _unpack(r["opponent_actions_zlib_b64"])
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": r["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.reset()
    trace = {}
    for t in range(719):
        env.step([tp[0][t + 1], tp[1][t + 1]])
        if t % 24 == 23 and (t // 24) in DAYS:
            obs = env.state[0].observation
            top, lin = obs["farms"][seat], obs["farms"][1 - seat]
            tp_p, tp_a = _tiles(top)
            ln_p, ln_a = _tiles(lin)
            trace[t // 24] = {"money_gap": float(top["money"]) - float(lin["money"]),
                              "plant_gap": tp_p - ln_p, "animal_gap": tp_a - ln_a,
                              "top_q": len(top.get("unlocked_quadrants") or []),
                              "lin_q": len(lin.get("unlocked_quadrants") or [])}
    final = [float(env.state[i].reward or 0) for i in (0, 1)]
    recorded = float((r.get("rewards") or {}).get("them") or 0)
    return {"episode": r["episode_id"], "team": r["source_team"],
            "rank": r["team_rank"], "opponent": r["opponent"],
            "opp_rating": r.get("opponent_rating"),
            "margin": final[seat] - final[1 - seat],
            "top_won": final[seat] > final[1 - seat],
            "exact": abs(final[seat] - recorded) < 1, "trace": trace}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--match", type=float, default=0.8)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    ref = references(["nb_tschinkel_2945"], 144)["nb_tschinkel_2945"]
    paths = []
    for path in sorted(CORPUS.glob("ep*.json")):
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if int(r.get("team_rank") or 9999) > args.top:
            continue
        opp = farmer_seq(_unpack(r["opponent_actions_zlib_b64"]), 144)
        if max(agreement(opp, x) for x in ref) >= args.match:
            paths.append(str(path))
    print(f"{len(paths)} real games of a top-{args.top} team against a "
          f"lineage-opening opponent", flush=True)
    with Pool(args.workers, maxtasksperchild=2) as pool:
        rows = [r for r in pool.imap_unordered(replay, paths) if r]

    exact = sum(r["exact"] for r in rows)
    wins = sum(r["top_won"] for r in rows)
    print(f"replays exact: {exact}/{len(rows)}; top team won {wins}/{len(rows)}; "
          f"median final margin {statistics.median(r['margin'] for r in rows):+,.0f}\n")
    print(f"  {'day':>4} {'money gap':>10} {'plant gap':>10} {'animal gap':>11} "
          f"{'quadrants top/lin':>18}   (top team minus lineage, median)")
    for d in DAYS:
        cells = [r["trace"][d] for r in rows if d in r["trace"]]
        if not cells:
            continue
        print(f"  {d:4d} {statistics.median(c['money_gap'] for c in cells):+10,.0f} "
              f"{statistics.median(c['plant_gap'] for c in cells):+10.0f} "
              f"{statistics.median(c['animal_gap'] for c in cells):+11.0f} "
              f"{statistics.median(c['top_q'] for c in cells):>9.0f} / "
              f"{statistics.median(c['lin_q'] for c in cells):.0f}")
    print("\n  games to watch (python -m tools.arena.arena episode <id> --open):")
    for r in sorted(rows, key=lambda r: -abs(r["margin"]))[:8]:
        print(f"    {r['episode']}  #{r['rank']} {r['team'][:18]:18s} vs "
              f"{r['opponent'][:18]:18s} ({r['opp_rating'] or 0:.0f})  "
              f"{'top won' if r['top_won'] else 'LINEAGE WON'} by {abs(r['margin']):,.0f}")


if __name__ == "__main__":
    main()
