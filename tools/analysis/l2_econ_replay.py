"""Replay our real ladder games from both tapes and log the whole economy.

Each record in rl/data/our_live_tapes holds a live episode's seed and both
players' action tapes. Replaying both tapes on the stock engine reproduces the
live game exactly (the final money of both players is checked against the
record). While it replays, the engine's own functions are wrapped so every
economic event is logged exactly as the engine commits it:

  * every market unit committed (player, step, op, item, price)
  * every hire (cost) and land purchase
  * every unit action, and whether the engine applied it or silently ignored it
  * per plant: waterings (and whether they added yield), fertilizer, harvests
  * per animal: feeds, cares, collections, production credited vs capped
  * shed overflow (DROP and end-of-day), decay and weed losses, escapes,
    fertilizer left uncollected (it does not accumulate)
  * market inventory at every step, and the town's shop unlocks

One JSON per game goes to rl/data/l2/econ/games/. Aggregate with
tools/analysis/l2_econ_report.py.

    python -m tools.analysis.l2_econ_replay --submission 56582917 56571049 --workers 1
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import zlib
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TAPES = ROOT / "rl" / "data" / "our_live_tapes"
OUT = ROOT / "rl" / "data" / "l2" / "econ" / "games"

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
            "WOOL", "FERTILIZER"]


def _unpack(blob: str):
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def _tile_key(tile):
    if tile is None or not isinstance(tile, dict):
        return tile
    return tuple(sorted(tile.items()))


def replay(path: str) -> dict:
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as E

    record = json.loads(Path(path).read_text(encoding="utf-8"))
    side = int(record["our_side"])
    ours = _unpack(record["our_actions_zlib_b64"])
    theirs = _unpack(record["opp_actions_zlib_b64"])
    tapes = [ours, theirs] if side == 0 else [theirs, ours]

    now = {"step": 0, "unit_player": -1, "eod_player": -1, "animal_player": -1,
           "plant_player": -1}
    market_log = []                      # (player, step, op, item, price)
    hires = []                           # (player, step, cost, ok)
    land = []                            # (player, step, cost, ok)
    verbs = [Counter(), Counter()]       # verb -> count
    noops = [Counter(), Counter()]       # verb -> ignored count
    moves_by_day = [Counter(), Counter()]
    plants = [dict(), dict()]            # (x,y,planted_day) -> ledger
    animals = [dict(), dict()]           # (x,y,placed_day) -> ledger
    overflow = [Counter(), Counter()]    # item -> units discarded
    decay_loss = [Counter(), Counter()]  # crop -> units lost to decay
    weed_loss = [Counter(), Counter()]   # crop -> units on plants that died unwatered
    weed_deaths = [Counter(), Counter()] # crop -> plants lost unwatered
    decay_deaths = [Counter(), Counter()]
    escapes = [Counter(), Counter()]
    manure_wasted = [0, 0]               # fertilizer left uncollected at refresh
    manure_made = [0, 0]
    care_capped = [0, 0]                 # production units lost to max_held
    prod_credited = [Counter(), Counter()]
    care_paid = [0, 0]
    ongoing_prod = [Counter(), Counter()]      # crop -> units credited
    ongoing_capped = [0, 0]
    fert_doubled = [Counter(), Counter()]
    plant_blocked = [0, 0]
    hands_by_day = [[0] * 30, [0] * 30]

    orig = {name: getattr(E, name) for name in (
        "_commit_unit", "_process_market", "_do_hire", "_do_buy_land",
        "_apply_unit_action", "_daily_refresh_plants", "_daily_refresh_animals",
        "_decay_plants", "_drop_inventories_to_shed")}

    def player_of(farm):
        for i, f in enumerate(now.get("farms") or []):
            if f is farm:
                return i
        return -1

    def process_market(state, env_):
        now["farms"] = state[0].observation.farms
        return orig["_process_market"](state, env_)

    def commit(op, item, price, farm, private, market, *rest):
        ok = orig["_commit_unit"](op, item, price, farm, private, market, *rest)
        if ok:
            market_log.append((player_of(farm), now["step"], op, item, price))
        return ok

    def do_hire(farm, private, board_size, mult=1):
        before = farm["hires_today"]
        cost = E._hire_cost(before, mult)
        orig["_do_hire"](farm, private, board_size, mult)
        hires.append((player_of(farm), now["step"], cost, farm["hires_today"] > before))

    def do_land(farm, board_size):
        n = len(farm["unlocked_quadrants"])
        cost = E.LAND_PRICES[n - 1] if n - 1 < len(E.LAND_PRICES) else 0
        orig["_do_buy_land"](farm, board_size)
        land.append((player_of(farm), now["step"], cost, len(farm["unlocked_quadrants"]) > n))

    def unit_action(farm, private, idx, action, board_size, day, tpd, cap=100):
        if idx == 0:
            now["unit_player"] += 1
        p = now["unit_player"]
        if p not in (0, 1):
            return orig["_apply_unit_action"](farm, private, idx, action, board_size, day, tpd, cap)
        if not isinstance(action, list) or not action:
            return orig["_apply_unit_action"](farm, private, idx, action, board_size, day, tpd, cap)
        op = action[0]
        pos = E._farmer_position(farm, idx)
        if pos is None:
            verbs[p][op] += 1
            noops[p][op] += 1
            return
        x, y = pos
        tile = farm["tiles"][y][x]
        tk = _tile_key(tile)
        inv = dict(E._farmer_inventory(private, idx))
        shed = dict(private["shed"])
        seeds = dict(private["seeds"])
        yu = tile.get("yield_units", 0) if isinstance(tile, dict) else 0
        orig["_apply_unit_action"](farm, private, idx, action, board_size, day, tpd, cap)
        pos2 = E._farmer_position(farm, idx)
        tile2 = farm["tiles"][y][x]
        inv2 = E._farmer_inventory(private, idx)
        changed = (tuple(pos2) != (x, y) or _tile_key(tile2) != tk or inv2 != inv
                   or private["shed"] != shed or private["seeds"] != seeds)
        verbs[p][op] += 1
        if op in E.FARMER_MOVES:
            moves_by_day[p][day] += 1
        if not changed and op != "PASS":
            noops[p][op] += 1
            return
        if op == "PASS":
            return
        if op == "PLANT":
            plants[p][(x, y, day)] = {"crop": action[1], "day": day, "water": [],
                                      "water_gain": 0, "fert": [], "harvest": []}
        elif op in ("WATER", "FERTILIZE", "HARVEST") and isinstance(tile, dict) \
                and tile.get("kind") == "PLANT":
            key = (x, y, tile["planted_day"])
            led = plants[p].setdefault(key, {"crop": tile["crop"], "day": tile["planted_day"],
                                             "water": [], "water_gain": 0, "fert": [],
                                             "harvest": []})
            age = day - tile["planted_day"]
            if op == "WATER":
                led["water"].append(age)
                gain = (tile2.get("yield_units", 0) if isinstance(tile2, dict) else 0) - yu
                led["water_gain"] += max(0, gain)
            elif op == "FERTILIZE":
                led["fert"].append(age)
            else:
                got = sum(inv2.values()) - sum(inv.values())
                led["harvest"].append((age, got, now["step"] % 24))
        elif isinstance(tile, dict) and "animal" in tile and op in (
                "FEED", "CARE", "COLLECT_FERTILIZER", "HARVEST"):
            key = (x, y, tile["placed_day"])
            led = animals[p].setdefault(key, {"animal": tile["animal"], "day": tile["placed_day"],
                                              "feed": 0, "care": 0, "collect": 0,
                                              "harvest": 0, "units": 0})
            if op == "FEED":
                led["feed"] += 1
            elif op == "CARE":
                led["care"] += 1
            elif op == "COLLECT_FERTILIZER":
                led["collect"] += 1
            else:
                led["harvest"] += 1
                led["units"] += sum(inv2.values()) - sum(inv.values())
        elif op == "PLACE" and action[1:2] and action[1] in E.ANIMALS and isinstance(tile2, dict) \
                and "animal" in tile2:
            animals[p][(x, y, day)] = {"animal": action[1], "day": day, "feed": 0, "care": 0,
                                       "collect": 0, "harvest": 0, "units": 0}
        elif op == "DROP":
            carried = sum(inv.values())
            stored = sum(private["shed"].values()) - sum(shed.values())
            if carried > stored:
                # DROP walks the inventory in insertion order; attribute the
                # discarded units by replaying that order.
                room = max(0, cap - sum(shed.values()))
                for item, n in inv.items():
                    take = min(n, room)
                    room -= take
                    if n > take:
                        overflow[p][item] += n - take

    def refresh_plants(farm, current_day, tpd):
        now["plant_player"] += 1
        p = now["plant_player"] % 2
        before = {}
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    before[(x, y)] = (t["crop"], t["yield_units"], t["watered_today"],
                                      t.get("fertilized_until_day", -1), t["planted_day"])
        orig["_daily_refresh_plants"](farm, current_day, tpd)
        for (x, y), (crop, yu, watered, fud, pday) in before.items():
            t = farm["tiles"][y][x]
            if isinstance(t, dict) and t.get("kind") == "WEED":
                weed_deaths[p][crop] += 1
                weed_loss[p][crop] += yu
            elif isinstance(t, dict) and t.get("kind") == "PLANT" and E.CROPS[crop]["ongoing"]:
                gain = t["yield_units"] - yu
                if gain > 0:
                    ongoing_prod[p][crop] += gain
                    if watered and fud >= current_day:
                        fert_doubled[p][crop] += 1
                cd = E.CROPS[crop]
                dsf = current_day + 1 - pday - cd["first_yield_day"]
                if dsf >= 0 and dsf % cd["interval"] == 0 and dsf // cd["interval"] + 1 <= cd["max_yield"]:
                    want = 2 if (watered and fud >= current_day) else 1
                    if gain < want:
                        ongoing_capped[p] += want - gain

    def refresh_animals(farm, day):
        now["animal_player"] += 1
        p = now["animal_player"] % 2
        before = {}
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict) and "animal" in t:
                    before[(x, y)] = dict(t)
                    if t.get("fertilizer_available"):
                        manure_wasted[p] += 1
        orig["_daily_refresh_animals"](farm, day)
        for (x, y), b in before.items():
            t = farm["tiles"][y][x]
            if not (isinstance(t, dict) and "animal" in t):
                escapes[p][b["animal"]] += 1
                continue
            manure_made[p] += 1
            a = E.ANIMALS[b["animal"]]
            dsf = day + 1 - b["placed_day"] - a["first_yield_day"]
            if dsf >= 0 and dsf % a["interval"] == 0:
                bonus = b.get("pending_care_bonus", 0) if b["fed_today"] else 0
                want = 1 + bonus
                got = t["yield_units"] - b["yield_units"]
                prod_credited[p][a["product"]] += got
                care_paid[p] += min(bonus, max(0, got - 1))
                if got < want:
                    care_capped[p] += want - got

    def decay(farm, step):
        # Called once per farm per step, player order.
        p = player_of(farm)
        before = {}
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get("kind") == "PLANT" and 0 <= t["max_lifespan_step"] <= step:
                    before[(x, y)] = (t["crop"], t["yield_units"])
        orig["_decay_plants"](farm, step)
        for (x, y), (crop, yu) in before.items():
            t = farm["tiles"][y][x]
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                decay_loss[p][crop] += max(0, yu - t["yield_units"])
            else:
                decay_loss[p][crop] += yu
                decay_deaths[p][crop] += 1

    def drop_eod(private, capacity):
        now["eod_player"] += 1
        p = now["eod_player"] % 2
        shed_before = sum(private["shed"].values())
        room = max(0, capacity - shed_before)
        for inv in private["inventories"]:
            for item, n in inv.items():
                if n <= 0:
                    continue
                take = min(n, room)
                room -= take
                if n > take:
                    overflow[p][item] += n - take
        return orig["_drop_inventories_to_shed"](private, capacity)

    E._commit_unit = commit
    E._process_market = process_market
    E._do_hire = do_hire
    E._do_buy_land = do_land
    E._apply_unit_action = unit_action
    E._daily_refresh_plants = refresh_plants
    E._daily_refresh_animals = refresh_animals
    E._decay_plants = decay
    E._drop_inventories_to_shed = drop_eod
    inv_path = {item: [] for item in PRODUCTS}
    money = [[], []]
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": record["seed"],
                                                   "runTimeout": 36000, "actTimeout": 60},
                   debug=False)
        env.reset()
        for t in range(719):
            now["step"] = t
            now["unit_player"] = -1
            obs = env.state[0].observation
            now["farms"] = obs.farms
            env.step([tapes[0][t + 1], tapes[1][t + 1]])
            obs = env.state[0].observation
            for item in PRODUCTS:
                inv_path[item].append(int(obs.market["inventory"][item]))
            if t % 24 == 0:
                for i in (0, 1):
                    money[i].append(float(obs.farms[i]["money"]))
            if t % 24 == 12:
                for i in (0, 1):
                    hands_by_day[i][t // 24] = len(obs.farms[i]["hands"])
        final_obs = [env.state[i].observation for i in (0, 1)]
        final = [float(env.state[i].reward or 0) for i in (0, 1)]
        shops = list(final_obs[0].town["unlocked_shops"])
        residue = []
        for i in (0, 1):
            priv = final_obs[i].private
            shed = {k: v for k, v in dict(priv["shed"]).items() if v}
            carried = Counter()
            for inv in priv["inventories"]:
                for k, v in inv.items():
                    carried[k] += v
            on_tiles = Counter()
            for row in final_obs[0].farms[i]["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("yield_units", 0) > 0:
                        on_tiles[t.get("crop") or E.ANIMALS[t["animal"]]["product"]] += t["yield_units"]
            residue.append({"shed": shed, "carried": dict(carried), "tiles": dict(on_tiles),
                            "seeds": {k: v for k, v in dict(priv["seeds"]).items() if v},
                            "quadrants": list(final_obs[0].farms[i]["unlocked_quadrants"])})
    finally:
        for name, fn in orig.items():
            setattr(E, name, fn)

    live = record.get("rewards") or {}
    us_live, them_live = live.get("us"), live.get("them")
    exact = (us_live is not None and abs(final[side] - float(us_live)) < 0.5
             and abs(final[1 - side] - float(them_live)) < 0.5)

    def plant_rows(p):
        return [{"x": k[0], "y": k[1], **v} for k, v in plants[p].items()]

    def animal_rows(p):
        return [{"x": k[0], "y": k[1], **v} for k, v in animals[p].items()]

    sides = []
    for p in (0, 1):
        sides.append({
            "verbs": dict(verbs[p]), "noops": dict(noops[p]),
            "moves_by_day": [moves_by_day[p][d] for d in range(30)],
            "plants": plant_rows(p), "animals": animal_rows(p),
            "overflow": dict(overflow[p]), "decay_loss": dict(decay_loss[p]),
            "decay_deaths": dict(decay_deaths[p]), "weed_loss": dict(weed_loss[p]),
            "weed_deaths": dict(weed_deaths[p]), "escapes": dict(escapes[p]),
            "manure_made": manure_made[p], "manure_wasted": manure_wasted[p],
            "care_capped": care_capped[p], "care_paid": care_paid[p],
            "animal_prod": dict(prod_credited[p]), "ongoing_prod": dict(ongoing_prod[p]),
            "ongoing_capped": ongoing_capped[p], "fert_doubled": dict(fert_doubled[p]),
            "money_by_day": money[p], "hands_by_day": hands_by_day[p],
            "residue": residue[p], "final": final[p],
        })
    return {
        "episode_id": record["episode_id"], "seed": record["seed"], "our_side": side,
        "submission": record.get("submission"), "opponent": record.get("opponent"),
        "opponent_rating": record.get("opponent_rating"), "won": record.get("won"),
        "exact": exact, "live": [us_live, them_live], "shops": shops,
        "market_log": market_log, "hires": hires, "land": land,
        "inv_path": inv_path, "sides": sides,
    }


def job(path: str) -> str:
    out = OUT / (Path(path).stem + ".json")
    if out.exists():
        return f"skip {out.name}"
    t0 = time.time()
    try:
        res = replay(path)
    except Exception as error:  # one broken game must not sink the run
        return f"ERROR {Path(path).name}: {type(error).__name__}: {error}"
    out.write_text(json.dumps(res, separators=(",", ":")), encoding="utf-8")
    return f"{out.name} exact={res['exact']} {time.time() - t0:.1f}s"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--submission", type=int, nargs="*", default=[56582917, 56571049])
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for f in sorted(TAPES.glob("ep*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        if not args.submission or rec.get("submission") in args.submission:
            paths.append(str(f))
    if args.limit:
        paths = paths[:args.limit]
    print(f"{len(paths)} games", flush=True)
    if args.workers <= 1:
        for p in paths:
            print(job(p), flush=True)
    else:
        with Pool(args.workers, maxtasksperchild=4) as pool:
            for line in pool.imap_unordered(job, paths):
                print(line, flush=True)


if __name__ == "__main__":
    main()
