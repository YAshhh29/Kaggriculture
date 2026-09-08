"""Behavior clone of a route recorded on the *current* ladder, not the
2026-09-04 cache.

Source: episode 106610780, Matthew Huang, live rating 2872.8.

**Why this route replaced RB25det.** Every route this project had to
choose from came from `kaggle_cache/`, captured on 2026-09-04, and every
one was screened against opponents drawn from that same cache. Profiling
the live corpus by what each agent *buys* showed what that cost us:
fourteen of the twenty-four teams we are actually drawn against post an
identical fingerprint -- 5 carrot seeds, 198 wheat, no geese -- which is
the public getting-started notebook run unmodified. RB25det's own
fingerprint is 6 carrot, 185 wheat, no geese. It is a member of that
family, so the search could only ever have found a good member of the
field we already sit in.

None of the nine teams rated above 2765 runs that opening. Screened under
the identical A+B guard stack against 32 live ladder opponents the route
was **not** selected against, both seats, 64 games:

    route                          mean coins   win rate   median margin
    Candidate D's (Andrey)             64,501     40.6%          -1,085
    RB25det (Candidate F until now)    67,514     37.5%          -3,786
    **this one (Matthew Huang)**       78,554   **92.2%**      **+18,030**

**Why this game of his and not another.** Section 9k measured that tape
quality belongs to the individual game rather than the player, so all
eight captured games of this submission were screened separately. The four
recorded during its climb all scored 87.5-93.8%; of the four recorded
later at 2873 against strong opposition, two scored 25%. A tape recorded
in a contested market encodes adaptations to scarcity that do not fit when
replayed into a market that is not contested the same way. This one is his
validation self-play, and it holds the best margin of the four.

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
    / "v1327-live-elite-mhuang-106610780.json"
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
            "Distilled elite-mhuang calendar must contain 720 records"
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
