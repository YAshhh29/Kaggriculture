"""Exact replays for the opponent-shadow study (L2 topic: shadow).

Shared helpers for tools/analysis/l2_shadow_*.py:

* load_game(path): an arena record (arena/games/*.json) or one of our live
  ladder tapes (rl/data/our_live_tapes/ep*.json) as {seed, tapes[2], ...}.
* Replay: steps the stock engine with both tapes (at env step t the action
  stored at index t+1), exposing before every step the exact observation each
  seat is given (JSON round-tripped, the way an agent process receives it).
* fresh_program(name): a fresh, never-shared instance of a known program
  (Agent A exactly as Kaggle loads it, Agent L, or an extracted public agent),
  so a shadow never shares module state with anything else.
* norm(action): the canonical {farmer, hands, market} form for comparisons.
"""

from __future__ import annotations

import base64
import json
import sys
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TAPES = ROOT / "rl" / "data" / "our_live_tapes"
GAMES = ROOT / "arena" / "games"
OUT = ROOT / "rl" / "data" / "l2" / "shadow"
LIVE_CONFIG = {"actTimeout": 1, "boardSize": 10, "episodeSteps": 720,
               "farmHandCostMult": 1, "maxMarketOrdersPerTurn": 10,
               "runTimeout": 1200, "seed": None, "shedCapacity": 100,
               "startingMoney": 3000, "townCenterSellInterval": 24,
               "townShopSellInterval": 4, "townShopUnlockInterval": 3,
               "turnsPerDay": 24, "weedSpawnChance": 0.005}


def unpack(blob: str) -> Any:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def load_game(path) -> dict[str, Any]:
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    if "tapes" in rec:
        return {"id": rec["game_id"], "kind": "arena", "seed": rec["seed"],
                "tapes": [unpack(t) for t in rec["tapes"]],
                "agents": rec["agents"], "rewards": rec["rewards"],
                "config": dict(LIVE_CONFIG)}
    side = int(rec["our_side"])
    tapes: list[Any] = [None, None]
    tapes[side] = unpack(rec["our_actions_zlib_b64"])
    tapes[1 - side] = unpack(rec["opp_actions_zlib_b64"])
    rewards = [0.0, 0.0]
    rewards[side] = rec["rewards"]["us"]
    rewards[1 - side] = rec["rewards"]["them"]
    return {"id": rec["episode_id"], "kind": "live", "seed": rec["seed"],
            "tapes": tapes, "our_side": side, "rewards": rewards,
            "config": rec.get("configuration") or dict(LIVE_CONFIG),
            "submission": rec.get("submission"), "opponent": rec.get("opponent"),
            "opponent_rating": rec.get("opponent_rating"), "won": rec.get("won")}


def _plain(x: Any) -> Any:
    return json.loads(json.dumps(x))


class Replay:
    """Step the stock engine with two fixed tapes; the game is reproduced exactly."""

    def __init__(self, seed: int):
        from kaggle_environments import make
        self.env = make("kaggriculture",
                        configuration={"episodeSteps": 720, "seed": seed,
                                       "runTimeout": 36000, "actTimeout": 60},
                        debug=False)
        self.env.reset()

    @property
    def step_index(self) -> int:
        return int(self.env.state[0].observation.step)

    def observation(self, seat: int) -> dict[str, Any]:
        s0 = self.env.state[0].observation
        me = self.env.state[seat].observation
        return {"remainingOverageTime": 60, "step": int(s0.step), "player": seat,
                "farms": _plain(s0.farms), "private": _plain(me.private),
                "market": _plain(s0.market), "town": _plain(s0.town),
                "day": int(s0.day), "hour": int(s0.hour)}

    def private(self, seat: int) -> dict[str, Any]:
        return _plain(self.env.state[seat].observation.private)

    def public(self) -> dict[str, Any]:
        s0 = self.env.state[0].observation
        return {"farms": _plain(s0.farms), "market": _plain(s0.market),
                "town": _plain(s0.town), "step": int(s0.step)}

    def step(self, a0: Any, a1: Any) -> None:
        self.env.step([a0, a1])

    def rewards(self) -> list[float]:
        return [float(self.env.state[i].reward or 0.0) for i in (0, 1)]


def norm(action: Any) -> dict[str, Any]:
    a = action if isinstance(action, dict) else {}
    a = _plain(a)
    return {"farmer": a.get("farmer") or ["PASS"],
            "hands": a.get("hands") or [],
            "market": a.get("market") or []}


PUBLIC = sorted(p.stem for p in (ROOT / "rl" / "public").glob("nb_*.py"))


def fresh_program(name: str):
    """A fresh instance of a program; each call gets its own module state."""
    if name == "A":
        from rl.candidate_l import parent_namespace
        return parent_namespace()[1]
    if name == "L":
        from rl.candidate_l import l_stack
        return l_stack()
    if name.startswith("nb_"):
        path = ROOT / "rl" / "public" / f"{name}.py"
        env: dict = {"__name__": f"shadow_{name}", "__file__": str(path)}
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), env)
        return env["agent"]
    raise ValueError(name)


def live_paths(submission: int | None = None) -> list[Path]:
    out = []
    for p in sorted(TAPES.glob("ep*.json")):
        if submission is None:
            out.append(p)
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("submission") == submission:
            out.append(p)
    return out
