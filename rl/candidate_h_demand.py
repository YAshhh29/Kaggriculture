"""Candidate H's market-demand layer.

A base farming policy decides what to plant, raise, harvest and when to
offer goods for sale. This layer sits on the action that policy returns and
re-decides only its SELL orders, from a model of the market Kaggriculture
actually runs:

* the town -- every unlocked shop instance takes one of each good it lists
  every four turns (single-good shops take two), and the town centre takes
  one of every product except fertilizer once a day. Shops only accumulate,
  so the next day's appetite for each good is known from the board;
* the price curve -- each book prices off its inventory against I0 with
  the per-good shape and target the rules document, so the value of selling
  a unit now can be set against the value of the same unit after the town
  has drained the book for a while.

For each good the policy wants to sell, units go now while today's marginal
price is at least what the same unit would fetch after the expected drain,
less a tolerance for the other farm selling into the same book. The rest
wait a turn and are reconsidered, since the base keeps offering them. The
layer never raises a quantity, never touches buys, hires or land, stands
aside on the closing turns so final liquidation is untouched, and sells
everything the policy offers whenever the shed is near its capacity.

Pure standard library, and self-contained so it can be appended to a
submission file.
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
DEFAULTS = {
    "enabled": True,
    "horizon": 24,           # turns ahead the drain is counted over
    "rival_share": 0.5,      # share of that drain the other farm refills
    "tolerance": 0.25,       # hold only for a gain above this fraction
    "room_high": 90,         # shed load at which everything offered goes
    "close_steps": 12,       # stand aside for the last turns of the game
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


def wrap(base_agent, settings: dict | None = None):
    """An agent that plays `base_agent` and re-decides its sales."""
    cfg = dict(DEFAULTS)
    cfg.update(settings or {})

    def agent(observation, configuration=None):
        action = base_agent(observation, configuration)
        try:
            return plan_sales(observation, action, cfg)
        except Exception:
            return action

    agent.demand_settings = cfg
    return agent
