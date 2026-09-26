"""Out-farm autopsy, part 1: replay a live game exactly and keep both farms' books.

Every record in rl/data/our_live_tapes holds a live episode's seed and both
sides' action tapes. Stepping the stock engine with tape[t+1] at step t
reproduces the live game to the coin. This replays a game that way (or with a
live agent in one seat, or with a shadow agent watching one seat) and logs, at
the engine, for BOTH seats:

  * every effective unit action: PLANT, HARVEST (units, fertilized or not),
    FERTILIZE, WATER (yield gain 0/1/2), FEED, COLLECT_FERTILIZER, CARE, BUILD,
    PLACE, DIG, PICKUP;
  * every committed market unit (sell / buy, item, price), every hire (cost)
    and every land purchase;
  * rot (units lost to decay), overflow binned at night, animals that escape;
  * a census at the end of each day (plants per crop and quadrant, animals,
    weeds, bare tiles, empty pens, quadrants, money, shed, seeds, peak hands).

    python -m tools.analysis.l2_outfarm_replay --episodes 113751067 113773538
    python -m tools.analysis.l2_outfarm_replay --losses        # all A/L losses < -1000

Outputs go to rl/data/l2/outfarm/books/ep<id>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TAPES = ROOT / "rl" / "data" / "our_live_tapes"
OUT = ROOT / "rl" / "data" / "l2" / "outfarm"
SUBMISSIONS = {56571049: "A", 56582917: "L"}
CONFIG = {"episodeSteps": 720, "runTimeout": 36000, "actTimeout": 60}


def load_record(episode: int) -> dict:
    return json.loads((TAPES / f"ep{episode}.json").read_text(encoding="utf-8"))


def select_losses(max_margin: float = -1000.0, subs=tuple(SUBMISSIONS)) -> list[dict]:
    rows = []
    for path in sorted(TAPES.glob("ep*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if r.get("submission") not in subs or r.get("won"):
            continue
        margin = float(r["rewards"]["us"]) - float(r["rewards"]["them"])
        if margin < max_margin:
            rows.append({"episode_id": r["episode_id"], "submission": r["submission"],
                         "opponent": r.get("opponent"), "rating": r.get("opponent_rating"),
                         "margin": margin, "our_side": r["our_side"]})
    return sorted(rows, key=lambda x: x["margin"])


def _quadrant(x: int, y: int, board: int = 10) -> str:
    half = board // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


class Book:
    """One seat's whole game, counted at the engine."""

    def __init__(self) -> None:
        self.plant: list = []        # [step, crop, x, y]
        self.harvest: list = []      # [step, crop/product, units, fertilized, planted_day, x, y]
        self.fertilize: list = []    # [step, crop, age, x, y]
        self.water = defaultdict(lambda: [0, 0, 0])   # day -> [no gain, +1, +2]
        self.feed = Counter()        # day -> n
        self.collect = Counter()     # day -> n
        self.care = Counter()        # day -> n
        self.build: list = []        # [step, kind, x, y]
        self.place: list = []        # [step, animal, x, y]
        self.dig: list = []          # [step, what, x, y]
        self.pickup = Counter()      # item -> n
        self.sales: list = []        # [step, item, price]
        self.buys: list = []         # [step, op, item, price]
        self.hires: list = []        # [step, cost]
        self.land: list = []         # [step, cost, quadrant]
        self.rot: list = []          # [step, crop, units]
        self.binned = Counter()      # item -> n
        self.escaped: list = []      # [day, animal]
        self.hands_peak = Counter()  # day -> max hands
        self.census: dict = {}       # day -> {...}

    def to_json(self) -> dict:
        return {
            "plant": self.plant, "harvest": self.harvest, "fertilize": self.fertilize,
            "water": {int(k): v for k, v in self.water.items()},
            "feed": dict(self.feed), "collect": dict(self.collect), "care": dict(self.care),
            "build": self.build, "place": self.place, "dig": self.dig,
            "pickup": dict(self.pickup), "sales": self.sales, "buys": self.buys,
            "hires": self.hires, "land": self.land, "rot": self.rot,
            "binned": dict(self.binned), "escaped": self.escaped,
            "hands_peak": dict(self.hands_peak), "census": self.census,
        }


