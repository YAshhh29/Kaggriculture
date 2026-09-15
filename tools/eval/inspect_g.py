"""Inspect Candidate G against the top of the ladder, one move at a time.

A panel says whether G wins. It cannot say why it loses. This plays G
against many replays of each strong opponent and judges every move both
farms make, by running the engine's own action code on a copy of the
state each worker actually stood in -- so "that move did nothing" is the
engine's verdict, not a guess.

What it judges, for G and for the opponent alike:

* labour -- each worker-turn is work, movement, a deliberate pass, or a
  no-op the engine silently ignored, and why it ignored it;
* losses -- crops that went to weed unwatered or rotted on the vine,
  animals that escaped, fertilizer never collected, care skipped, output
  wasted at an animal's holding cap, early harvests, shed overflow, and
  goods still unsold when the season ended;
* the market and the town's demand -- what each farm sold into each book,
  at what price against base, how much went at the floor, how much of the
  town's actual consumption each farm captured, and which books were
  paying well on days G had nothing to sell.

Losses are priced in coins at the price quoted that turn, so the findings
rank themselves. Every run is kept under rl/data/inspections and compared
with the one before, which is what turns it into a review rather than a
snapshot.

    python -m tools.eval.inspect_g --opponents 12 --tapes 6
    python -m tools.eval.inspect_g --set COUNT_CARRIED=true --label carried
    python -m tools.eval.inspect_g --drill 108716055 --seat 0 --from 250 --to 275

Two caveats it reports rather than hides. The opponent is a replayed tape,
so it cannot react to G. And a tape replayed on another seed drifts out of
step with its own farm -- the opponent's no-op rate is printed as a measure
of how faithful the replay still is.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "rl" / "data" / "inspections"
TURNS = 24
SHED_CAP = 100
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}

# Where in G each kind of defect is decided. A pointer for whoever reads
# the report, not a diagnosis: the drill view is how a cause is confirmed.
WHERE = {
    "noop": "claim() / still_possible(): a job was handed out that the "
            "engine then refused",
    "idle": "job_value(): nothing worth doing was offered to that worker",
    "died_unwatered": "WATER jobs in job_value (BAND_WATER) and crew size "
                      "(hands_target)",
    "rotted": "harvest timing: HARVEST_HOLD and BAND_HARVEST",
    "early_harvest": "harvest gate in job_value and HARVEST_HOLD",
    "escaped": "FEED jobs (BAND_FEED), wheat PICKUP, the emergency ration",
    "care_missed": "CARE jobs (BAND_SERVICE)",
    "fertilizer_uncollected": "COLLECT_FERTILIZER jobs (BAND_SERVICE)",
    "capped_yield": "animal HARVEST jobs (HARVEST_AT, BAND_HARVEST)",
    "overflow": "DROP timing and shed selling in market_orders()",
    "stranded": "closing sell and DROP_FROM_STEP",
    "sell_regret": "SELL timing and quantities in market_orders()",
    "open_books": "crop and herd choice: CROP_TILES, herd_plan()",
}


# Losses priced from what was *available*, not from what a different move
# would certainly have banked. Early harvest is the proof: a fix that cut
# it from 17,236 to 6,890 coins a game lost 1,643 a game of margin across
# 96 paired games, because the grain it saved was not grain G could sell
# or needed. These are ranked, but labelled, and never read as coins in
# the bank.
ESTIMATED = {"early_harvest", "care_missed"}

LOSSES = ("died_unwatered", "rotted", "early_harvest", "escaped",
          "care_missed", "fertilizer_uncollected", "capped_yield",
          "overflow", "stranded")


# --------------------------------------------------------------------------
# The engine's ledger: every coin, with the step it moved on.

LEDGER: list[tuple[int, int, str, str, float]] = []


def install_ledger() -> None:
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    if getattr(engine, "_inspect_ledger", False):
        return
    now: dict[str, Any] = {"farms": [], "step": 0}
    process, commit = engine._process_market, engine._commit_unit
    hire, land = engine._do_hire, engine._do_buy_land

    def seat(farm) -> int:
        for index, candidate in enumerate(now["farms"]):
            if candidate is farm:
                return index
        return -1

    def process_market(state, env):
        now["farms"] = state[0].observation.farms
        now["step"] = int(state[0].observation.step or 0)
        return process(state, env)

    def commit_unit(op, item, price, farm, *rest):
        ok = commit(op, item, price, farm, *rest)
        if ok:
            LEDGER.append((seat(farm), now["step"], op, str(item),
                           float(price)))
        return ok

    def do_hire(farm, *rest):
        before = farm["money"]
        hire(farm, *rest)
        if farm["money"] != before:
            LEDGER.append((seat(farm), now["step"], "HIRE", "HAND",
                           float(before - farm["money"])))

    def do_buy_land(farm, *rest):
        before = farm["money"]
        land(farm, *rest)
        if farm["money"] != before:
            LEDGER.append((seat(farm), now["step"], "BUY_LAND", "LAND",
                           float(before - farm["money"])))

    engine._process_market = process_market
    engine._commit_unit = commit_unit
    engine._do_hire = do_hire
    engine._do_buy_land = do_buy_land
    engine._inspect_ledger = True


def play(spec: str, overrides: dict, tape: str, seed: int, seat: int):
    import importlib

    from kaggle_environments import make

    from tools.eval.fair_town import install as fair_town
    from tools.eval.measure_panel import resolve

    install_ledger()
    # Same seed, same town, whatever G does -- see tools/eval/fair_town.py.
    fair_town()
    module_name, attr = spec.split(":")
    module = importlib.import_module(module_name)
    # Overrides are put back after the game. They used to stay set on the
    # imported module, so in any process that played more than one config
    # the "baseline" games after the first override were not baselines.
    saved = {key: getattr(module, key) for key in (overrides or {})}
    try:
        for key, value in (overrides or {}).items():
            setattr(module, key, value)
        mine = getattr(module, attr)
        opponent = resolve("clone:" + tape)
        agents = [mine, opponent] if seat == 0 else [opponent, mine]
        # runTimeout: the framework's 1,200-second episode limit is wall
        # clock, and with a dozen games sharing the cores it killed five
        # games of one inspection and the whole baseline of a panel.
        # actTimeout: the per-turn limit is wall clock too. Once a loaded
        # machine pushes one agent past a second a turn and through its spare
        # time, the framework marks it TIMEOUT, never asks it for a move
        # again, and still pays out the money it holds -- so the game looks
        # finished. Five v11 baseline games froze G this way from day 16 to
        # 24 while the same games in v10 played out normally.
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": seed,
                                  "runTimeout": 36000, "actTimeout": 60},
                   debug=False)
        LEDGER.clear()
        env.run(agents)
    finally:
        for key, value in saved.items():
            setattr(module, key, value)
    return env, list(LEDGER)


# --------------------------------------------------------------------------
# Judging one worker's move.

def _copy_state(farm: dict, private: dict) -> tuple[dict, dict]:
    tiles = [[dict(t) if isinstance(t, dict) else t for t in row]
             for row in farm["tiles"]]
    return (
        {"tiles": tiles, "farmer": list(farm["farmer"]),
         "hands": [list(h) for h in farm.get("hands") or []]},
        {"shed": dict(private.get("shed") or {}),
         "seeds": dict(private.get("seeds") or {}),
         "inventories": [dict(i) for i in
                         (private.get("inventories") or [{}])]},
    )


def _signature(farm: dict, private: dict, idx: int, x: int, y: int) -> str:
    position = farm["farmer"] if idx == 0 else farm["hands"][idx - 1]
    inventory = (private["inventories"][idx]
                 if idx < len(private["inventories"]) else {})
    return json.dumps([position, farm["tiles"][y][x], inventory,
                       private["shed"], private["seeds"]], sort_keys=True,
                      default=str)


def _beside_shed(x: int, y: int, board: int) -> bool:
    half = board // 2
    return x in (half - 1, half) and y in (half - 1, half)


def why_refused(verb: str, unit: list, tile: Any, inventory: dict,
                private: dict, x: int, y: int, board: int,
                blocked: set) -> str:
    """The engine's reason for ignoring a move, in words."""
    from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS

    item = unit[1] if len(unit) > 1 else None
    beside = _beside_shed(x, y, board)
    animal_here = isinstance(tile, dict) and "animal" in tile
    if verb in MOVES:
        return "walked off the board"
    if verb == "DROP":
        return "not beside the shed" if not beside else "carrying nothing"
    if verb == "PICKUP":
        if not beside:
            return "not beside the shed"
        return f"shed holds no {item}"
    if verb == "PLACE":
        if item in ANIMALS:
            if int(inventory.get(item, 0)) <= 0:
                return f"no {item} in hand"
            return f"not on an empty {ANIMALS[item]['structure']}"
        if not beside:
            return "not beside the shed"
        return f"no {item} in hand or shed full"
    if tile == "LOCKED":
        return "tile is locked"
    if verb == "PLANT":
        if item in blocked:
            return f"more PLANT {item} this turn than seeds, all cancelled"
        if tile is not None:
            kind = tile.get("kind") if isinstance(tile, dict) else tile
            return f"tile not empty ({kind})"
        return f"no {item} seed"
    if verb == "WATER":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return "nothing to water"
        return "already watered today"
    if verb == "HARVEST":
        if not isinstance(tile, dict):
            return "nothing here"
        if int(tile.get("yield_units", 0) or 0) <= 0:
            return "nothing ready"
        return "not yet harvestable"
    if verb == "FERTILIZE":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return "no plant here"
        return "no fertilizer in hand"
    if verb == "DIG":
        return "tile already empty" if tile is None else "animal on tile"
    if verb in ("BUILD_COOP", "BUILD_PASTURE"):
        return "tile not empty"
    if verb == "FEED":
        if not animal_here:
            return "no animal here"
        if tile.get("fed_today"):
            return "already fed today"
        return "no wheat in hand"
    if verb == "COLLECT_FERTILIZER":
        return "no animal here" if not animal_here else "none ready"
    if verb == "CARE":
        return "no animal here" if not animal_here else "already cared for"
    return "not an action the engine knows"


