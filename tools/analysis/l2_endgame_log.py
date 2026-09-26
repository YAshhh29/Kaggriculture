"""Exact market log of our live ladder games, for the endgame study.

Each record in rl/data/our_live_tapes holds a live episode's seed, our seat
and both action tapes. Replaying both tapes on the seed with the stock engine
reproduces the live game exactly (tape convention: the action stored at index
k was chosen observing step k-1, so env step t applies tape[t + 1]).

This replays every game of the chosen submissions and logs, by wrapping the
engine's own functions:
  * every committed market unit (step, who, op, item, price), aggregated per
    (step, who, op, item) as units / revenue / first price / last price;
  * the market inventory every agent observed at the start of each step;
  * the town's shops at the start of every day;
  * goods the engine destroys: night-drop overflow and DROP overflow;
  * both sheds and money at every day start and at the end, and the goods
    still in shed / hand inventories when the game ends (never sold).

The same runner replays a game with an order-rewrite layer on our seat
(``replay(record, layer=...)``): our unit actions and the opponent's tape are
fixed, our market orders go through ``layer(observation, parent_action)``.
That is the offline test bench for endgame policies.

    python -m tools.analysis.l2_endgame_log log --submissions 56571049 56582917
"""

from __future__ import annotations

import argparse
import base64
import copy
import json
import sys
import time
import zlib
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TAPES = ROOT / "rl" / "data" / "our_live_tapes"
OUT = ROOT / "rl" / "data" / "l2" / "endgame"
LOGS = OUT / "logs"
ITEMS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
         "WOOL", "FERTILIZER"]
SUBMISSIONS = {56571049: "A", 56582917: "L"}


def unpack(blob: str):
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def records(submissions=(56571049, 56582917)):
    out = []
    for p in sorted(TAPES.glob("ep*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("submission") in submissions:
            out.append(r)
    return out


def plain(x):
    """Kaggle Struct -> plain python (dict/list/number)."""
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    return x


def replay(record, layer=None, log=True, our_tape=None, opp_tape=None):
    """Replay a live game; optionally rewrite our seat's action with
    ``layer(observation_dict, parent_action) -> action`` (called at every
    step with the observation our agent saw and the action it played)."""
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine

    side = int(record["our_side"])
    ours = our_tape if our_tape is not None else unpack(record["our_actions_zlib_b64"])
    theirs = opp_tape if opp_tape is not None else unpack(record["opp_actions_zlib_b64"])
    tapes = [ours, theirs] if side == 0 else [theirs, ours]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.reset()
    who = lambda player: 0 if player == side else 1   # 0 = us, 1 = them

    now = {"step": 0, "farm_ids": [], "farm_step": -1, "drop_calls": 0}
    sales = {}          # (step, who, op, item) -> [units, revenue, first, last]
    discards = []       # [step, who, item, n, kind]
    orig_commit = engine._commit_unit
    orig_market = engine._process_market
    orig_apply = engine._apply_unit_action
    orig_drop = engine._drop_inventories_to_shed
    orig_eod = engine._end_of_day

    def process_market(state, env_):
        now["farms"] = state[0].observation.farms
        return orig_market(state, env_)

    def commit(op, item, price, farm, private, market, *rest):
        ok = orig_commit(op, item, price, farm, private, market, *rest)
        if ok:
            player = next(i for i, f in enumerate(now["farms"]) if f is farm)
            key = (now["step"], who(player), op, item)
            cell = sales.get(key)
            if cell is None:
                sales[key] = [1, price, price, price]
            else:
                cell[0] += 1
                cell[1] += price
                cell[3] = price
        return ok

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
                left = inv.get(item, 0)
                lost = n - gained - left
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

    engine._commit_unit = commit
    engine._process_market = process_market
    engine._apply_unit_action = apply_unit
    engine._drop_inventories_to_shed = drop_to_shed
    engine._end_of_day = end_of_day
    inv_log, shops, money, sheds = [], [], [], []
    layer_actions = 0
    try:
        for t in range(719):
            now["step"] = t
            obs_us = env.state[side].observation
            if log:
                market = obs_us["market"]["inventory"]
                inv_log.append([int(market[i]) for i in ITEMS])
                if t % 24 == 0:
                    shops.append(list(obs_us["town"]["unlocked_shops"]))
                    farms = obs_us["farms"]
                    money.append([float(farms[side]["money"]),
                                  float(farms[1 - side]["money"])])
                    sheds.append([dict(env.state[side].observation["private"]["shed"]),
                                  dict(env.state[1 - side].observation["private"]["shed"])])
            acts = [tapes[0][t + 1], tapes[1][t + 1]]
            if layer is not None:
                obs = plain(obs_us)
                new = layer(obs, copy.deepcopy(acts[side]))
                if new != acts[side]:
                    layer_actions += 1
                acts[side] = new
            env.step(acts)
    finally:
        engine._commit_unit = orig_commit
        engine._process_market = orig_market
        engine._apply_unit_action = orig_apply
        engine._drop_inventories_to_shed = orig_drop
        engine._end_of_day = orig_eod

    rewards = [float(env.state[i].reward or 0) for i in (0, 1)]
    final = {"us": rewards[side], "them": rewards[1 - side]}
    out = {"episode_id": record["episode_id"],
           "submission": record.get("submission"),
           "agent": SUBMISSIONS.get(record.get("submission"), "?"),
           "side": side, "opponent": record.get("opponent"),
           "opponent_rating": record.get("opponent_rating"),
           "live": record["rewards"], "replay": final,
           "exact": final == {"us": record["rewards"]["us"],
                              "them": record["rewards"]["them"]},
           "layer_actions": layer_actions}
    if log:
        last = env.state
        leftover = []
        for player in (side, 1 - side):
            private = last[player].observation["private"]
            shed = {k: int(v) for k, v in dict(private["shed"]).items() if v}
            hands = {}
            for inv in private["inventories"]:
                for k, v in dict(inv).items():
                    if v:
                        hands[k] = hands.get(k, 0) + int(v)
            leftover.append({"shed": shed, "hands": hands})
        out.update({
            "items": ITEMS, "inv": inv_log, "shops": shops, "money": money,
            "sheds": sheds, "leftover": leftover, "discards": discards,
            "sales": [[k[0], k[1], k[2], k[3], v[0], v[1], v[2], v[3]]
                      for k, v in sorted(sales.items())],
        })
    return out


def _job(path):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    started = time.time()
    try:
        out = replay(record)
    except Exception as error:   # one broken game must not sink the run
        return {"episode_id": record["episode_id"], "error": repr(error)}
    out["seconds"] = round(time.time() - started, 1)
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / f"ep{record['episode_id']}.json").write_text(
        json.dumps(out, separators=(",", ":")), encoding="utf-8")
    return {k: out[k] for k in ("episode_id", "agent", "exact", "live", "replay",
                                "seconds")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("log")
    p.add_argument("--submissions", type=int, nargs="+", default=[56571049, 56582917])
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--redo", action="store_true")
    args = ap.parse_args()
    paths = []
    for path in sorted(TAPES.glob("ep*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if r.get("submission") not in args.submissions:
            continue
        if not args.redo and (LOGS / path.name).exists():
            continue
        paths.append(str(path))
    print(f"{len(paths)} games to log", flush=True)
    with Pool(args.workers, maxtasksperchild=8) as pool:
        for row in pool.imap_unordered(_job, paths):
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
