"""Pull the real leaderboard, and every match the top teams have played.

The live corpus so far came from one place: the opponents *our own*
submission happened to be drawn against. That is a sample of the ladder
around our rating, not the top of it, and the nine 2765-2882 teams in it
were found by accident rather than by looking.

This looks. `LeaderboardService/GetLeaderboard` gives the ranked board with
each team's current submission id, and `EpisodeService/ListEpisodes` then
gives that submission's **complete** match history -- every opponent, both
rewards, and the rating each side carried into the game. None of that
needs a replay download, so the whole record of the top of the board costs
one request per team.

That record is the thing worth having. A tape shows what one agent did
once; a match history shows who a submission beats, who beats it, by how
much, and whether its wins are broad or a handful of favourable draws.

    KAGGLE_API_TOKEN=... python -m tools.data.fetch_leaderboard_records \\
        --top 40

Writes `rl/data/leaderboard.jsonl` (one row per team) and
`rl/data/top_matches.jsonl` (one row per match).
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
BOARD_OUT = ROOT / "rl" / "data" / "leaderboard.jsonl"
MATCH_OUT = ROOT / "rl" / "data" / "top_matches.jsonl"
BOARD_URL = (
    "https://www.kaggle.com/api/i/"
    "competitions.LeaderboardService/GetLeaderboard"
)
EPISODE_URL = (
    "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
)
COMPETITION_ID = 147734


def post(url: str, payload: dict, token: str, pause: float) -> dict | None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    delay = max(pause, 2.0)
    for _ in range(6):
        response = requests.post(url, headers=headers, json=payload,
                                 timeout=120)
        if response.status_code == 200:
            time.sleep(pause)
            return response.json()
        if response.status_code == 429:
            time.sleep(delay)
            delay = min(delay * 2, 90.0)
            continue
        return None
    return None


def leaderboard(token: str, pause: float, top: int) -> list[dict[str, Any]]:
    payload = post(BOARD_URL, {"competitionId": COMPETITION_ID,
                               "pageSize": max(top, 60)}, token, pause)
    if payload is None:
        raise SystemExit("could not read the leaderboard")
    rows = payload.get("publicLeaderboard") or []
    return [
        {
            "rank": int(row.get("rank", 0)),
            "team_id": int(row.get("teamId", 0)),
            "submission_id": int(row.get("submissionId", 0)),
            "rating": float(row.get("displayScore") or 0.0),
        }
        for row in rows[:top]
    ]


def matches(payload: dict, team_id: int) -> list[dict[str, Any]]:
    """Every game in the listing, from this team's point of view."""
    names = {
        team["id"]: team.get("teamName", "")
        for team in (payload.get("teams") or [])
    }
    out: list[dict[str, Any]] = []
    for episode in payload.get("episodes") or []:
        agents = episode.get("agents") or []
        if len(agents) != 2:
            continue
        mine = next(
            (a for a in agents if a.get("teamId") == team_id), None
        )
        theirs = next(
            (a for a in agents if a.get("teamId") != team_id), None
        )
        if mine is None:
            continue
        if theirs is None:                       # self-play validation
            theirs = agents[1] if agents[0] is mine else agents[0]
        ours = mine.get("reward")
        rival = theirs.get("reward")
        if ours is None or rival is None:
            continue
        out.append({
            "episode_id": episode.get("id"),
            "create_time": episode.get("createTime"),
            "team_id": team_id,
            "team": names.get(team_id, ""),
            "reward": float(ours),
            "rating": mine.get("updatedScore") or mine.get("initialScore"),
            "opponent_id": theirs.get("teamId"),
            "opponent": names.get(theirs.get("teamId"), ""),
            "opponent_reward": float(rival),
            "opponent_rating": (
                theirs.get("updatedScore") or theirs.get("initialScore")
            ),
            "margin": float(ours) - float(rival),
            "won": float(ours) > float(rival),
            "self_play": theirs.get("teamId") == team_id,
        })
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=40)
    parser.add_argument("--pause", type=float, default=3.0)
    args = parser.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment")

    BOARD_OUT.parent.mkdir(parents=True, exist_ok=True)
    board = leaderboard(token, args.pause, args.top)
    print(f"leaderboard: {len(board)} teams, "
          f"{board[0]['rating']:.1f} down to {board[-1]['rating']:.1f}",
          flush=True)

    total = 0
    with BOARD_OUT.open("w", encoding="utf-8") as board_file, \
            MATCH_OUT.open("w", encoding="utf-8") as match_file:
        for row in board:
            payload = post(EPISODE_URL,
                           {"submissionId": row["submission_id"]},
                           token, args.pause)
            if payload is None:
                print(f"  rank {row['rank']}: listing failed", flush=True)
                continue
            names = {
                team["id"]: team.get("teamName", "")
                for team in (payload.get("teams") or [])
            }
            row["name"] = names.get(row["team_id"], "")
            games = matches(payload, row["team_id"])
            wins = sum(1 for g in games if g["won"] and not g["self_play"])
            played = sum(1 for g in games if not g["self_play"])
            row["games"] = played
            row["wins"] = wins
            row["win_rate"] = wins / played if played else 0.0
            board_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            board_file.flush()
            for game in games:
                match_file.write(json.dumps(game, ensure_ascii=False) + "\n")
            match_file.flush()
            total += len(games)
            safe = row["name"].encode("ascii", "replace").decode()[:22]
            print(f"  #{row['rank']:3d} {safe:24s} {row['rating']:7.1f}  "
                  f"{wins:3d}/{played:3d} = {row['win_rate']:5.1%}",
                  flush=True)
    print(f"\n{total} matches written to {MATCH_OUT.name}", flush=True)


if __name__ == "__main__":
    main()
