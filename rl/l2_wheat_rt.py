"""L2 candidate (wheat economy): the town-draw wheat round trip.

Every 4 steps (step % 4 == 0) the town eats wheat right after that step's
market: each wheat shop instance (BAKERY, PIZZA_SHOP, BRUNCH_SPOT,
ICE_CREAM_SHOP, FARMERS_MARKET) removes one unit, and the town centre one
more at step % 24 == 0. Wheat is priced by market inventory, so after a draw
of D units every unit is worth about D / (2 sqrt(deficit)) more. Buying q
wheat at step s (before the draw) and selling the same q at s + 1 (after it)
earns  sum_j p(I - D - j) - p(I - j)  with nothing else changing: BUY_PRODUCT
quotes at the post-buy inventory, so a round trip against an unchanged market
nets exactly zero and the draw is the whole profit.

Measured on the 70 faithful 2600-2700 team games (tools/analysis/l2_wheat_*):
30 teams do this (61,296 units bought at step % 4 == 0, 57,418 sold one step
later) and earn $0.19 a unit; Agent A does it only in its opening tapes.
That is where those teams' "extra" wheat buys and sells come from: their net
wheat sold is the same as A's.

The parent never sees the round trip: at the sell step it is shown the shed
without our wheat and the market inventory without our purchase, so its own
decisions are the ones it makes without this layer. The layer never buys when
the purchase could starve a parent order (cash), never lets bought wheat push
a same-turn DROP over the 100-unit shed (a DROP discards overflow), and only
trades when the exact engine price table says the draw pays.

    python -m tools.eval.paired rl.l2_wheat_rt:build --label wheat-rt60
"""

from __future__ import annotations

from rl.market_front import _mf_price

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

    def buy_order(obs, action, step):
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
        if gain < max(cfg["min_profit"], cfg["min_per_unit"] * q):
            report["rt_skip_profit"] += 1
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
            st = states[player] = {"step": -1, "pending": 0, "pend_step": -1}
        st["step"] = step
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
            if pending > 0:
                return sell_order(action, pending)
            if cfg["first_step"] <= step <= cfg["last_step"] and step % 4 == 0:
                action, q = buy_order(observation, action, step)
                if q:
                    st["pending"], st["pend_step"] = q, step
        except Exception:
            report["rt_errors"] += 1
        return action

    wheat_rt_agent.telemetry = report
    return wheat_rt_agent


def _stack(**overrides):
    from rl.candidate_l import l_stack
    return l_stack(inner=lambda agent, env: rt_inner(agent, env, **overrides))


def build():
    return _stack()


def build_q30():
    return _stack(q_max=30)


def build_q90():
    return _stack(q_max=90)
