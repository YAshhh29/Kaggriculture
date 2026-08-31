"""Build a compact behavior-cloning calendar from a public replay."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any

from research.collection.collect_live_replay_league import _resolve_player


PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}


def build_model(
    replay_path: Path,
    team_name: str,
) -> dict[str, Any]:
    replay_bytes = replay_path.read_bytes()
    replay = json.loads(replay_bytes)
    player = _resolve_player(replay, "auto", team_name)
    actions = [
        record[player].get("action") or PASS_ACTION
        for record in replay["steps"]
    ]
    if len(actions) != 720:
        raise ValueError(f"Expected 720 replay records, found {len(actions)}")
    raw = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    payload = base64.b64encode(zlib.compress(raw, level=9)).decode("ascii")
    return {
        "model_type": "public_calendar_behavior_clone",
        "simulator_version": replay["module_version"],
        "source_episode_id": int(replay["info"]["EpisodeId"]),
        "source_seed": int(replay["info"]["seed"]),
        "source_team": team_name,
        "source_player": player,
        "records": len(actions),
        "replay_sha256": hashlib.sha256(replay_bytes).hexdigest(),
        "actions_sha256": hashlib.sha256(raw).hexdigest(),
        "actions_zlib_b64": payload,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--team-name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = build_model(args.replay, args.team_name)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(model, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Model: {args.output}")
    print(f"Episode: {model['source_episode_id']}")
    print(f"Actions SHA-256: {model['actions_sha256']}")


if __name__ == "__main__":
    main()
