"""Behavior clone of an elite cow/sheep-pasture strategy ("fog flower").

Source: episode 105144807, player 1 ("fog flower", public leaderboard
score 2882.6 at capture time), which beat "Giulio Ravasio" (leaderboard
rank #2, 2965.4) 71471-69193. Unlike the two rejected clones in
`experimental_distilled_pasture_agent.py` (sourced from this project's own
match history, where opponents are matched near this project's own rating
by Kaggle's ladder), this source was pulled directly from the leaderboard
via the Kaggle API and is a genuinely elite, top-tier result -- a much
stronger candidate than anything sourced from this project's own games.
See rl/GOAL.md section 9c.

Same method as `experimental_distilled_calendar_agent.py`: a fixed,
open-loop, per-step lookup into the exact recorded action sequence.
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
    / "v1327-public-elite-fogflower-105144807.json"
)
MODEL_PAYLOAD: str | None = None
PASS = ["PASS"]


def _load_actions() -> tuple[dict[str, Any], ...]:
    payload = MODEL_PAYLOAD
    if payload is None:
        model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
        payload = str(model["actions_zlib_b64"])
    compressed = base64.b64decode(payload)
    actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    if len(actions) != 720:
        raise ValueError(
            "Distilled elite-pasture calendar must contain 720 records"
        )
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
    """Execute the learned elite cow/sheep-pasture action calendar."""
    return decide(observation)
