"""Harvest recent high-rated episodes from the live Kaggle ladder.

The cached corpus in `kaggle_cache/` was captured on 2026-09-04 and stops
at episode 105437827. The ladder does not stop: by 2026-09-08 episode ids
had reached 106712827, so roughly 1.3 million ids of newer play -- and the
current top of the leaderboard -- were invisible to every route search this
project has run.

This walks the recent id range, keeps the episodes whose agents carry a
high live rating, and records **every** such episode per team rather than
one game each. That last part matters: section 9k measured that tape
quality belongs to the individual *game* and not to the player, so judging
a team from a single replay is judging noise. With several games per team
the consistent performers can be told apart from the lucky ones.

Ratings come straight from the episode record -- each agent carries
`initialScore` and `updatedScore`, which are the live ladder numbers at
the moment that game was played, so no separate leaderboard join is
needed.

Requires a Kaggle API token in `KAGGLE_API_TOKEN`. The token is read from
the environment and never written anywhere.

    KAGGLE_API_TOKEN=... python -m tools.data.harvest_recent_episodes \\
        --min-rating 2700 --samples 4000

Output is appended to `rl/data/recent_episodes.jsonl` as it lands, so the
walk is resumable and a rate-limit stop costs nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "rl" / "data" / "recent_episodes.jsonl"
ENDPOINT = (
    "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
)
COMPETITION_ID = 147734


def fetch(ids: list[int], token: str, pause: float) -> dict | None:
    """One batched request, backing off politely on a rate limit."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    delay = pause
    for _ in range(6):
        response = requests.post(
            ENDPOINT, headers=headers, json={"ids": ids}, timeout=90
        )
        if response.status_code == 200:
            time.sleep(pause)
            return response.json()
        if response.status_code == 429:
            time.sleep(delay)
            delay = min(delay * 2, 60.0)
            continue
        return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-rating", type=float, default=2700.0)
    parser.add_argument("--samples", type=int, default=3000)
    parser.add_argument("--batch", type=int, default=20)
    parser.add_argument("--pause", type=float, default=1.5)
    parser.add_argument("--low", type=int, default=105_450_000)
    parser.add_argument("--high", type=int, default=106_712_000)
    parser.add_argument("--seed", type=int, default=5)
    args = parser.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment")

    seen: set[int] = set()
    if OUTPUT.exists():
        for line in OUTPUT.read_text(encoding="utf-8").splitlines():
            try:
                seen.add(int(json.loads(line)["episode_id"]))
            except Exception:
                continue
    print(f"{len(seen)} episodes already recorded", flush=True)

    random.seed(args.seed)
    probes = random.sample(range(args.low, args.high), args.samples)
    kept = 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("a", encoding="utf-8") as handle:
        for start in range(0, len(probes), args.batch):
            ids = [i for i in probes[start:start + args.batch] if i not in seen]
            if not ids:
                continue
            payload = fetch(ids, token, args.pause)
            if payload is None:
                print("stopping: request failed or rate limit persisted",
                      flush=True)
                break
            teams = {
                t["id"]: t.get("teamName", "")
                for t in (payload.get("teams") or [])
            }
            for episode in payload.get("episodes") or []:
                agents = episode.get("agents") or []
                ratings = [
                    a.get("updatedScore") or a.get("initialScore") or 0.0
                    for a in agents
                ]
                if not ratings or max(ratings) < args.min_rating:
                    continue
                handle.write(json.dumps({
                    "episode_id": episode["id"],
                    "create_time": episode.get("createTime"),
                    "agents": [
                        {
                            "team_id": a.get("teamId"),
                            "team_name": teams.get(a.get("teamId"), ""),
                            "reward": a.get("reward"),
                            "rating": a.get("updatedScore")
                            or a.get("initialScore"),
                            "index": a.get("index", 0),
                        }
                        for a in agents
                    ],
                }, ensure_ascii=False) + "\n")
                kept += 1
            handle.flush()
            done = start + args.batch
            if done % (args.batch * 10) == 0:
                print(f"  probed {done}/{len(probes)}  kept {kept}", flush=True)
    print(f"kept {kept} episodes rated >= {args.min_rating:.0f}", flush=True)


if __name__ == "__main__":
    main()
