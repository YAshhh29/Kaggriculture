"""Collect compact opponent schedules from public Kaggle episodes."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from policies.live_macro_features import extract_live_macro_features


REPLAY_URL = "https://www.kaggle.com/competitions/episodes/{}/replay.json"
DECISION_POINTS = (
    (6, 0),
    *((day, hour) for day in range(9, 13) for hour in (8, 12)),
)


def _fetch_replay(episode_id: int) -> dict[str, Any]:
    request = Request(
        REPLAY_URL.format(episode_id),
        headers={"User-Agent": "Kaggriculture-research/1.0"},
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def _decision_contexts(
    replay: dict[str, Any],
    own_player: int,
) -> dict[str, dict[str, Any]]:
    observations = {
        (
            int(observation.get("day", -1)),
            int(observation.get("hour", -1)),
        ): observation
        for step in replay["steps"]
        if isinstance(
            observation := step[own_player].get("observation"),
            dict,
        )
    }
    missing = [point for point in DECISION_POINTS if point not in observations]
    if missing:
        raise ValueError(f"Replay is missing decision contexts: {missing}")
    return {
        f"day{day}_hour{hour}": {
            "features": extract_live_macro_features(observations[(day, hour)]),
            "shops": observations[(day, hour)].get("town", {}).get(
                "unlocked_shops", []
            ),
        }
        for day, hour in DECISION_POINTS
    }


def merge_records(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Refresh known episodes and append new ones without relabeling them."""
    merged = {int(record["episode_id"]): record for record in existing}
    for record in incoming:
        episode_id = int(record["episode_id"])
        previous = merged.get(episode_id)
        if previous is not None:
            identity = ("seed", "own_player", "expected_rewards")
            if any(previous[key] != record[key] for key in identity):
                raise ValueError(f"Conflicting episode metadata: {episode_id}")
        merged[episode_id] = record
    return [merged[episode_id] for episode_id in sorted(merged)]


def _resolve_player(
    replay: dict[str, Any],
    player_text: str,
    team_name: str | None,
) -> int:
    requested = None if player_text.casefold() == "auto" else int(player_text)
    if team_name is None:
        if requested is None:
            raise ValueError("episode:auto requires --team-name")
        return requested
    agents = replay.get("info", {}).get("Agents", [])
    matches = [
        player
        for player, agent in enumerate(agents)
        if str(agent.get("Name", "")).casefold() == team_name.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one replay agent named {team_name!r}, "
            f"found {len(matches)}"
        )
    resolved = matches[0]
    if requested is not None and requested != resolved:
        raise ValueError(
            f"Requested player {requested} is not {team_name!r}; "
            f"replay player is {resolved}"
        )
    return resolved


def compact_episode(
    specification: str,
    team_name: str | None = None,
) -> dict[str, Any]:
    """Download and compact one ``episode_id:own_player`` specification."""
    episode_text, player_text = specification.split(":", 1)
    episode_id = int(episode_text)
    replay = _fetch_replay(episode_id)
    if int(replay.get("info", {}).get("EpisodeId", -1)) != episode_id:
        raise ValueError(f"Episode ID mismatch for {episode_id}")
    if replay.get("module_version") != "1.32.7":
        raise ValueError(f"Unexpected simulator for {episode_id}")
    if len(replay.get("steps", [])) != 720:
        raise ValueError(f"Incomplete replay for {episode_id}")
    own_player = _resolve_player(replay, player_text, team_name)
    opponent_player = 1 - own_player
    contexts = _decision_contexts(replay, own_player)
    day6 = contexts["day6_hour0"]
    return {
        "episode_id": episode_id,
        "seed": int(replay["info"]["seed"]),
        "own_player": own_player,
        "expected_rewards": replay["rewards"],
        "day6_features": day6["features"],
        "day6_shops": day6["shops"],
        "decision_contexts": contexts,
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
    parser.add_argument("--append", action="store_true")
    parser.add_argument(
        "--team-name",
        help="validate or auto-resolve the requested player's replay name",
    )
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        incoming = list(
            executor.map(
                partial(compact_episode, team_name=args.team_name),
                args.episode,
            )
        )
    existing = []
    if args.append and args.output.is_file():
        existing = json.loads(
            args.output.read_text(encoding="utf-8")
        ).get("records", [])
    records = merge_records(existing, incoming)
    report = {
        "simulator_version": "1.32.7",
        "records": records,
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
