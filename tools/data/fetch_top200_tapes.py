"""Collect replays of the current top of the ladder, won games and lost.

A team that only ever wins teaches you what works; a team's losses teach you
what beats it. This fetches both for each of the top N teams on the live
leaderboard, and keeps a compact record per episode -- the seed, both sides'
action tapes (zlib + base64), both rewards and who won -- rather than the
~30 MB replay, which is discarded once read.

The leaderboard and the episode listings need the token (inline, never in a
file). The replays themselves are public and need none.

    KAGGLE_API_TOKEN=... python -m tools.data.fetch_top200_tapes \\
        --top 200 --per-team 4 --pause 0.4
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
import zlib
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "kaggle_cache" / "top200_tapes"
BOARD_URL = ("https://www.kaggle.com/api/i/"
             "competitions.LeaderboardService/GetLeaderboard")
EPISODE_URL = ("https://www.kaggle.com/api/i/"
               "competitions.EpisodeService/ListEpisodes")
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode}.json"
COMPETITION_ID = 147734
PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}


def pack(actions: list[Any]) -> str:
    raw = json.dumps(actions, separators=(",", ":")).encode()
    return base64.b64encode(zlib.compress(raw)).decode()


def post(url: str, payload: dict, token: str, pause: float) -> dict | None:
    """One API call, with room for the rate limiter to calm down."""
    delay = 8.0
    for _ in range(5):
        response = requests.post(
            url, headers={"Authorization": f"Bearer {token}",
                          "Content-Type": "application/json"},
            json=payload, timeout=120)
        if response.status_code == 200:
            time.sleep(pause)
            return response.json()
        # 429 is the documented limit; a burst also starts returning 400.
        if response.status_code in (400, 429):
            time.sleep(delay)
            delay = min(delay * 2, 120.0)
            continue
        return None
    return None


def leaderboard(token: str, top: int, pause: float) -> list[dict[str, Any]]:
    payload = post(BOARD_URL, {"competitionId": COMPETITION_ID,
                               "pageSize": max(top, 60)}, token, pause)
    if payload is None:
        raise SystemExit("could not read the leaderboard")
    rows = (payload.get("publicLeaderboard") or [])[:top]
    return [{"rank": r.get("rank"), "team_id": r.get("teamId"),
             "submission": r.get("submissionId"),
             "score": float(r.get("displayScore") or 0)}
            for r in rows if r.get("submissionId")]


def episodes_for(row: dict, token: str, pause: float) -> list[dict[str, Any]]:
    """That team's finished games, each tagged with whether they won it."""
    payload = post(EPISODE_URL, {"submissionId": row["submission"]},
                   token, pause)
    if payload is None:
        return []
    names = {t["id"]: t.get("teamName", "") for t in (payload.get("teams") or [])}
    out = []
    for episode in payload.get("episodes") or []:
        agents = episode.get("agents") or []
        mine = next((a for a in agents if a.get("teamId") == row["team_id"]), None)
        other = next((a for a in agents if a.get("teamId") != row["team_id"]), None)
        if mine is None or other is None or mine.get("reward") is None:
            continue
        out.append({
            "episode_id": episode["id"],
            "seat": int(mine.get("index", 0)),
            "reward": float(mine["reward"]),
            "opponent_reward": float(other.get("reward") or 0),
            "opponent": names.get(other.get("teamId"), ""),
            "opponent_rating": (other.get("updatedScore")
                                or other.get("initialScore") or 0.0),
            "team_name": names.get(row["team_id"], ""),
        })
    for e in out:
        e["won"] = e["reward"] > e["opponent_reward"]
    return out


def balanced(games: list[dict], per_team: int) -> list[dict]:
    """Half won, half lost, newest first, so the corpus shows both faces."""
    games = sorted(games, key=lambda g: -g["episode_id"])
    won = [g for g in games if g["won"]]
    lost = [g for g in games if not g["won"]]
    half = max(1, per_team // 2)
    picked = won[:half] + lost[:half]
    if len(picked) < per_team:  # top of the ladder rarely loses
        rest = [g for g in games if g not in picked]
        picked += rest[: per_team - len(picked)]
    return picked[:per_team]


def keep(game: dict, row: dict) -> bool:
    """Download one replay, store the tapes, throw the replay away."""
    path = OUT / f"ep{game['episode_id']}.json"
    if path.exists():
        return False
    try:
        response = requests.get(
            REPLAY_URL.format(episode=game["episode_id"]), timeout=300)
        if response.status_code != 200:
            return False
        replay = response.json()
    except Exception:  # a broken download must not stop the sweep
        return False
    steps = replay.get("steps") or []
    if not steps:
        return False
    seat = game["seat"]
    tapes = {}
    for label, who in (("them", seat), ("opponent", 1 - seat)):
        tapes[label] = pack([steps[i][who].get("action") or PASS_ACTION
                             for i in range(len(steps))])
    record = {
        "episode_id": game["episode_id"],
        "source_team": game["team_name"],
        "team_rank": row["rank"],
        "team_score": row["score"],
        "seat": seat,
        "won": game["won"],
        "rewards": {"them": game["reward"],
                    "opponent": game["opponent_reward"]},
        "opponent": game["opponent"],
        "opponent_rating": game["opponent_rating"],
        "seed": (replay.get("info") or {}).get("seed"),
        "actions_zlib_b64": tapes["them"],
        "opponent_actions_zlib_b64": tapes["opponent"],
        "configuration": {k: v for k, v in
                          (replay.get("configuration") or {}).items()
                          if k != "marketParams"},
    }
    del replay
    path.write_text(json.dumps(record), encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=200)
    parser.add_argument("--per-team", type=int, default=4)
    parser.add_argument("--pause", type=float, default=0.4)
    parser.add_argument("--start", type=int, default=0,
                        help="skip this many leaderboard rows, to resume")
    args = parser.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment")

    OUT.mkdir(parents=True, exist_ok=True)
    rows = leaderboard(token, args.top, args.pause)
    print(f"top {len(rows)} teams, scores {rows[0]['score']:.0f} to "
          f"{rows[-1]['score']:.0f}", flush=True)

    kept = seen = 0
    for i, row in enumerate(rows):
        if i < args.start:
            continue
        games = episodes_for(row, token, args.pause)
        if not games:
            print(f"  [{i + 1}/{len(rows)}] rank {row['rank']}: no episodes",
                  flush=True)
            continue
        picked = balanced(games, args.per_team)
        got = sum(keep(g, row) for g in picked)
        kept += got
        seen += len(picked)
        name = picked[0]["team_name"] or "?"
        print(f"  [{i + 1}/{len(rows)}] rank {row['rank']:3d} {name[:24]:24s} "
              f"{sum(g['won'] for g in picked)}W/{sum(not g['won'] for g in picked)}L "
              f"kept {got}  (total {kept})", flush=True)
    print(f"done: {kept} new tapes, {seen} considered, in "
          f"{OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