def _tile_brief(tile: Any, day: int) -> str:
    if tile is None:
        return "empty"
    if not isinstance(tile, dict):
        return str(tile)
    if "animal" in tile:
        return (f"{tile['animal']} y{tile.get('yield_units', 0)}"
                f"{' fed' if tile.get('fed_today') else ''}"
                f"{' cared' if tile.get('cared_today') else ''}"
                f"{' manure' if tile.get('fertilizer_available') else ''}")
    if tile.get("kind") == "PLANT":
        return (f"{tile['crop']} age{day - tile['planted_day']} "
                f"y{tile.get('yield_units', 0)}"
                f"{' W' if tile.get('watered_today') else ''}")
    return str(tile.get("kind"))


def _new_side() -> dict[str, Any]:
    return {
        "turns": Counter(), "verbs": Counter(), "noop": Counter(),
        "idle_by_day": Counter(),
        "loss_units": Counter(), "loss_coins": Counter(),
        "tile_days": Counter(), "sold": Counter(), "revenue": Counter(),
        "floor_units": Counter(), "low_units": Counter(),
        "regret": Counter(), "spend": Counter(), "open_book_coins": Counter(),
        "open_book_days": Counter(), "crowded_units": 0,
    }


def analyse(steps, ledger, me: int, drill: tuple[int, int] | None = None):
    """Judge one finished game. Returns plain data, plus drill lines."""
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    first = next(i for i, s in enumerate(steps)
                 if s[0]["observation"].get("farms"))
    board = len(steps[first][0]["observation"]["farms"][0]["tiles"])
    sides = (me, 1 - me)
    label = {me: "G", 1 - me: "OPP"}
    stats = {s: _new_side() for s in sides}
    evidence: dict[str, list] = defaultdict(list)
    lines: list[str] = []
    prices_at: dict[int, dict] = {}
    demand: dict[str, Counter] = defaultdict(Counter)
    timeline: dict[int, dict] = {}
    agree = checked = 0

    # Sales by (seat, step), so shed overflow can be reckoned after the
    # market has run.
    shed_delta: dict[tuple[int, int], int] = Counter()
    for seat, step, op, item, price in ledger:
        if op == "SELL":
            shed_delta[(seat, step)] -= 1
        elif op in ("BUY_PRODUCT", "BUY_ANIMAL"):
            shed_delta[(seat, step)] += 1

    for k in range(first + 1, len(steps)):
        before, after = steps[k - 1], steps[k]
        o0 = before[0]["observation"]
        farms = o0.get("farms")
        if not farms:
            continue
        step = int(o0.get("step", k - 1) or 0)
        day, hour = divmod(step, TURNS)
        prices = dict((o0.get("market") or {}).get("prices") or {})
        prices_at[step] = prices
        end_of_day = hour == TURNS - 1

        # The town's appetite this turn, exactly as _town_consume takes it.
        shops = list((o0.get("town") or {}).get("unlocked_shops") or [])
        if step % 4 == 0:
            for shop in shops:
                goods = engine.SHOPS[shop]
                for good in goods:
                    demand[good][day] += 2 if len(goods) == 1 else 1
        if step % TURNS == 0:
            for good in engine.TOWN_CENTER_PRODUCTS:
                demand[good][day] += 1

        for side in sides:
            st = stats[side]
            private = before[side]["observation"].get("private") or {}
            action = after[side].get("action")
            action = action if isinstance(action, dict) else {}
            farm, priv = _copy_state(farms[side], private)
            hands = action.get("hands") or []
            units = [action.get("farmer", ["PASS"]),
                     *(hands if isinstance(hands, list) else [])]
            planting = Counter(u[1] for u in units
                               if isinstance(u, list) and len(u) >= 2
                               and u[0] == "PLANT")
            blocked = {c for c, n in planting.items()
                       if n > int(priv["seeds"].get(c, 0))}
            workers = 1 + len(farm["hands"])
            drilling = (drill is not None and drill[0] <= step <= drill[1])

            def mark(kind, _side=side, _step=step, **info):
                # A few concrete cases of each loss, so it can be drilled.
                bucket = evidence["loss: " + kind]
                if _side == me and len(bucket) < 3:
                    bucket.append({"step": _step, **info})

            for idx, unit in enumerate(units):
                if idx >= workers:
                    st["turns"]["phantom"] += 1
                    continue
                verb = (str(unit[0]) if isinstance(unit, list) and unit
                        else "PASS")
                x, y = engine._farmer_position(farm, idx)
                tile = farm["tiles"][y][x]
                # What the worker saw, frozen before the engine mutates it.
                seen = _tile_brief(tile, day)
                st["verbs"][verb] += 1
                reason = ""
                if verb == "PASS" or not isinstance(unit, list):
                    cls = "idle"
                    st["idle_by_day"][day] += side == me
                else:
                    inventory = engine._farmer_inventory(priv, idx)
                    pre_tile = dict(tile) if isinstance(tile, dict) else tile
                    if verb not in MOVES:
                        reason = why_refused(verb, unit, tile, inventory,
                                             priv, x, y, board, blocked)
                    signature = _signature(farm, priv, idx, x, y)
                    allowed = (["PASS"] if verb == "PLANT" and len(unit) > 1
                               and unit[1] in blocked else unit)
                    engine._apply_unit_action(farm, priv, idx, allowed, board,
                                              day, TURNS, SHED_CAP)
                    if _signature(farm, priv, idx, x, y) != signature:
                        cls = "move" if verb in MOVES else "work"
                        reason = ""
                        if (verb == "HARVEST" and isinstance(pre_tile, dict)
                                and pre_tile.get("kind") == "PLANT"):
                            _judge_harvest(st, pre_tile, day, prices, engine,
                                           mark, idx, [x, y])
                    else:
                        cls = "noop"
                        st["noop"][f"{verb}: {reason}"] += 1
                        key = f"{verb}: {reason}"
                        if side == me and len(evidence[key]) < 3:
                            evidence[key].append(
                                {"step": step, "worker": idx, "at": [x, y],
                                 "tile": _tile_brief(pre_tile, day)})
                st["turns"][cls] += 1
                if drilling:
                    lines.append(
                        f"{step:4d} d{day:02d}h{hour:02d} {label[side]:3s} "
                        f"w{idx:<2d} {json.dumps(unit):34s} {cls:5s} "
                        f"({x},{y}) {seen}"
                        + (f"  <- {reason}" if cls == "noop" else ""))

            # Does applying the moves reproduce where the engine put
            # everyone? If not, every verdict above is suspect.
            if not end_of_day:
                real = after[0]["observation"]["farms"][side]
                checked += 1
                agree += (real["farmer"] == farm["farmer"]
                          and [list(h) for h in real["hands"][:len(farm["hands"])]]
                          == farm["hands"])

            _judge_ground(st, farm, step, day, end_of_day, prices, engine,
                          mark)
            if end_of_day:
                _judge_overflow(st, priv, after[side]["observation"],
                                shed_delta.get((side, step), 0), prices,
                                mark)
                timeline.setdefault(day, {})[label[side]] = {
                    "money": float(farms[side].get("money", 0) or 0),
                    "hands": len(farms[side].get("hands") or []),
                }
        if drilling:
            lines.append(
                f"     money G {farms[me]['money']:,.0f}  OPP "
                f"{farms[1 - me]['money']:,.0f}   prices "
                + " ".join(f"{g[:4]}={p}" for g, p in prices.items()))

    last = steps[-1]
    for side in sides:
        private = last[side]["observation"].get("private") or {}
        final_prices = (last[0]["observation"].get("market") or {}).get(
            "prices") or {}
        held: Counter[str] = Counter(private.get("shed") or {})
        for inventory in private.get("inventories") or []:
            held.update(inventory)
        unsold = {good: units for good, units in held.items()
                  if good in final_prices and units > 0}
        for good, units in unsold.items():
            stats[side]["loss_units"]["stranded"] += units
            stats[side]["loss_coins"]["stranded"] += (
                units * float(final_prices[good]))
        if side == me and unsold:
            evidence["loss: stranded"].append(
                {"step": int(last[0]["observation"].get("step", 0) or 0),
                 "held": unsold})

    _judge_market(stats, ledger, sides, prices_at, demand, engine)

    return {
        "stats": {label[s]: _plain(stats[s]) for s in sides},
        "demand": {g: sum(c.values()) for g, c in demand.items()},
        "evidence": dict(evidence),
        "timeline": timeline,
        "agreement": agree / checked if checked else 0.0,
        "reward": {label[s]: float(last[s].get("reward") or 0)
                   for s in sides},
    }, lines