def _census(farm, private) -> dict:
    plants: Counter = Counter()
    by_quad: dict = defaultdict(Counter)
    animals: Counter = Counter()
    weeds = bare = pens = owned = 0
    tiles = farm["tiles"]
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile == "LOCKED":
                continue
            owned += 1
            q = _quadrant(x, y, len(tiles))
            if tile is None:
                bare += 1
            elif isinstance(tile, dict):
                if "animal" in tile:
                    animals[tile["animal"]] += 1
                    by_quad[q][tile["animal"]] += 1
                elif tile.get("kind") == "PLANT":
                    plants[tile["crop"]] += 1
                    by_quad[q][tile["crop"]] += 1
                elif tile.get("kind") == "WEED":
                    weeds += 1
                    by_quad[q]["WEED"] += 1
                elif tile.get("kind") in ("COOP", "PASTURE"):
                    pens += 1
                    by_quad[q]["PEN"] += 1
    return {"money": float(farm["money"]), "plants": dict(plants), "animals": dict(animals),
            "by_quad": {q: dict(c) for q, c in by_quad.items()},
            "weeds": weeds, "bare": bare, "pens": pens, "owned": owned,
            "quadrants": list(farm["unlocked_quadrants"]),
            "shed": {k: int(v) for k, v in private["shed"].items() if int(v)},
            "seeds": {k: int(v) for k, v in private["seeds"].items() if int(v)}}


