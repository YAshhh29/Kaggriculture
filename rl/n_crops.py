"""Agent N, part 1: grow what the town will pay for (three quadrants, A's crew).

A's route plants wheat on the same tiles cycle after cycle and, in towns where
strawberries still sell high late in the game, digs its (spent) strawberries
out to make room for more wheat. ShunkiKyoya (-22.5k against L2) kept a
second strawberry batch alive and sold 102 strawberries from day 26 to our 44.

A strawberry plant produces 4 times, every 2 days from 10 days after planting
(+2 a time when fertilized and watered), and dies only after two days unwatered.
A's route keeps visiting a wheat tile every day or two to water it, harvests it
every few days, and re-plants it -- a PLANT on an occupied tile is a no-op
that costs no seed. So when the route plants wheat between `first_day` and
`last_day`, N plants a strawberry instead; the route's own visits then water
and harvest it, and its harvests land on days 21-29. N buys the seeds, stops
any DIG of a converted tile, and sells the strawberries the route never
planned to sell as they reach the shed (V9-herd style).

The gate is strict (towns where the day-11 strawberry quote is at least
`min_price` and enough shops eat strawberries): in most towns both mirror
farms flood the same strawberry batch and the late price collapses (day-24
median 7-12 when the day-11 quote is below 180).
"""

from __future__ import annotations

STRAWBERRY_SHOPS = ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")
MAX_ORDERS = 10

DEFAULTS = {
    "decide_day": 11,
    "min_price": 180,
    "min_shops": 3,
    "budget": 8,          # tiles converted
    "first_day": 11,
    "last_day": 14,
    "cash_reserve": 1500,
    "crop": "STRAWBERRY",
    "replace": ("WHEAT", "CARROT"),
    "sell_extra": True,
}


def n_crops_inner(parent, env, **overrides):
    cfg = dict(DEFAULTS)
    cfg.update(overrides)
    crop = cfg["crop"]
    states: dict = {}
    report = {"n_active": 0, "n_seeds_bought": 0, "n_swaps": 0, "n_digs_blocked": 0,
              "n_extra_sold": 0, "n_errors": 0}

    def decide(obs):
        shops = obs["town"]["unlocked_shops"]
        n_shops = sum(s in STRAWBERRY_SHOPS for s in shops)
        price = int(obs["market"]["prices"].get(crop, 0))
        return price >= cfg["min_price"] and n_shops >= cfg["min_shops"]

    def free_slot(market):
        return len(market) < MAX_ORDERS

    def n_agent(observation, configuration=None):
        step = int(observation["step"])
        player = int(observation["player"])
        st = states.get(player)
        if st is None or step <= st["step"]:
            st = states[player] = {"step": -1, "active": None, "tiles": set(), "swaps": 0,
                                   "ordered": 0}
        st["step"] = step
        action = parent(observation, configuration)
        try:
            action = shape(observation, action, st, step)
        except Exception:
            report["n_errors"] += 1
        return action

    def shape(obs, action, st, step):
        day, hour = step // 24, step % 24
        if not isinstance(action, dict):
            return action
        if st["active"] is None and day >= cfg["decide_day"]:
            st["active"] = decide(obs)
            report["n_active"] = int(st["active"])
        if not st["active"] and not st["tiles"]:
            return action
        seat = int(obs["player"])
        farm = obs["farms"][seat]
        private = obs["private"]
        seeds = int((private.get("seeds") or {}).get(crop, 0))
        market = [list(o) for o in action.get("market") or []]
        units = [list(action.get("farmer") or ["PASS"])] + [list(c) for c in action.get("hands") or []]
        pos = [farm["farmer"]] + list(farm["hands"])
        changed = False
        # 1. seeds for the batch, bought ahead of the planting window
        if st["active"] and st["ordered"] < cfg["budget"] and day <= cfg["last_day"] and hour >= 1:
            need = cfg["budget"] - st["ordered"]
            cost = need * 100
            if free_slot(market) and float(farm["money"]) >= cost + cfg["cash_reserve"]:
                market.append(["BUY_SEED", crop, need])
                st["ordered"] += need
                report["n_seeds_bought"] += need
                changed = True
        # 2. swap the route's plantings on the window's days
        planting = 0
        # only our own seeds: A may hold strawberry seed for its own plantings
        theirs = sum(1 for c in units if c[:2] == ["PLANT", crop])
        ours = min(st["ordered"] - st["swaps"], seeds - theirs)
        if st["active"] and cfg["first_day"] <= day <= cfg["last_day"]:
            for i, c in enumerate(units):
                if st["swaps"] >= cfg["budget"] or planting >= ours:
                    break
                if len(c) >= 2 and c[0] == "PLANT" and c[1] in cfg["replace"] and i < len(pos):
                    x, y = pos[i]
                    if farm["tiles"][y][x] is None:
                        c[1] = crop
                        st["tiles"].add((x, y))
                        st["swaps"] += 1
                        planting += 1
                        report["n_swaps"] += 1
                        changed = True
        # 3. never dig a converted plant while it lives
        for i, c in enumerate(units):
            if c and c[0] == "DIG" and i < len(pos) and tuple(pos[i]) in st["tiles"]:
                x, y = pos[i]
                tile = farm["tiles"][y][x]
                if isinstance(tile, dict) and tile.get("crop") == crop:
                    units[i] = ["PASS"] if tile.get("watered_today") else ["WATER"]
                    report["n_digs_blocked"] += 1
                    changed = True
        st["tiles"] = {t for t in st["tiles"]
                       if isinstance(farm["tiles"][t[1]][t[0]], dict)
                       and farm["tiles"][t[1]][t[0]].get("crop") == crop} | \
                      {tuple(pos[i]) for i, c in enumerate(units)
                       if c[:2] == ["PLANT", crop] and i < len(pos)}
        # 4. sell what the route never planned to sell, as it reaches the shed
        if cfg["sell_extra"] and st["swaps"] and day >= 20 and step < 718 and free_slot(market):
            native = env["_IMPL"].chassis.players.get(seat) or {}
            route = native.get("route")
            if route in env["_IMPL"].chassis.routes:
                view = env["FarmView"](obs)
                stock = env["projected_shed"](dict(action, farmer=units[0], hands=units[1:], market=market),
                                              view).get(crop, 0)
                selling = sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ["SELL", crop])
                planned = env["_IMPL"].chassis.future_sells(route, crop, step + 1)
                extra = int(stock) - selling - int(planned)
                if extra > 0:
                    market.append(["SELL", crop, extra])
                    report["n_extra_sold"] += extra
                    changed = True
        if not changed:
            return action
        return dict(action, farmer=units[0], hands=units[1:], market=market)

    n_agent.telemetry = report
    return n_agent
