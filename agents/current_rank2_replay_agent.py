"""Replay Ryo Hasegawa's actions from public episode 99058164."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPLAY_PATH = (
    Path(__file__).resolve().parent.parent
    / "artifacts"
    / "top-replays"
    / "episode-99058164-rank1-vs-rank2-replay.json"
)
SOURCE_PLAYER = 1
SOURCE_SEED = 1_192_301_511


def _load_actions() -> tuple[dict[str, Any], ...]:
    replay = json.loads(REPLAY_PATH.read_text(encoding="utf-8"))
    return tuple(
        record[SOURCE_PLAYER].get("action") or {
            "farmer": ["PASS"],
            "hands": [],
            "market": [],
        }
        for record in replay["steps"]
    )


ACTIONS = _load_actions()


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Return the Ryo action following the current replay step."""
    next_record = int(observation.get("step", 0)) + 1
    if next_record >= len(ACTIONS):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    return ACTIONS[next_record]
