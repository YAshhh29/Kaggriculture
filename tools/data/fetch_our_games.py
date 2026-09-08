"""Download our own live games, with the full state, not just the tape.

Every evaluation in this project has been made against frozen tapes, and
the live record now says that instrument is not merely imprecise but
pointed the wrong way: the panel scored Candidate F 18.7 points above
Candidate D on identical games, and live D holds ~1744 while F holds
~1687 internally and 1356 on the board. A measurement that inverts the
ordering it is used to make cannot be repaired by running more of it.

So this fetches the replays of games *we actually played* -- both sides'
observations at every step, not the compact action tape -- so the question
"what was true in the games we lost" can be asked of real opposition
instead of recordings.

Replays are ~30 MB each, so this keeps a reduced trace rather than the
raw file: per-day money for both farms, both herds, both planted counts,
the market inventory of all nine goods, and our own action mix. That is
enough to compare our decisions against the opponent's at the moment the
game turned, and it costs kilobytes.

    KAGGLE_API_TOKEN=... python -m tools.data.fetch_our_games \\
        --submission 56076097 --games 40
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
OUT = ROOT / "rl" / "data" / "our_games.jsonl"
EPISODE_URL = (
    "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
)
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode}.json"
OUR_TEAM = 16724366
GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")
TURNS_PER_DAY = 24
MARKET_I0 = 10000


def farm_snapshot(farm: Any) -> dict[str, Any]:
    if not isinstance(farm, dict):
        return {}
    herd = planted = owned = 0
    for row in farm.get("tiles") or []:
        for tile in row:
            if tile == "LOCKED":
                continue
            owned += 1
            if isinstance(tile, dict):
                if "animal" in tile:
                    herd += 1
                elif tile.get("kind") == "PLANT":
                    planted += 1
    return {
        "money": float(farm.get("money", 0) or 0),
        "herd": herd,
        "planted": planted,
        "tiles": owned,
        "hands": len(farm.get("hands") or []),
        "quadrants": len(farm.get("unlocked_quadrants") or []),
    }


def reduce_replay(replay: dict[str, Any], side: int) -> dict[str, Any]:
    steps = replay.get("steps") or []
    days: list[dict[str, Any]] = []
    for day in range(30):
        index = min(day * TURNS_PER_DAY, len(steps) - 1)
        step = steps[index]
        observation = None
        for view in step:
            candidate = view.get("observation")
            if isinstance(candidate, dict) and candidate.get("farms"):
                observation = candidate
                break
        if observation is None:
            continue
        farms = observation.get("farms") or []
        stock = (observation.get("market") or {}).get("inventory") or {}
        days.append({
            "day": day,
            "us": farm_snapshot(farms[side] if side < len(farms) else None),
            "them": farm_snapshot(
                farms[1 - side] if 1 - side < len(farms) else None
            ),
            "market": {
                g: float(stock.get(g, MARKET_I0)) - MARKET_I0 for g in GOODS
            },
        })
    verbs: dict[str, int] = {}
    sells: dict[str, int] = {}
    for step in steps:
        if side >= len(step):
            continue
        action = step[side].get("action")
        if not isinstance(action, dict):
            continue
        for unit in [action.get("farmer"), *(action.get("hands") or [])]:
            if isinstance(unit, list) and unit:
                verbs[str(unit[0])] = verbs.get(str(unit[0]), 0) + 1
        for order in action.get("market") or []:
            if isinstance(order, list) and len(order) > 2 and order[0] == "SELL":
                sells[str(order[1])] = sells.get(str(order[1]), 0) + int(order[2])
    final = steps[-1] if steps else []
    return {
        "days": days,
        "verbs": verbs,
        "sell_requests": sells,
        "our_reward": float(final[side].get("reward") or 0) if final else 0.0,
        "their_reward": (
            float(final[1 - side].get("reward") or 0) if final else 0.0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=int, required=True)
    parser.add_argument("--games", type=int, default=40)
    parser.add_argument("--pause", type=float, default=2.0)
    parser.add_argument("--label", default="")
    args = parser.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment")

    response = requests.post(
        EPISODE_URL,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json={"submissionId": args.submission}, timeout=120,
    )
    payload = response.json()
    names = {t["id"]: t.get("teamName", "")
             for t in (payload.get("teams") or [])}
    episodes = []
    for episode in payload.get("episodes") or []:
        agents = episode.get("agents") or []
        mine = next((a for a in agents if a.get("teamId") == OUR_TEAM), None)
        other = next((a for a in agents if a.get("teamId") != OUR_TEAM), None)
        if mine is None or other is None or mine.get("reward") is None:
            continue
        episodes.append({
            "episode_id": episode["id"],
            "side": int(mine.get("index", 0)),
            "opponent": names.get(other.get("teamId"), ""),
            "opponent_rating": (other.get("updatedScore")
                                or other.get("initialScore") or 0.0),
            "won": float(mine["reward"]) > float(other.get("reward") or 0),
        })
    episodes = episodes[: args.games]
    print(f"{len(episodes)} games to fetch "
          f"({sum(1 for e in episodes if e['won'])} won)", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            done.add(json.loads(line)["episode_id"])
    kept = 0
    with OUT.open("a", encoding="utf-8") as handle:
        for row in episodes:
            if row["episode_id"] in done:
                continue
            try:
                raw = requests.get(
                    REPLAY_URL.format(episode=row["episode_id"]), timeout=180
                )
                if raw.status_code != 200:
                    continue
                replay = raw.json()
            except Exception:
                continue
            row.update(reduce_replay(replay, row["side"]))
            del replay
            row["submission"] = args.submission
            row["label"] = args.label
            handle.write(json.dumps(row) + "\n")
            handle.flush()
            kept += 1
            if kept % 5 == 0:
                print(f"  {kept}/{len(episodes)}", flush=True)
            time.sleep(args.pause)
    print(f"kept {kept} reduced traces in {OUT.name}", flush=True)


if __name__ == "__main__":
    main()
