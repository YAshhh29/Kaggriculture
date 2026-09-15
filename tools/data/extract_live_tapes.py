"""Keep what it takes to replay our own live ladder games exactly.

A live Kaggriculture replay records the episode's seed (``info.seed``) and
both agents' actions. Playing the opponent's recorded actions against our
agent, with the same seed and seat, reproduces the live game exactly: on
episode 109250573 all 720 of Agent H's actions and both final rewards
matched the ladder to the coin. So every game we played on the ladder
becomes a test case, and a new version of an agent can be played on the
exact games the old one lost.

Replays are about 30 MB each, so this keeps a compact record per episode --
seed, our side, both action tapes (zlib + base64), live rewards, and a
day-by-day summary of both farms -- and discards the raw replay. Episode
ids come from ``rl/data/our_games.jsonl`` (``tools.data.fetch_our_games``);
the replay files themselves are public, so no token is needed.

    python -m tools.data.extract_live_tapes --submission 56247912
"""

from __future__ import annotations

import argparse
import base64
import json
import time
import zlib
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
GAMES = ROOT / "rl" / "data" / "our_games.jsonl"
OUT = ROOT / "rl" / "data" / "our_live_tapes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode}.json"
PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}


def pack(actions: list[Any]) -> str:
    raw = json.dumps(actions, separators=(",", ":")).encode()
    return base64.b64encode(zlib.compress(raw)).decode()


def unpack(blob: str) -> list[Any]:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def farm_day(farm: dict[str, Any], private: dict[str, Any]) -> dict[str, Any]:
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
    shed = (private or {}).get("shed") or {}
    return {
        "money": float(farm.get("money", 0) or 0),
        "herd": herd,
        "planted": planted,
        "tiles": owned,
        "shed": sum(int(v) for v in shed.values()),
    }


def summarise(steps: list[Any], side: int) -> list[dict[str, Any]]:
    """Both farms at the start of each day, and hands at midday."""
    days = []
    for day in range(30):
        start = min(day * 24, len(steps) - 1)
        noon = min(day * 24 + 12, len(steps) - 1)
        row: dict[str, Any] = {"day": day}
        for label, who in (("us", side), ("them", 1 - side)):
            view = steps[start][who].get("observation") or {}
            shared = steps[start][0].get("observation") or {}
            farms = shared.get("farms") or view.get("farms") or []
            if who >= len(farms):
                continue
            row[label] = farm_day(farms[who], view.get("private") or {})
            noon_farms = (steps[noon][0].get("observation") or {}).get(
                "farms") or []
            if who < len(noon_farms):
                row[label]["hands"] = len(noon_farms[who].get("hands") or [])
        days.append(row)
    return days


def extract(replay: dict[str, Any], side: int) -> dict[str, Any]:
    steps = replay["steps"]
    tapes = []
    for who in (0, 1):
        tapes.append([steps[i][who].get("action") or PASS_ACTION
                      for i in range(len(steps))])
    rewards = replay.get("rewards") or [None, None]
    return {
        "seed": (replay.get("info") or {}).get("seed"),
        "our_side": side,
        "team_names": (replay.get("info") or {}).get("TeamNames"),
        "rewards": {"us": rewards[side], "them": rewards[1 - side]},
        "our_actions_zlib_b64": pack(tapes[side]),
        "opp_actions_zlib_b64": pack(tapes[1 - side]),
        "days": summarise(steps, side),
        "configuration": {k: v for k, v in
                          (replay.get("configuration") or {}).items()
                          if k != "marketParams"},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=int, required=True)
    parser.add_argument("--pause", type=float, default=1.0)
    args = parser.parse_args()

    rows = [json.loads(line) for line in
            GAMES.read_text(encoding="utf-8").splitlines()]
    games = {int(r["episode_id"]): r for r in rows
             if r.get("submission") == args.submission}
    OUT.mkdir(parents=True, exist_ok=True)
    kept = skipped = 0
    for episode, row in sorted(games.items()):
        path = OUT / f"ep{episode}.json"
        if path.exists():
            skipped += 1
            continue
        try:
            response = requests.get(REPLAY_URL.format(episode=episode),
                                    timeout=300)
            if response.status_code != 200:
                print(f"  ep{episode} HTTP {response.status_code}", flush=True)
                continue
            replay = response.json()
        except Exception as error:  # a broken download must not stop the rest
            print(f"  ep{episode} {type(error).__name__}", flush=True)
            continue
        record = extract(replay, int(row["side"]))
        del replay
        record.update({
            "episode_id": episode,
            "submission": args.submission,
            "opponent": row.get("opponent"),
            "opponent_rating": row.get("opponent_rating"),
            "won": row.get("won"),
        })
        path.write_text(json.dumps(record), encoding="utf-8")
        kept += 1
        if kept % 10 == 0:
            print(f"  {kept} extracted", flush=True)
        time.sleep(args.pause)
    print(f"extracted {kept}, already held {skipped}, "
          f"{len(games)} games for submission {args.submission}")


if __name__ == "__main__":
    main()
