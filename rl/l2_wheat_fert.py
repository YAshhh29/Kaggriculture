"""L2 candidate (wheat economy): spend carried fertilizer on young wheat, no hires, no purchases.

What the 2600-2700 teams that out-harvest A do (tools/analysis/l2_wheat_*):
every hand tends animals first (FEED, CARE, COLLECT_FERTILIZER), so it
carries 1-3 fertilizer, then works its own field route and, on reaching an
age-2 wheat plant, spends one turn on FERTILIZE immediately before the WATER.
Fertilized for ages 2-4, the plant ends at 6 units (5 if pulled at age 3)
instead of 4 (3). The teams do this 13.1 times a game; A 0.3 times.

A's crew is booked until hour 23, so that extra turn does not exist on A's
schedule. This layer finds it without new hands and without buying:

R1  A WATER on age-1 wheat adds nothing (wheat grows only on ages 2-4) and
    is not needed for survival when the plant was watered on day 0. A unit
    about to spend a turn on it while carrying spare fertilizer fertilizes
    instead (A's v9_fert does this only from day 14).
R2  A unit idling (PASS or a sure no-op) on young unfertilized wheat while
    carrying spare fertilizer fertilizes it.
R3  The teams' F->W pair. A unit carrying fertilizer whose tape waters an
    unfertilized age-2 wheat plant later today, and whose current command is
    skippable (PASS, a sure no-op, or COLLECT_FERTILIZER while it already
    carries one), skips that command and runs its own tape one step early up
    to the plant, where the freed turn becomes FERTILIZE; the tape's WATER
    then lands on its own step and the unit is back in sync. The early
    segment may only contain moves, WATER, HARVEST, DIG, FEED, CARE,
    COLLECT_FERTILIZER and FERTILIZE; any command that would be a no-op at
    the unit's real position, any other unit on those tiles one step either
    side, or any parent command that departs from the tape ends the run with
    one PASS, which puts the unit back in sync.

Every use is priced: gain x wheat price must beat the fertilizer's sale
price (twice that when a COLLECT is skipped) plus a margin, so the layer is
inert while fertilizer sells for more than the wheat it adds (days 1-13).
Market orders are never changed.

    python -m tools.eval.paired rl.l2_wheat_fert:build --label wheat-fert
"""

from __future__ import annotations

MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
EARLY_OK = {"WATER", "HARVEST", "DIG", "FEED", "CARE", "COLLECT_FERTILIZER", "FERTILIZE", "PASS"}
SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))

DEFAULTS = {
    "first_day": 6,
    "last_day": 28,
    "margin": 8.0,        # coins a use must clear
    "r1": True, "r2": True, "r3": True,
    "r3_max_segment": 12,
    "r3_last_hour": 21,
    "r3_collect": True,   # may skip a COLLECT_FERTILIZER to free the turn
}


def _cmd(action, idx):
    if idx == 0:
        return list(action.get("farmer") or ["PASS"])
    hands = action.get("hands") or []
    return list(hands[idx - 1]) if idx - 1 < len(hands) else ["PASS"]


def _set(action, idx, cmd):
    if idx == 0:
        action["farmer"] = list(cmd)
    else:
        hands = [list(h) for h in (action.get("hands") or [])]
        while len(hands) < idx:
            hands.append(["PASS"])
        hands[idx - 1] = list(cmd)
        action["hands"] = hands


def _tape_cmds(tape, t):
    if tape is None or not (0 <= t < len(tape)) or not isinstance(tape[t], dict):
        return [["PASS"]]
    a = tape[t]
    return [list(a.get("farmer") or ["PASS"])] + [list(h) for h in (a.get("hands") or [])]


def _step_pos(pos, cmd):
    if cmd and cmd[0] in MOVES:
        dx, dy = MOVES[cmd[0]]
        nx, ny = pos[0] + dx, pos[1] + dy
        if 0 <= nx < 10 and 0 <= ny < 10:
            return (nx, ny)
    return pos


def _position_same(a, b):
    """Two commands leave a unit on the same tile."""
    am = a[0] if a and a[0] in MOVES else None
    bm = b[0] if b and b[0] in MOVES else None
    return am == bm


def _young_wheat(tile, day):
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "WHEAT":
        return day - int(tile.get("planted_day", day))
    return None


def _gain(tile, day):
    """Extra wheat units one FERTILIZE now adds, if the tape waters every day to age 4."""
    age = _young_wheat(tile, day)
    if age is None or age > 3:
        return 0
    until = int(tile.get("fertilized_until_day", -1))
    watered = bool(tile.get("watered_today"))
    y = int(tile.get("yield_units", 1))
    future = [d for d in range(max(age, 2), 5) if not (d == age and watered)]
    plain = len(future)
    covered = sum(1 for d in future if day + (d - age) > until and d - age <= 2)
    return max(0, min(covered, 6 - y - plain))


