"""Capture the winner's tape from specific games, chosen by provenance.

Route selection has been done twice on local panels and both times the
panel was wrong: Candidate D and Candidate F are structurally identical to
Candidate C1 and C2 -- one frozen route under the same A+B guards, with
C's selector a documented placeholder that never switches -- yet C1 and C2
reached 2100-2200 live while D sits at mu 1744 and F at 1691. **Only the
route differs, and it is worth roughly six hundred points.**

Their provenance differs completely. C1 clones episode 105144807, "fog
flower" at 2882.6, in a game where they beat the leaderboard's number two.
F clones episode 106610780, which is Matthew Huang's *validation self-play
game at rating 600* -- an agent playing itself before it had a rating at
all. D's route was picked by ranking candidates on their own final reward.

So this selects on the one criterion that has actually produced a good
route: **a top-rated team beating another strong team, by a wide margin,
in a real ranked game.** `rl/data/top_matches.jsonl` holds 5,835 such
records from the leaderboard's top forty, and 1,971 of them are 2700+
beating 2650+. The winner is the max-reward side, which is exactly what
`extract_tape` falls back to.

    KAGGLE_API_TOKEN=... python -m tools.data.fetch_by_episode \\
        --min-rating 2700 --min-opponent 2650 --top 20
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
MATCHES = ROOT / "rl" / "data" / "top_matches.jsonl"
OUT_DIR = ROOT / "kaggle_cache" / "live_clones"
INDEX = ROOT / "rl" / "data" / "live_opponents.jsonl"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode}.json"

from tools.data.fetch_live_opponents import extract_tape  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-rating", type=float, default=2700.0)
    parser.add_argument("--min-opponent", type=float, default=2650.0)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--per-team", type=int, default=3)
    parser.add_argument("--pause", type=float, default=1.5)
    args = parser.parse_args()

    if not os.environ.get("KAGGLE_API_TOKEN"):
        raise SystemExit("set KAGGLE_API_TOKEN in the environment")

    rows = [json.loads(x) for x in
            MATCHES.read_text(encoding="utf-8").splitlines()]
    games = [
        r for r in rows
        if not r.get("self_play") and r.get("won")
        and (r.get("rating") or 0) >= args.min_rating
        and (r.get("opponent_rating") or 0) >= args.min_opponent
    ]
    games.sort(key=lambda r: -r["margin"])

    picked: list[dict] = []
    per_team: dict[str, int] = {}
    for game in games:
        team = game["team"]
        if per_team.get(team, 0) >= args.per_team:
            continue
        per_team[team] = per_team.get(team, 0) + 1
        picked.append(game)
        if len(picked) >= args.top:
            break

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done = set()
    if INDEX.exists():
        for line in INDEX.read_text(encoding="utf-8").splitlines():
            done.add(int(json.loads(line)["episode_id"]))

    kept = 0
    with INDEX.open("a", encoding="utf-8") as index:
        for game in picked:
            episode = int(game["episode_id"])
            if episode in done:
                print(f"  ep{episode} already held", flush=True)
                continue
            try:
                response = requests.get(
                    REPLAY_URL.format(episode=episode), timeout=180
                )
                if response.status_code != 200:
                    print(f"  ep{episode} HTTP {response.status_code}",
                          flush=True)
                    continue
                replay = response.json()
            except Exception as error:
                print(f"  ep{episode} {type(error).__name__}", flush=True)
                continue
            got = extract_tape(replay, 0)      # 0 -> the max-reward side
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
                    "source_team": game["team"],
                    "source_episode_id": str(episode),
                }), encoding="utf-8"
            )
            index.write(json.dumps({
                "episode_id": episode,
                "team_id": game.get("team_id", 0),
                "name": game["team"],
                "rating": game.get("rating") or 0.0,
                "reward": reward,
                "beat": game.get("opponent"),
                "beat_rating": game.get("opponent_rating"),
                "margin": game.get("margin"),
            }, ensure_ascii=False) + "\n")
            index.flush()
            kept += 1
            safe = game["team"].encode("ascii", "replace").decode()[:20]
            print(f"  ep{episode} {safe:22s} {game['rating']:6.0f} beat "
                  f"{str(game['opponent'])[:18]:20s} "
                  f"{game['opponent_rating']:6.0f} by "
                  f"{game['margin']:+,.0f}", flush=True)
            time.sleep(args.pause)
    print(f"\ncaptured {kept} winner tapes", flush=True)


if __name__ == "__main__":
    main()
