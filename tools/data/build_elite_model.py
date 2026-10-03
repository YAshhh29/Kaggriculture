"""Turn one elite replay side into a verified route model file.

Mirrors the schema already used by
`models/v1327-public-elite-fogflower-105144807.json` exactly, including the
compact-separator `actions_sha256` convention (a spaced-separator hash was a
real bug once; see docs/research/GOAL.md section 9c).

Usage:
    python -m tools.data.build_elite_model <replay.json> "<Team Name>" <out.json>
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import zlib
from pathlib import Path
from typing import Any


SIMULATOR_VERSION = "1.32.7"
MODEL_TYPE = "public_calendar_behavior_clone"


def build_model(
    replay_path: Path,
    team: str,
    leaderboard_context: str | None = None,
) -> dict[str, Any]:
    raw = replay_path.read_bytes()
    replay = json.loads(raw)
    if str(replay.get("module_version", "")) != SIMULATOR_VERSION:
        raise ValueError(f"unexpected simulator: {replay.get('module_version')}")
    if replay.get("statuses") != ["DONE", "DONE"]:
        raise ValueError(f"replay did not finish: {replay.get('statuses')}")
    names = [
        str(agent.get("Name", ""))
        for agent in replay.get("info", {}).get("Agents", [])
    ]
    matches = [i for i, n in enumerate(names) if n.casefold() == team.casefold()]
    if len(matches) != 1:
        raise ValueError(f"team {team!r} not unique in {names}")
    side = matches[0]
    steps = replay.get("steps") or []
    if len(steps) != 720:
        raise ValueError(f"expected 720 records, found {len(steps)}")
    actions = [step[side].get("action") for step in steps]
    if any(a is None for a in actions):
        raise ValueError("replay contains a missing action record")

    payload = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    model = {
        "model_type": MODEL_TYPE,
        "simulator_version": SIMULATOR_VERSION,
        "source_episode_id": int(replay["info"]["EpisodeId"]),
        "source_seed": int(replay["info"].get("seed", -1)),
        "source_team": names[side],
        "source_player": side,
        "source_leaderboard_context": leaderboard_context,
        "records": 720,
        "replay_sha256": hashlib.sha256(raw).hexdigest(),
        "actions_sha256": hashlib.sha256(payload).hexdigest(),
        "actions_zlib_b64": base64.b64encode(
            zlib.compress(payload, level=9)
        ).decode("ascii"),
    }
    verify(model)
    return model


def verify(model: dict[str, Any]) -> None:
    """Re-derive every hash the packaging pipeline will later check."""
    compressed = base64.b64decode(str(model["actions_zlib_b64"]), validate=True)
    actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    if len(actions) != 720 or model["records"] != 720:
        raise ValueError("model must contain exactly 720 records")
    payload = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(payload).hexdigest() != model["actions_sha256"]:
        raise ValueError("actions_sha256 mismatch")


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    replay, team, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    context = sys.argv[4] if len(sys.argv) > 4 else None
    model = build_model(replay, team, context)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    print(f"team          : {model['source_team']} (player {model['source_player']})")
    print(f"episode       : {model['source_episode_id']}")
    print(f"actions_sha256: {model['actions_sha256']}")
    print(f"written       : {out}")


if __name__ == "__main__":
    main()