def _judge_harvest(st, tile, day, prices, engine, mark, worker, at) -> None:
    """A one-time crop cut before watering had finished adding to it."""
    spec = engine.CROPS[tile["crop"]]
    if spec["ongoing"]:
        return
    age = day - tile["planted_day"]
    window = (spec["max_yield_day"] + 1) // 2
    still = sum(1 for d in range(age, spec["max_yield_day"] + 1)
                if d >= window and (d > age or not tile["watered_today"]))
    held = int(tile.get("yield_units", 0) or 0)
    lost = min(spec["max_yield"], held + still) - held
    if lost > 0:
        st["loss_units"]["early_harvest"] += lost
        st["loss_coins"]["early_harvest"] += lost * float(
            prices.get(tile["crop"], 0) or 0)
        mark("early_harvest", worker=worker, at=at,
             tile=_tile_brief(tile, day), units_forgone=lost)


def _judge_ground(st, farm, step, day, end_of_day, prices, engine,
                  mark) -> None:
    """Rot every turn; neglect, escapes and idle ground at nightfall."""
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                mls = int(tile.get("max_lifespan_step", -1))
                if (mls >= 0 and step >= mls and (step - mls) % 2 == 0
                        and int(tile.get("yield_units", 0) or 0) > 0):
                    st["loss_units"]["rotted"] += 1
                    st["loss_coins"]["rotted"] += float(
                        prices.get(tile["crop"], 0) or 0)
                    mark("rotted", at=[x, y], tile=_tile_brief(tile, day))
    if not end_of_day:
        return
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if isinstance(tile, dict) and tile.get("kind") != "WEED":
                brief = {"at": [x, y], "tile": _tile_brief(tile, day)}
            if tile is None:
                st["tile_days"]["empty"] += 1
                continue
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "WEED":
                st["tile_days"]["weed"] += 1
            elif kind == "PLANT":
                st["tile_days"]["crop"] += 1
                if not tile["watered_today"]:
                    st["tile_days"]["unwatered"] += 1
                    if int(tile.get("consecutive_unwatered", 0)) >= 1:
                        crop = tile["crop"]
                        st["loss_units"]["died_unwatered"] += 1
                        st["loss_coins"]["died_unwatered"] += (
                            engine.CROPS[crop]["seed"]
                            + int(tile.get("yield_units", 0) or 0)
                            * float(prices.get(crop, 0) or 0))
                        mark("died_unwatered", **brief)
            elif "animal" in tile:
                animal = tile["animal"]
                spec = engine.ANIMALS[animal]
                product = spec["product"]
                price = float(prices.get(product, 0) or 0)
                st["tile_days"]["animal"] += 1
                if not tile.get("fed_today"):
                    st["tile_days"]["unfed"] += 1
                    if int(tile.get("consecutive_unfed", 0)) >= 1:
                        st["loss_units"]["escaped"] += 1
                        st["loss_coins"]["escaped"] += (
                            spec["cost"]
                            + int(tile.get("yield_units", 0) or 0) * price)
                        mark("escaped", **brief)
                elif not tile.get("cared_today"):
                    st["loss_units"]["care_missed"] += 1
                    st["loss_coins"]["care_missed"] += price
                    mark("care_missed", **brief)
                if tile.get("fertilizer_available"):
                    st["loss_units"]["fertilizer_uncollected"] += 1
                    st["loss_coins"]["fertilizer_uncollected"] += float(
                        prices.get("FERTILIZER", 0) or 0)
                    mark("fertilizer_uncollected", **brief)
                since = day + 1 - tile["placed_day"] - spec["first_yield_day"]
                if (since >= 0 and since % spec["interval"] == 0
                        and int(tile.get("yield_units", 0) or 0)
                        >= spec["max_held"]):
                    st["loss_units"]["capped_yield"] += 1
                    st["loss_coins"]["capped_yield"] += price
                    mark("capped_yield", **brief)
            elif kind in ("COOP", "PASTURE"):
                st["tile_days"]["empty_pen"] += 1