def replay(record: dict, agents: dict | None = None, shadows: dict | None = None,
           books: bool = True) -> dict:
    """Play one live game with the stock engine.

    agents:  {seat: callable} replaces that seat's recorded tape with a live agent.
    shadows: {seat: callable} is called on every observation of that seat (a deep
             copy, exactly what Kaggle passes); its answers are recorded, not played.
    """
    from copy import deepcopy

    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as K

    from rl.replay_agent import build_replay_agent
    from tools.data.extract_live_tapes import unpack

    side = int(record["our_side"])
    tapes = {side: unpack(record["our_actions_zlib_b64"]),
             1 - side: unpack(record["opp_actions_zlib_b64"])}
    agents = dict(agents or {})
    shadows = dict(shadows or {})
    shadow_log: dict = {s: [] for s in shadows}
    played: dict = {0: [], 1: []}

    def seat_agent(seat):
        tape_agent = build_replay_agent(tuple(tapes[seat]))
        live = agents.get(seat)
        shadow = shadows.get(seat)

        def act(obs, cfg=None):
            if shadow is not None:
                try:
                    answer = shadow(deepcopy(obs), cfg)
                except Exception as error:  # a crash is data, not a stop
                    answer = {"error": f"{type(error).__name__}: {error}"}
                shadow_log[seat].append(deepcopy(answer))
            action = live(obs, cfg) if live is not None else tape_agent(obs)
            played[seat].append(deepcopy(action))
            return action
        return act

    book = [Book(), Book()]
    ctx = {"step": 0, "farms": {}, "privates": {}}
    raw = {name: getattr(K, name) for name in (
        "_commit_unit", "_apply_unit_action", "_decay_plants", "_drop_inventories_to_shed",
        "_daily_refresh_animals", "_do_hire", "_do_buy_land", "_end_of_day")}

    def seat_of_farm(farm):
        return ctx["farms"].get(id(farm))

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        ok = raw["_commit_unit"](op, item, price, farm, private, market, shed_capacity)
        s = seat_of_farm(farm)
        if ok and s is not None:
            if op == "SELL":
                book[s].sales.append([ctx["step"], item, int(price)])
            else:
                book[s].buys.append([ctx["step"], op, item, float(price)])
        return ok

    def unit(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
        s = seat_of_farm(farm)
        if s is None or not isinstance(action, list) or not action:
            return raw["_apply_unit_action"](farm, private, idx, action, board_size, day,
                                             turns_per_day, shed_capacity)
        op = action[0]
        pos = farm["farmer"] if idx == 0 else (
            farm["hands"][idx - 1] if idx - 1 < len(farm["hands"]) else None)
        if pos is None:
            return raw["_apply_unit_action"](farm, private, idx, action, board_size, day,
                                             turns_per_day, shed_capacity)
        x, y = int(pos[0]), int(pos[1])
        before = farm["tiles"][y][x]
        before = dict(before) if isinstance(before, dict) else before
        inv = private["inventories"][idx] if idx < len(private["inventories"]) else {}
        inv_before = dict(inv)
        result = raw["_apply_unit_action"](farm, private, idx, action, board_size, day,
                                           turns_per_day, shed_capacity)
        after = farm["tiles"][y][x]
        inv_after = private["inventories"][idx] if idx < len(private["inventories"]) else {}
        step = ctx["step"]
        b = book[s]
        if op == "PLANT":
            if before is None and isinstance(after, dict) and after.get("kind") == "PLANT":
                b.plant.append([step, after["crop"], x, y])
        elif op == "HARVEST" and isinstance(before, dict):
            units = int(before.get("yield_units", 0) or 0)
            got = sum(inv_after.values()) - sum(inv_before.values())
            if got > 0:
                if before.get("kind") == "PLANT":
                    fert = int(before.get("fertilized_until_day", -1)) >= int(before["planted_day"])
                    b.harvest.append([step, before["crop"], got, fert, int(before["planted_day"]), x, y])
                elif "animal" in before:
                    product = K.ANIMALS[before["animal"]]["product"]
                    b.harvest.append([step, product, got, False, int(before.get("placed_day", 0)), x, y])
        elif op == "FERTILIZE" and isinstance(before, dict) and isinstance(after, dict):
            if after.get("fertilized_until_day", -1) != before.get("fertilized_until_day", -1) \
                    or inv_before.get("FERTILIZER", 0) != inv_after.get("FERTILIZER", 0):
                b.fertilize.append([step, before.get("crop"), day - int(before.get("planted_day", day)), x, y])
        elif op == "WATER" and isinstance(before, dict) and before.get("kind") == "PLANT" \
                and not before.get("watered_today"):
            gain = int(after.get("yield_units", 0)) - int(before.get("yield_units", 0)) \
                if isinstance(after, dict) else 0
            b.water[day][max(0, min(2, gain))] += 1
        elif op == "FEED" and isinstance(after, dict) and after.get("fed_today") \
                and isinstance(before, dict) and not before.get("fed_today"):
            b.feed[day] += 1
        elif op == "COLLECT_FERTILIZER" and isinstance(before, dict) \
                and before.get("fertilizer_available") and isinstance(after, dict) \
                and not after.get("fertilizer_available"):
            b.collect[day] += 1
        elif op == "CARE" and isinstance(before, dict) and not before.get("cared_today") \
                and isinstance(after, dict) and after.get("cared_today"):
            b.care[day] += 1
        elif op in ("BUILD_COOP", "BUILD_PASTURE") and before is None and isinstance(after, dict):
            b.build.append([step, after.get("kind"), x, y])
        elif op == "PLACE" and isinstance(after, dict) and "animal" in after \
                and not (isinstance(before, dict) and "animal" in before):
            b.place.append([step, after["animal"], x, y])
        elif op == "DIG" and before is not None and after is None:
            what = before.get("kind") if isinstance(before, dict) else str(before)
            if what == "PLANT":
                what = "PLANT:" + str(before.get("crop"))
            b.dig.append([step, what, x, y])
        elif op == "PICKUP":
            for item, n in inv_after.items():
                if n > inv_before.get(item, 0):
                    b.pickup[item] += n - inv_before.get(item, 0)
        return result

    def decay(farm, step):
        s = seat_of_farm(farm)
        if s is None:
            return raw["_decay_plants"](farm, step)
        before = {}
        for y, row in enumerate(farm["tiles"]):
            for x, tile in enumerate(row):
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    before[(x, y)] = (tile["crop"], int(tile.get("yield_units", 0) or 0))
        result = raw["_decay_plants"](farm, step)
        lost: Counter = Counter()
        for (x, y), (crop, was) in before.items():
            tile = farm["tiles"][y][x]
            now = int(tile.get("yield_units", 0) or 0) if isinstance(tile, dict) \
                and tile.get("kind") == "PLANT" else 0
            if was > now:
                lost[crop] += was - now
        for crop, n in lost.items():
            book[s].rot.append([step, crop, n])
        return result

    def drop(private, capacity):
        s = ctx["privates"].get(id(private))
        if s is None:
            return raw["_drop_inventories_to_shed"](private, capacity)
        carried: Counter = Counter()
        for bag in private["inventories"]:
            carried.update({k: int(v) for k, v in bag.items() if int(v) > 0})
        before = Counter({k: int(v) for k, v in private["shed"].items()})
        result = raw["_drop_inventories_to_shed"](private, capacity)
        after = Counter({k: int(v) for k, v in private["shed"].items()})
        for item, n in carried.items():
            kept = after.get(item, 0) - before.get(item, 0)
            if n > kept:
                book[s].binned[item] += n - kept
        return result

    def refresh_animals(farm, day):
        s = seat_of_farm(farm)
        if s is None:
            return raw["_daily_refresh_animals"](farm, day)
        before = {(x, y): tile["animal"] for y, row in enumerate(farm["tiles"])
                  for x, tile in enumerate(row) if isinstance(tile, dict) and "animal" in tile}
        result = raw["_daily_refresh_animals"](farm, day)
        for (x, y), animal in before.items():
            tile = farm["tiles"][y][x]
            if not (isinstance(tile, dict) and "animal" in tile):
                book[s].escaped.append([day, animal])
        return result

    def hire(farm, private, board_size, mult=1):
        money = float(farm["money"])
        result = raw["_do_hire"](farm, private, board_size, mult)
        s = seat_of_farm(farm)
        if s is not None and float(farm["money"]) < money:
            book[s].hires.append([ctx["step"], money - float(farm["money"])])
        return result

    def buy_land(farm, board_size):
        money = float(farm["money"])
        n = len(farm["unlocked_quadrants"])
        result = raw["_do_buy_land"](farm, board_size)
        s = seat_of_farm(farm)
        if s is not None and len(farm["unlocked_quadrants"]) > n:
            book[s].land.append([ctx["step"], money - float(farm["money"]),
                                 farm["unlocked_quadrants"][-1]])
        return result

    def end_of_day(state, env_, day):
        farms = state[0].observation.farms
        for s, farm in enumerate(farms):
            book[s].hands_peak[day] = max(book[s].hands_peak[day], len(farm["hands"]))
        result = raw["_end_of_day"](state, env_, day)
        for s, farm in enumerate(farms):
            book[s].census[day] = _census(farm, state[s].observation.private)
        return result

    env = make("kaggriculture", configuration={**CONFIG, "seed": record["seed"]}, debug=False)
    raw_interpreter = env.interpreter

    market_inv: list = []

    def interpreter(state, e):
        obs0 = state[0].observation
        if hasattr(obs0, "farms") and obs0.farms:
            ctx["step"] = int(obs0.get("step", 0) or 0)
            market_inv.append({k: int(v) - 10000 for k, v in obs0.market.inventory.items()})
            ctx["farms"] = {id(f): s for s, f in enumerate(obs0.farms)}
            ctx["privates"] = {id(st.observation.private): s for s, st in enumerate(state)}
            for s, f in enumerate(obs0.farms):
                d = ctx["step"] // 24
                book[s].hands_peak[d] = max(book[s].hands_peak[d], len(f["hands"]))
        return raw_interpreter(state, e)

    if books:
        env.interpreter = interpreter
        K._commit_unit = commit
        K._apply_unit_action = unit
        K._decay_plants = decay
        K._drop_inventories_to_shed = drop
        K._daily_refresh_animals = refresh_animals
        K._do_hire = hire
        K._do_buy_land = buy_land
        K._end_of_day = end_of_day
    try:
        env.run([seat_agent(0), seat_agent(1)])
    finally:
        for name, fn in raw.items():
            setattr(K, name, fn)
    final = env.steps[-1]
    rewards = [float(final[i].get("reward") or 0.0) for i in (0, 1)]
    town = list(env.steps[-1][0]["observation"]["town"]["unlocked_shops"])
    shops_by_day = {}
    for t in range(0, len(env.steps), 24):
        shops_by_day[t // 24] = list(env.steps[t][0]["observation"]["town"]["unlocked_shops"])
    return {"episode_id": record["episode_id"], "seed": record["seed"], "our_side": side,
            "opponent": record.get("opponent"), "submission": record.get("submission"),
            "live": record["rewards"], "rewards": rewards,
            "exact": (round(rewards[side]) == round(record["rewards"]["us"])
                      and round(rewards[1 - side]) == round(record["rewards"]["them"])),
            "statuses": [str(final[i].get("status")) for i in (0, 1)],
            "town": town, "shops_by_day": shops_by_day,
            "books": [b.to_json() for b in book] if books else None,
            "market_inv": market_inv if books else None,
            "shadow": shadow_log, "played": played}


def _job(episode: int) -> dict:
    record = load_record(episode)
    out = replay(record)
    out.pop("played", None)
    out.pop("shadow", None)
    path = OUT / "books" / f"ep{episode}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out), encoding="utf-8")
    return {"episode_id": episode, "exact": out["exact"], "rewards": out["rewards"],
            "live": out["live"], "our_side": out["our_side"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--episodes", type=int, nargs="*", default=[])
    ap.add_argument("--losses", action="store_true")
    ap.add_argument("--max-margin", type=float, default=-1000.0)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    episodes = list(args.episodes)
    if args.losses:
        episodes += [r["episode_id"] for r in select_losses(args.max_margin)]
    episodes = sorted(set(episodes))
    print(f"{len(episodes)} games", flush=True)
    with Pool(min(2, args.workers), maxtasksperchild=1) as pool:
        for row in pool.imap_unordered(_job, episodes):
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
