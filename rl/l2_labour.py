# ---- BEGIN l2_labour (in-place labour recycler) ----
# A unit whose command this turn is PASS, or a command the engine will
# certainly ignore, is given a useful command ON ITS OWN TILE instead. The
# unit does not move, so the parent's route (its "tape") is untouched: the
# next command the parent gives it starts from the same square.
#
# It only ever issues:
#   CARE      an animal already fed today and not yet cared for, whose banked
#             bonus can still be paid before the season ends and fits under
#             the holding cap;
#   WATER     a plant not yet watered today -- unless a fertilizer is being
#             carried and the plant is in a stage where fertilizing before
#             watering would earn more (one-time crop in its bonus window,
#             ongoing crop on a production eve);
#   HARVEST   a plant that is already decaying (yield can only fall), or an
#             animal whose output would overflow its holding cap tonight;
#   COLLECT_FERTILIZER  late in the day only (hour >= 22), when the replays
#             show the tape never collects it itself;
#   DIG       a weed under a PASSing unit.
# It never moves a unit, never PLANTs, FEEDs, FERTILIZEs, PICKUPs, DROPs or
# PLACEs (so it never spends seeds, wheat or fertilizer the parent needs),
# never harvests a plant that could still grow, never touches market orders,
# and never adds to the shed past a safety margin. Any error returns the
# parent's action unchanged.

import time as _lb_time

_LB_CROPS = {  # first_yield_day, max_yield_day, interval, max_yield, ongoing
    "WHEAT": (2, 4, 0, 6, False), "CARROT": (2, 3, 0, 4, False),
    "TOMATO": (8, 8, 1, 4, True), "STRAWBERRY": (10, 10, 2, 4, True),
    "MELON": (10, 12, 0, 6, False)}
_LB_ANIMALS = {"GOOSE": (4, 1, 4), "COW": (8, 2, 6), "SHEEP": (6, 3, 6)}
_LB_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_LB_SHED_CAP = 100
_LB_SHED_MARGIN = 4
_LB_LAST_DAY = 29


def _lb_get(v, k, d=None):
    if isinstance(v, dict):
        return v.get(k, d)
    g = getattr(v, "get", None)
    return g(k, d) if callable(g) else getattr(v, k, d)


def _lb_beside_shed(x, y):
    return x in (4, 5) and y in (4, 5)


def _lb_noop(cmd, tile, inv, seeds, x, y, blocked, day=0):
    """True when the engine will certainly ignore cmd (mirrors _apply_unit_action)."""
    if not isinstance(cmd, list) or not cmd:
        return True
    op = cmd[0]
    if op == "PASS":
        return True
    if op in _LB_MOVES:
        dx, dy = _LB_MOVES[op]
        return not (0 <= x + dx < 10 and 0 <= y + dy < 10)
    item = cmd[1] if len(cmd) > 1 else None
    if op == "DROP":
        return not _lb_beside_shed(x, y) or not any(int(n or 0) > 0 for n in inv.values())
    if op in ("PICKUP", "PLACE"):
        return False   # judged conservatively as work: never replaced
    if tile == "LOCKED":
        return True
    d = isinstance(tile, dict)
    kind = tile.get("kind") if d else None
    animal = d and "animal" in tile
    if op == "PLANT":
        return item in blocked or tile is not None or int(seeds.get(item, 0) or 0) <= 0
    if op == "WATER":
        return kind != "PLANT" or bool(tile.get("watered_today"))
    if op == "HARVEST":
        if not d or int(tile.get("yield_units", 0) or 0) <= 0:
            return True
        if kind == "PLANT" and tile.get("crop") in _LB_CROPS:
            return day - int(tile.get("planted_day", 0)) < _LB_CROPS[tile["crop"]][0]
        return False
    if op == "FERTILIZE":
        return kind != "PLANT" or int(inv.get("FERTILIZER", 0) or 0) <= 0
    if op == "DIG":
        return tile is None or animal
    if op in ("BUILD_COOP", "BUILD_PASTURE"):
        return tile is not None
    if op == "FEED":
        return not animal or bool(tile.get("fed_today")) or int(inv.get("WHEAT", 0) or 0) <= 0
    if op == "COLLECT_FERTILIZER":
        return not animal or not tile.get("fertilizer_available")
    if op == "CARE":
        return not animal or bool(tile.get("cared_today"))
    return False


