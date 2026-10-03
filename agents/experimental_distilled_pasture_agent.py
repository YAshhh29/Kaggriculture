"""REJECTED clone of a currently-prevalent cow/sheep-pasture strategy.

Kept for the record, not used by anything live -- see docs/research/GOAL.md section
9a. Source: episode 105113156, player 1 ("Mikhail_Komkin"), a live Kaggle
game against this project's own (older) Candidate A/B, final score
105007-61586, its largest observed margin against Candidate A/B across 24
real replays. Chosen because at least 15-18 of those 24 games, across many
different team names, share this same COW~8/SHEEP~6/3-quadrant signature
-- not one idiosyncratic opponent, but the current dominant meta archetype.

Tested (both raw and with Candidate A's guard layer applied via
`build_candidate_a_agent(baseline=...)`) against the *current* Candidate B
on 3 fresh seeds, both seats (6 games each): lost 0-6 both times, guards
firing zero times. A second independent episode from the same archetype
(105061000, "Mwanza Wambua", its own largest margin against Candidate
A/B) was cloned the same way and tested the same way: also 0-6, both
raw and guarded. Two independently-sourced episodes of the current
dominant meta archetype both lose decisively to the current Candidate B
on seeds neither was recorded on. Likely explanation: Kaggle's ladder
pairs similarly-rated opponents, so games from this project's own match
history reflect players near this project's own rating, not top-of-
leaderboard play the way the original Crop Dusta calendar clone (which
this project also could not source from its own match history) evidently
was. A genuinely strong second route probably needs a replay involving a
top-leaderboard player, not just any recent opponent.

Same method as `experimental_distilled_calendar_agent.py`: a fixed,
open-loop, per-step lookup into the exact recorded action sequence. No
adaptation to a different game -- see `candidates/candidate_a.py` for the guard
layer this was tested with.
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
