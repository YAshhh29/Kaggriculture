"""Lean exact replay of a live game: both tapes on the seed, no framework.

kaggle_environments' env.run deep-copies and schema-checks the whole state on
every step (about 26 s a game on a busy machine). The game itself is only the
interpreter, so this drives kaggriculture.interpreter directly with the same
seed handling and the same tape convention (the action stored at index k was
chosen observing step k-1, so engine step s applies tape[s + 1]). Rewards are
checked against the live record by the caller.

Hooks let an observer see the engine's own calls as they happen:
    replay(seed, tapes, observer) where observer may define
    before_step(state, step), unit(farm, private, idx, action, day, apply),
    decay(farm, step, apply), end_of_day(state, env, day, apply).
Each hook that wraps an engine call receives `apply` (the original engine
function with its arguments bound) and must call it exactly once.
"""

from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path

from kaggle_environments.envs.kaggriculture import kaggriculture as K
from kaggle_environments.utils import Struct

ROOT = Path(__file__).resolve().parents[2]
TAPES = ROOT / "rl" / "data" / "our_live_tapes"
PASS = {"farmer": ["PASS"], "hands": [], "market": []}
CONFIG = dict(episodeSteps=720, boardSize=10, startingMoney=3000,
              maxMarketOrdersPerTurn=10, turnsPerDay=24, shedCapacity=100,
              weedSpawnChance=0.005, townShopUnlockInterval=3,
              townShopSellInterval=4, townCenterSellInterval=24,
              farmHandCostMult=1, actTimeout=1, runTimeout=1200)

_ORIG = {"apply": K._apply_unit_action, "decay": K._decay_plants,
         "eod": K._end_of_day}
_OBS = {"cur": None}


def unpack(blob: str):
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def records(submission: int | None = None):
    out = []
    for p in sorted(TAPES.glob("ep*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if submission is None or r.get("submission") == submission:
            out.append((p, r))
    return out


def _apply_hook(farm, private, idx, action, board_size, day, tpd, cap=100):
    obs = _OBS["cur"]
    run = lambda: _ORIG["apply"](farm, private, idx, action, board_size, day,
                                 tpd, cap)
    if obs is None or not hasattr(obs, "unit"):
        return run()
    return obs.unit(farm, private, idx, action, day, run)


def _decay_hook(farm, step):
    obs = _OBS["cur"]
    run = lambda: _ORIG["decay"](farm, step)
    if obs is None or not hasattr(obs, "decay"):
        return run()
    return obs.decay(farm, step, run)


def _eod_hook(state, env, day):
    obs = _OBS["cur"]
    run = lambda: _ORIG["eod"](state, env, day)
    if obs is None or not hasattr(obs, "end_of_day"):
        return run()
    return obs.end_of_day(state, env, day, run)


def _install():
    K._apply_unit_action = _apply_hook
    K._decay_plants = _decay_hook
    K._end_of_day = _eod_hook


class _Env:
    def __init__(self, seed):
        self.configuration = Struct(**CONFIG, seed=seed)
        self.info = {}
        self.done = False


def replay(seed, tapes, observer=None):
    """Play tapes[0] (seat 0) and tapes[1] (seat 1) on `seed`.

    Returns (rewards, state)."""
    _install()
    _OBS["cur"] = observer
    try:
        env = _Env(seed)
        state = [Struct(observation=Struct(step=0, player=i,
                                           remainingOverageTime=60),
                        action=None, status="ACTIVE", reward=0, info={})
                 for i in range(2)]
        K.interpreter(state, env)
        for s in range(0, 720):
            state[0].observation.step = s
            for i in range(2):
                a = tapes[i][s + 1] if s + 1 < len(tapes[i]) else PASS
                state[i].action = a
            if observer is not None and hasattr(observer, "before_step"):
                observer.before_step(state, s)
            K.interpreter(state, env)
            if state[0].status == "DONE":
                break
        return [state[i].reward for i in range(2)], state
    finally:
        _OBS["cur"] = None


def replay_record(record, observer=None):
    side = int(record["our_side"])
    us = unpack(record["our_actions_zlib_b64"])
    them = unpack(record["opp_actions_zlib_b64"])
    tapes = [us, them] if side == 0 else [them, us]
    rewards, state = replay(record["seed"], tapes, observer)
    return {"us": rewards[side], "them": rewards[1 - side]}, state, tapes


if __name__ == "__main__":
    import sys
    import time
    sub = int(sys.argv[1]) if len(sys.argv) > 1 else 56582917
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    for p, r in records(sub)[:n]:
        t = time.time()
        got, _, _ = replay_record(r)
        print(p.name, got, r["rewards"], "EXACT" if got == r["rewards"] else
              "MISMATCH", f"{time.time() - t:.1f}s")