def _lb_effect(cmd, tile, inv, seeds, day, step, blocked):
    """New tile after an (effective) command, for later units this turn."""
    op = cmd[0] if cmd else "PASS"
    d = isinstance(tile, dict)
    if op == "WATER" and d and tile.get("kind") == "PLANT":
        return dict(tile, watered_today=True)
    if op == "CARE" and d and "animal" in tile:
        return dict(tile, cared_today=True)
    if op == "FEED" and d and "animal" in tile and int(inv.get("WHEAT", 0) or 0) > 0:
        return dict(tile, fed_today=True)
    if op == "COLLECT_FERTILIZER" and d and "animal" in tile:
        return dict(tile, fertilizer_available=False)
    if op == "HARVEST" and d and int(tile.get("yield_units", 0) or 0) > 0:
        if tile.get("kind") == "PLANT":
            spec = _LB_CROPS.get(tile.get("crop"))
            if spec and not spec[4]:
                return None
        return dict(tile, yield_units=0)
    if op == "DIG" and d and "animal" not in tile:
        return None
    if op == "PLANT" and tile is None and len(cmd) > 1 and cmd[1] in _LB_CROPS \
            and cmd[1] not in blocked:
        return {"kind": "PLANT", "crop": cmd[1], "planted_day": day,
                "watered_today": False, "consecutive_unwatered": 1,
                "yield_units": 0 if _LB_CROPS[cmd[1]][4] else 1,
                "max_lifespan_step": -1, "fertilized_until_day": -1}
    if op in ("BUILD_COOP", "BUILD_PASTURE") and tile is None:
        return {"kind": "COOP" if op == "BUILD_COOP" else "PASTURE"}
    return tile


def _lb_produces_tonight(tile, day):
    first, interval, _ = _LB_ANIMALS[tile["animal"]]
    since = day + 1 - int(tile.get("placed_day", 0)) - first
    return since >= 0 and since % interval == 0


