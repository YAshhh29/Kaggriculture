# ---- BEGIN market_front (Agent L's own layer) ----
# Queue order in a mirror-dominated ladder.
#
# The engine settles market orders slot by slot: for slot i it takes both
# players' i-th orders and trades them one unit at a time at a shared price.
# So a sale in an earlier slot sells its whole quantity before a rival's sale
# of the same item in a later slot, at the undamaged price, and the rival
# sells into the damage. The public lineage -- and exact copies of Agent A,
# which the ladder is full of -- put their orders in the same slots every
# time. This layer reorders the parent's own orders (never their quantities)
# so the orders whose price damage is largest land in the earliest slots:
#
# * orders that do not trade against the market (HIRE, BUY_SEED, BUY_ANIMAL,
#   BUY_LAND) and empty slots move behind every SELL / BUY_PRODUCT;
# * among SELL / BUY_PRODUCT orders, the permutation is chosen to maximise
#   the damage we avoid against a copy of ourselves (whose slots are the
#   parent's slots), breaking ties by putting larger damage earlier.
#
# A sale moved earlier can only get more money for later purchases in the
# same turn, so reordering never makes a purchase fail that would have
# succeeded.

import itertools as _mf_it
import math as _mf_math

_MF_PARAMS = {   # engine MARKET_PARAMS
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
_MF_I0 = 10000
_MF_PRICED = ("SELL", "BUY_PRODUCT")


def _mf_shape(func, x, T):
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return _mf_math.sqrt(x)
    if func == "log":
        return _mf_math.log(1.0 + x)
    if func == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def _mf_price(item, inventory):
    base, T, below, bt, above, at = _MF_PARAMS[item]
    if inventory < _MF_I0:
        amp = bt * base / _mf_shape(below, T, T)
        price = base + amp * _mf_shape(below, _MF_I0 - inventory, T)
    else:
        amp = at * base / _mf_shape(above, T, T)
        price = base - amp * _mf_shape(above, inventory - _MF_I0, T)
    return max(1, int(round(price)))


def _mf_damage(order, inventory):
    """Coins a same-item rival order loses per unit when this order goes first,
    times our units: the price move our own units cause."""
    try:
        op, item, n = order[0], order[1], int(order[2])
    except (IndexError, TypeError, ValueError):
        return 0.0
    if item not in _MF_PARAMS or n <= 0:
        return 0.0
    inv = int(inventory.get(item, _MF_I0))
    if op == "SELL":
        move = _mf_price(item, inv) - _mf_price(item, inv + n)
    else:
        move = _mf_price(item, inv - 1 - n) - _mf_price(item, inv - 1)
    return float(n * abs(move))


def _mf_keep_sell_first(orders, new, items, report=None):
    """Put back in front any SELL of `items` that the parent queued before a
    BUY_PRODUCT of the same item: with the shed near full, a buy moved ahead of
    the sale fills short (N's day-27 tomato fertilizer: one tile unfertilized)."""
    for s in [o for o in orders if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] in items]:
        later = [o for o in orders[orders.index(s) + 1:] if isinstance(o, list) and len(o) >= 3
                 and o[0] == "BUY_PRODUCT" and o[1] == s[1]]
        if not later:
            continue
        first = min(new.index(b) for b in later)
        if new.index(s) > first:
            new.remove(s)
            new.insert(first, s)
            if report is not None:
                report["sell_first_repairs"] = report.get("sell_first_repairs", 0) + 1
    return new


