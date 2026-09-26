"""A bare harness around the stock Kaggriculture interpreter, for experiments.

It drives kaggriculture.interpreter directly (no agents, no framework copies),
so a test can put the game in any state, submit exact actions for both
players, and read back exactly what the engine did. Used by the l2_econ_*
scripts to verify rules and compute economics with the engine's own code.

    from tools.analysis.l2_econ_sim import Sim
    sim = Sim(seed=7)
    sim.step(p0={"farmer": ["PLANT", "WHEAT"], "market": [["BUY_SEED", "WHEAT", 1]]})
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import kaggle_environments.envs.kaggriculture.kaggriculture as E  # noqa: E402
from kaggle_environments.utils import Struct  # noqa: E402

PASS = {"farmer": ["PASS"], "hands": [], "market": []}


class _Env:
    def __init__(self, seed: int, **config):
        cfg = {"episodeSteps": 720, "boardSize": 10, "startingMoney": 3000,
               "maxMarketOrdersPerTurn": 10, "turnsPerDay": 24, "shedCapacity": 100,
               "weedSpawnChance": 0.005, "townShopUnlockInterval": 3,
               "townShopSellInterval": 4, "townCenterSellInterval": 24, "seed": seed}
        cfg.update(config)
        self.configuration = Struct(**cfg)
        self.info = {}
        self.done = False


class Sim:
    """Two players, stock rules. self.step_no is the step about to be played."""

    def __init__(self, seed: int = 1, **config):
        self.env = _Env(seed, **config)
        self.state = [Struct(observation=Struct(step=0), action=None, reward=0, status="ACTIVE")
                      for _ in range(2)]
        E.interpreter(self.state, self.env)
        self.step_no = 0

    # --- views -----------------------------------------------------------
    @property
    def obs(self):
        return self.state[0].observation

    @property
    def market(self):
        return self.obs.market

    def farm(self, p: int):
        return self.obs.farms[p]

    def private(self, p: int):
        return self.state[p].observation.private

    def tile(self, p: int, x: int, y: int):
        return self.farm(p)["tiles"][y][x]

    @property
    def day(self) -> int:
        return self.step_no // 24

    @property
    def hour(self) -> int:
        return self.step_no % 24

    # --- driving ---------------------------------------------------------
    def step(self, p0: dict | None = None, p1: dict | None = None) -> None:
        for i, a in enumerate((p0, p1)):
            a = a or PASS
            self.state[i].action = {"farmer": a.get("farmer", ["PASS"]),
                                    "hands": a.get("hands", []),
                                    "market": a.get("market", [])}
            self.state[i].observation.step = self.step_no
        E.interpreter(self.state, self.env)
        self.step_no += 1

    def run_to(self, step: int, p0=None, p1=None) -> None:
        """PASS (or repeat the given actions) until step_no == step."""
        while self.step_no < step:
            self.step(p0, p1)

    def to_day(self, day: int, hour: int = 0) -> None:
        self.run_to(day * 24 + hour)

    # --- state surgery ---------------------------------------------------
    def put_plant(self, p: int, x: int, y: int, crop: str, planted_day: int) -> dict:
        tile = E._new_plant(crop, planted_day, 24)
        self.farm(p)["tiles"][y][x] = tile
        return tile

    def put_animal(self, p: int, x: int, y: int, animal: str, placed_day: int) -> dict:
        tile = E._new_animal(animal, placed_day)
        self.farm(p)["tiles"][y][x] = tile
        return tile

    def move_farmer(self, p: int, x: int, y: int) -> None:
        self.farm(p)["farmer"] = [x, y]

    def carry(self, p: int, item: str, n: int, idx: int = 0) -> None:
        inv = E._farmer_inventory(self.private(p), idx)
        inv[item] = inv.get(item, 0) + n
