"""Behavior clone of the route that wins most often, not the one that
scores most.

Source: episode 105419382, the "RB25det" side.

**Why this route and not the higher-scoring one.** Kaggle's simulation
ladder rates on match *outcomes* -- a game won by one coin counts exactly
as much as a game won by fifty thousand -- but every route this project
has selected, Candidate D's included, was chosen by ranking candidates on
mean reward. Screened under the identical A+B guard stack against 80 real
opponents drawn from the cached corpus, both seats, 160 games each:

    route                     mean coins   win rate
    Candidate D's (Andrey)       100,815        85%   (136/160)
    **this one (RB25det)**        92,459    **95%**   (152/160)

It gives up about 8,000 coins a game and wins sixteen more games in a
hundred and sixty.

**The counter-argument, and why it is answered.** The Andrey agent's own
docstring explains that it chose own-reward over win rate deliberately,
because section 9m measured that win rate against *frozen tapes*
overstates live strength by roughly forty points, while coin production is
largely self-determined and transfers. That is a fair objection to
absolute win rates -- but not to a relative ordering measured on an
identical panel, and the ordering is checked again in 10.8k against the
forty strongest opponents in the corpus specifically, which is the regime
where the objection would bite hardest.

Same open-loop mechanism as the other distilled agents: a per-step lookup
into the recorded action sequence, indexed `step + 1` because the action
recorded at replay index k was chosen while observing step k-1.
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
    / "v1327-public-elite-rb25det-105419382.json"
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
            "Distilled elite-andrey calendar must contain 720 records"
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
