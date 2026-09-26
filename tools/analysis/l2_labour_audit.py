"""How much of our labour is wasted, and what an in-place recycler could take.

Replays our real ladder games exactly (both tapes on the seed, see
l2_labour_replay) and, through hooks on the engine's own functions, judges
every farmer/hand command on our side at the moment the engine applies it:

  move   - a move that changed the unit's position
  work   - a non-move command that changed state
  pass   - PASS (or a hand with no command in the list)
  noop   - anything the engine silently ignored (with the engine's reason)

For every pass/noop hand-turn it lists the useful IN-PLACE commands that
existed on that unit's tile at that moment (the state after the units before
it this turn): WATER, HARVEST, FERTILIZE, CARE, COLLECT_FERTILIZER, DIG, FEED.
An in-place substitute keeps the unit where it is, so the tape's path is
untouched.

Each opportunity is then valued against what the tape itself did afterwards
(the replay knows the future): a WATER the tape did later that day is worth 0
(pre-emption), a CARE on an animal that ends the day fed and uncared banks
one unit, a COLLECT_FERTILIZER still uncollected at nightfall is a lost
fertilizer, a HARVEST at max of a decaying plant saves the units that rot
before the tape's own harvest, an animal HARVEST saves units lost to the
holding cap. Opportunities are de-duplicated per (command, tile, day).

It also counts the day-level waste the tape cannot see at all (animals fed
but not cared, fertilizer left uncollected, plants unwatered, one-time crops
harvested below max, rot, capped animal output, deaths, escapes) and how much
of it had an idle unit standing on the tile that day.

    python -m tools.analysis.l2_labour_audit --submission 56582917 --label L
    python -m tools.analysis.l2_labour_audit --submission 56571049 --label A
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments.envs.kaggriculture import kaggriculture as K

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.l2_labour_replay import records, replay_record  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "labour"
TPD = 24
MOVES = K.FARMER_MOVES
BOARD = 10


# ----------------------------------------------------------------- helpers
def ident(tile, x, y):
    if not isinstance(tile, dict):
        return None
    if tile.get("kind") == "PLANT":
        return ("P", x, y, tile["crop"], tile["planted_day"])
    if "animal" in tile:
        return ("A", x, y, tile["animal"], tile["placed_day"])
    if tile.get("kind") == "WEED":
        return ("W", x, y)
    return ("S", x, y, tile.get("kind"))


def brief(tile):
    if not isinstance(tile, dict):
        return tile
    keep = ("kind", "crop", "planted_day", "watered_today",
            "consecutive_unwatered", "yield_units", "max_lifespan_step",
            "fertilized_until_day", "animal", "placed_day", "fed_today",
            "consecutive_unfed", "cared_today", "fertilizer_available",
            "pending_care_bonus")
    return {k: tile[k] for k in keep if k in tile}


def growth_left(tile, day):
    """Units watering can still add to a one-time crop from now on."""
    cd = K.CROPS[tile["crop"]]
    if cd["ongoing"]:
        return 0
    ws = (cd["max_yield_day"] + 1) // 2
    age = day - tile["planted_day"]
    add = 0
    for d in range(max(age, ws), cd["max_yield_day"] + 1):
        if d == age and tile["watered_today"]:
            continue
        add += 2 if tile["fertilized_until_day"] >= day + (d - age) else 1
    return max(0, min(cd["max_yield"], tile["yield_units"] + add)
               - tile["yield_units"])


def candidates(tile, inv, day, step):
    """In-place commands that would change state on this tile right now."""
    out = []
    if not isinstance(tile, dict):
        return out
    kind = tile.get("kind")
    if kind == "PLANT":
        cd = K.CROPS[tile["crop"]]
        age = day - tile["planted_day"]
        if not tile["watered_today"]:
            out.append("WATER")
        if tile["yield_units"] > 0 and age >= cd["first_yield_day"]:
            out.append("HARVEST")
        if int(inv.get("FERTILIZER", 0)) > 0 and \
                tile["fertilized_until_day"] < day + 2:
            out.append("FERTILIZE")
    elif kind == "WEED":
        out.append("DIG")
    elif "animal" in tile:
        if not tile["cared_today"]:
            out.append("CARE")
        if tile["fertilizer_available"]:
            out.append("COLLECT_FERTILIZER")
        if tile["yield_units"] > 0:
            out.append("HARVEST")
        if not tile["fed_today"] and int(inv.get("WHEAT", 0)) > 0:
            out.append("FEED")
    return out


def noop_reason(verb, unit, tile, inv, private, x, y, blocked):
    beside = K._is_shed_adjacent((x, y), BOARD)
    animal_here = isinstance(tile, dict) and "animal" in tile
    item = unit[1] if len(unit) > 1 else None
    if blocked:
        return "PLANT: more than seeds, all cancelled"
    if verb in MOVES:
        return "walked off the board"
    if verb == "DROP":
        return "not beside shed" if not beside else "carrying nothing"
    if verb == "PICKUP":
        return "not beside shed" if not beside else f"shed has no {item}"
    if verb == "PLACE":
        if item in K.ANIMALS:
            if int(inv.get(item, 0)) <= 0:
                return f"no {item} in hand"
            return "not on empty structure"
        return "not beside shed" if not beside else "nothing to place/shed full"
    if tile == "LOCKED":
        return "tile locked"
    if verb == "PLANT":
        if tile is not None:
            k = tile.get("kind") if isinstance(tile, dict) else tile
            return f"tile not empty ({k})"
        return f"no {item} seed"
    if verb == "WATER":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return "nothing to water"
        return "already watered"
    if verb == "HARVEST":
        if not isinstance(tile, dict):
            return "nothing here"
        if int(tile.get("yield_units", 0) or 0) <= 0:
            return "zero yield"
        return "immature"
    if verb == "FERTILIZE":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return "no plant"
        return "no fertilizer in hand"
    if verb == "DIG":
        return "empty tile" if tile is None else "animal on tile"
    if verb in ("BUILD_COOP", "BUILD_PASTURE"):
        return "tile not empty"
    if verb == "FEED":
        if not animal_here:
            return "no animal"
        if tile.get("fed_today"):
            return "already fed"
        return "no wheat in hand"
    if verb == "COLLECT_FERTILIZER":
        return "no animal" if not animal_here else "none available"
    if verb == "CARE":
        return "no animal" if not animal_here else "already cared"
    return "unknown command"


def _sig(farm, private, idx, x, y):
    pos = farm["farmer"] if idx == 0 else farm["hands"][idx - 1]
    inv = private["inventories"][idx] if idx < len(private["inventories"]) else {}
    return json.dumps([pos, farm["tiles"][y][x], inv, private["shed"],
                       private["seeds"]], sort_keys=True, default=str)


# ----------------------------------------------------------------- observer
class Audit:
    def __init__(self, side):
        self.side = side
        self.farm = None
        self.step = 0
        self.raw_units = []
        self.turns = Counter()          # (cls, who) -> n
        self.noop_reasons = Counter()
        self.idle_where = Counter()     # tile kind under idle unit
        self.idle_hour = Counter()
        self.idle_day = Counter()
        self.opps = []                  # pass/noop hand-turns with candidates
        self.events = defaultdict(list)  # (verb, ident) -> [(step, idx, info)]
        self.eod = {}                   # day -> {ident: brief}
        self.eod_inv = {}               # day -> carried FERTILIZER units at night
        self.deaths = []                # (day, ident, brief) died at refresh
        self.escapes = []
        self.rot = []                   # (step, ident)
        self.prices = {}
        self.cap_waste = []             # (day, ident, units)
        self.acted = set()
        self.hands_n = 0

    # -- engine hooks
    def before_step(self, state, step):
        self.step = step
        obs0 = state[0].observation
        self.farm = obs0.farms[self.side]
        a = state[self.side].action or {}
        hands = a.get("hands") or [] if isinstance(a, dict) else []
        self.raw_units = [a.get("farmer", ["PASS"]) if isinstance(a, dict)
                          else ["PASS"], *hands]
        self.prices[step] = dict(obs0.market["prices"])
        self.hands_n = len(self.farm["hands"])
        self.acted = set()
        # plant-blocking rule, as the interpreter computes it
        priv = state[self.side].observation.private
        demand = Counter(u[1] for u in self.raw_units
                         if isinstance(u, list) and len(u) >= 2
                         and u[0] == "PLANT")
        self.blocked = {c for c, n in demand.items()
                        if n > priv["seeds"].get(c, 0)}
        self.private = priv
        # hands the command list does not reach are never called by the engine
        day = step // TPD
        for idx in range(len(self.raw_units), self.hands_n + 1):
            x, y = self.farm["hands"][idx - 1]
            tile = self.farm["tiles"][y][x]
            inv = priv["inventories"][idx] if idx < len(priv["inventories"]) else {}
            self.turns[("absent", "hand")] += 1
            self._idle(idx, x, y, tile, ident(tile, x, y), brief(tile),
                       candidates(tile, inv, day, step), "pass", "ABSENT",
                       {k: v for k, v in inv.items() if v}, day)

    def unit(self, farm, private, idx, action, day, apply):
        if farm is not self.farm:
            return apply()
        pos = K._farmer_position(farm, idx)
        if pos is None:              # command for a hand that does not exist
            self.turns[("phantom", "hand")] += 1
            return apply()
        self.acted.add(idx)
        x, y = pos
        who = "farmer" if idx == 0 else "hand"
        raw = self.raw_units[idx] if idx < len(self.raw_units) else ["PASS"]
        verb = str(raw[0]) if isinstance(raw, list) and raw else "PASS"
        tile = farm["tiles"][y][x]
        inv = K._farmer_inventory(private, idx)
        pre = brief(tile)
        tid = ident(tile, x, y)
        blocked = (verb == "PLANT" and len(raw) > 1 and raw[1] in self.blocked)
        cands = candidates(tile, inv, day, self.step)
        carried = {k: v for k, v in inv.items() if v}
        sig = _sig(farm, private, idx, x, y)
        result = apply()
        changed = _sig(farm, private, idx, x, y) != sig
        if verb == "PASS" and not blocked:
            cls = "pass"
        elif changed:
            cls = "move" if verb in MOVES else "work"
        else:
            cls = "noop"
        self.turns[(cls, who)] += 1
        if cls == "noop":
            self.noop_reasons[f"{verb}: " + noop_reason(
                verb, raw, tile, inv, private, x, y, blocked)] += 1
        if cls in ("pass", "noop"):
            self._idle(idx, x, y, tile, tid, pre, cands, cls, verb, carried,
                       day)
        if cls == "work":
            info = {}
            if verb == "HARVEST":
                info = {"units": pre.get("yield_units", 0), "pre": pre}
            elif verb == "FERTILIZE" or verb == "WATER":
                info = {"pre": pre}
            self.events[(verb, tid if verb != "PLANT" else ("E", x, y))].append(
                (self.step, idx, info))
            if verb == "PLANT":
                self.events[("PLANT@", (x, y))].append((self.step, idx, {}))
        return result

    def _idle(self, idx, x, y, tile, tid, pre, cands, cls, verb, carried, day):
        kind = ("empty" if tile is None else tile if isinstance(tile, str)
                else ("animal" if "animal" in tile else tile.get("kind")))
        self.idle_where[kind] += 1
        self.idle_hour[self.step % TPD] += 1
        self.idle_day[day] += 1
        self.opps.append({"step": self.step, "day": day, "idx": idx,
                          "cls": cls, "verb": verb, "x": x, "y": y,
                          "ident": tid, "tile": pre, "cands": cands,
                          "carried": carried,
                          "beside_shed": K._is_shed_adjacent((x, y), BOARD)})

    def decay(self, farm, step, apply):
        if farm is self.farm:
            for y, row in enumerate(farm["tiles"]):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        mls = t["max_lifespan_step"]
                        if mls >= 0 and step >= mls and (step - mls) % 2 == 0 \
                                and t["yield_units"] > 0:
                            self.rot.append((step, ident(t, x, y)))
        return apply()

    def end_of_day(self, state, env, day, apply):
        farm = state[0].observation.farms[self.side]
        # hands with no command at all this step idle too (never in the list)
        snap = {}
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get("kind") in (
                        "PLANT", "COOP", "PASTURE", "WEED"):
                    if t.get("kind") in ("COOP", "PASTURE") and "animal" not in t:
                        continue
                    snap[ident(t, x, y)] = brief(t)
        self.eod[day] = snap
        priv = state[self.side].observation.private
        self.eod_inv[day] = sum(int(i.get("FERTILIZER", 0))
                                for i in priv["inventories"])
        # capped animal output at tonight's production
        for tid, t in snap.items():
            if tid[0] != "A":
                continue
            a = K.ANIMALS[t["animal"]]
            since = day + 1 - t["placed_day"] - a["first_yield_day"]
            if since >= 0 and since % a["interval"] == 0 and \
                    t["consecutive_unfed"] + (0 if t["fed_today"] else 1) < 2:
                bonus = t.get("pending_care_bonus", 0) if t["fed_today"] else 0
                over = t["yield_units"] + 1 + bonus - a["max_held"]
                if over > 0:
                    self.cap_waste.append((day, tid, over))
        result = apply()
        after = state[0].observation.farms[self.side]["tiles"]
        for tid, t in snap.items():
            x, y = tid[1], tid[2]
            now = after[y][x]
            if tid[0] == "P" and isinstance(now, dict) and now.get("kind") == "WEED":
                self.deaths.append((day, tid, t))
            if tid[0] == "A" and isinstance(now, dict) and "animal" not in now:
                self.escapes.append((day, tid, t))
        return result


# ----------------------------------------------------------------- valuation
def _later(events, key, day, step, idx):
    """Did the tape do this on `day` after (step, idx)?"""
    for s, i, _ in events.get(key, []):
        if s // TPD == day and (s, i) > (step, idx):
            return True
    return False


def _harvest_after(events, tid, step):
    for s, i, info in events.get(("HARVEST", tid), []):
        if s >= step:
            return s, info.get("units", 0)
    return None, 0


def value_game(au: Audit, reward):
    ev = au.events
    price = lambda item, step: float(au.prices.get(step, {}).get(item, 0) or 0)
    seen = set()
    rows = []
    for o in au.opps:
        tid, day, step, idx, t = o["ident"], o["day"], o["step"], o["idx"], o["tile"]
        for verb in o["cands"]:
            key = (verb, tid, day)
            first = key not in seen
            seen.add(key)
            gain, units, note = 0.0, 0, ""
            if verb == "WATER":
                if _later(ev, ("WATER", tid), day, step, idx):
                    note = "tape waters later"
                else:
                    cd = K.CROPS[t["crop"]]
                    age = day - t["planted_day"]
                    died = any(d == day and dt == tid for d, dt, _ in au.deaths)
                    hs, hu = _harvest_after(ev, tid, step)
                    if died:
                        units = max(1, t["yield_units"]) + growth_left(t, day)
                        gain = units * price(t["crop"], step) + cd["seed"]
                        note = "rescue (died unwatered)"
                    elif not cd["ongoing"] and \
                            (cd["max_yield_day"] + 1) // 2 <= age <= cd["max_yield_day"] \
                            and t["yield_units"] < cd["max_yield"]:
                        units = min(cd["max_yield"], t["yield_units"] + (
                            2 if t["fertilized_until_day"] >= day else 1)) - t["yield_units"]
                        if hs is not None:
                            gain = units * price(t["crop"], hs)
                            note = "window bonus, harvested"
                        else:
                            note = "window bonus, never harvested"
                            units = 0
                    elif cd["ongoing"] and t["fertilized_until_day"] >= day:
                        since = day + 1 - t["planted_day"] - cd["first_yield_day"]
                        if since >= 0 and since % cd["interval"] == 0 and \
                                since // cd["interval"] + 1 <= cd["max_yield"]:
                            units = 1
                            gain = price(t["crop"], step)
                            note = "fertilized production doubled"
                        else:
                            note = "survival only"
                    else:
                        note = "survival only"
            elif verb == "CARE":
                if _later(ev, ("CARE", tid), day, step, idx):
                    note = "tape cares later"
                else:
                    end = au.eod.get(day, {}).get(tid)
                    if end and end["fed_today"] and not end["cared_today"]:
                        a = K.ANIMALS[t["animal"]]
                        # next production tick and whether it pays out
                        paid = False
                        for d2 in range(day + 1, 30):
                            s2 = au.eod.get(d2, {}).get(tid)
                            if s2 is None:
                                break
                            since = d2 + 1 - t["placed_day"] - a["first_yield_day"]
                            if since >= 0 and since % a["interval"] == 0:
                                room = a["max_held"] - s2["yield_units"] - 1 - \
                                    s2.get("pending_care_bonus", 0)
                                paid = s2["fed_today"] and room >= 1
                                break
                        if paid:
                            units = 1
                            gain = price(a["product"], step)
                            note = "banked, paid"
                        else:
                            note = "banked, lost (unfed/capped/end)"
                    else:
                        note = "animal unfed at night"
            elif verb == "COLLECT_FERTILIZER":
                if _later(ev, ("COLLECT_FERTILIZER", tid), day, step, idx):
                    note = "tape collects later"
                else:
                    end = au.eod.get(day, {}).get(tid)
                    if end and end["fertilizer_available"]:
                        units = 1
                        gain = price("FERTILIZER", step)
                        note = "uncollected at night (sale value)"
                    else:
                        note = "animal gone"
            elif verb == "HARVEST" and tid and tid[0] == "P":
                cd = K.CROPS[t["crop"]]
                at_max = (growth_left(t, day) == 0) if not cd["ongoing"] else True
                decaying = t["max_lifespan_step"] >= 0 and step >= t["max_lifespan_step"]
                if not at_max:
                    note = "below max"
                else:
                    hs, hu = _harvest_after(ev, tid, step)
                    got = hu if hs is not None else 0
                    if cd["ongoing"] and not decaying:
                        # early harvest of an ongoing crop only avoids the cap
                        note = "ongoing, not decaying"
                    else:
                        units = max(0, t["yield_units"] - got)
                        gain = units * price(t["crop"], step)
                        note = ("decaying" if decaying else "at max") + (
                            ", tape harvests later" if hs is not None else ", tape never harvests")
            elif verb == "HARVEST" and tid and tid[0] == "A":
                waste = [u for d, w, u in au.cap_waste if w == tid and d == day]
                if waste and not _later(ev, ("HARVEST", tid), day, step, idx):
                    units = waste[0]
                    gain = units * price(K.ANIMALS[t["animal"]]["product"], step)
                    note = "capped tonight"
                else:
                    note = "no cap loss"
            elif verb == "DIG":
                later_dig = any(s > step for s, _, _ in ev.get(("DIG", tid), []))
                note = "tape digs later" if later_dig else "weed stays"
            elif verb == "FERTILIZE":
                used = any(s // TPD == day and s > step and i == idx
                           for (v, _), lst in ev.items() if v == "FERTILIZE"
                           for s, i, _ in lst)
                note = "unit uses its fertilizer later today" if used else \
                    "unit carries fertilizer unused"
            elif verb == "FEED":
                end = au.eod.get(day, {}).get(tid)
                note = "unfed at night" if end and not end["fed_today"] else "fed later"
            rows.append({"verb": verb, "first": first, "gain": gain,
                         "units": units, "note": note, "step": step,
                         "day": day, "idx": idx, "cls": o["cls"],
                         "ident": list(tid) if tid else None})
    return rows


def day_waste(au: Audit):
    """Waste visible at nightfall, and whether an idle unit stood on it."""
    idle_on = defaultdict(set)      # (day, ident) -> set of idle verbs possible
    for o in au.opps:
        if o["ident"]:
            for v in o["cands"]:
                idle_on[(o["day"], o["ident"])].add(v)
    price = lambda item, day: float(au.prices.get(day * TPD + 12, {}).get(item, 0) or 0)
    w = Counter()
    coins = Counter()
    rec = Counter()
    for day, snap in au.eod.items():
        for tid, t in snap.items():
            if tid[0] == "A":
                prod = K.ANIMALS[t["animal"]]["product"]
                if t["fed_today"] and not t["cared_today"]:
                    w["care_missed_fed"] += 1
                    coins["care_missed_fed"] += price(prod, day)
                    rec["care_missed_fed"] += "CARE" in idle_on[(day, tid)]
                if not t["fed_today"]:
                    w["animal_unfed"] += 1
                if t["fertilizer_available"]:
                    w["fert_uncollected"] += 1
                    coins["fert_uncollected"] += price("FERTILIZER", day)
                    rec["fert_uncollected"] += "COLLECT_FERTILIZER" in idle_on[(day, tid)]
            elif tid[0] == "P":
                cd = K.CROPS[t["crop"]]
                age = day - t["planted_day"]
                if not t["watered_today"]:
                    w["plant_unwatered"] += 1
                    rec["plant_unwatered"] += "WATER" in idle_on[(day, tid)]
                    if not cd["ongoing"] and (cd["max_yield_day"] + 1) // 2 <= age \
                            <= cd["max_yield_day"] and t["yield_units"] < cd["max_yield"]:
                        w["window_unwatered"] += 1
                        coins["window_unwatered"] += price(t["crop"], day)
                        rec["window_unwatered"] += "WATER" in idle_on[(day, tid)]
            elif tid[0] == "W":
                w["weed_tile_days"] += 1
                rec["weed_tile_days"] += "DIG" in idle_on[(day, tid)]
    for day, tid, units in au.cap_waste:
        prod = K.ANIMALS[tid[3]]["product"]
        w["animal_cap_units"] += units
        coins["animal_cap_units"] += units * price(prod, day)
        rec["animal_cap_units"] += units if "HARVEST" in idle_on[(day, tid)] else 0
    for day, tid, t in au.deaths:
        w["plants_died"] += 1
        coins["plants_died"] += K.CROPS[tid[3]]["seed"] + t["yield_units"] * price(tid[3], day)
        rec["plants_died"] += "WATER" in idle_on[(day, tid)]
    for day, tid, t in au.escapes:
        w["animals_escaped"] += 1
        coins["animals_escaped"] += K.ANIMALS[tid[3]]["cost"]
    for step, tid in au.rot:
        w["rot_units"] += 1
        coins["rot_units"] += float(au.prices.get(step, {}).get(tid[3], 0) or 0)
        rec["rot_units"] += "HARVEST" in idle_on[(step // TPD, tid)]
    # one-time crops the tape cut below max
    for (verb, tid), lst in au.events.items():
        if verb != "HARVEST" or not tid or tid[0] != "P":
            continue
        for s, i, info in lst:
            pre = info.get("pre") or {}
            if pre.get("kind") == "PLANT" and not K.CROPS[pre["crop"]]["ongoing"]:
                lost = growth_left(pre, s // TPD)
                if lost:
                    w["harvest_below_max_units"] += lost
                    coins["harvest_below_max_units"] += lost * float(
                        au.prices.get(s, {}).get(pre["crop"], 0) or 0)
    return dict(w), {k: round(v) for k, v in coins.items()}, dict(rec)


# ----------------------------------------------------------------- driver
def audit_one(record):
    side = int(record["our_side"])
    au = Audit(side)
    got, state, tapes = replay_record(record, au)
    exact = got == record["rewards"]
    rows = value_game(au, got)
    waste, coins, rec = day_waste(au)
    turns = {f"{c}/{w}": n for (c, w), n in au.turns.items()}
    return {
        "episode_id": record["episode_id"], "submission": record["submission"],
        "exact": exact, "reward": got, "won": record.get("won"),
        "opponent_rating": record.get("opponent_rating"),
        "turns": turns, "noop_reasons": dict(au.noop_reasons),
        "idle_where": dict(au.idle_where),
        "idle_hour": dict(au.idle_hour), "idle_day": dict(au.idle_day),
        "opps": rows, "waste": waste, "waste_coins": coins,
        "waste_idle_on_tile": rec,
        "idle_detail": [{k: o[k] for k in ("step", "idx", "cls", "verb", "x",
                                           "y", "cands", "beside_shed")}
                        | {"kind": (o["tile"] or {}).get("kind") if isinstance(
                            o["tile"], dict) else o["tile"]}
                        for o in au.opps],
    }


def summarise(games, label):
    lines = [f"== {label}: {len(games)} games, exact replays "
             f"{sum(g['exact'] for g in games)}/{len(games)}"]
    tot = Counter()
    for g in games:
        tot.update(g["turns"])
    all_turns = sum(tot.values()) - tot.get("phantom/hand", 0)
    lines.append("unit-turns per game (median), share of all unit-turns:")
    for key in sorted(tot):
        per = [g["turns"].get(key, 0) for g in games]
        lines.append(f"  {key:14s} median {statistics.median(per):6.0f}  "
                     f"share {tot[key] / max(1, all_turns):6.1%}")
    reasons = Counter()
    for g in games:
        reasons.update(g["noop_reasons"])
    lines.append("top no-op reasons (per game mean):")
    for r, n in reasons.most_common(18):
        lines.append(f"  {n / len(games):7.1f}  {r}")
    where = Counter()
    for g in games:
        where.update(g["idle_where"])
    lines.append("tile under idle/no-op unit (per game mean): " + ", ".join(
        f"{k} {v / len(games):.1f}" for k, v in where.most_common()))
    hours = Counter()
    for g in games:
        hours.update({int(k): v for k, v in g["idle_hour"].items()})
    lines.append("idle/no-op by hour (per game mean): " + " ".join(
        f"{h}:{hours[h] / len(games):.0f}" for h in range(24)))
    # opportunities
    by = defaultdict(lambda: Counter())
    gains = defaultdict(list)
    for g in games:
        per = Counter()
        for r in g["opps"]:
            k = (r["verb"], r["note"])
            by[k]["all"] += 1
            if r["first"]:
                by[k]["unique"] += 1
                by[k]["units"] += r["units"]
                by[k]["coins"] += r["gain"]
                per[r["verb"]] += r["gain"]
        for v in ("WATER", "CARE", "COLLECT_FERTILIZER", "HARVEST", "DIG",
                  "FERTILIZE", "FEED"):
            gains[v].append(per.get(v, 0.0))
    lines.append("in-place opportunities at idle/no-op turns (per game means;"
                 " unique = first per command/tile/day):")
    for (v, note), c in sorted(by.items(), key=lambda kv: -kv[1]["coins"]):
        lines.append(f"  {v:18s} {note:40s} turns {c['all'] / len(games):6.1f}  "
                     f"unique {c['unique'] / len(games):6.1f}  units "
                     f"{c['units'] / len(games):5.1f}  coins {c['coins'] / len(games):8.0f}")
    lines.append("estimated recyclable coins per game by command (mean / median):")
    total = [0.0] * len(games)
    for v, lst in gains.items():
        for i, x in enumerate(lst):
            total[i] += x
        lines.append(f"  {v:18s} {statistics.mean(lst):8.0f} / {statistics.median(lst):8.0f}")
    lines.append(f"  {'ALL':18s} {statistics.mean(total):8.0f} / {statistics.median(total):8.0f}")
    # day-level waste
    wk = sorted({k for g in games for k in g["waste"]})
    lines.append("day-level waste per game (mean): count | coins | with an idle unit on the tile that day")
    for k in wk:
        n = statistics.mean(g["waste"].get(k, 0) for g in games)
        c = statistics.mean(g["waste_coins"].get(k, 0) for g in games)
        r = statistics.mean(g["waste_idle_on_tile"].get(k, 0) for g in games)
        lines.append(f"  {k:26s} {n:8.1f} | {c:8.0f} | {r:6.1f}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", type=int, default=56582917)
    ap.add_argument("--label", default="L")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    recs = records(args.submission)
    if args.limit:
        recs = recs[: args.limit]
    t = time.time()
    games = []
    for p, r in recs:
        games.append(audit_one(r))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"audit_{args.label}.json").write_text(json.dumps(games), encoding="utf-8")
    text = summarise(games, args.label)
    (OUT / f"audit_{args.label}.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"({time.time() - t:.0f}s)")


if __name__ == "__main__":
    main()
