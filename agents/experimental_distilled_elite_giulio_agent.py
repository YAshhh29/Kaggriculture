"""Behavior clone of the leaderboard #2 elite strategy ("Giulio Ravasio").

Source: episode 105144807, player 0 ("Giulio Ravasio", public leaderboard
rank #2 at 2965.4 when captured), pulled from the leaderboard via the
Kaggle API rather than from this project's own match history -- the
sourcing distinction that separated the two viable clones from the four
rejected ones (see docs/research/GOAL.md sections 9b/9c).

This is the second elite baseline, kept deliberately distinct from
`experimental_distilled_elite_pasture_agent.py` ("fog flower", 2882.6) so
that the two Candidate C variants differ by strategy rather than by a
hair -- two agents differing by ~1 decision per game would be
indistinguishable against the leaderboard's measured +/-35 point noise on
identical bytes.

Measured, wrapped in the same guard and market-timing stack: beats
Candidate B 8-0 on fresh seeds (970-973, both seats) and loses 2-6
head-to-head to the fog flower variant. Strong in absolute terms, weaker
than C1 -- recorded here so nobody has to rediscover it.

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
    / "v1327-public-elite-giulio-105144807.json"
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
            "Distilled elite-giulio calendar must contain 720 records"
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
    """Execute the learned leaderboard-#2 action calendar."""
    return decide(observation)
