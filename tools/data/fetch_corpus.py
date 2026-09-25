"""Build a fresh replay corpus of the top N teams, won games and lost.

Replaces the old top200_tapes sweep, which had three problems that cost this
project real results:

* It wrote into the same directory the panels read from, so a fetch running
  during a measurement silently changed which tapes an arm played. Two
  comparisons were voided that way. This writes to its own directory, and
  panels should pin an explicit tape list regardless.
* Its retry covered HTTP 400/429 only. A ConnectTimeout raised straight out of
  requests and ended the whole sweep -- twice. Every network call here is
  retried on exceptions too, with backoff.
* It downloaded ~30 MB replays one at a time. The leaderboard and episode
  listings are rate-limited API calls and stay sequential; the replays are
  public storage and are fetched on a thread pool.

For each team the newest games are taken half won and half lost, so the
corpus shows how a team wins and how it gets beaten. Each record keeps the
seed, both sides' action tapes, both rewards, both team names and ratings --
enough to replay the whole game locally and deterministically -- and the
30 MB replay is discarded. A snapshot of the leaderboard as it stood at fetch
time is written beside the tapes, so ranks and ratings are never guessed later.

    KAGGLE_API_TOKEN=... python -m tools.data.fetch_corpus --top 500 --per-team 8
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

from tools.data.fetch_top200_tapes import (BOARD_URL, COMPETITION_ID,
                                           EPISODE_URL, PASS_ACTION,
                                           REPLAY_URL, balanced, pack)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "kaggle_cache" / "corpus_v2"
_LOCK = threading.Lock()


def _log(message: str) -> None:
    with _LOCK:
        print(message, flush=True)


def post(url: str, payload: dict, token: str, pause: float) -> dict | None:
    """A rate-limited API call that survives both 429s and dropped sockets."""
    delay = 8.0
    for attempt in range(7):
        try:
            response = requests.post(
                url, headers={"Authorization": f"Bearer {token}",
                              "Content-Type": "application/json"},
                json=payload, timeout=120)
        except requests.RequestException as error:
            _log(f"    network error ({type(error).__name__}), "
                 f"retry {attempt + 1} in {delay:.0f}s")
            time.sleep(delay)
            delay = min(delay * 2, 180.0)
            continue
        if response.status_code == 200:
            time.sleep(pause)
            return response.json()
        if response.status_code in (400, 429, 500, 502, 503, 504):
            time.sleep(delay)
            delay = min(delay * 2, 180.0)
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
             "team_name": r.get("teamName", ""),
             "submission": r.get("submissionId"),
             "score": float(r.get("displayScore") or 0)}
            for r in rows if r.get("submissionId")]


def episodes_for(row: dict, token: str, pause: float) -> list[dict[str, Any]]:
    payload = post(EPISODE_URL, {"submissionId": row["submission"]},
                   token, pause)
    if payload is None:
        return []
    names = {t["id"]: t.get("teamName", "")
             for t in (payload.get("teams") or [])}
    out = []
    for episode in payload.get("episodes") or []:
        agents = episode.get("agents") or []
        mine = next((a for a in agents
                     if a.get("teamId") == row["team_id"]), None)
        other = next((a for a in agents
                      if a.get("teamId") != row["team_id"]), None)
        if mine is None or other is None or mine.get("reward") is None:
            continue
        out.append({
            "episode_id": episode["id"],
            "seat": int(mine.get("index", 0)),
            "reward": float(mine["reward"]),
            "opponent_reward": float(other.get("reward") or 0),
            "opponent": names.get(other.get("teamId"), ""),
            "opponent_team_id": other.get("teamId"),
            "opponent_rating": (other.get("updatedScore")
                                or other.get("initialScore") or 0.0),
            "team_name": names.get(row["team_id"], "") or row["team_name"],
        })
    for e in out:
        e["won"] = e["reward"] > e["opponent_reward"]
    return out


def download(game: dict, row: dict, out: Path) -> str:
    """One replay to a compact record. Returns 'kept', 'exists' or 'failed'."""
    path = out / f"ep{game['episode_id']}.json"
    if path.exists():
        return "exists"
    replay = None
    delay = 5.0
    for _ in range(5):
        try:
            response = requests.get(
                REPLAY_URL.format(episode=game["episode_id"]), timeout=300)
            if response.status_code == 200:
                replay = response.json()
                break
            if response.status_code == 404:
                return "failed"
        except (requests.RequestException, ValueError):
            pass
        time.sleep(delay)
        delay = min(delay * 2, 90.0)
    if not replay:
        return "failed"
    steps = replay.get("steps") or []
    if not steps:
        return "failed"
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
        "opponent_team_id": game.get("opponent_team_id"),
        "opponent_rating": game["opponent_rating"],
        "seed": (replay.get("info") or {}).get("seed"),
        "actions_zlib_b64": tapes["them"],
        "opponent_actions_zlib_b64": tapes["opponent"],
        "configuration": {k: v for k, v in
                          (replay.get("configuration") or {}).items()
                          if k != "marketParams"},
    }
    del replay
    tmp = path.with_suffix(".part")
    tmp.write_text(json.dumps(record), encoding="utf-8")
    tmp.replace(path)  # never leave a half-written tape for a panel to read
    return "kept"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=500)
    parser.add_argument("--per-team", type=int, default=8)
    parser.add_argument("--pause", type=float, default=0.5)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--start", type=int, default=0,
                        help="skip this many leaderboard rows, to resume")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment")

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    rows = leaderboard(token, args.top, args.pause)
    snapshot = {"fetched_at_unix": int(time.time()), "rows": rows}
    (out / "leaderboard.json").write_text(json.dumps(snapshot, indent=1),
                                           encoding="utf-8")
    _log(f"top {len(rows)} teams, ratings {rows[0]['score']:.0f} "
         f"to {rows[-1]['score']:.0f}; snapshot saved")

    counts = {"kept": 0, "exists": 0, "failed": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = []
        for i, row in enumerate(rows):
            if i < args.start:
                continue
            games = episodes_for(row, token, args.pause)
            if not games:
                _log(f"  [{i + 1}/{len(rows)}] rank {row['rank']}: "
                     f"no episodes")
                continue
            picked = balanced(games, args.per_team)
            won = sum(g["won"] for g in picked)
            _log(f"  [{i + 1}/{len(rows)}] rank {row['rank']:3d} "
                 f"{(picked[0]['team_name'] or '?')[:26]:26s} "
                 f"{row['score']:7.1f}  queued {len(picked)} "
                 f"({won}W/{len(picked) - won}L)")
            pending += [pool.submit(download, g, row, out) for g in picked]
            # Drain finished downloads as we go so memory stays flat.
            still = []
            for f in pending:
                if f.done():
                    counts[f.result()] += 1
                else:
                    still.append(f)
            pending = still
        for f in as_completed(pending):
            counts[f.result()] += 1
    _log(f"done: {counts['kept']} new, {counts['exists']} already held, "
         f"{counts['failed']} failed, in {out}")


if __name__ == "__main__":
    main()
