"""Find the top of the ladder through the games themselves.

The leaderboard API gives team ids; the episode API only takes submission
ids. So this climbs: list a submission's episodes, note every opponent's
submission id and live rating (each episode's agents carry `submissionId` and
`updatedScore`), then list the episodes of the highest-rated ones found so
far, and repeat. It stops when it holds --want submissions rated at least
--min-rating, and writes them with their recent episode ids to
rl/data/top_submissions.json -- the input for fetching top players' own
games (their exact moves and seeds are in each public replay).

    KAGGLE_API_TOKEN=... python -m tools.data.climb_ladder --start 56613410 56609589 \\
        --min-rating 2850 --want 12
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "rl" / "data" / "top_submissions.json"
EPISODE_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"


def episodes_of(token: str, submission: int) -> dict:
    r = requests.post(EPISODE_URL, headers={"Authorization": f"Bearer {token}",
                                            "Content-Type": "application/json"},
                      json={"submissionId": submission}, timeout=120)
    if r.status_code != 200:
        return {}
    return r.json()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=int, nargs="+", required=True, help="submission ids to start from")
    ap.add_argument("--min-rating", type=float, default=2850)
    ap.add_argument("--want", type=int, default=12)
    ap.add_argument("--max-calls", type=int, default=60)
    ap.add_argument("--pause", type=float, default=2.0)
    args = ap.parse_args()
    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN inline")

    seen: dict[int, dict] = {}        # submission -> {"rating", "team", "episodes": [...]}
    queue = list(args.start)
    listed: set[int] = set()
    calls = 0
    while queue and calls < args.max_calls:
        sub = queue.pop(0)
        if sub in listed:
            continue
        listed.add(sub)
        payload = episodes_of(token, sub)
        calls += 1
        names = {t["id"]: t.get("teamName", "") for t in (payload.get("teams") or [])}
        for ep in payload.get("episodes") or []:
            for a in ep.get("agents") or []:
                s = a.get("submissionId")
                if not s:
                    continue
                rating = a.get("updatedScore") or a.get("initialScore") or 0.0
                row = seen.setdefault(s, {"rating": 0.0, "team": names.get(a.get("teamId"), ""),
                                          "team_id": a.get("teamId"), "episodes": []})
                row["rating"] = max(row["rating"], float(rating))
                if ep["id"] not in row["episodes"]:
                    row["episodes"].append(ep["id"])
        top = [s for s, r in seen.items() if r["rating"] >= args.min_rating]
        best = sorted((s for s in seen if s not in listed), key=lambda s: -seen[s]["rating"])
        print(f"call {calls}: listed {sub} ({seen.get(sub, {}).get('team', '')}, "
              f"{seen.get(sub, {}).get('rating', 0):.0f}); {len(seen)} submissions seen, "
              f"{len(top)} >= {args.min_rating:.0f}; next best {seen[best[0]]['rating']:.0f}" if best else "",
              flush=True)
        if len([s for s in top if s in listed]) >= args.want:
            break
        queue = best[:3] + queue
        time.sleep(args.pause)
    top = sorted(((s, r) for s, r in seen.items() if r["rating"] >= args.min_rating),
                 key=lambda kv: -kv[1]["rating"])
    OUT.write_text(json.dumps({str(s): r for s, r in top}, indent=1), encoding="utf-8")
    print(f"\n{len(top)} submissions rated >= {args.min_rating:.0f} -> {OUT.relative_to(ROOT)}")
    for s, r in top[:20]:
        print(f"  {s} {r['team'][:24]:24s} {r['rating']:.0f}  {len(r['episodes'])} episodes known")


if __name__ == "__main__":
    main()
