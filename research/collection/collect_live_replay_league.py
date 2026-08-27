"""Collect compact opponent schedules from public Kaggle episodes."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from policies.live_macro_features import extract_live_macro_features


REPLAY_URL = "https://www.kaggle.com/competitions/episodes/{}/replay.json"


def _fetch_replay(episode_id: int) -> dict[str, Any]:
    request = Request(
        REPLAY_URL.format(episode_id),
        headers={"User-Agent": "Kaggriculture-research/1.0"},
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def compact_episode(specification: str) -> dict[str, Any]:
    """Download and compact one ``episode_id:own_player`` specification."""
    episode_text, player_text = specification.split(":", 1)
    episode_id = int(episode_text)
    own_player = int(player_text)
    replay = _fetch_replay(episode_id)
    if int(replay.get("info", {}).get("EpisodeId", -1)) != episode_id:
        raise ValueError(f"Episode ID mismatch for {episode_id}")
    if replay.get("module_version") != "1.32.7":
        raise ValueError(f"Unexpected simulator for {episode_id}")
    if len(replay.get("steps", [])) != 720:
        raise ValueError(f"Incomplete replay for {episode_id}")
    opponent_player = 1 - own_player
    observation = next(
        state["observation"]
        for step in replay["steps"]
        if (state := step[own_player]).get("observation", {}).get("day") == 6
        and state["observation"].get("hour") == 0
    )
    return {
        "episode_id": episode_id,
        "seed": int(replay["info"]["seed"]),
        "own_player": own_player,
        "expected_rewards": replay["rewards"],
        "day6_features": extract_live_macro_features(observation),
        "day6_shops": observation.get("town", {}).get(
            "unlocked_shops", []
        ),
        "opponent_actions": [
            step[opponent_player].get("action")
            or {"farmer": ["PASS"], "hands": [], "market": []}
            for step in replay["steps"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--episode",
        action="append",
        required=True,
        help="episode_id:own_player",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        records = list(executor.map(compact_episode, args.episode))
    report = {
        "simulator_version": "1.32.7",
        "records": sorted(records, key=lambda record: record["episode_id"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Episodes: {len(records)}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()