"""L5 candidate: the endgame selling race.

Goods left in the shed at the end are worth nothing, and every good is priced
by market inventory, which only the town lowers. Selling a unit now beats
holding it for the final dump exactly when the opponent will sell more of the
good before the end than the town eats, and the answer is the same for every
unit: sell all of it now, or hold all of it. The opponent's sales are measured
exactly each step (inventory change + town consumption - our sales); the layer
sells a good's whole shed stock when their recent selling rate, projected to
the end, exceeds the town's remaining consumption of it.

    python -m tools.eval.live_replay run --agent factory --package stack.l2_combo:l5 ...
"""

from __future__ import annotations

RACE_ITEMS = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
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
FINAL_STEP = 718          # the last step agents act; its market is the final dump
MAX_ORDERS = 10

DEFAULTS = {
    "first_step": 672,    # day 28
    "lookback": 24,       # steps of opponent selling that set their rate
    "margin": 0.0,        # units their projected sales must exceed the town's by
    "items": RACE_ITEMS,
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
    """Upper bound on the units of `item` our orders sell this step.

    A SELL fills from the shed after this step's unit actions, so what the
    workers carry may land in time; counting it keeps the opponent's measured
    sales an underestimate."""
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


def race_wrap(agent, **overrides):
    cfg = dict(DEFAULTS)
    cfg.update(overrides)
    items = tuple(cfg["items"])
    states: dict = {}
    report = {"race_orders": 0, "race_units": 0, "race_merged": 0, "race_no_slot": 0,
              "race_errors": 0, "race_log": []}

    def watch(obs, st, step):
        prev, st["prev"] = st["prev"], None
        if prev is None or prev[0] != step - 1:
            return
        inv = obs["market"]["inventory"]
        for item in items:
            sold = int(inv[item]) - prev[1][item] + prev[2][item] - prev[3][item]
            st["flow"].setdefault(item, []).append((step - 1, sold))

    def race(obs, action, st, step):
        shops = obs["town"]["unlocked_shops"]
        shed = obs["private"].get("shed") or {}
        market = [list(o) for o in action.get("market") or []]
        for item in items:
            stock = int(shed.get(item, 0))
            if stock <= 0:
                continue
            flow = [u for s, u in st["flow"].get(item, []) if s >= step - cfg["lookback"]]
            if not flow:
                continue
            rate = max(0.0, sum(flow) / cfg["lookback"])
            theirs = rate * (FINAL_STEP - step)
            town = sum(eaten(shops, s, item) for s in range(step, FINAL_STEP))
            if theirs <= town + cfg["margin"]:
                continue
            planned = sum(int(o[2]) for o in market
                          if len(o) >= 3 and o[0] == "SELL" and o[1] == item)
            extra = stock - planned
            if extra <= 0:
                continue
            for o in market:
                if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                    o[2] = int(o[2]) + extra
                    report["race_merged"] += 1
                    break
            else:
                if len(market) >= MAX_ORDERS:
                    report["race_no_slot"] += 1
                    continue
                market.append(["SELL", item, extra])
            report["race_orders"] += 1
            report["race_units"] += extra
            report["race_log"].append((step, item, extra, round(theirs, 1), town))
        return dict(action, market=market)

    def race_agent(observation, configuration=None):
        step = int(observation["step"])
        player = int(observation["player"])
        st = states.get(player)
        if st is None or step <= st["step"]:
            st = states[player] = {"step": -1, "prev": None, "flow": {}}
        st["step"] = step
        action = agent(observation, configuration)
        try:
            if step >= cfg["first_step"] - cfg["lookback"] - 1:
                watch(observation, st, step)
            if cfg["first_step"] <= step < FINAL_STEP and isinstance(action, dict):
                action = race(observation, action, st, step)
        except Exception:
            report["race_errors"] += 1
        try:
            inv = observation["market"]["inventory"]
            shops = observation["town"]["unlocked_shops"]
            st["prev"] = (step, {i: int(inv[i]) for i in items},
                          {i: eaten(shops, step, i) for i in items},
                          {i: our_sold(observation, action, i) for i in items})
        except Exception:
            report["race_errors"] += 1
            st["prev"] = None
        return action

    race_agent.telemetry = report
    return race_agent
