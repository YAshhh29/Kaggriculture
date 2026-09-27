"""Agent M, part 1: a seller that learns the opponent's selling clock in-game.

Where L loses close games (2026-09-27, 51 close losses of L2/L3/L4): from day
24 on, the opponent sold goods we were holding in the shed at better prices
than we later got, worth +460 a game to them (strawberry +329, milk +122) --
more than the median losing margin (-581). Against PeterDreamHan (-215) the
pattern is plain: every other day both farms have a lot of ~21 strawberries in
the shed from hour 0; they sell theirs at hour 1 (60 down to 22), ours waits
for the parent's schedule at hour 12 and sells into their supply (36 down to
1). The same repeats on days 24, 26 and 28.

The opponent's sales of every good are measured exactly each step (inventory
change + what the town ate - what we sold), so the clock is visible: this
layer keeps each good's recent "lots" (one-step sales of at least `min_lot`
units). Both farms run near-identical plans, so when we hold a lot, they hold
one too; from `lead` steps before the earliest hour at which they sold such a
lot in the last few days,
it sells what we hold before they do, at the first step with a free order
slot (A fills all ten at hour 0 with the day's hires), first in our queue,
until they sell that day's lot.

It stands down while the opponent shadow is in sync with a known program (the
shadow's exact early sales know better) and before `first_step`.

    python -m tools.eval.live_replay run --agent factory --package rl.l2_combo:m1 ...
"""

from __future__ import annotations

ITEMS = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
MAX_ORDERS = 10
LAST_STEP = 718

DEFAULTS = {
    "first_step": 480,    # day 20
    "min_lot": 5,         # opponent units in one step that count as a lot
    "min_stock": 4,       # our shed units worth racing for
    "lead": 1,            # steps before their earliest hour
    "late": 2,            # keep trying this long after it (a full order list at hour 0:
                          # A hires the day's crew then)
    "size_frac": 0.5,     # their lot must be at least half our stock
    "value_check": False, # M2: race only if their lot outweighs what the town eats
                          # before the hour we usually sell (else waiting is better)
    "own_default": 12,    # steps ahead assumed for our sale before we have sold one
    "before_us": False,   # M7: race only if their most recent comparable lot came at an
                          # earlier hour than the one our own stack sells such lots at
    "after_beaten": False,  # M5: race a good only after the opponent has sold a lot of
                            # it while we held one (the loss mechanism, seen in this game)
    "pace_check": 0.0,    # M4: race only if at least this share of their units of the
                          # good in the last `pace_steps` came in comparable lots
    "pace_steps": 48,
    "require_own_lot": False,  # M3: race only goods our own stack sells as whole lots
                               # (a stack that sells a few units an hour keeps the
                               # price up; dumping the lot first crashes it)
    "recent_days": 3,
    "items": ITEMS,
}


def eaten(shops, step: int, item: str) -> int:
    """Units of `item` the town removes after the market at `step`."""
    n = 0
    if step % 4 == 0:
        for s in shops:
            goods = SHOPS.get(s, ())
            if item in goods:
                n += 2 if len(goods) == 1 else 1
    if step % 24 == 0:
        n += 1
    return n


def our_sold(obs, action, item: str) -> int:
    """Upper bound on the units of `item` our orders sell this step (shed plus
    what the workers carry, since a DROP lands before the market)."""
    private = obs["private"]
    have = int((private.get("shed") or {}).get(item, 0))
    have += sum(int((inv or {}).get(item, 0)) for inv in private.get("inventories") or [])
    n = 0
    for o in (action.get("market") or [])[:MAX_ORDERS]:
        if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == item:
            try:
                n += max(0, int(o[2]))
            except (TypeError, ValueError):
                pass
    return min(n, have)


def their_hour(lots, stock: int, step: int, cfg) -> int | None:
    """The hour of day at which the opponent sells a lot like ours, or None.

    Both farms grow the same crops on the same cycle, so a lot in our shed
    means one in theirs; what we learn from them is when they sell it: the
    earliest hour of their last few lots at least `size_frac` of our stock,
    within the last `recent_days`."""
    size = max(cfg["min_lot"], stock * cfg["size_frac"])
    big = [s for s, u in lots if u >= size and s >= step - 24 * cfg["recent_days"]]
    if not big:
        return None
    return min(s % 24 for s in big[-3:])


def their_lot(lots, stock: int, step: int, cfg) -> int:
    """Units in their most recent lot comparable to ours (0 if none)."""
    size = max(cfg["min_lot"], stock * cfg["size_frac"])
    big = [u for s, u in lots if u >= size and s >= step - 24 * cfg["recent_days"]]
    return big[-1] if big else 0


def our_hour(sales, stock: int, cfg):
    """The hour of day at which our own stack sold its last comparable lot."""
    size = max(cfg["min_lot"], stock * cfg["size_frac"])
    big = [s for s, u in sales if u >= size]
    return big[-1] % 24 if big else None