def _judge_overflow(st, priv, final_obs, sold_delta, prices, mark) -> None:
    """Units the nightly drop threw away because the shed was full."""
    carried: Counter[str] = Counter()
    for inventory in priv["inventories"]:
        carried.update({k: int(v) for k, v in inventory.items() if v > 0})
    in_shed = sum(int(v) for v in priv["shed"].values()) + sold_delta
    final = sum(int(v) for v in
                ((final_obs.get("private") or {}).get("shed") or {}).values())
    lost = max(0, in_shed + sum(carried.values()) - final)
    if lost and carried:
        per_unit = sum(n * float(prices.get(g, 0) or 0)
                       for g, n in carried.items()) / sum(carried.values())
        st["loss_units"]["overflow"] += lost
        st["loss_coins"]["overflow"] += lost * per_unit
        mark("overflow", units=lost, carried=dict(carried))


def _judge_market(stats, ledger, sides, prices_at, demand, engine) -> None:
    base = {g: p["base"] for g, p in engine.MARKET_PARAMS.items()}
    selling: dict[tuple[int, int, str], int] = Counter()
    for seat, step, op, item, price in ledger:
        if op == "SELL":
            selling[(seat, step, item)] += 1
    daily_sold: dict[int, Counter] = {s: Counter() for s in sides}
    for seat, step, op, item, price in ledger:
        if seat not in stats:
            continue
        st = stats[seat]
        day = step // TURNS
        if op == "SELL":
            st["sold"][item] += 1
            st["revenue"][item] += price
            daily_sold[seat][(item, day)] += 1
            if price <= 1:
                st["floor_units"][item] += 1
            elif price < 0.5 * base[item]:
                st["low_units"][item] += 1
            # Best price the book offered in the next day, in hindsight.
            ahead = [float(prices_at[s].get(item, 0) or 0)
                     for s in range(step + 1, step + TURNS)
                     if s in prices_at]
            if ahead and max(ahead) > price:
                st["regret"][item] += max(ahead) - price
            if selling.get((1 - seat, step, item)):
                st["crowded_units"] += 1
        elif op == "HIRE":
            st["spend"]["hire"] += price
        elif op == "BUY_LAND":
            st["spend"]["land"] += price
        elif op == "BUY_SEED":
            st["spend"]["seed " + item] += price
        elif op == "BUY_ANIMAL":
            st["spend"]["animal " + item] += price
        elif op == "BUY_PRODUCT":
            st["spend"]["buy " + item] += price

    # Books paying well above base on a day this farm sold none of them.
    # An upper bound on what was there to take: the town's whole appetite
    # that day at that day's price.
    for side in sides:
        for good, by_day in demand.items():
            for day, units in by_day.items():
                quotes = [float(prices_at[s].get(good, 0) or 0)
                          for s in range(day * TURNS, (day + 1) * TURNS)
                          if s in prices_at]
                if not quotes:
                    continue
                mean = statistics.mean(quotes)
                if (mean >= 1.2 * base[good]
                        and not daily_sold[side][(good, day)]):
                    stats[side]["open_book_days"][good] += 1
                    stats[side]["open_book_coins"][good] += units * mean


