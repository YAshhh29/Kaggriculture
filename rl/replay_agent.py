"""Build a callable agent that replays a fixed, real recorded action tape.

Same convention as agents/experimental_distilled_elite_pasture_agent.py and
agents/experimental_distilled_elite_giulio_agent.py, generalized over any
720-record action list: a pure, open-loop, per-step lookup with no internal
cursor, so it is legal to hand it observations starting at any step. Used to
turn kaggle_cache/clones/opp_<episode_id>.json (real opponents' actual
action sequences, extracted by tools/data/build_opponent_clones.py) into
local head-to-head opponents for benchmark.run_game.
"""

from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path
from typing import Any

from rl.runtime import AgentAction


PASS: list[str] = ["PASS"]


def load_clone_actions(path: Path) -> tuple[AgentAction, ...]:
    clone = json.loads(path.read_text(encoding="utf-8"))
    compressed = base64.b64decode(str(clone["actions_zlib_b64"]))
    actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    if len(actions) != 720:
        raise ValueError(f"{path} must contain 720 action records")
    return tuple(actions)


def build_replay_agent(actions: tuple[AgentAction, ...] | list[AgentAction]):
    def decide(observation: dict[str, Any]) -> AgentAction:
        # The action recorded at replay index k was chosen while observing
        # step k-1 (empirically confirmed against kaggle_environments, not
        # assumed -- see rl/GOAL.md; matches the existing
        # experimental_distilled_elite_pasture_agent.py convention).
        next_record = int(observation.get("step", 0)) + 1
        if next_record >= len(actions):
            return {"farmer": PASS, "hands": [], "market": []}
        planned = actions[next_record]
        return {
            "farmer": list(planned.get("farmer", PASS)),
            "hands": [list(action) for action in planned.get("hands", [])],
            "market": [list(order) for order in planned.get("market", [])],
        }

    return decide


def load_replay_agent(path: Path):
    return build_replay_agent(load_clone_actions(path))
