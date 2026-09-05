"""Behavior clone of the strongest tape found by systematic search.

Source: episode 105531280, player 1 ("Giulio Ravasio", public leaderboard
2908.0 at capture), the winning side of a 2026-09-04 top-table game.

This is *not* the same Giulio game Candidate C2 clones. C2 uses episode
105144807, captured 2026-09-03. This one was selected by scoring **191
candidate tapes** -- every side of every cached replay belonging to a team
rated 2400+ on the game that team won -- on our own final reward across
fixed seeds with the same guard stack. See rl/GOAL.md section 9n.

Why own-reward drove the search rather than win rate: section 9m measured
that win rate against frozen tapes overstates live strength by roughly
forty points, while our own coin production is almost entirely
self-determined (a probe showed byte-identical farm play across seeds,
with reward moving only through market prices). Coins transfer; tape-panel
win rate does not.

Same open-loop mechanism as the other distilled agents: a per-step lookup
into the recorded action sequence, indexed `step + 1` because the action
recorded at replay index k was the one chosen while observing step k-1
(verified empirically against the simulator, not assumed).
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
    / "v1327-public-elite-giulio2-105531280.json"
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
            "Distilled elite-giulio2 calendar must contain 720 records"
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
    """Execute the searched-best elite action calendar."""
    return decide(observation)