def _plain(side: dict[str, Any]) -> dict[str, Any]:
    return {k: (dict(v) if isinstance(v, Counter) else v)
            for k, v in side.items()}


# --------------------------------------------------------------------------
# Choosing the field.

def pick_field(opponents: int, tapes: int, min_tapes: int,
               max_margin: float) -> list[tuple[str, int, list[str]]]:
    """Strongest current opponents that we hold enough replays of."""
    from tools.data.profile_tapes import INDEX, TAPES

    data = ROOT / "rl" / "data"
    current = {int(json.loads(line)["episode_id"]) for line in
               (data / "top_matches.jsonl").read_text(
                   encoding="utf-8").splitlines()}
    rank = {}
    for line in (data / "leaderboard.jsonl").read_text(
            encoding="utf-8").splitlines():
        row = json.loads(line)
        rank[row.get("name")] = int(row.get("rank") or 99)
    held: dict[str, dict[int, str]] = defaultdict(dict)
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        episode = int(row["episode_id"])
        path = TAPES / f"live_{episode}.json"
        if episode not in current or not path.exists():
            continue
        if max_margin and abs(float(row.get("margin") or 0)) > max_margin:
            continue
        held[str(row.get("name"))][episode] = str(path)
    ranked = sorted((n for n, eps in held.items() if len(eps) >= min_tapes),
                    key=lambda n: (rank.get(n, 99), -len(held[n])))
    return [(n, rank.get(n, 99),
             [held[n][e] for e in sorted(held[n], reverse=True)[:tapes]])
            for n in ranked[:opponents]]


def inspect_one(job):
    spec, overrides, name, tape, seed, seat = job
    try:
        env, ledger = play(spec, overrides, tape, seed, seat)
        result, _ = analyse(env.steps, ledger, seat)
        result.update({"opponent": name, "tape": Path(tape).stem,
                       "seed": seed, "seat": seat,
                       # A TIMEOUT here means G stopped acting mid-game.
                       "status": {"G": env.state[seat].status,
                                  "OPP": env.state[1 - seat].status}})
        return result
    except Exception as error:  # a broken tape must not sink the run
        return {"opponent": name, "tape": Path(tape).stem,
                "error": f"{type(error).__name__}: {error}"}


# --------------------------------------------------------------------------
# Judging the whole run.

def per_game(games, side, section, key=None):
    values = []
    for game in games:
        block = game["stats"][side][section]
        values.append(sum(block.values()) if key is None
                      else block.get(key, 0))
    return statistics.mean(values) if values else 0.0