def fert_inner(parent, env, **overrides):
    cfg = dict(DEFAULTS)
    cfg.update(overrides)
    noop = env["_is_noop"]
    chassis = env["_IMPL"].chassis
    states: dict = {}
    report = {"wf_r1": 0, "wf_r2": 0, "wf_r3_start": 0, "wf_r3_done": 0, "wf_r3_abort": 0,
              "wf_r3_collect_skips": 0, "wf_value": 0.0, "wf_errors": 0}

    def planned_fert(tape, t, idx):
        n = 0
        for k in range(t, (t // 24 + 1) * 24):
            c = _tape_cmds(tape, k)
            if idx < len(c) and c[idx] and c[idx][0] == "FERTILIZE":
                n += 1
        return n

    def forecast(tape, t, positions):
        """Tape positions of every unit at steps t..end of day (start: now)."""
        end = (t // 24 + 1) * 24
        track = {t: list(positions)}
        cur = list(positions)
        for k in range(t, end - 1):
            cmds = _tape_cmds(tape, k)
            cur = [_step_pos(p, cmds[i] if i < len(cmds) else ["PASS"]) for i, p in enumerate(cur)]
            track[k + 1] = list(cur)
        return track

    def act(obs, action, st):
        step = int(obs["step"])
        day, hour = step // 24, step % 24
        player = int(obs["player"])
        if st.get("day") != day:
            st.update(day=day, early={})
        if not (cfg["first_day"] <= day <= cfg["last_day"]):
            return action
        farm = obs["farms"][player]
        tiles = farm["tiles"]
        positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]
        invs = obs["private"].get("inventories") or []
        seeds = obs["private"].get("seeds") or {}
        prices = obs["market"]["prices"]
        p_w, p_f = float(prices["WHEAT"]), float(prices["FERTILIZER"])
        native = chassis.players.get(player) or {}
        tape = chassis.routes.get(native.get("route"))
        tape_now = _tape_cmds(tape, step)
        action = dict(action)
        spare = {}

        def spare_of(i):
            if i not in spare:
                have = int((invs[i] if i < len(invs) else {}).get("FERTILIZER", 0))
                spare[i] = have - planned_fert(tape, step, i)
            return spare[i]

        track = None
        # ---- units already running one step early (R3)
        for i, run in list(st["early"].items()):
            if i >= len(positions):
                st["early"].pop(i)
                continue
            mine = _cmd(action, i)
            tape_i = tape_now[i] if i < len(tape_now) else ["PASS"]
            pos = positions[i]
            if not _position_same(mine, tape_i):
                _set(action, i, ["PASS"])
                st["early"].pop(i)
                report["wf_r3_abort"] += 1
                continue
            if step == run["t2"] - 1:
                tile = tiles[pos[1]][pos[0]]
                ok = (pos == run["tile"] and _young_wheat(tile, day) == 2
                      and int(tile.get("planted_day", -9)) == run["birth"]
                      and int(tile.get("fertilized_until_day", -1)) < day
                      and int((invs[i] if i < len(invs) else {}).get("FERTILIZER", 0)) > 0)
                _set(action, i, ["FERTILIZE"] if ok else ["PASS"])
                report["wf_r3_done" if ok else "wf_r3_abort"] += 1
                if ok:
                    report["wf_value"] += run["value"]
                st["early"].pop(i)
                continue
            raw = _tape_cmds(tape, step + 1)
            nxt = raw[i] if i < len(raw) else ["PASS"]
            tile = tiles[pos[1]][pos[0]]
            inv = invs[i] if i < len(invs) else {}
            if nxt[0] not in MOVES and (nxt[0] not in EARLY_OK
                                        or (nxt[0] != "PASS" and noop(nxt, tile, inv, seeds, list(pos), 10))):
                _set(action, i, ["PASS"])
                st["early"].pop(i)
                report["wf_r3_abort"] += 1
                continue
            if track is None:
                track = forecast(tape, step, positions)
            dest = _step_pos(pos, nxt)
            crowd = any(j != i and j < len(track.get(k, [])) and track[k][j] == dest
                        for j in range(len(positions)) for k in (step, step + 1) if k in track)
            if crowd:
                _set(action, i, ["PASS"])
                st["early"].pop(i)
                report["wf_r3_abort"] += 1
                continue
            _set(action, i, nxt)

        for i, pos in enumerate(positions):
            # Only units that follow the route tape: the parent's own extra
            # workers (V219 tomatoes, input workers) carry fertilizer for jobs
            # of their own.
            if i in st["early"] or i >= len(tape_now):
                continue
            mine = _cmd(action, i)
            tile = tiles[pos[1]][pos[0]]
            inv = invs[i] if i < len(invs) else {}
            op = mine[0] if mine else "PASS"
            # ---- R1: age-1 WATER -> FERTILIZE
            if (cfg["r1"] and op == "WATER" and _young_wheat(tile, day) == 1
                    and not tile.get("watered_today")
                    and int(tile.get("consecutive_unwatered", 1)) == 0
                    and int(tile.get("fertilized_until_day", -1)) < day and spare_of(i) > 0):
                g = _gain(tile, day)
                if g * p_w - p_f >= cfg["margin"]:
                    _set(action, i, ["FERTILIZE"])
                    spare[i] -= 1
                    report["wf_r1"] += 1
                    report["wf_value"] += g * p_w - p_f
                    continue
            idle = op == "PASS" or (op not in MOVES and noop(mine, tile, inv, seeds, list(pos), 10))
            # ---- R2: idle on young unfertilized wheat -> FERTILIZE
            if cfg["r2"] and idle and spare_of(i) > 0 and _young_wheat(tile, day) is not None:
                g = _gain(tile, day)
                if g and g * p_w - p_f >= cfg["margin"]:
                    _set(action, i, ["FERTILIZE"])
                    spare[i] -= 1
                    report["wf_r2"] += 1
                    report["wf_value"] += g * p_w - p_f
                    continue
            # ---- R3: start a one-step-early run toward an age-2 WATER
            if not cfg["r3"] or hour > cfg["r3_last_hour"] or tape is None:
                continue
            tape_i = tape_now[i] if i < len(tape_now) else ["PASS"]
            if not _position_same(mine, tape_i):
                continue
            skip_collect = (cfg["r3_collect"] and op == "COLLECT_FERTILIZER"
                            and not noop(mine, tile, inv, seeds, list(pos), 10))
            if not (idle or skip_collect):
                continue
            carried = spare_of(i)
            if carried <= 0:
                continue
            if track is None:
                track = forecast(tape, step, positions)
            p = pos
            target = None
            for k in range(step + 1, min((day + 1) * 24, step + 1 + cfg["r3_max_segment"])):
                c = _tape_cmds(tape, k)
                ck = c[i] if i < len(c) else ["PASS"]
                if ck[0] == "WATER":
                    tl = tiles[p[1]][p[0]]
                    if (_young_wheat(tl, day) == 2 and not tl.get("watered_today")
                            and int(tl.get("fertilized_until_day", -1)) < day):
                        target = (k, p, tl)
                        break
                if ck[0] not in MOVES and ck[0] not in EARLY_OK:
                    break
                p = _step_pos(p, ck)
            if target is None:
                continue
            k2, tpos, tl = target
            if k2 == step + 1 and tpos != pos:
                continue
            gain = 2
            for k in range(k2 + 1, (day + 1) * 24):
                c = _tape_cmds(tape, k)
                if i < len(c) and c[i] and c[i][0] == "HARVEST":
                    q = track.get(k)
                    if q and i < len(q) and q[i] == tpos:
                        gain = 1
                        break
            value = gain * p_w - p_f - (p_f if skip_collect else 0.0)
            if value < cfg["margin"]:
                continue
            if k2 == step + 1:
                # The WATER comes next on this very tile: the skipped turn is
                # the FERTILIZE, nothing runs early.
                _set(action, i, ["FERTILIZE"])
                spare[i] = carried - 1
                report["wf_r3_done"] += 1
                report["wf_value"] += value
                if skip_collect:
                    report["wf_r3_collect_skips"] += 1
                continue
            raw = _tape_cmds(tape, step + 1)
            nxt = raw[i] if i < len(raw) else ["PASS"]
            if nxt[0] not in MOVES and (nxt[0] not in EARLY_OK
                                        or (nxt[0] != "PASS" and noop(nxt, tile, inv, seeds, list(pos), 10))):
                continue
            dest = _step_pos(pos, nxt)
            if any(j != i and j < len(track.get(k, [])) and track[k][j] == dest
                   for j in range(len(positions)) for k in (step, step + 1) if k in track):
                continue
            st["early"][i] = {"t2": k2, "tile": tpos, "birth": int(tl.get("planted_day", -1)),
                              "value": value}
            spare[i] = carried - 1
            _set(action, i, nxt)
            report["wf_r3_start"] += 1
            if skip_collect:
                report["wf_r3_collect_skips"] += 1
        return action

    def wheat_fert_agent(observation, configuration=None):
        step = int(observation["step"])
        player = int(observation["player"])
        st = states.get(player)
        if st is None or step <= st["step"]:
            st = states[player] = {"step": -1, "day": -1, "early": {}}
        st["step"] = step
        action = parent(observation, configuration)
        try:
            if isinstance(action, dict):
                return act(observation, action, st)
        except Exception:
            report["wf_errors"] += 1
            st["early"] = {}
        return action

    wheat_fert_agent.telemetry = report
    return wheat_fert_agent


def _stack(**overrides):
    from rl.candidate_l import l_stack
    return l_stack(inner=lambda agent, env: fert_inner(agent, env, **overrides))


def build():
    return _stack()


def build_r12():
    """Zero-turn rules only (R1 + R2)."""
    return _stack(r3=False)


def build_nocollect():
    """R3 frees its turn only from idle or no-op commands, never a COLLECT."""
    return _stack(r3_collect=False)
