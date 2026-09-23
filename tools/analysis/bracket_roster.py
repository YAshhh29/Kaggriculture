"""Who is actually in a given rating band, and which recorded games we hold.

Asked directly: name the best agents in my bracket, show the replays used
to learn from them, and say what was learned. This answers the first two
halves from the tape corpus itself -- every tape carries the tracked
team's name, rank and rating, the opponent's rating, the episode id and
the result, so the roster is a fact about the data rather than a claim
about it.

    python -m tools.analysis.bracket_roster --low 2600 --high 2900
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAPES = ROOT / "kaggle_cache" / "top200_tapes"
REPLAY = "https://www.kaggle.com/competitions/episodes/{}/replay.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--low", type=float, default=2600.0)
    ap.add_argument("--high", type=float, default=2900.0)
    ap.add_argument("--show", type=int, default=25,
                    help="how many teams to list in full")
    ap.add_argument("--episodes", type=int, default=3,
                    help="episode ids to print per team")
    args = ap.parse_args()

    teams: dict[str, dict] = defaultdict(
        lambda: {"eps": [], "rank": None, "rating": None,
                 "won": 0, "lost": 0, "opp": []})
    total = skipped = 0
    for path in sorted(TAPES.glob("ep*.json")):
        total += 1
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            skipped += 1
            continue
        rating = r.get("team_score")
        if not isinstance(rating, (int, float)):
            skipped += 1
            continue
        if not (args.low <= rating <= args.high):
            continue
        name = str(r.get("source_team", "?"))
        t = teams[name]
        t["rank"] = r.get("team_rank")
        t["rating"] = rating
        t["eps"].append(r.get("episode_id"))
        t["won" if r.get("won") else "lost"] += 1
        orat = r.get("opponent_rating")
        if isinstance(orat, (int, float)):
            t["opp"].append(orat)

    order = sorted(teams.items(), key=lambda kv: -(kv[1]["rating"] or 0))
    games = sum(len(t["eps"]) for _n, t in order)
    print(f"\n{len(order)} distinct teams rated {args.low:.0f}-{args.high:.0f}"
          f" across {games} recorded games "
          f"(corpus {total} tapes, {skipped} unusable)\n")

    print(f"  {'rank':>5} {'rating':>8} {'games':>6} {'W-L':>7}  team")
    for name, t in order[: args.show]:
        wl = f"{t['won']}-{t['lost']}"
        print(f"  {str(t['rank']):>5} {t['rating']:8.1f} "
              f"{len(t['eps']):6d} {wl:>7}  {name[:38]}")
    if len(order) > args.show:
        print(f"  ... and {len(order) - args.show} more teams in band")

    print(f"\nreplays held for the top {min(args.show, len(order))} "
          f"(episode id -- fetchable at {REPLAY.format('<id>')}):\n")
    for name, t in order[: args.show]:
        eps = ", ".join(str(e) for e in t["eps"][: args.episodes])
        more = (f" (+{len(t['eps']) - args.episodes} more)"
                if len(t["eps"]) > args.episodes else "")
        print(f"  {name[:34]:34s} rank {str(t['rank']):>4}  {eps}{more}")


if __name__ == "__main__":
    main()
