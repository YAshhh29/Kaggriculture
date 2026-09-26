"""Fast exact test bench for endgame market policies on our live ladder games.

The stock engine's interpreter is driven directly (no kaggle_environments
runner, whose per-step schema checks and deep copies cost ~8 s a game), with
both recorded tapes (env step t applies tape[t + 1]). With unmodified tapes
this reproduces every live game to the coin (checked by ``verify``).

A policy is an order-rewrite layer ``layer(observation, parent_action) ->
action`` on our seat. Our unit actions and the opponent's whole tape stay as
recorded; only what the layer does to our market orders changes the game.
The run is snapshotted at a start step so many policies can be replayed from
the same point in a fraction of a second.

Caveat (applies to every tape replay): the opponent cannot react, and our own
parent cannot react to the different shed/cash our layer leaves it with.
Here that means our parent's later market orders are the recorded ones; the
layer sees them and can rewrite them. The in-agent test is
tools.eval.live_replay / tools.eval.paired with rl.l2_endgame.

    python -m tools.analysis.l2_endgame_bench verify
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_endgame_log import (ITEMS, LOGS, SUBMISSIONS,  # noqa: E402
                                           records, unpack)

CFG = dict(episodeSteps=720, boardSize=10, startingMoney=3000,
           maxMarketOrdersPerTurn=10, turnsPerDay=24, shedCapacity=100,
           weedSpawnChance=0.005, townShopUnlockInterval=3,
           townShopSellInterval=4, townCenterSellInterval=24,
           farmHandCostMult=1, actTimeout=60, runTimeout=36000)


class _Env:
    def __init__(self, seed):
        from kaggle_environments.utils import Struct
        self.configuration = Struct(**dict(CFG, seed=seed))
        self.info = {}
        self.done = False


def _fresh(seed):
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine
    from kaggle_environments.utils import Struct
    env = _Env(seed)
    state = [Struct(observation=Struct(step=0, player=i, remainingOverageTime=60),
                    action=None, status="ACTIVE", reward=0, info={})
             for i in range(2)]
    engine.interpreter(state, env)
    return state, env


def observation(state, side, step):
    obs0 = state[0].observation
    return {"player": side, "step": step, "day": step // 24, "hour": step % 24,
            "farms": obs0.farms, "market": obs0.market, "town": obs0.town,
            "private": state[side].observation.private}


class Game:
    """One live game, replayable from snapshots."""

    def __init__(self, record):
        self.record = record
        self.side = int(record["our_side"])
        self.ours = unpack(record["our_actions_zlib_b64"])
        self.theirs = unpack(record["opp_actions_zlib_b64"])
        self.snapshots = {}

    def tapes(self):
        return ([self.ours, self.theirs] if self.side == 0
                else [self.theirs, self.ours])

    def run(self, layer=None, start=0, snap_at=(), sales=None, stop=719,
            hooks=None):
        """Play steps [start, stop). ``layer`` rewrites our action from
        ``start`` on. ``sales`` (a list) receives (step, who, op, item, price)
        for every committed unit when given. Returns (state, env)."""
        import kaggle_environments.envs.kaggriculture.kaggriculture as engine
        if start == 0:
            state, env = _fresh(self.record["seed"])
        else:
            state, env = copy.deepcopy(self.snapshots[start])
        tapes = self.tapes()
        side = self.side
        orig_commit = engine._commit_unit
        orig_market = engine._process_market
        now = {"step": start}
        if sales is not None:
            def process_market(st, env_):
                now["farms"] = st[0].observation.farms
                return orig_market(st, env_)

            def commit(op, item, price, farm, private, market, *rest):
                ok = orig_commit(op, item, price, farm, private, market, *rest)
                if ok:
                    player = 0 if farm is now["farms"][0] else 1
                    sales.append((now["step"], 0 if player == side else 1,
                                  op, item, price))
                return ok
            engine._commit_unit = commit
            engine._process_market = process_market
        try:
            for t in range(start, stop):
                if t in snap_at:
                    self.snapshots[t] = copy.deepcopy((state, env))
                now["step"] = t
                state[0].observation.step = t
                acts = [tapes[0][t + 1], tapes[1][t + 1]]
                if layer is not None:
                    acts[side] = layer(observation(state, side, t),
                                       copy.deepcopy(acts[side]))
                if hooks is not None:
                    hooks(t, state, acts)
                for i in (0, 1):
                    state[i].action = acts[i]
                engine.interpreter(state, env)
            if stop in snap_at:
                self.snapshots[stop] = copy.deepcopy((state, env))
        finally:
            engine._commit_unit = orig_commit
            engine._process_market = orig_market
        return state, env

    def result(self, state):
        money = [float(state[0].observation.farms[i]["money"]) for i in (0, 1)]
        return {"us": money[self.side], "them": money[1 - self.side]}


def verify(limit=0):
    rows = records()
    if limit:
        rows = rows[:limit]
    bad = 0
    t0 = time.time()
    for r in rows:
        g = Game(r)
        state, _ = g.run()
        res = g.result(state)
        ok = res == {"us": r["rewards"]["us"], "them": r["rewards"]["them"]}
        bad += not ok
        if not ok:
            print("MISMATCH", r["episode_id"], res, r["rewards"])
    print(f"{len(rows)} games, {bad} mismatches, {time.time() - t0:.1f}s")


def log_game(record, layer=None):
    """Replay a game (optionally with a layer) and return the same log as
    tools.analysis.l2_endgame_log: sales per (step, who, op, item), observed
    market inventory per step, shops / money / sheds per day, goods destroyed
    by overflow, goods left unsold at the end."""
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine
    g = Game(record)
    side = g.side
    who = lambda player: 0 if player == side else 1   # noqa: E731
    now = {"step": 0, "farm_ids": [], "farm_step": -1, "drop_calls": 0}
    discards, inv_log, shops, money, sheds, unit_sales = [], [], [], [], [], []
    orig_apply = engine._apply_unit_action
    orig_drop = engine._drop_inventories_to_shed
    orig_eod = engine._end_of_day

    def apply_unit(farm, private, idx, action, *rest, **kw):
        if now["farm_step"] != now["step"]:
            now["farm_step"] = now["step"]
            now["farm_ids"] = []
        if not any(f is farm for f in now["farm_ids"]):
            now["farm_ids"].append(farm)
        player = next(i for i, f in enumerate(now["farm_ids"]) if f is farm)
        if isinstance(action, list) and action and action[0] == "DROP":
            inv = engine._farmer_inventory(private, idx)
            before = dict(inv)
            shed_before = dict(private["shed"])
            orig_apply(farm, private, idx, action, *rest, **kw)
            for item, n in before.items():
                gained = private["shed"].get(item, 0) - shed_before.get(item, 0)
                lost = n - gained - inv.get(item, 0)
                if lost > 0:
                    discards.append([now["step"], who(player), item, lost, "drop"])
            return None
        return orig_apply(farm, private, idx, action, *rest, **kw)

    def end_of_day(state, env_, day):
        now["drop_calls"] = 0
        return orig_eod(state, env_, day)

    def drop_to_shed(private, capacity):
        player = now["drop_calls"]
        now["drop_calls"] += 1
        held = {}
        for inv in private["inventories"]:
            for item, n in inv.items():
                if n > 0:
                    held[item] = held.get(item, 0) + n
        shed_before = dict(private["shed"])
        orig_drop(private, capacity)
        for item, n in held.items():
            gained = private["shed"].get(item, 0) - shed_before.get(item, 0)
            if n - gained > 0:
                discards.append([now["step"], who(player), item, n - gained, "night"])

    def hooks(t, state, acts):
        now["step"] = t
        obs0 = state[0].observation
        inv_log.append([int(obs0.market["inventory"][i]) for i in ITEMS])
        if t % 24 == 0:
            shops.append(list(obs0.town["unlocked_shops"]))
            money.append([float(obs0.farms[side]["money"]),
                          float(obs0.farms[1 - side]["money"])])
            sheds.append([dict(state[side].observation.private["shed"]),
                          dict(state[1 - side].observation.private["shed"])])

    engine._apply_unit_action = apply_unit
    engine._drop_inventories_to_shed = drop_to_shed
    engine._end_of_day = end_of_day
    try:
        state, _ = g.run(layer=layer, sales=unit_sales, hooks=hooks)
    finally:
        engine._apply_unit_action = orig_apply
        engine._drop_inventories_to_shed = orig_drop
        engine._end_of_day = orig_eod
    agg = {}
    for step, w, op, item, price in unit_sales:
        cell = agg.get((step, w, op, item))
        if cell is None:
            agg[(step, w, op, item)] = [1, price, price, price]
        else:
            cell[0] += 1
            cell[1] += price
            cell[3] = price
    leftover = []
    for player in (side, 1 - side):
        private = state[player].observation.private
        shed = {k: int(v) for k, v in dict(private["shed"]).items() if v}
        hands = {}
        for inv in private["inventories"]:
            for k, v in dict(inv).items():
                if v:
                    hands[k] = hands.get(k, 0) + int(v)
        leftover.append({"shed": shed, "hands": hands})
    final = g.result(state)
    return {"episode_id": record["episode_id"],
            "submission": record.get("submission"),
            "agent": SUBMISSIONS.get(record.get("submission"), "?"),
            "side": side, "opponent": record.get("opponent"),
            "opponent_rating": record.get("opponent_rating"),
            "live": record["rewards"], "replay": final,
            "exact": final == {"us": record["rewards"]["us"],
                               "them": record["rewards"]["them"]},
            "items": ITEMS, "inv": inv_log, "shops": shops, "money": money,
            "sheds": sheds, "leftover": leftover, "discards": discards,
            "sales": [[k[0], k[1], k[2], k[3], v[0], v[1], v[2], v[3]]
                      for k, v in sorted(agg.items())]}


def _log_job(record):
    out = log_game(record)
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / f"ep{record['episode_id']}.json").write_text(
        json.dumps(out, separators=(",", ":")), encoding="utf-8")
    return out["episode_id"], out["exact"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--limit", type=int, default=0)
    p = sub.add_parser("log")
    p.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    if args.command == "verify":
        verify(args.limit)
    elif args.command == "log":
        rows = records()
        with Pool(args.workers) as pool:
            done = pool.map(_log_job, rows)
        print(f"logged {len(done)} games, {sum(not ok for _, ok in done)} not exact")


if __name__ == "__main__":
    main()