def m_sell_wrap(agent, **overrides):
    cfg = dict(DEFAULTS)
    cfg.update(overrides)
    items = tuple(cfg["items"])
    states: dict = {}
    report = {"m_sell_orders": 0, "m_sell_units": 0, "m_sell_no_slot": 0, "m_sell_shadow_skips": 0,
              "m_sell_value_skips": 0, "m_sell_own_skips": 0, "m_sell_pace_skips": 0, "m_sell_unbeaten_skips": 0, "m_sell_later_skips": 0, "m_sell_errors": 0, "m_sell_log": []}

    def watch(obs, st, step):
        prev, st["prev"] = st["prev"], None
        if prev is None or prev[0] != step - 1:
            return
        inv = obs["market"]["inventory"]
        for item in items:
            sold = int(inv[item]) - prev[1][item] + prev[2][item] - prev[3][item]
            if sold > 0:
                st["flows"].setdefault(item, []).append((step - 1, sold))
            if sold >= cfg["min_lot"]:
                st["lots"].setdefault(item, []).append((step - 1, sold))
                if prev[4].get(item, 0) >= max(cfg["min_stock"], sold * cfg["size_frac"])                         and prev[3][item] == 0:
                    st["beaten"][item] = st["beaten"].get(item, 0) + 1

    def pre_empt(obs, action, st, step):
        day, hour = step // 24, step % 24
        shed = obs["private"].get("shed") or {}
        market = [list(o) for o in action.get("market") or []]
        for item in items:
            stock = int(shed.get(item, 0))
            if stock < cfg["min_stock"]:
                continue
            lots = st["lots"].get(item, [])
            if item in cfg.get("trace", ()):
                report.setdefault("m_sell_trace", []).append((step, item, stock, lots[-3:]))
            if lots and lots[-1][0] // 24 == day:
                continue          # they have sold a lot of it today: the race is over
            hour_o = their_hour(lots, stock, step, cfg)
            if hour_o is None or not hour_o - cfg["lead"] <= hour <= hour_o + cfg["late"]:
                continue
            if cfg["before_us"]:
                mine = our_hour(st["sales"].get(item, []), stock, cfg)
                size = max(cfg["min_lot"], stock * cfg["size_frac"])
                recent = [s_ for s_, u in lots if u >= size and s_ >= step - 24 * cfg["recent_days"]]
                if mine is None or not recent or recent[-1] % 24 >= mine:
                    report["m_sell_later_skips"] += 1
                    continue
            if cfg["after_beaten"] and not st["beaten"].get(item):
                report["m_sell_unbeaten_skips"] += 1
                continue
            if cfg["pace_check"] > 0:
                size = max(cfg["min_lot"], stock * cfg["size_frac"])
                recent = [u for s_, u in st["flows"].get(item, []) if s_ >= step - cfg["pace_steps"]]
                in_lots = sum(u for u in recent if u >= size)
                if not recent or in_lots < cfg["pace_check"] * sum(recent):
                    report["m_sell_pace_skips"] += 1
                    continue
            if cfg["require_own_lot"] and our_hour(st["sales"].get(item, []), stock, cfg) is None:
                report["m_sell_own_skips"] += 1
                continue
            if cfg["value_check"]:
                mine = our_hour(st["sales"].get(item, []), stock, cfg)
                wait = cfg["own_default"] if mine is None else (mine - hour) % 24
                if mine is not None and wait == 0:
                    continue      # we sell at this hour anyway
                town = sum(eaten(obs["town"]["unlocked_shops"], s, item) for s in range(step, step + wait))
                if their_lot(lots, stock, step, cfg) <= town:
                    report["m_sell_value_skips"] += 1
                    continue
            planned = sum(int(o[2]) for o in market if len(o) >= 3 and o[0] == "SELL" and o[1] == item)
            extra = stock - planned
            if extra <= 0:
                continue
            for o in market:
                if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                    o[2] = int(o[2]) + extra
                    break
            else:
                if len(market) >= MAX_ORDERS:
                    report["m_sell_no_slot"] += 1
                    report.setdefault("m_sell_full", []).append((step, item, [list(o) for o in market]))
                    continue
                # our race order goes first: slot i trades against their slot i
                market.insert(0, ["SELL", item, extra])
            report["m_sell_orders"] += 1
            report["m_sell_units"] += extra
            report["m_sell_log"].append((step, item, extra, hour_o))
        return dict(action, market=market)

    def m_sell_agent(observation, configuration=None):
        step = int(observation["step"])
        player = int(observation["player"])
        st = states.get(player)
        if st is None or step <= st["step"]:
            st = states[player] = {"step": -1, "prev": None, "lots": {}, "sales": {}, "flows": {},
                                   "beaten": {}}
        st["step"] = step
        action = agent(observation, configuration)
        try:
            # our own clock is learned from what the stack below would sell, never
            # from M's races (else one race makes "our hour" the race hour)
            for i in items:
                n = our_sold(observation, action, i)
                if n >= cfg["min_lot"]:
                    st["sales"].setdefault(i, []).append((step, n))
        except Exception:
            report["m_sell_errors"] += 1
        try:
            watch(observation, st, step)
            if cfg["first_step"] <= step < LAST_STEP and isinstance(action, dict):
                if (getattr(agent, "telemetry", None) or {}).get("shadow_insync_programs", 0):
                    report["m_sell_shadow_skips"] += 1
                else:
                    action = pre_empt(observation, action, st, step)
        except Exception as error:
            report["m_sell_errors"] += 1
            report["m_sell_last_error"] = repr(error)
        try:
            inv = observation["market"]["inventory"]
            shops = observation["town"]["unlocked_shops"]
            shed = observation["private"].get("shed") or {}
            st["prev"] = (step, {i: int(inv[i]) for i in items},
                          {i: eaten(shops, step, i) for i in items},
                          {i: our_sold(observation, action, i) for i in items},
                          {i: int(shed.get(i, 0)) for i in items})
        except Exception:
            report["m_sell_errors"] += 1
            st["prev"] = None
        return action

    m_sell_agent.telemetry = report
    return m_sell_agent
