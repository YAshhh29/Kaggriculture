"""Replay the opponent from future-labor ladder episode 100978351."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
import zlib


SCHEDULE_PATH = (
    Path(__file__).resolve().parent
    / "replay_schedules"
    / "episode-100978351-player1-actions.zlib.b64"
)
SOURCE_PLAYER = 1
SOURCE_SEED = 1_426_717_232


def _load_actions() -> tuple[dict[str, Any], ...]:
    payload = zlib.decompress(
        base64.b64decode(SCHEDULE_PATH.read_bytes())
    )
    actions = json.loads(payload.decode("utf-8"))
    if len(actions) != 720 or not all(
        isinstance(action, dict) for action in actions
    ):
        raise ValueError("Invalid first-loss replay schedule")
    return tuple(actions)


ACTIONS = _load_actions()


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Return the captured opponent action following the current step."""
    next_record = int(observation.get("step", 0)) + 1
    if next_record >= len(ACTIONS):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    return ACTIONS[next_record]