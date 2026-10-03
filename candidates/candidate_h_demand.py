"""Candidate H's market-demand layer: re-decides a base policy's SELL orders.

It models the town (every unlocked shop takes one of each good it lists every
four turns; the town centre takes one of each product a day) and each good's
price curve. A unit sells now only if today's marginal price is at least what
it would fetch after the expected drain, less a tolerance for the other farm;
the rest are reconsidered next turn. It never raises a quantity or touches
hires or land, stands aside on the closing turns, and sells everything offered
when the shed is nearly full. Opening seed buys are touched only when
guard_cash is switched on with a feed_reserve. Pure standard library and
self-contained, so it can be appended to a submission file.
"""

from __future__ import annotations

import copy

TURNS = 24
LAST_STEP = 718
SHED_CAPACITY = 100
I0 = 10000
HINGE_GAIN = 8.0

SHOP_GOODS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
CENTER_GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
                "MILK", "WOOL")

# (base, T, below shape, below target, above shape, above target)
CURVES = {
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

# Tuned head to head against the same farming base without this layer, in a
# fixed town, both seats (which come out identical, so each pair is one game):
#
#     tolerance 0.04 (first guess)   H wins  4 of 12, margin -1,076 a game
#     rival_share 0.8                H wins  8 of 12, margin   -153
#     horizon 8                      H wins  7 of 12, margin   +105
#     tolerance 0.15                 H wins  9 of 12, margin   +174
#     tolerance 0.15, horizon 8      H wins 15 of 24, margin   +234
#     tolerance 0.25, horizon 8      H wins 18 of 24, margin   +170
#     tolerance 0.25                 H wins 19 of 24, margin   +223
#
# Holding stock for a small expected gain lets the other farm sell into the
# book first. Only a clear gain is worth waiting for.
#
# Wrapped around Candidate G instead, at tolerance 0.25 and played against
# plain G the same way, it is neutral: 10 wins, 10 losses and 4 ties in 24
# games, margin +24 a game. G's own selling leaves it little to re-time, so
# it is not used in G.
DEFAULTS = {
    "enabled": True,
    "horizon": 24,           # turns ahead the drain is counted over
    "rival_share": 0.5,      # share of that drain the other farm refills
    "tolerance": 0.25,       # hold only for a gain above this fraction
    "room_high": 90,         # shed load at which everything offered goes
    "close_steps": 12,       # stand aside for the last turns of the game
    # Cash kept back from seed on the opening days -- see guard_cash. 0 is off.
    #
    # Measured against the V40 base with the demand layer at tolerance 0.25,
    # 12 current top-team replays plus 24 head-to-head games against the
    # base itself:
    #     0     replays +94 a game against the base (better in 7 of 12),
    #           head to head H wins 19 of 24, +223
    #     30    replays -189 a game (better in 5 of 12), head to head H
    #           wins 11 of 24, +12 -- even the last few day-0 wheat seeds
    #           cost the edge the layer has over its base
    #     150   replays -2,339 a game (worse in all 12), head to head H
    #           wins 1 of 24, -1,612
    #     300   replays -5,241 a game (worse in all 12), head to head H
    #           wins 1 of 24, -4,895
    # In simulation the base never runs dry, so the guard only cuts opening
    # seed -- mostly the day-0 melons that pay for day 10 -- and wins
    # nothing back. The live collapse depends on a real opponent's opening
    # squeezing H's cash, which replays cannot reproduce. Off.
    # Measured and OFF. Sales before purchases is worth +734 a game on our
    # own scheduler, and it costs this one 14,143: against the published
    # aurax7 agent the margin goes from -990 to -15,133 and the own score
    # from 98,271 to 87,214. The base under this layer is a chassis that
    # orders its own queue on purpose, and the same reordering wrecked our
    # replay agent too (-84,732). A route's market queue is part of the
    # route; only re-order a queue this layer wrote itself.
    "sequence_orders": False,
    "feed_reserve": 0.0,
    "reserve_until_day": 2,
    # Coins seed orders may never take the purse below, so the next morning's
    # hires can be paid -- see guard_cash. 0 is off.
    "hire_reserve": 0.0,
    # Last day the hire reserve applies; None applies it every day.
    #
    # Every day at 15, on the v14 top-team field (83 games, paired against H
    # as submitted): H's wins rise from 71 to 78 and the clean-game margin by
    # +3,762 a game, but the median game is -49, better in only 9 of 54 and
    # worse in 45, and H's own score is lower in 74 of 83. H runs its purse
    # near zero every day, so a reserve on every day trims a seed most days;
    # the gain is a few rescued day-1 collapses. The collapses start on day 0.
    #
    # Days 0-1 is the one to ship (submissions/candidate-h2). Replayed on H's
    # 84 real ladder games (tools.eval.live_replay, same seeds, seats and
    # opponent moves; H as submitted reproduces all 84 to the coin):
    #     every day   wins 48 -> 72; the 21 early-collapse games 0 -> 19, but
    #                 in the other 63 own score is lower in 40; 3 wins lost
    #     days 0-3    wins 48 -> 73; other 63 worse in 35; 2 wins lost
    #     days 0-1    wins 48 -> 68; collapse games 0 -> 20 (own score
    #                 +15,025 a game); the other 63 are identical in 61 and
    #                 better in 2; no win lost
    # On the v14 top-team field (83 games) days 0-1 takes wins from 71 to 78,
    # better in 8 and worse in 0 (every day and days 0-3: worse in 45 of 54
    # clean games). Head to head against its own base it wins 19 of 24,
    # exactly as H does without it.
    "hire_reserve_until_day": None,
}


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _shape(func: str, x: float, T: float) -> float:
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return x ** 0.5
    if func == "log":
        import math
        return math.log1p(x)
    if func == "hinge":
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x


def price(item: str, inventory: float) -> float:
    """The book's quote at a given inventory, floored at 1."""
    base, T, below, below_t, above, above_t = CURVES[item]
    if inventory < I0:
        amp = below_t * base / _shape(below, T, T)
        value = base + amp * _shape(below, I0 - inventory, T)
    else:
        amp = above_t * base / _shape(above, T, T)
        value = base - amp * _shape(above, inventory - I0, T)
    return max(1.0, float(round(value)))


def town_drain(shops, step: int, horizon: int, item: str) -> int:
    """Units of `item` the town removes over the next `horizon` turns."""
    total = 0
    for s in range(step, step + horizon):
        if s % 4 == 0:
            for shop in shops:
                goods = SHOP_GOODS.get(shop, ())
                if item in goods:
                    total += 2 if len(goods) == 1 else 1
        if s % TURNS == 0 and item in CENTER_GOODS:
            total += 1
    return total


def units_to_sell_now(item: str, offered: int, inventory: float, shops,
                      step: int, cfg: dict) -> int:
    """How many of `offered` units are worth more now than after the drain."""
    horizon = max(1, min(int(cfg["horizon"]), LAST_STEP - step - 1))
    drain = town_drain(shops, step, horizon, item)
    effective = drain * (1.0 - float(cfg["rival_share"]))
    keep_for_later = 1.0 + float(cfg["tolerance"])
    now = 0
    for i in range(offered):
        today = price(item, inventory + i)
        later = price(item, inventory - effective + i)
        if today * keep_for_later >= later or later <= 1.0:
            now += 1
        else:
            break
    return now


def plan_sales(observation, action, cfg: dict):
    """Return `action` with its SELL quantities re-decided."""
    if not cfg.get("enabled", True) or not isinstance(action, dict):
        return action
    step = int(_get(observation, "step", 0) or 0)
    if step >= LAST_STEP - int(cfg["close_steps"]):
        return action
    orders = action.get("market") or []
    if not any(isinstance(o, list) and o and o[0] == "SELL" for o in orders):
        return action

    private = _get(observation, "private", {}) or {}
    shed = _get(private, "shed", {}) or {}
    load = sum(int(v) for v in shed.values())
    for inventory in _get(private, "inventories", []) or []:
        load += sum(int(v) for v in (inventory or {}).values() if int(v) > 0)
    if load >= int(cfg["room_high"]):
        return action

    market = _get(observation, "market", {}) or {}
    books = _get(market, "inventory", {}) or {}
    shops = list(_get(_get(observation, "town", {}) or {},
                      "unlocked_shops", []) or [])

    revised = copy.deepcopy(action)
    kept = []
    for order in revised.get("market") or []:
        if (isinstance(order, list) and len(order) >= 3 and order[0] == "SELL"
                and order[1] in CURVES and order[1] in books):
            item = order[1]
            offered = min(int(order[2]), int(shed.get(item, 0) or 0))
            if offered <= 0:
                kept.append(order)
                continue
            now = units_to_sell_now(item, offered, float(books[item]), shops,
                                    step, cfg)
            if now <= 0:
                continue
            kept.append(["SELL", item, now if now < offered else order[2]])
        else:
            kept.append(order)
    revised["market"] = kept
    return revised


SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100,
             "MELON": 80}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}