def judge(games: list[dict]) -> dict[str, Any]:
    n = len(games)
    out: dict[str, Any] = {"games": n}
    rewards = [(g["reward"]["G"], g["reward"]["OPP"]) for g in games]
    out["mean_g"] = statistics.mean(a for a, _ in rewards)
    out["mean_opp"] = statistics.mean(b for _, b in rewards)
    out["margin"] = statistics.mean(a - b for a, b in rewards)
    out["wins"] = sum(1 for a, b in rewards if a > b)
    out["agreement"] = statistics.mean(g["agreement"] for g in games)

    labour = {}
    for side in ("G", "OPP"):
        total = sum(sum(g["stats"][side]["turns"].values()) for g in games)
        classes = Counter()
        for g in games:
            classes.update(g["stats"][side]["turns"])
        labour[side] = {c: classes[c] / total for c in classes} if total else {}
    out["labour"] = labour

    noops = Counter()
    for g in games:
        noops.update(g["stats"]["G"]["noop"])
    turns = sum(sum(g["stats"]["G"]["turns"].values()) for g in games)
    examples: dict[str, list] = defaultdict(list)
    for g in games:
        for key, items in g["evidence"].items():
            for item in items:
                if len(examples[key]) < 3:
                    examples[key].append({"tape": g["tape"],
                                          "seat": g["seat"],
                                          "seed": g["seed"], **item})
    out["noops"] = [{"what": k, "per_game": v / n, "share": v / turns,
                     "examples": examples.get(k, [])}
                    for k, v in noops.most_common(15)]

    losses = {}
    for key in LOSSES:
        losses[key] = {
            "g_units": per_game(games, "G", "loss_units", key),
            "g_coins": per_game(games, "G", "loss_coins", key),
            "opp_units": per_game(games, "OPP", "loss_units", key),
            "opp_coins": per_game(games, "OPP", "loss_coins", key),
            "games_hit": sum(1 for g in games
                             if g["stats"]["G"]["loss_coins"].get(key, 0) > 0),
            "examples": examples.get("loss: " + key, []),
        }
    out["losses"] = losses

    goods = sorted({k for g in games for s in ("G", "OPP")
                    for k in g["stats"][s]["sold"]} | set(
        k for g in games for k in g["demand"]))
    market = {}
    for good in goods:
        row = {}
        for side in ("G", "OPP"):
            sold = per_game(games, side, "sold", good)
            revenue = per_game(games, side, "revenue", good)
            row[side] = {
                "sold": sold, "revenue": revenue,
                "price": revenue / sold if sold else 0.0,
                "floor": per_game(games, side, "floor_units", good),
                "low": per_game(games, side, "low_units", good),
                "regret": per_game(games, side, "regret", good),
                "open_days": per_game(games, side, "open_book_days", good),
                "open_coins": per_game(games, side, "open_book_coins", good),
            }
        town = statistics.mean(g["demand"].get(good, 0) for g in games)
        row["town"] = town
        market[good] = row
    out["market"] = market
    out["crowded"] = {s: statistics.mean(g["stats"][s]["crowded_units"]
                                         for g in games)
                      for s in ("G", "OPP")}
    spend = {}
    for side in ("G", "OPP"):
        keys = {k for g in games for k in g["stats"][side]["spend"]}
        spend[side] = {k: per_game(games, side, "spend", k) for k in keys}
    out["spend"] = spend
    tile_days = {}
    for side in ("G", "OPP"):
        keys = {k for g in games for k in g["stats"][side]["tile_days"]}
        tile_days[side] = {k: per_game(games, side, "tile_days", k)
                           for k in keys}
    out["tile_days"] = tile_days

    days = sorted({int(d) for g in games for d in g["timeline"]})
    timeline = {}
    for day in days:
        mine = [g["timeline"][d]["G"]["money"] for g in games
                for d in [day if day in g["timeline"] else str(day)]
                if d in g["timeline"] and "G" in g["timeline"][d]]
        theirs = [g["timeline"][d]["OPP"]["money"] for g in games
                  for d in [day if day in g["timeline"] else str(day)]
                  if d in g["timeline"] and "OPP" in g["timeline"][d]]
        if mine and theirs:
            timeline[day] = (statistics.median(mine),
                             statistics.median(theirs))
    out["timeline"] = timeline

    by_opp: dict[str, list] = defaultdict(list)
    for g in games:
        by_opp[g["opponent"]].append(g)
    out["opponents"] = [
        {"name": name, "games": len(gs),
         "wins": sum(1 for g in gs if g["reward"]["G"] > g["reward"]["OPP"]),
         "margin": statistics.mean(g["reward"]["G"] - g["reward"]["OPP"]
                                   for g in gs),
         "opp_noop": statistics.mean(
             g["stats"]["OPP"]["turns"].get("noop", 0)
             / max(1, sum(g["stats"]["OPP"]["turns"].values())) for g in gs)}
        for name, gs in by_opp.items()]

    # The ranked list: defects priced in coins per game, then the money
    # gaps by good, then labour problems that have no price attached.
    findings = []
    for key, row in losses.items():
        if row["g_coins"] > 0:
            findings.append({
                "kind": "loss (estimate)" if key in ESTIMATED else "loss",
                "what": key, "coins_per_game": row["g_coins"],
                "opp_coins_per_game": row["opp_coins"],
                "games_hit": f"{row['games_hit']}/{n}",
                "example": (row["examples"] or [None])[0],
                "where": WHERE.get(key, "")})
    for good, row in market.items():
        gap = row["OPP"]["revenue"] - row["G"]["revenue"]
        if gap > 0:
            findings.append({
                "kind": "revenue gap", "what": good, "coins_per_game": gap,
                "detail": (f"G sells {row['G']['sold']:.0f} at "
                           f"{row['G']['price']:.0f}, opponent "
                           f"{row['OPP']['sold']:.0f} at "
                           f"{row['OPP']['price']:.0f}; town takes "
                           f"{row['town']:.0f}"),
                "where": WHERE["open_books"]})
        if row["G"]["regret"] > 0:
            findings.append({
                "kind": "sell timing", "what": good,
                "coins_per_game": row["G"]["regret"],
                "detail": "hindsight: best price in the next day minus the "
                          "price taken; an upper bound",
                "where": WHERE["sell_regret"]})
    findings.sort(key=lambda f: -f["coins_per_game"])
    out["findings"] = findings
    return out


# --------------------------------------------------------------------------
# Reporting.

# An opponent replay refusing more than this share of its moves has fallen
# out of step with its own farm, and the game says little about G.
DESYNC = 0.02


def _opp_noop(game: dict) -> float:
    turns = game["stats"]["OPP"]["turns"]
    return turns.get("noop", 0) / max(1, sum(turns.values()))


def _fmt_share(d: dict, key: str) -> str:
    return f"{100 * d.get(key, 0):5.1f}%"


