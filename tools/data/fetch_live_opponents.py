"""Build a corpus of *current* opponents from the live ladder.

Every evaluation in this project until now ran against `kaggle_cache/`,
captured 2026-09-04. That panel is badly misleading: on it Candidate D
wins 85-92% of games, while its 166 real games on the ladder over the same
period won **45.2%**. A panel of stale, weaker tapes makes every candidate
look strong and, worse, makes a 1,000-coin improvement look like noise --
when the live median winning margin is 1,151 coins and the median losing
margin 2,889.

This fixes the panel. For each opponent we have actually met on the
ladder, it lists that submission's episodes, downloads a few, and keeps
only the opponent's 720-action tape -- the same compact clone format
`kaggle_cache/clones/` already uses. The replays themselves are 30 MB
apiece and are discarded once the tape is out.

Two properties matter and both were asked for directly:

* **several games per player, not one.** Section 9k measured that tape
  quality belongs to the individual game rather than the player, so a
  single replay tells you almost nothing about how someone plays. With
  three or four games each, a consistent style separates from a lucky
  draw.
* **current play.** These submissions are the ones on the ladder now.

Requires `KAGGLE_API_TOKEN` in the environment; it is never written down.

    KAGGLE_API_TOKEN=... python -m tools.data.fetch_live_opponents \\
        --opponents 30 --per-opponent 3
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
import zlib
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "kaggle_cache" / "live_clones"
INDEX = ROOT / "rl" / "data" / "live_opponents.jsonl"
LIST_URL = (
    "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
)
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode}.json"
OUR_TEAM = 16724366
OUR_SUBMISSION = 56076097


def api(payload: dict, token: str, pause: float) -> dict | None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    delay = max(pause, 2.0)
    for _ in range(5):
        response = requests.post(
            LIST_URL, headers=headers, json=payload, timeout=120
        )
        if response.status_code == 200:
            time.sleep(pause)
            return response.json()
        if response.status_code == 429:
            time.sleep(delay)
            delay = min(delay * 2, 90.0)
            continue
        return None
    return None


def live_opponents(token: str, pause: float) -> list[dict]:
    """Opponents we have actually played, with their live rating."""
    payload = api({"submissionId": OUR_SUBMISSION}, token, pause)
    if payload is None:
        raise SystemExit("could not list our own episodes")
    names = {
        t["id"]: t.get("teamName", "")
        for t in (payload.get("teams") or [])
    }
    submission = {
        s["teamId"]: s["id"]
        for s in (payload.get("submissions") or [])
        if s.get("teamId") != OUR_TEAM
    }
    rating: dict[int, float] = {}
    for episode in payload.get("episodes") or []:
        for agent in episode.get("agents") or []:
            team = agent.get("teamId")
            if team == OUR_TEAM or not agent.get("updatedScore"):
                continue
            rating[team] = max(rating.get(team, 0.0), agent["updatedScore"])
    rows = [
        {
            "team_id": team,
            "submission_id": sid,
            "name": names.get(team, ""),
            "rating": rating.get(team, 0.0),
        }
        for team, sid in submission.items()
    ]
    rows.sort(key=lambda r: -r["rating"])
    return rows


def extract_tape(replay: dict, team_id: int) -> tuple[list, float] | None:
    """That team's 720 actions and its final reward, from a full replay."""
    steps = replay.get("steps") or []
    if len(steps) < 700:
        return None
    info = replay.get("info") or {}
    teams = info.get("TeamId") or info.get("teamId") or []
    side = None
    if isinstance(teams, list):
        for index, value in enumerate(teams):
            if int(value or 0) == team_id:
                side = index
                break
    if side is None:
        rewards = [
            (steps[-1][p].get("reward") or 0.0) for p in range(len(steps[-1]))
        ]
        side = rewards.index(max(rewards))
    actions = [
        (step[side].get("action") if side < len(step) else None)
        for step in steps
    ]
    reward = steps[-1][side].get("reward") if side < len(steps[-1]) else None
    return actions, float(reward or 0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponents", type=int, default=30)
    parser.add_argument("--per-opponent", type=int, default=3)
    parser.add_argument("--min-rating", type=float, default=1700.0)
    parser.add_argument("--pause", type=float, default=3.0)
    args = parser.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if INDEX.exists():
        for line in INDEX.read_text(encoding="utf-8").splitlines():
            done.add(int(json.loads(line)["episode_id"]))

    rows = [r for r in live_opponents(token, args.pause)
            if r["rating"] >= args.min_rating][:args.opponents]
    print(f"{len(rows)} live opponents rated >= {args.min_rating:.0f}",
          flush=True)

    with INDEX.open("a", encoding="utf-8") as index:
        for row in rows:
            payload = api({"submissionId": row["submission_id"]},
                          token, args.pause)
            if payload is None:
                print("  list failed, stopping", flush=True)
                break
            episodes = [e["id"] for e in (payload.get("episodes") or [])]
            taken = 0
            for episode in reversed(episodes):     # newest first
                if taken >= args.per_opponent:
                    break
                if episode in done:
                    continue
                try:
                    response = requests.get(
                        REPLAY_URL.format(episode=episode), timeout=180
                    )
                    if response.status_code != 200:
                        continue
                    replay = response.json()
                except Exception:
                    continue
                got = extract_tape(replay, row["team_id"])
                del replay
                if got is None:
                    continue
                actions, reward = got
                blob = base64.b64encode(
                    zlib.compress(
                        json.dumps(actions, separators=(",", ":")).encode()
                    )
                ).decode()
                (OUT_DIR / f"live_{episode}.json").write_text(
                    json.dumps({
                        "actions_zlib_b64": blob,
                        "source_team": row["name"],
                        "source_episode_id": str(episode),
                    }), encoding="utf-8"
                )
                index.write(json.dumps({
                    "episode_id": episode,
                    "team_id": row["team_id"],
                    "name": row["name"],
                    "rating": row["rating"],
                    "reward": reward,
                }, ensure_ascii=False) + "\n")
                index.flush()
                taken += 1
                time.sleep(args.pause)
            safe = row["name"].encode("ascii", "replace").decode()[:24]
            print(f"  {safe:26s} rating {row['rating']:6.0f}  tapes {taken}",
                  flush=True)


if __name__ == "__main__":
    main()