def _lb_care_pays(tile, day):
    """A CARE today banks +1 that is paid on a later production dawn."""
    first, interval, held = _LB_ANIMALS[tile["animal"]]
    start = int(tile.get("placed_day", 0)) + first
    nxt = day + 2   # banked tonight after tonight's production; next payout day
    k = max(0, -(-(nxt - start) // interval)) if nxt > start else 0
    payout = start + k * interval
    if payout > _LB_LAST_DAY:     # production dawns after day 29 never happen
        return False
    pending = int(tile.get("pending_care_bonus", 0) or 0)
    return int(tile.get("yield_units", 0) or 0) + pending + 2 <= held


def _lb_choose(tile, inv, any_fert, day, hour, step, room, cls):
    if not isinstance(tile, dict):
        return None, 0
    kind = tile.get("kind")
    if kind == "WEED":
        return (["DIG"], 0) if cls == "pass" else (None, 0)
    if "animal" in tile and tile.get("animal") in _LB_ANIMALS:
        _, _, held = _LB_ANIMALS[tile["animal"]]
        y = int(tile.get("yield_units", 0) or 0)
        if not tile.get("cared_today") and tile.get("fed_today") and _lb_care_pays(tile, day):
            return ["CARE"], 0
        if y > 0 and hour >= 20 and _lb_produces_tonight(tile, day):
            bonus = int(tile.get("pending_care_bonus", 0) or 0) if tile.get("fed_today") else 0
            if y + 1 + bonus > held and y <= room:
                return ["HARVEST"], y
        if tile.get("fertilizer_available") and hour >= 22 and room >= 1:
            return ["COLLECT_FERTILIZER"], 1
        return None, 0
    if kind == "PLANT" and tile.get("crop") in _LB_CROPS:
        first, myd, interval, maxy, ongoing = _LB_CROPS[tile["crop"]]
        age = day - int(tile.get("planted_day", 0))
        y = int(tile.get("yield_units", 0) or 0)
        mls = int(tile.get("max_lifespan_step", -1))
        if y > 0 and mls >= 0 and step >= mls and age >= first and y <= room:
            return ["HARVEST"], y
        if not tile.get("watered_today"):
            fert_now = int(tile.get("fertilized_until_day", -1)) >= day
            if any_fert and not fert_now:
                in_window = (not ongoing) and (myd + 1) // 2 <= age <= myd and y < maxy
                eve = ongoing and age + 1 >= first
                if in_window or eve:
                    return None, 0
            return ["WATER"], 0
    return None, 0


def lb_recycle(obs, action, tel):
    """Rewrite PASS / certain no-op unit commands into in-place work."""
    player = int(_lb_get(obs, "player", 0) or 0)
    farms = _lb_get(obs, "farms") or []
    if player >= len(farms) or not isinstance(action, dict):
        return action
    farm = farms[player]
    private = _lb_get(obs, "private") or {}
    step = int(_lb_get(obs, "step", 0) or 0)
    day, hour = divmod(step, 24)
    if step >= 718:
        return action
    tiles = _lb_get(farm, "tiles") or []
    positions = [list(_lb_get(farm, "farmer"))] + [list(p) for p in (_lb_get(farm, "hands") or [])]
    invs = [dict(i or {}) for i in (_lb_get(private, "inventories") or [])]
    seeds = dict(_lb_get(private, "seeds") or {})
    shed = dict(_lb_get(private, "shed") or {})
    hands = list(action.get("hands") or [])
    cmds = [action.get("farmer") or ["PASS"]] + hands
    # hands with no command are idle too; pad so they can be given work
    while len(cmds) < len(positions):
        cmds.append(["PASS"])
    demand = {}
    for c in cmds:
        if isinstance(c, list) and len(c) >= 2 and c[0] == "PLANT":
            demand[c[1]] = demand.get(c[1], 0) + 1
    blocked = {k for k, n in demand.items() if n > int(seeds.get(k, 0) or 0)}
    any_fert = any(int(i.get("FERTILIZER", 0) or 0) > 0 for i in invs)
    carried = sum(max(0, int(n or 0)) for i in invs for n in i.values())
    room = _LB_SHED_CAP - _LB_SHED_MARGIN - sum(max(0, int(n or 0)) for n in shed.values()) - carried
    overlay = {}
    changed = False
    for i in range(min(len(cmds), len(positions))):
        x, y = int(positions[i][0]), int(positions[i][1])
        tile = overlay[(x, y)] if (x, y) in overlay else tiles[y][x]
        inv = invs[i] if i < len(invs) else {}
        cmd = cmds[i]
        cls = "pass" if (isinstance(cmd, list) and cmd and cmd[0] == "PASS") else "other"
        if _lb_noop(cmd, tile, inv, seeds, x, y, blocked, day):
            alt, gain = _lb_choose(tile, inv, any_fert, day, hour, step, room,
                                   "pass" if cls == "pass" else "noop")
            if alt is not None:
                cmds[i] = alt
                room -= gain
                changed = True
                tel[alt[0]] = tel.get(alt[0], 0) + 1
                tel["from_" + cls] = tel.get("from_" + cls, 0) + 1
                cmd = alt
            else:
                continue
        if cmd and cmd[0] not in _LB_MOVES and cmd[0] != "PASS":
            overlay[(x, y)] = _lb_effect(cmd, tile, inv, seeds, day, step, blocked)
    if not changed:
        return action
    out = dict(action)
    out["farmer"] = cmds[0]
    out["hands"] = cmds[1:len(positions)] if len(hands) < len(positions) - 1 else \
        cmds[1:1 + len(hands)]
    return out


def lb_wrap(parent):
    tel = {"lb_errors": 0, "lb_turns": 0, "lb_ms_max": 0.0}

    def labour_agent(observation, configuration=None):
        action = parent(observation, configuration)
        t0 = _lb_time.perf_counter()
        try:
            new = lb_recycle(observation, action, tel)
            if new is not action:
                tel["lb_turns"] += 1
            action = new
        except Exception:
            tel["lb_errors"] += 1
        ms = (_lb_time.perf_counter() - t0) * 1000.0
        if ms > tel["lb_ms_max"]:
            tel["lb_ms_max"] = ms
        return action

    labour_agent.telemetry = tel
    return labour_agent
# ---- END l2_labour ----


def build():
    """Agent L with the in-place recycler wrapped outside it."""
    from rl.candidate_l import l_stack
    return l_stack(outer=lb_wrap)