def report(verdict: dict, meta: dict, previous: dict | None,
           games: list[dict] | None = None) -> str:
    v = verdict
    out = [f"# Inspection of Candidate G -- {meta['when']}", ""]
    out.append(f"- G source `{meta['g_sha']}` at commit `{meta['git']}`"
               + (f", overrides `{meta['overrides']}`"
                  if meta["overrides"] else "")
               + (f", label `{meta['label']}`" if meta["label"] else ""))
    out.append(f"- {v['games']} games against {len(v['opponents'])} "
               f"opponents; match snapshot newest game "
               f"{meta['snapshot_newest']} ({meta['snapshot_age_h']:.0f}h old)")
    out.append(f"- engine-model agreement {100 * v['agreement']:.2f}% of "
               f"turns (below 99% means the verdicts cannot be trusted)")
    if meta.get("errors"):
        out.append(f"- {meta['errors']} games failed and are excluded")
    broken = [g for g in games or [] if _opp_noop(g) > DESYNC]
    out += ["", "## Scoreboard", "",
            f"G {v['mean_g']:,.0f}, opponent {v['mean_opp']:,.0f}, margin "
            f"{v['margin']:+,.0f}, wins {v['wins']}/{v['games']}", ""]
    if games:
        solid = [g for g in games if _opp_noop(g) <= DESYNC]
        solid_wins = sum(1 for g in solid
                         if g["reward"]["G"] > g["reward"]["OPP"])
        out += [f"{len(broken)} games had an opponent replay refusing over "
                f"{100 * DESYNC:.0f}% of its moves; on the other "
                f"{len(solid)} G wins {solid_wins}"
                + (f" with margin {statistics.mean(g['reward']['G'] - g['reward']['OPP'] for g in solid):+,.0f}"
                   if solid else ""), ""]
    out += [
            "| opponent | games | wins | margin | opponent replay no-op |",
            "|---|---:|---:|---:|---:|"]
    for row in sorted(v["opponents"], key=lambda r: r["margin"]):
        out.append(f"| {row['name']} | {row['games']} | {row['wins']} | "
                   f"{row['margin']:+,.0f} | {100 * row['opp_noop']:.1f}% |")

    out += ["", "## Findings, ranked by coins per game", "",
            "| # | kind | what | G coins/game | detail | where in G |",
            "|---:|---|---|---:|---|---|"]
    for i, f in enumerate(v["findings"][:20], 1):
        detail = f.get("detail") or (
            f"opponent {f.get('opp_coins_per_game', 0):,.0f}/game, "
            f"hit in {f.get('games_hit', '?')} games")
        example = f.get("example")
        if example:
            detail += (f"; e.g. tape {example['tape']} seat {example['seat']}"
                       f" seed {example['seed']} step {example['step']}"
                       + (f" at {example['at']} ({example['tile']})"
                          if "tile" in example else ""))
        out.append(f"| {i} | {f['kind']} | {f['what']} | "
                   f"{f['coins_per_game']:,.0f} | {detail} | {f['where']} |")

    out += ["", "## Labour: where worker-turns go", "",
            "| | work | move | idle | no-op | phantom |",
            "|---|---:|---:|---:|---:|---:|"]
    for side in ("G", "OPP"):
        d = v["labour"][side]
        out.append(f"| {side} | {_fmt_share(d, 'work')} | "
                   f"{_fmt_share(d, 'move')} | {_fmt_share(d, 'idle')} | "
                   f"{_fmt_share(d, 'noop')} | {_fmt_share(d, 'phantom')} |")
    out += ["", "G's moves the engine ignored:", ""]
    for row in v["noops"]:
        example = row["examples"][0] if row["examples"] else None
        out.append(f"- {row['per_game']:.1f}/game ({100 * row['share']:.2f}% "
                   f"of turns) **{row['what']}**"
                   + (f" -- e.g. tape {example['tape']} seat "
                      f"{example['seat']} seed {example['seed']} step "
                      f"{example['step']} worker {example['worker']} on "
                      f"{example['tile']}" if example else ""))

    out += ["", "## Losses per game", "",
            "| loss | G units | G coins | opp units | opp coins | G games hit |",
            "|---|---:|---:|---:|---:|---:|"]
    for key, row in v["losses"].items():
        out.append(f"| {key} | {row['g_units']:.1f} | {row['g_coins']:,.0f} "
                   f"| {row['opp_units']:.1f} | {row['opp_coins']:,.0f} | "
                   f"{row['games_hit']} |")
    td = v["tile_days"]
    out.append("")
    out.append("Ground, tile-days per game (G / opp): " + ", ".join(
        f"{k} {td['G'].get(k, 0):.0f}/{td['OPP'].get(k, 0):.0f}"
        for k in ("crop", "animal", "empty", "weed", "empty_pen",
                  "unwatered", "unfed")))

    out += ["", "## Market and the town's demand, per game", "",
            "| good | town takes | G sold | opp sold | G price | opp price "
            "| G floor | G revenue | opp revenue | G open-book days |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for good, row in sorted(v["market"].items(),
                            key=lambda kv: -(kv[1]["OPP"]["revenue"]
                                             - kv[1]["G"]["revenue"])):
        g, o = row["G"], row["OPP"]
        out.append(f"| {good} | {row['town']:.0f} | {g['sold']:.0f} | "
                   f"{o['sold']:.0f} | {g['price']:.0f} | {o['price']:.0f} | "
                   f"{g['floor']:.1f} | {g['revenue']:,.0f} | "
                   f"{o['revenue']:,.0f} | {g['open_days']:.1f} |")
    out.append("")
    out.append(f"Units sold on the same turn as the other farm sold the same "
               f"good: G {v['crowded']['G']:.0f}, opponent "
               f"{v['crowded']['OPP']:.0f} per game.")

    out += ["", "## Spending per game", "", "| item | G | opponent |",
            "|---|---:|---:|"]
    for key in sorted(set(v["spend"]["G"]) | set(v["spend"]["OPP"])):
        out.append(f"| {key} | {v['spend']['G'].get(key, 0):,.0f} | "
                   f"{v['spend']['OPP'].get(key, 0):,.0f} |")

    out += ["", "## Money by day (median)", "", "| day | G | opponent | gap |",
            "|---:|---:|---:|---:|"]
    for day, (mine, theirs) in v["timeline"].items():
        if int(day) % 3 == 2 or int(day) == 29:
            out.append(f"| {day} | {mine:,.0f} | {theirs:,.0f} | "
                       f"{theirs - mine:+,.0f} |")

    if previous:
        p = previous["verdict"]
        out += ["", f"## Since the last inspection ({previous['meta']['when']}"
                f", {previous['meta'].get('label') or 'no label'})", ""]
        out.append(f"- margin {p['margin']:+,.0f} -> {v['margin']:+,.0f}, "
                   f"wins {p['wins']}/{p['games']} -> {v['wins']}/{v['games']}"
                   f", G {p['mean_g']:,.0f} -> {v['mean_g']:,.0f}")
        if not previous["meta"].get("fair_town"):
            out.append("- **the earlier run used the coupled town, so none "
                       "of these deltas are comparable**")
        # Game by game, on the games both runs actually share.
        before = {(g["tape"], g["seat"], g["seed"]): g["reward"]
                  for g in previous.get("games", [])}
        pairs = [(before[key], g["reward"]) for g in games or []
                 for key in [(g["tape"], g["seat"], g["seed"])]
                 if key in before]
        # Only games where the opponent's replay stayed in step in *both*
        # runs. A replay cannot adapt: when G's selling starves it of cash
        # early, its purchases fail and everything after them no-ops. One
        # SpaTaro replay refused 583 moves in a baseline game G "won" 88k
        # to 63k, and 5 in the variant, where it banked 104k.
        before_clean = {(g["tape"], g["seat"], g["seed"]): _opp_noop(g)
                        for g in previous.get("games", [])}
        clean = [(before[key], g["reward"]) for g in games or []
                 for key in [(g["tape"], g["seat"], g["seed"])]
                 if key in before and before_clean[key] <= DESYNC
                 and _opp_noop(g) <= DESYNC]
        if clean:
            cd = [(a["G"] - a["OPP"]) - (b["G"] - b["OPP"]) for b, a in clean]
            out.append(
                f"- paired on {len(clean)} games where the opponent replay "
                f"stayed in step in both runs: margin "
                f"{statistics.mean(cd):+,.0f} per game (median "
                f"{statistics.median(cd):+,.0f}), better in "
                f"{sum(x > 0 for x in cd)}, worse in "
                f"{sum(x < 0 for x in cd)}")
        if pairs:
            deltas = [(a["G"] - a["OPP"]) - (b["G"] - b["OPP"])
                      for b, a in pairs]
            out.append(
                f"- paired on {len(pairs)} identical games: margin "
                f"{statistics.mean(deltas):+,.0f} per game, better in "
                f"{sum(d > 0 for d in deltas)}, worse in "
                f"{sum(d < 0 for d in deltas)}; G's own score better in "
                f"{sum(a['G'] > b['G'] for b, a in pairs)}")
        for key in LOSSES:
            a = p["losses"].get(key, {}).get("g_coins", 0)
            b = v["losses"][key]["g_coins"]
            if abs(b - a) >= 50:
                out.append(f"- {key}: {a:,.0f} -> {b:,.0f} coins/game")
        for cls in ("idle", "noop"):
            a = p["labour"]["G"].get(cls, 0)
            b = v["labour"]["G"].get(cls, 0)
            out.append(f"- G {cls} share {100 * a:.1f}% -> {100 * b:.1f}%")
        if previous["meta"].get("field") != meta.get("field"):
            out.append("- the opponent field differs from last time, so "
                       "these deltas mix a change in G with a change in "
                       "opponents")

    out += ["", "## Caveats", "",
            "- Opponents are replayed tapes: they cannot react to G, so "
            "anything G does to the market is felt by a farm that cannot "
            "adapt.",
            "- A tape replayed on a seed it was not recorded on drifts; the "
            "opponent no-op column above says how far.",
            "- Early-harvest, care and open-book coins are estimates of what "
            "was available, not of what a different decision would certainly "
            "have earned. Rot, escapes, deaths, overflow and stranded goods "
            "are exact.",
            f"- Drill into any example with `python -m tools.eval.inspect_g "
            f"--drill EPISODE --seat S --seed SEED --from STEP --to STEP`."]
    return "\n".join(out) + "\n"


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              cwd=ROOT, capture_output=True, text=True,
                              timeout=20).stdout.strip() or "?"
    except Exception:
        return "?"


