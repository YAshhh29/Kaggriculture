"""Fast exact replay of a Kaggriculture game from two recorded tapes.

`kaggle_environments.make(...).step` spends ~18 s a game on copies and schema
checks. This drives the stock engine's own `interpreter` directly on a
minimal state (the same Struct objects the framework builds), so the game
logic is byte-for-byte the engine's; only the framework bookkeeping is gone.
`verify()` checks it against the live rewards.

Tape convention: the action stored at index k was chosen observing step k-1,
so at step t both tapes contribute index t+1.

    python -m tools.analysis.l2_land_fast --verify 5
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import zlib
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TAPES = ROOT / "rl" / "data" / "our_live_tapes"
CORPUS = ROOT / "kaggle_cache" / "corpus_v2"

CONFIG = {"episodeSteps": 720, "boardSize": 10, "startingMoney": 3000,
          "maxMarketOrdersPerTurn": 10, "turnsPerDay": 24, "shedCapacity": 100,
          "weedSpawnChance": 0.005, "townShopUnlockInterval": 3,
          "townShopSellInterval": 4, "townCenterSellInterval": 24,
          "farmHandCostMult": 1, "actTimeout": 1, "runTimeout": 1200}


def unpack(blob: str) -> list:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


class FastGame:
    """The stock interpreter on a bare two-player state."""

    def __init__(self, seed: int):
        from kaggle_environments.envs.kaggriculture import kaggriculture as E
        from kaggle_environments.utils import Struct
        self.E = E
        self.configuration = Struct(**{**CONFIG, "seed": seed})
        self.info: dict = {}
        self.done = False
        self.state = [Struct(observation=Struct(step=0, player=i), action=None,
                             status="ACTIVE", reward=0) for i in (0, 1)]
        E.interpreter(self.state, self)
        self.t = 0

    @property
    def obs(self):
        return self.state[0].observation

    def private(self, i: int) -> dict:
        return self.state[i].observation.private

    def step(self, actions: list) -> None:
        for i in (0, 1):
            self.state[i].action = actions[i]
        self.state[0].observation.step = self.t
        for i in (0, 1):
            self.state[i].observation.step = self.t
        self.E.interpreter(self.state, self)
        self.t += 1

    def money(self) -> list[float]:
        return [float(f["money"]) for f in self.obs.farms]


def replay(seed: int, tapes: list) -> Iterator[tuple[int, FastGame, list]]:
    """Yield (t, game, actions) before step t is applied, then apply it."""
    g = FastGame(seed)
    for t in range(719):
        acts = [tapes[i][t + 1] if t + 1 < len(tapes[i]) else
                {"farmer": ["PASS"], "hands": [], "market": []} for i in (0, 1)]
        yield t, g, acts
        g.step(acts)
    yield 719, g, None


def live_record(path) -> tuple[int, int, list, dict]:
    r = json.loads(Path(path).read_text(encoding="utf-8"))
    side = int(r["our_side"])
    tp = [None, None]
    tp[side] = unpack(r["our_actions_zlib_b64"])
    tp[1 - side] = unpack(r["opp_actions_zlib_b64"])
    return int(r["seed"]), side, tp, r


def corpus_record(path) -> tuple[int, int, list, dict]:
    r = json.loads(Path(path).read_text(encoding="utf-8"))
    seat = int(r["seat"])
    tp = [None, None]
    tp[seat] = unpack(r["actions_zlib_b64"])
    tp[1 - seat] = unpack(r["opponent_actions_zlib_b64"])
    return int(r["seed"]), seat, tp, r


def live_paths(submission: int) -> list[Path]:
    out = []
    for p in sorted(TAPES.glob("ep*.json")):
        try:
            if json.loads(p.read_text(encoding="utf-8")).get("submission") == submission:
                out.append(p)
        except (OSError, ValueError):
            continue
    return out


def verify(n: int) -> None:
    for p in live_paths(56582917)[:n]:
        seed, side, tp, r = live_record(p)
        t0 = time.time()
        g = None
        for _, g, _ in replay(seed, tp):
            pass
        m = g.money()
        ok = m[side] == r["rewards"]["us"] and m[1 - side] == r["rewards"]["them"]
        print(f"{p.name}: us {m[side]:,.0f} (live {r['rewards']['us']:,.0f}) them "
              f"{m[1 - side]:,.0f} (live {r['rewards']['them']:,.0f}) "
              f"{'EXACT' if ok else 'MISMATCH'} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", type=int, default=3)
    verify(ap.parse_args().verify)
