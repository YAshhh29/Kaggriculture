"""L2 candidate (wheat economy): the town-draw wheat round trip.

Every step % 4 == 0 the town eats wheat right after the market (one unit per
wheat shop, one more at step % 24 == 0). Wheat is priced by market inventory,
so q units bought before the draw and sold one step later earn the price rise
the draw causes; against an unchanged market the trip nets exactly zero. The
parent never sees the trip (its view of the shed and market excludes our
wheat). The layer never buys when the purchase could starve a parent order or
overflow the shed, and trades only when the engine's price table says it pays.

    python -m tools.eval.paired stack.l2_wheat_rt:build --label wheat-rt60
"""

from __future__ import annotations

from stack.market_front import _mf_price

WHEAT_SHOPS = ("BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "ICE_CREAM_SHOP", "FARMERS_MARKET")
_SEED = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
_ANIMAL = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
_LAND = (1000, 2000, 4000)
MAX_ORDERS = 10

DEFAULTS = {
    "q_max": 60,          # units per round trip
    "q_min": 10,          # smaller trips are skipped
    "first_step": 144,    # day 6: the route is chosen and cash slack returns
    "last_step": 716,     # the sale lands on step <= 717
    "reserve": 1500.0,    # cash kept free after every parent purchase
    "min_profit": 2.0,    # coins per trip, from the exact price table
    "min_per_unit": 0.04,
    "room_margin": 10,
    # Opponent-aware pricing (0 = off, the L2/L3 layer). The opponent's net
    # wheat sold in each trip window (the draw step and the next) follows from
    # the public inventory, the town draw and our own orders; a trip is priced
    # against each of the last `flow_window` windows (see _flow_gain).
    "flow_window": 0,
    "flow_stat": "mean",
    "q_quiet": 0,         # N3: trip size while the opponent's last windows are all quiet
    "quiet_windows": 8,
    "quiet_units": 2,     # gross opponent units a window still counted as quiet
    # N3: the pre-draw trap. Some 2400+ forks buy X wheat at step % 4 == 3 and
    # sell X in their last queue slot at the draw step, after our (and the base
    # plan's own) draw-step round-trip purchase has walked the price up; the trip
    # then sells after the draw into X extra units. 185 such events in N's 29
    # games against 2400+ rivals; our 91 bitten trips lost 9,586. The rival's net
    # purchase at s-1 is exact from public data (no draw on a %3 step). When it is
    # at least `trap_guard` units: skip our trip, strip the parent's draw-step
    # wheat purchases of at least `trap_min_order`, and cut its next sale by as much.
    "trap_guard": 0,
    "trap_min_order": 10,
    # N4: a rival running its own round trip at the same draw step. The engine
    # settles the two purchases unit by unit, so the smaller trip takes the
    # cheap end of both curves and our units beyond the rival's size buy at the
    # top and sell at the bottom (Ilya & Yurnero, 45 a trip to our 60: -3.3k
    # on wheat). The rival's draw-step purchase is exact from public data; the
    # trip is sized on the median of its last `lock_windows` purchases, unit by
    # unit (`_lock_profit`). lock_after: our purchase settles after theirs
    # (stack/draw_last.py pads it to the last slot).
    "lockstep": 0,
    "lock_windows": 8,
    "lock_after": False,
    # N7: a sandwicher sells into the draw step right after our purchase (its
    # slot 2) and buys back the next step right after our sale (slot 9), then
    # repeats: it trades against our trip's own price impact ("42", live 9-29:
    # -5.9k on wheat with identical farms). Netting its draw-step sale against
    # its next-step purchase hides it (the window looks flat), but only the sale
    # lands between our buy and our sale. With sandwich on, a window where the
    # rival net-sold at the draw and net-bought the next step counts the sale.
    "sandwich": False,  # or "median": ignore one-off sales (a harvest sold once)
}


def _fib(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def draw_units(shops, step: int) -> int:
    """Wheat the town removes after this step's market."""
    if step % 4:
        return 0
    d = sum(1 for s in shops if s in WHEAT_SHOPS)
    if step % 24 == 0:
        d += 1
    return d


def trip_profit(inventory: int, q: int, d: int) -> int:
    """Exact coins from buying q before a draw of d and selling q after it."""
    return sum(_mf_price("WHEAT", inventory - d - j) - _mf_price("WHEAT", inventory - j)
               for j in range(1, q + 1))


def purchase_cost(obs, market) -> float:
    """Upper bound on what the parent's own orders this turn can spend."""
    farm = obs["farms"][int(obs["player"])]
    inv = obs["market"]["inventory"]
    hires = int(farm.get("hires_today", 0))
    quads = len(farm.get("unlocked_quadrants") or ["NW"])
    cost = 0.0
    for o in market or []:
        if not isinstance(o, list) or not o:
            continue
        op = o[0]
        if op == "HIRE":
            cost += _fib(hires)
            hires += 1
        elif op == "BUY_LAND":
            if quads - 1 < len(_LAND):
                cost += _LAND[quads - 1]
                quads += 1
        elif op in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT") and len(o) >= 3:
            try:
                n = max(0, int(o[2]))
            except (TypeError, ValueError):
                continue
            if op == "BUY_SEED":
                cost += _SEED.get(o[1], 100) * n
            elif op == "BUY_ANIMAL":
                cost += _ANIMAL.get(o[1], 500) * n
            elif o[1] in ("WHEAT", "FERTILIZER"):
                cost += (_mf_price(o[1], int(inv.get(o[1], 10000)) - n) + 1) * n
    return cost


def shed_room(env, obs, action, step: int) -> int:
    """Units the shed can take for a round trip without risking a DROP overflow.

    Counts the shed after this turn's unit actions (the parent's own
    projection), the parent's purchases, and the full cargo (+6) of every unit
    whose tape command next turn is a DROP, since that DROP lands before our
    sale and a DROP discards what does not fit."""
    player = int(obs["player"])
    view = env["FarmView"](obs)
    proj = env["projected_shed"](action, view)
    total = sum(max(0, int(v)) for v in proj.values())
    buys = 0
    for o in action.get("market") or []:
        if isinstance(o, list) and len(o) >= 3 and o[0] in ("BUY_PRODUCT", "BUY_ANIMAL"):
            try:
                buys += max(0, int(o[2]))
            except (TypeError, ValueError):
                pass
    chassis = env["_IMPL"].chassis
    native = chassis.players.get(player) or {}
    tape = chassis.routes.get(native.get("route"))
    nxt = tape[step + 1] if tape is not None and step + 1 < len(tape) else {}
    cmds = [nxt.get("farmer") or ["PASS"]] + list(nxt.get("hands") or [])
    invs = obs["private"].get("inventories") or []
    drops = 0
    for i, c in enumerate(cmds):
        if c and c[0] == "DROP" and i < len(invs):
            drops += sum(max(0, int(v)) for v in (invs[i] or {}).values()) + 6
    return 100 - total - buys - drops


def our_net_wheat(obs, action) -> int:
    """Wheat our final orders take off the market (buys minus filled sells).

    The engine fills a queue slot by slot; a SELL fills only while the shed
    holds wheat, so sells are capped by the shed after the earlier slots."""
    have = int((obs["private"].get("shed") or {}).get("WHEAT", 0))
    net = 0
    for o in (action.get("market") or [])[:MAX_ORDERS]:
        if not isinstance(o, list) or len(o) < 3 or o[1] != "WHEAT":
            continue
        try:
            n = max(0, int(o[2]))
        except (TypeError, ValueError):
            continue
        if o[0] == "BUY_PRODUCT":
            net += n
            have += n
        elif o[0] == "SELL":
            n = min(n, max(0, have))
            net -= n
            have -= n
    return net


def _flow_gain(base: int, q: int, d: int, windows, stat: str = "mean") -> float:
    """Mean trip profit if the opponent again sells what it sold in each window.

    Their net sales between our buy and our sale land before or alongside our
    sale, so a window with w units sold works like a draw of d - w. Windows in
    which they bought count as zero: this never trades more than the plain
    layer. With stat="median" the trip is priced against the median window,
    so only an opponent that sells into most windows stops the trips."""
    if stat == "median":
        w = sorted(windows)[len(windows) // 2]
        return trip_profit(base, q, d - max(0, w))
    return sum(trip_profit(base, q, d - max(0, w)) for w in windows) / len(windows)


def _lock_profit(inventory: int, q: int, d: int, k: int, after: bool = False) -> float:
    """Exact coins from our q-unit trip when a rival buys k at the draw step and
    sells k at the next, both settled unit by unit with ours (lockstep); with
    after, our purchase settles once the rival's k are bought."""
    cost = 0.0
    for j in range(1, q + 1):
        if after or j > k:
            before = inventory - k - (j - 1)
        else:
            before = inventory - 2 * (j - 1)
        cost += _mf_price("WHEAT", before - 1)
    low = inventory - q - k - d
    rev = 0.0
    for j in range(1, q + 1):
        before = low + 2 * (j - 1) if j <= k else low + k + (j - 1)
        rev += _mf_price("WHEAT", before)
    return rev - cost


def _strip_wheat_buys(action, min_order: int):
    """Drop the queue's wheat purchases of at least min_order units; (action, units)."""
    market, stripped = [], 0
    for o in action.get("market") or []:
        if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
            try:
                n = int(o[2])
            except (TypeError, ValueError):
                n = 0
            if n >= min_order:
                stripped += n
                continue
        market.append(o)
    return (dict(action, market=market), stripped) if stripped else (action, 0)


def _cut_wheat_sale(action, n: int):
    """Reduce the queue's wheat sales by n units (the purchase we stripped)."""
    market = []
    for o in action.get("market") or []:
        if n > 0 and isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT":
            try:
                q = int(o[2])
            except (TypeError, ValueError):
                q = 0
            cut = min(q, n)
            n -= cut
            if q - cut > 0:
                market.append(["SELL", "WHEAT", q - cut])
            continue
        market.append(o)
    return dict(action, market=market)


def _masked(obs, q: int):
    """The observation without our round-trip wheat (shed) and purchase (market)."""
    obs2 = dict(obs)
    private = dict(obs["private"])
    shed = dict(private.get("shed") or {})
    have = int(shed.get("WHEAT", 0))
    shed["WHEAT"] = have - min(have, q)
    private["shed"] = shed
    obs2["private"] = private
    market = dict(obs["market"])
    inv = dict(market["inventory"])
    prices = dict(market["prices"])
    inv["WHEAT"] = int(inv["WHEAT"]) + q
    prices["WHEAT"] = _mf_price("WHEAT", inv["WHEAT"])
    market["inventory"] = inv
    market["prices"] = prices
    obs2["market"] = market
    return obs2


def rt_inner(parent, env, **overrides):
    cfg = dict(DEFAULTS)
    cfg.update(overrides)
    states: dict = {}
    report = {"rt_trips": 0, "rt_units": 0, "rt_expected": 0.0, "rt_sells": 0,
              "rt_merged_sells": 0, "rt_unsold": 0, "rt_skip_cash": 0, "rt_skip_room": 0,
              "rt_skip_slots": 0, "rt_skip_profit": 0, "rt_errors": 0}
    window = int(cfg["flow_window"])
    if window > 0:
        report.update({"rt_skip_flow": 0, "rt_windows": [], "rt_flow_errors": 0,
                       "rt_trap_skips": 0, "rt_trap_stripped": 0, "rt_trap_cut": 0})

    def buy_order(obs, action, step, windows=(), gross=(), kbuys=()):
        market = [list(o) for o in action.get("market") or []]
        if len(market) >= MAX_ORDERS:
            report["rt_skip_slots"] += 1
            return action, 0
        d = draw_units(obs["town"]["unlocked_shops"], step)
        if d <= 0:
            return action, 0
        farm = obs["farms"][int(obs["player"])]
        inv = int(obs["market"]["inventory"]["WHEAT"])
        net_parent = 0
        for o in market:
            if len(o) >= 3 and o[1] == "WHEAT":
                n = max(0, int(o[2]))
                net_parent += n if o[0] == "BUY_PRODUCT" else (-n if o[0] == "SELL" else 0)
        base = inv - net_parent
        q = int(cfg["q_max"])
        # N3: size up only while the opponent trades no wheat around the draw --
        # gross units, since a rival's own round trip nets to zero in a window
        # (bigger trips lost against rivals that trade: BorisV, Zenith Ye)
        if cfg["q_quiet"] and len(gross) >= cfg["quiet_windows"] and                 all(g <= cfg["quiet_units"] for g in list(gross)[-cfg["quiet_windows"]:]):
            q = int(cfg["q_quiet"])
        free = float(farm["money"]) - purchase_cost(obs, market) - float(cfg["reserve"])
        while q >= cfg["q_min"] and q * (_mf_price("WHEAT", base - q) + 1) > free:
            q -= 5
        if q < cfg["q_min"]:
            report["rt_skip_cash"] += 1
            return action, 0
        room = shed_room(env, obs, action, step) - int(cfg["room_margin"])
        q = min(q, room)
        if q < cfg["q_min"]:
            report["rt_skip_room"] += 1
            return action, 0
        gain = trip_profit(base, q, d)
        if cfg["lockstep"] and len(kbuys) >= 3:
            k = sorted(kbuys)[len(kbuys) // 2]
            if k >= 5:
                best_q, best = 0, None
                for cand in sorted(set(list(range(int(cfg["q_min"]), q + 1, 5)) + [q])):
                    g = _lock_profit(base, cand, d, k, cfg["lock_after"])
                    if g >= max(cfg["min_profit"], cfg["min_per_unit"] * cand) and (best is None or g > best):
                        best_q, best = cand, g
                if not best_q:
                    report["rt_skip_lock"] = report.get("rt_skip_lock", 0) + 1
                    return action, 0
                if best_q != q:
                    report["rt_lock_resized"] = report.get("rt_lock_resized", 0) + 1
                q, gain = best_q, trip_profit(base, best_q, d)
        if gain < max(cfg["min_profit"], cfg["min_per_unit"] * q):
            report["rt_skip_profit"] += 1
            return action, 0
        if windows:
            gain = _flow_gain(base, q, d, windows, cfg["flow_stat"])
            if gain < max(cfg["min_profit"], cfg["min_per_unit"] * q):
                report["rt_skip_flow"] += 1
                return action, 0
        market.append(["BUY_PRODUCT", "WHEAT", q])
        report["rt_trips"] += 1
        report["rt_units"] += q
        report["rt_expected"] += gain
        return dict(action, market=market), q

    def sell_order(action, q):
        market = [list(o) for o in action.get("market") or []]
        if len(market) < MAX_ORDERS:
            market.append(["SELL", "WHEAT", q])
            report["rt_sells"] += 1
        else:
            for o in market:
                if len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT":
                    o[2] = int(o[2]) + q
                    report["rt_merged_sells"] += 1
                    break
            else:
                report["rt_unsold"] += 1   # stays in the shed; the parent owns it from now on
        return dict(action, market=market)

    def wheat_rt_agent(observation, configuration=None):
        step = int(observation["step"])
        player = int(observation["player"])
        st = states.get(player)
        if st is None or step <= st["step"]:
            st = states[player] = {"step": -1, "pending": 0, "pend_step": -1,
                                   "prev": None, "flow": {}, "windows": [], "gross": [], "kbuys": []}
        st["step"] = step
        if window > 0:
            watch(observation, st, step)
        pending = st["pending"] if st["pend_step"] == step - 1 else 0
        st["pending"] = 0
        view = observation
        if pending > 0:
            try:
                view = _masked(observation, pending)
            except Exception:
                report["rt_errors"] += 1
                view = observation
        action = parent(view, configuration)
        try:
            owe, st["owe"] = st.get("owe"), None
            if owe and owe[0] == step:
                action = _cut_wheat_sale(action, owe[1])
                report["rt_trap_cut"] += owe[1]
            trap = (cfg["trap_guard"] and window > 0 and step % 4 == 0
                    and st["flow"].get(step - 1, 0) <= -cfg["trap_guard"])
            if pending > 0:
                action = sell_order(action, pending)
            elif trap:
                report["rt_trap_skips"] += 1
                action, stripped = _strip_wheat_buys(action, cfg["trap_min_order"])
                if stripped:
                    st["owe"] = (step + 1, stripped)
                    report["rt_trap_stripped"] += stripped
            elif cfg["first_step"] <= step <= cfg["last_step"] and step % 4 == 0:
                action, q = buy_order(observation, action, step,
                                      st["windows"][-window:] if window > 0 else (),
                                      st["gross"][-window:] if window > 0 else (),
                                      st["kbuys"][-int(cfg["lock_windows"]):] if window > 0 else ())
                if q:
                    st["pending"], st["pend_step"] = q, step
        except Exception:
            report["rt_errors"] += 1
        if window > 0:
            try:
                st["prev"] = (step, int(observation["market"]["inventory"]["WHEAT"]),
                              our_net_wheat(observation, action),
                              draw_units(observation["town"]["unlocked_shops"], step))
            except Exception:
                report["rt_flow_errors"] += 1
                st["prev"] = None
        return action

    def watch(obs, st, step):
        """Record what the opponent sold last step, and close a trip window."""
        prev, st["prev"] = st["prev"], None
        if prev is None or prev[0] != step - 1:
            return
        try:
            inv = int(obs["market"]["inventory"]["WHEAT"])
        except Exception:
            report["rt_flow_errors"] += 1
            return
        # inventory change = their net sold - our net bought - the town draw
        st["flow"][step - 1] = inv - prev[1] + prev[2] + prev[3]
        s = step - 2
        if s % 4 == 0 and s in st["flow"] and s + 1 in st["flow"]:
            a, b = st["flow"].pop(s), st["flow"].pop(s + 1)
            w = a + b
            if cfg["sandwich"] and a > 0 and b < 0:
                w = a
                report["rt_sandwich_windows"] = report.get("rt_sandwich_windows", 0) + 1
            st["windows"].append(w)
            st["gross"].append(abs(a) + abs(b))
            st["kbuys"].append(max(0, -a))      # the rival's own draw-step purchase
            report["rt_windows"].append((s, w))
        st["flow"] = {k: v for k, v in st["flow"].items() if k >= step - 2}

    wheat_rt_agent.telemetry = report
    return wheat_rt_agent


def _stack(**overrides):
    from stack.candidate_l import l_stack
    return l_stack(inner=lambda agent, env: rt_inner(agent, env, **overrides))


def build():
    return _stack()


def build_q30():
    return _stack(q_max=30)


def build_q90():
    return _stack(q_max=90)
