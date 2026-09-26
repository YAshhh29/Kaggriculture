"""Exact event trace of one Kaggriculture game: every unit action with its effect.

Hooks the engine's own functions (as tools/analysis/sales_race.py does) and
records, per step and seat:

- every unit command with the unit's position and what it changed
  (PLANT / WATER / FERTILIZE / HARVEST / COLLECT_FERTILIZER / PICKUP / FEED
  / DROP / PLACE, with the plant's crop, age and yield before and after);
- every market unit the engine commits (SELL / BUY_PRODUCT / BUY_SEED /
  BUY_ANIMAL, with the price) and every HIRE (with its fee);
- a snapshot of shed, money, crew and town at the last step of every day.

Agents are callables as Kaggle calls them; a recorded side is a replay agent
(the action stored at index k was chosen observing step k-1).

    from tools.analysis.l2_wheat_trace import trace
    log = trace(seed, [agent0, agent1])
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CONFIG = {"episodeSteps": 720, "runTimeout": 36000, "actTimeout": 60}


def _tile_brief(tile):
    if tile is None:
        return None
    if tile == "LOCKED":
        return "LOCKED"
    if isinstance(tile, dict):
        if tile.get("kind") == "PLANT":
            return ("PLANT", tile["crop"], int(tile["planted_day"]),
                    int(tile.get("yield_units", 0)),
                    int(tile.get("fertilized_until_day", -1)),
                    bool(tile.get("watered_today")))
        if "animal" in tile:
            return ("ANIMAL", tile["animal"], bool(tile.get("fertilizer_available")),
                    bool(tile.get("fed_today")), int(tile.get("yield_units", 0)))
        return (tile.get("kind"),)
    return str(tile)


def trace(seed: int, agents: list, keep_units: bool = True) -> dict:
    """Play one game with both agents; return the event log and final rewards."""
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine

    env = make("kaggriculture", configuration={**CONFIG, "seed": seed}, debug=False)
    now = {"step": -1, "seat_of": {}}
    units: list = []      # (t, seat, idx, op, arg, x, y, before, after, inv_before, inv_after)
    market: list = []     # (t, seat, op, item, price)
    hires: list = []      # (t, seat, fee, n_today_after)
    daily: list = []      # (day, seat, money, shed, hands, town)

    raw_unit = engine._apply_unit_action
    raw_commit = engine._commit_unit
    raw_hire = engine._do_hire
    raw_interpreter = env.interpreter

    def unit(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
        seat = now["seat_of"].get(id(farm))
        if seat is None or not isinstance(action, list) or not action:
            return raw_unit(farm, private, idx, action, board_size, day, turns_per_day,
                            shed_capacity)
        pos = farm["farmer"] if idx == 0 else (
            farm["hands"][idx - 1] if idx - 1 < len(farm["hands"]) else None)
        if pos is None:
            return raw_unit(farm, private, idx, action, board_size, day, turns_per_day,
                            shed_capacity)
        x, y = int(pos[0]), int(pos[1])
        before = _tile_brief(farm["tiles"][y][x])
        inv = private["inventories"][idx] if idx < len(private["inventories"]) else {}
        inv_before = dict(inv)
        result = raw_unit(farm, private, idx, action, board_size, day, turns_per_day,
                          shed_capacity)
        after = _tile_brief(farm["tiles"][y][x])
        inv_after = dict(private["inventories"][idx]) if idx < len(private["inventories"]) else {}
        op = action[0]
        arg = action[1:] if len(action) > 1 else None
        if keep_units or op not in ("NORTH", "SOUTH", "EAST", "WEST", "PASS"):
            units.append((now["step"], seat, idx, op, arg, x, y, before, after,
                          inv_before, inv_after))
        return result

    def commit(op, item, price, farm, private, mkt, *rest):
        ok = raw_commit(op, item, price, farm, private, mkt, *rest)
        if ok:
            seat = now["seat_of"].get(id(farm))
            market.append((now["step"], seat, op, item, price))
        return ok

    def hire(farm, private, board_size, mult=1):
        before = len(farm["hands"])
        money = float(farm["money"])
        out = raw_hire(farm, private, board_size, mult)
        if len(farm["hands"]) > before:
            hires.append((now["step"], now["seat_of"].get(id(farm)),
                          money - float(farm["money"]), int(farm["hires_today"])))
        return out

    def interpreter(state, e):
        obs0 = state[0].observation
        farms = getattr(obs0, "farms", None)
        if farms:
            now["seat_of"] = {id(f): s for s, f in enumerate(farms)}
            now["step"] = int(obs0.get("step", 0) if hasattr(obs0, "get") else obs0.step)
            step = now["step"]
            if step % 24 == 23:
                for s, f in enumerate(farms):
                    priv = state[s].observation.private
                    daily.append((step // 24, s, float(f["money"]), dict(priv["shed"]),
                                  len(f["hands"]), list(obs0.town["unlocked_shops"]),
                                  sum(1 for row in f["tiles"] for t in row if t is None)))
        return raw_interpreter(state, e)

    engine._apply_unit_action = unit
    engine._commit_unit = commit
    engine._do_hire = hire
    env.interpreter = interpreter
    try:
        env.run(agents)
    finally:
        engine._apply_unit_action = raw_unit
        engine._commit_unit = raw_commit
        engine._do_hire = raw_hire
    final = env.steps[-1]
    actions = [[env.steps[k][i].get("action") for k in range(len(env.steps))] for i in (0, 1)]
    return {"seed": seed,
            "rewards": [float(final[i].get("reward") or 0) for i in (0, 1)],
            "statuses": [str(final[i].get("status")) for i in (0, 1)],
            "units": units, "market": market, "hires": hires, "daily": daily,
            "actions": actions}
