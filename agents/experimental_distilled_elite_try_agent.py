"""Behavior clone of a route selected on provenance, not on a panel.

Source: episode 106683123, team "try" (live rating 2782.6), in a ranked
game they won by **100,906 coins against Sida Zuo at 2697**.

**Why the selection rule changed.** Candidate C1, C2, D and F are the same
architecture -- one frozen route under identical A+B guards, since
Candidate C's selector is a documented placeholder that never switches --
and they scored 2094.7, 2023.7, 1936.4 and 1375.8 live. The whole
seven-hundred-point spread is which tape. That choice was made twice on
local panels and both were wrong: the panel put F 18.7 points above D and
F came in 561 points below it.

The one criterion with a live result behind it is C1's own provenance: a
top-rated team **beating another strong team by a wide margin in a real
ranked game**. Not a validation self-play at rating 600, which is what the
panel picked for F. `rl/data/top_matches.jsonl` holds 5,835 such records
from the leaderboard's top forty and 1,971 of them qualify; this is the
seventh largest margin among them and its author is 2783.

Measured over 128 games against every agent this project has put on the
ladder -- C1, C2, D and F, sixteen seeds, both seats:

    this route          112/128 = 87.5%   median margin +13,265
    ep106716117 (same author)  110/128 = 85.9%   +11,840
    C1 (live 2094.7, then 1743.6)  40/128 = 31.2%        +0

**That is local evidence and local evidence has been wrong here before.**
It is reported because the gap is 55 points where the one that misled us
was 18, and because it agrees with the provenance rule rather than
standing alone. It is not a rating forecast.

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
    / "v1327-live-elite-try-106683123.json"
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
            "Distilled elite-try calendar must contain 720 records"
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
    """Execute the live-ladder elite action calendar."""
    return decide(observation)