def guard_cash(observation, action, cfg: dict):
    """Trim opening seed orders that would leave no cash to feed the herd.

    In H's first 40 live games, 16 were lost the same way and none of those
    was won. The base spends the opening purse on seed down to a coin or two
    by the end of day 0 (a median of 1 against the opponent's 56), cannot
    buy the few wheat its animals need on day 1, and two animals escape that
    night. The herd then sits at 3 while the opponent's grows to 6, and the
    game goes by a median of 25,388. In the other 24 games H held the same
    cash as its opponent and won 13.

    On the opening days, seed orders are cut so the money left after them
    stays at `feed_reserve`. Animals, hires and feed are never touched.
    """
    # The hire reserve is the part that matters. Replaying live episode
    # 109250573 turn by turn showed the collapse is not feed money at all:
    # both farms end day 0 with the same two animals unfed, but H's last seed
    # orders take its purse to exactly 0 by hour 21 while the opponent keeps
    # 50. At hour 0 of day 1 both order three hands, which cost 1, 1 and 2
    # coins; H cannot pay even that, plays day 1 with the farmer alone, feeds
    # one animal, and two escape that night. A dozen coins kept back pays for
    # five hands, so this reserve is tiny and applies every day.
    step = int(_get(observation, "step", 0) or 0)
    reserve = float(cfg.get("hire_reserve", 0) or 0)
    until = cfg.get("hire_reserve_until_day")
    if until is not None and step // TURNS > int(until):
        reserve = 0.0
    if step // TURNS <= int(cfg.get("reserve_until_day", 2)):
        reserve = max(reserve, float(cfg.get("feed_reserve", 0) or 0))
    if reserve <= 0 or not isinstance(action, dict):
        return action
    farms = _get(observation, "farms", []) or []
    player = int(_get(observation, "player", 0) or 0)
    if player >= len(farms):
        return action
    running = float(_get(farms[player], "money", 0) or 0)
    books = _get(_get(observation, "market", {}) or {}, "inventory", {}) or {}
    revised = copy.deepcopy(action)
    kept = []
    for order in revised.get("market") or []:
        if not (isinstance(order, list) and len(order) >= 3):
            kept.append(order)
            continue
        op, item = order[0], order[1]
        try:
            quantity = int(order[2])
        except (TypeError, ValueError):
            kept.append(order)
            continue
        if op == "BUY_SEED" and item in SEED_COST:
            cost = SEED_COST[item]
            quantity = min(quantity, max(0, int((running - reserve) // cost)))
            if quantity > 0:
                running -= cost * quantity
                kept.append([op, item, quantity])
            continue
        if op == "BUY_ANIMAL" and item in ANIMAL_COST:
            running -= ANIMAL_COST[item] * quantity
        elif op == "BUY_PRODUCT" and item in CURVES and item in books:
            running -= price(item, float(books[item])) * quantity
        kept.append(order)
    revised["market"] = kept
    return revised


def sequence_orders(action, cfg: dict):
    """Put sales first in the market list, then purchases priced off the book.

    `_process_market` walks both players' orders by index and quotes each
    side's current unit at the same pre-commit inventory. A sale at a lower
    index therefore brings in its cash and frees its shed room before
    anything that needs either, and a unit that fails on cash or on a full
    shed aborts the whole order it belongs to. Fixed-price orders -- seed,
    animals, hires, land -- do not care where they sit, so they go last.
    Anything past the tenth order is never read at all.

    Measured on our other agent, where the same change is worth 734 coins a
    game, higher in 18 games of 38 and lower in 4.
    """
    if not cfg.get("sequence_orders", True) or not isinstance(action, dict):
        return action
    orders = action.get("market") or []
    if len(orders) < 2:
        return action
    rank = {"SELL": 0, "BUY_PRODUCT": 1}
    revised = dict(action)
    revised["market"] = sorted(
        orders, key=lambda o: rank.get(str(o[0]) if isinstance(o, list)
                                       and o else "", 2))
    return revised


def wrap(base_agent, settings: dict | None = None):
    """An agent that plays `base_agent` and re-decides its sales."""
    cfg = dict(DEFAULTS)
    cfg.update(settings or {})
    import inspect
    try:
        takes_config = len(inspect.signature(base_agent).parameters) >= 2
    except (TypeError, ValueError):
        takes_config = True

    def agent(observation, configuration=None):
        # Call the base with the arguments it accepts. Passing a
        # configuration to a one-argument agent raised on every turn and
        # that side scored nearly nothing.
        action = (base_agent(observation, configuration) if takes_config
                  else base_agent(observation))
        try:
            return sequence_orders(
                guard_cash(observation,
                           plan_sales(observation, action, cfg), cfg), cfg)
        except Exception:
            return action

    agent.demand_settings = cfg
    return agent