def mf_reorder(market, inventory, report=None, sell_first=()):
    orders = list(market or [])
    priced = [(i, o) for i, o in enumerate(orders)
              if isinstance(o, list) and len(o) >= 3 and o[0] in _MF_PRICED]
    other = [o for o in orders if o and not (isinstance(o, list) and len(o) >= 3
                                              and o[0] in _MF_PRICED)]
    if not priced:
        return orders
    weights = [_mf_damage(o, inventory) for _, o in priced]
    slots = [i for i, _ in priced]
    n = len(priced)
    if n <= 7:
        best, best_key = None, None
        for perm in _mf_it.permutations(range(n)):
            # perm[k] = which priced order goes to new slot k
            gain = sum(weights[j] * ((slots[j] > k) - (slots[j] < k))
                       for k, j in enumerate(perm))
            tie = sum(weights[j] * (n - k) for k, j in enumerate(perm))
            key = (round(gain, 6), round(tie, 6), tuple(-j for j in perm))
            if best_key is None or key > best_key:
                best, best_key = perm, key
    else:
        best = sorted(range(n), key=lambda j: -weights[j])
    new = [priced[j][1] for j in best] + other
    if sell_first:
        new = _mf_keep_sell_first(orders, new, sell_first, report)
    if report is not None and new != orders:
        report["reordered_turns"] = report.get("reordered_turns", 0) + 1
    return new


def _mf_stock(observation, action, item):
    """Units of `item` the shed will hold when this step's market runs: the
    shed, plus what our units drop or place there this step (units act first)."""
    player = int(observation["player"])
    private = observation["private"]
    stock = int((private.get("shed") or {}).get(item, 0))
    invs = private.get("inventories") or []
    commands = [action.get("farmer")] + list(action.get("hands") or [])
    for i, c in enumerate(commands):
        if not (isinstance(c, list) and c) or i >= len(invs):
            continue
        carried = int((invs[i] or {}).get(item, 0))
        if c[0] == "DROP" or (c[0] == "PLACE" and len(c) >= 2 and c[1] == item):
            stock += carried if c[0] == "DROP" else min(carried, int(c[2]) if len(c) >= 3 else 1)
    return stock


def _mf_cap_counters(observation, market, report=None):
    """A same-step counter pair (SELL x n and BUY_PRODUCT x n) is a round trip
    that assumes n units in stock. With less, the sale fills short and the
    purchase buys the difference outright: in three live games the base plan's
    step-3 pair (SELL 20 / BUY 20 wheat, 5 in stock) spent 432 of a 1,043-coin
    opening budget, the opening tape ran out of cash and every game was lost by
    15-20k. Cap the buy-back at what the sale can fill."""
    out = [list(o) if isinstance(o, list) else o for o in market]
    sells = {}
    for o in out:
        if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
            try:
                sells[o[1]] = sells.get(o[1], 0) + int(o[2])
            except (TypeError, ValueError):
                pass
    for o in out:
        if not (isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_PRODUCT"):
            continue
        item = o[1]
        try:
            n = int(o[2])
        except (TypeError, ValueError):
            continue
        if n <= 0 or sells.get(item, 0) != n:
            continue
        stock = observation.get("_mf_stock_" + item)
        if stock is not None and stock < n:
            o[2] = max(0, int(stock))
            if report is not None:
                report["counter_caps"] = report.get("counter_caps", 0) + 1
                report["counter_units_saved"] = report.get("counter_units_saved", 0) + n - o[2]
    return out


def mf_wrap(parent, sell_first=(), cap_counters=False):
    report = {"reordered_turns": 0, "errors": 0}

    def front_agent(observation, configuration=None):
        action = parent(observation, configuration)
        try:
            if cap_counters and isinstance(action, dict) and action.get("market"):
                market = list(action["market"])
                items = {o[1] for o in market if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_PRODUCT"}
                view = {"_mf_stock_" + it: _mf_stock(observation, action, it) for it in items}
                capped = _mf_cap_counters(view, market, report)
                if capped != market:
                    action = dict(action, market=capped)
        except Exception:
            report["errors"] += 1
        try:
            if isinstance(action, dict) and action.get("market"):
                inventory = observation["market"]["inventory"]
                new = mf_reorder(action["market"], inventory, report, sell_first)
                if new != action["market"]:
                    action = dict(action, market=new)
        except Exception:
            report["errors"] += 1
        return action

    front_agent.telemetry = report
    return front_agent
# ---- END market_front ----