def _snapshot_meta() -> tuple[str, float]:
    path = ROOT / "rl" / "data" / "top_matches.jsonl"
    newest = max((json.loads(line).get("create_time") or "")
                 for line in path.read_text(encoding="utf-8").splitlines())
    age = (time.time() - path.stat().st_mtime) / 3600.0
    return newest[:16], age


def _parse(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def drill(args, overrides) -> None:
    from tools.data.profile_tapes import TAPES

    tape = str(TAPES / f"live_{args.drill}.json")
    env, ledger = play(args.spec, overrides, tape, args.seed, args.seat)
    _, lines = analyse(env.steps, ledger, args.seat,
                       drill=(args.start, args.stop))
    print(f"G in seat {args.seat}, seed {args.seed}, against "
          f"live_{args.drill}; final G {env.state[args.seat].reward:,.0f} "
          f"opponent {env.state[1 - args.seat].reward:,.0f}\n")
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default="rl.candidate_g:agent")
    parser.add_argument("--opponents", type=int, default=12)
    parser.add_argument("--tapes", type=int, default=6,
                        help="replays per opponent")
    parser.add_argument("--min-tapes", type=int, default=3)
    parser.add_argument("--max-margin", type=float, default=20000.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--set", action="append", default=[],
                        help="NAME=VALUE override (JSON value), repeatable")
    parser.add_argument("--label", default="")
    parser.add_argument("--against", default="",
                        help="compare with the latest run carrying this "
                             "label, instead of the latest run")
    parser.add_argument("--drill", type=int, default=0,
                        help="episode id of a held tape to step through")
    parser.add_argument("--seat", type=int, default=0)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--from", dest="start", type=int, default=0)
    parser.add_argument("--to", dest="stop", type=int, default=48)
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    overrides = {}
    for item in args.set:
        name, _, raw = item.partition("=")
        overrides[name] = _parse(raw)

    if args.drill:
        drill(args, overrides)
        return

    field = pick_field(args.opponents, args.tapes, args.min_tapes,
                       args.max_margin)
    if not field:
        raise SystemExit("no current opponent has enough replays held")
    jobs = []
    for name, _, paths in field:
        for i, path in enumerate(paths):
            jobs.append((args.spec, overrides, name, path, 11 + i, i % 2))
    print(f"inspecting G over {len(jobs)} games against {len(field)} "
          f"opponents: " + ", ".join(f"{n} (#{r}, {len(p)})"
                                     for n, r, p in field), flush=True)

    with Pool(args.workers) as pool:
        results = pool.map(inspect_one, jobs)
    games = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    for r in errors[:5]:
        print(f"  failed: {r['opponent']} {r['tape']}: {r['error']}")
    if not games:
        raise SystemExit("every game failed")

    OUT.mkdir(parents=True, exist_ok=True)
    previous = None
    for path in sorted(OUT.glob("inspect_*.json"), reverse=True):
        candidate = json.loads(path.read_text(encoding="utf-8"))
        if not args.against or candidate["meta"].get("label") == args.against:
            previous = candidate
            break
    newest, age = _snapshot_meta()
    source = (ROOT / args.spec.split(":")[0].replace(".", "/")).with_suffix(
        ".py")
    meta = {
        "when": time.strftime("%Y-%m-%d %H:%M"),
        "git": _git_sha(),
        "g_sha": hashlib.sha1(source.read_bytes()).hexdigest()[:12]
        if source.exists() else "?",
        "overrides": overrides, "label": args.label, "fair_town": True,
        "snapshot_newest": newest, "snapshot_age_h": age,
        "errors": len(errors),
        "field": [[n, [Path(p).stem for p in ps]] for n, _, ps in field],
    }
    verdict = judge(games)
    text = report(verdict, meta, previous, games)
    # Label and microseconds in the name. Stamped to the second, four
    # inspections finishing together at 17:45 wrote over each other and the
    # baseline two of them were meant to be paired with was lost.
    slug = "".join(c if c.isalnum() else "-" for c in args.label)[:40]
    stamp = (time.strftime("%Y%m%d-%H%M%S")
             + f"-{int(time.time() * 1e6) % 1_000_000:06d}"
             + (f"-{slug}" if slug else ""))
    (OUT / f"inspect_{stamp}.json").write_text(
        json.dumps({"meta": meta, "verdict": verdict, "games": games},
                   default=str), encoding="utf-8")
    (OUT / f"inspect_{stamp}.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"saved rl/data/inspections/inspect_{stamp}.md and .json")


if __name__ == "__main__":
    main()
