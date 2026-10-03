"""Rejected route-following agent distilled from a recorded ladder game.

Kept for reference and not used by any live agent. The source is a live
game against an older version of this project's agent, chosen because many
opponents shared its cow/sheep pasture build (COW~8, SHEEP~6, 3 quadrants).
Raw and with Candidate A's guard layer
(`build_candidate_a_agent(baseline=...)`), it lost 0-6 to Candidate B on
fresh seeds. The likely reason is that games near our own rating do not
supply strong routes; those need a top-leaderboard game.

Open-loop playback at index `step + 1`; the guard layer is in
`candidates/candidate_a.py`.
"""

from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path
from typing import Any


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "v1327-public-pasture-105113156.json"
)
PASS = ["PASS"]


def _load_actions() -> tuple[dict[str, Any], ...]:
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    payload = str(model["actions_zlib_b64"])
    compressed = base64.b64decode(payload)
    actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    if len(actions) != 720:
        raise ValueError("Distilled pasture calendar must contain 720 records")
    return tuple(actions)


CALENDAR_ACTIONS = _load_actions()


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    next_record = int(observation.get("step", 0)) + 1
    if next_record >= len(CALENDAR_ACTIONS):
        return {"farmer": PASS, "hands": [], "market": []}
    planned = CALENDAR_ACTIONS[next_record]
    return {
        "farmer": list(planned.get("farmer", PASS)),
        "hands": [
            list(action) for action in planned.get("hands", [])
        ],
        "market": [list(order) for order in planned.get("market", [])],
    }


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Execute the learned cow/sheep-pasture action calendar."""
    return decide(observation)
