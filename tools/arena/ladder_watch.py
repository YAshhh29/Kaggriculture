"""Watch our agents on the live ladder: ratings, recent games, and replays.

For each of our recent submissions this prints the live rating and its latest
ladder games -- who it played, their rating, the result and the margin -- and
can render those real games into the arena so they can be watched in Kaggle's
own viewer.

The token is read from the environment and never written anywhere.

    KAGGLE_API_TOKEN=... python -m tools.arena.ladder_watch
    KAGGLE_API_TOKEN=... python -m tools.arena.ladder_watch --submissions 3 --games 12
    KAGGLE_API_TOKEN=... python -m tools.arena.ladder_watch --render 4 --open
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.data.fetch_corpus import EPISODE_URL, post  # noqa: E402

SUBMISSIONS_URL = ("https://www.kaggle.com/api/v1/competitions/submissions/"
                   "list/kaggriculture")


def our_submissions(token: str) -> list[dict]:
    r = requests.get(SUBMISSIONS_URL, headers={"Authorization": f"Bearer {token}"},
                     timeout=60)
    r.raise_for_status()
    return r.json()


def recent_games(submission: int, token: str) -> list[dict]:
    payload = post(EPISODE_URL, {"submissionId": submission}, token, 0.5)
    if not payload:
        return []
    names = {t["id"]: t.get("teamName", "") for t in (payload.get("teams") or [])}
    out = []
    for e in payload.get("episodes") or []:
        agents = e.get("agents") or []
        mine = next((a for a in agents if a.get("submissionId") == submission), None)
        other = next((a for a in agents if a.get("submissionId") != submission), None)
        if not mine or not other or mine.get("reward") is None:
            continue
        ours, theirs = float(mine["reward"]), float(other.get("reward") or 0)
        out.append({"episode": e["id"], "opponent": names.get(other.get("teamId"), "?"),
                    "opp_rating": float(other.get("updatedScore") or
                                        other.get("initialScore") or 0),
                    "ours": ours, "theirs": theirs, "won": ours > theirs})
    out.sort(key=lambda g: -g["episode"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--submissions", type=int, default=3,
                    help="how many of our newest scored submissions to show")
    ap.add_argument("--games", type=int, default=10, help="recent games each")
    ap.add_argument("--render", type=int, default=0,
                    help="render this many of the newest games into the arena")
    ap.add_argument("--open", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment (inline)")

    subs = [s for s in our_submissions(token) if s.get("status") == "complete"]
    to_render: list[int] = []
    for s in subs[: args.submissions]:
        desc = (s.get("descriptionNullable") or "").strip().replace("\n", " ")
        score = s.get("publicScoreNullable") or "-"
        games = recent_games(s["ref"], token)
        print(f"\n== {s.get('date', '')[:16]}  live {score}  "
              f"submission {s['ref']}  {desc[:50]!r}")
        if not games:
            print("   no scored ladder games yet")
            continue
        wins = sum(g["won"] for g in games)
        print(f"   {len(games)} ladder games so far: {wins} won "
              f"({100 * wins / len(games):.0f}%), median opponent rating "
              f"{statistics.median(g['opp_rating'] for g in games):.0f}")
        for g in games[: args.games]:
            print(f"   ep {g['episode']}  {'WON ' if g['won'] else 'lost'} "
                  f"{g['ours']:9,.0f} : {g['theirs']:<9,.0f} "
                  f"({g['ours'] - g['theirs']:+8,.0f})  vs {g['opponent'][:24]:24s} "
                  f"{g['opp_rating']:6.0f}")
        to_render += [g["episode"] for g in games[: args.render]]

    if to_render:
        from tools.arena.arena import build_index, render_episode, _open
        print(f"\nrendering {len(to_render)} ladder games into the arena ...")
        for ep in to_render:
            try:
                out = render_episode(str(ep))
                print(f"   watch: {out}")
            except Exception as error:  # a missing replay must not stop the rest
                print(f"   ep {ep}: {type(error).__name__} {error}")
        index = build_index()
        print(f"   index: {index}")
        if args.open:
            _open(index)


if __name__ == "__main__":
    main()
