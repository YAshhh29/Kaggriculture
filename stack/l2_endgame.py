"""L2 endgame candidate: Agent L plus one order-rewrite layer on its parent.

The layer only changes the TIMING and QUANTITY of the parent's SELL orders in
the final days, never its unit actions, purchases or hires:

* "Trickle dump": when the parent sells only part of the shed stock of a
  non-input item this step (the route tapes trickle goods out 1-6 units a
  step), it sells the whole stock now -- unless the town eats that item right
  after this step's market (then waiting one step is worth the tick's bounce,
  and the parent's own timing is kept).
* Inputs (WHEAT, FERTILIZER) are never touched: the parent picks them up as
  feed / fertilizer and its plan must not be starved.
* Optional clone gate: fire only while the opponent's farm is identical to
  ours (an exact copy of our parent), because then the opponent will trickle
  the same goods on the next steps and selling first takes the better prices.

Evidence (exact replays of our 148 live A/L games, tools/analysis/
l2_endgame_policies.py, opponents as recorded): ungated +110 margin per game
(A games +147, L games +26, median about 0, 11 losses flipped to wins, none
the other way); in the 14 games against exact copies +292 per game. Every
hold-back rule tested (sell after the town tick, hold the final day to 717,
hold floor-priced glut goods) lost 60-450 per game.

    python -m tools.eval.paired stack.l2_endgame:build --label endgame-dump
    python -m tools.eval.paired stack.l2_endgame:build_gated --label endgame-dump-clone
"""

from __future__ import annotations

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
            "WOOL", "FERTILIZER")
INPUTS = ("WHEAT", "FERTILIZER")
SHOPS = {"BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
         "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
         "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
         "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
         "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY")}
SHED_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
ANIMALS = ("COW", "SHEEP", "GOOSE")


def town_eats_after(shops, item, step):
    """True when the town removes ``item`` right after this step's market."""
    if step % 24 == 0 and item != "FERTILIZER":
        return True
    if step % 4 == 0:
        return any(item in SHOPS.get(s, ()) for s in shops)
    return False


def projected_shed(obs, action):
    """Shed after this step's unit actions, before the market (engine order:
    DROP moves a shed-adjacent unit's goods up to 100, PLACE up to the room,
    PICKUP removes)."""
    private = obs["private"]
    shed = {k: int(v) for k, v in dict(private["shed"]).items()}
    farm = obs["farms"][int(obs["player"])]
    positions = [farm["farmer"]] + list(farm["hands"])
    units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    invs = list(private["inventories"])
    total = sum(shed.values())
    for i, act in enumerate(units[:len(positions)]):
        if not act or tuple(positions[i]) not in SHED_ACCESS:
            continue
        inv = dict(invs[i]) if i < len(invs) else {}
        op = act[0]
        if op == "DROP":
            for item, n in inv.items():
                take = min(int(n), max(0, 100 - total))
                shed[item] = shed.get(item, 0) + take
                total += take
        elif op == "PICKUP" and len(act) >= 2:
            n = int(act[2]) if len(act) >= 3 else 1
            take = min(max(0, n), shed.get(act[1], 0))
            shed[act[1]] = shed.get(act[1], 0) - take
            total -= take
        elif op == "PLACE" and len(act) >= 2 and act[1] not in ANIMALS:
            n = int(act[2]) if len(act) >= 3 else 1
            take = min(max(0, n), int(inv.get(act[1], 0)), max(0, 100 - total))
            shed[act[1]] = shed.get(act[1], 0) + take
            total += take
    return shed


def _sells(market):
    out = {}
    for o in market or []:
        if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL":
            try:
                out[o[1]] = out.get(o[1], 0) + max(0, int(o[2]))
            except (TypeError, ValueError):
                pass
    return out


def _canon(tile):
    if isinstance(tile, dict):
        return tuple(sorted((k, repr(v)) for k, v in tile.items()))
    return tile


def farms_identical(obs):
    farms = obs["farms"]
    me = int(obs["player"])
    a, b = farms[me], farms[1 - me]
    if list(a["farmer"]) != list(b["farmer"]):
        return False
    if [list(h) for h in a["hands"]] != [list(h) for h in b["hands"]]:
        return False
    for ra, rb in zip(a["tiles"], b["tiles"]):
        for x, y in zip(ra, rb):
            if _canon(x) != _canon(y):
                return False
    return True


class MirrorMeter:
    """Online estimate of how often the opponent sells the same item in the
    same step as we do. The opponent's sales of a non-input item are exact
    from the public market inventory: inventory(t+1) - inventory(t) = our
    units + their units - the town's consumption after step t (no one can
    buy these items; a unit sold at $1 does not move the inventory, so steps
    quoted at $5 or less are skipped)."""

    def __init__(self, since=480, min_events=6):
        self.since = since
        self.min_events = min_events
        self.prev = None
        self.events = 0
        self.hits = 0

    def observe(self, obs):
        step = int(obs["step"])
        inv = obs["market"]["inventory"]
        prev = self.prev
        if prev is not None and prev["step"] == step - 1 and prev["step"] >= self.since:
            for item, ours in prev["ours"].items():
                if ours <= 0 or prev["prices"].get(item, 0) <= 5:
                    continue
                eaten = town_eats_units(prev["shops"], item, prev["step"])
                theirs = int(inv[item]) - int(prev["inv"][item]) + eaten - ours
                self.events += 1
                self.hits += theirs >= 1

    def remember(self, obs, stock, final_market):
        sold = _sells(final_market)
        self.prev = {"step": int(obs["step"]),
                     "inv": {i: int(obs["market"]["inventory"][i]) for i in PRODUCTS},
                     "prices": {i: int(obs["market"]["prices"].get(i, 0)) for i in PRODUCTS},
                     "shops": list(obs["town"]["unlocked_shops"]),
                     "ours": {i: min(q, stock.get(i, 0)) for i, q in sold.items()
                              if i not in INPUTS and i in PRODUCTS}}

    def rate(self):
        return self.hits / self.events if self.events >= self.min_events else 0.0


PRICE = {  # engine MARKET_PARAMS: base, T, below shape, target, above shape, target
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


def _shape(func, x, T):
    import math
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    u = x / T   # hinge
    return u + 8.0 * max(0.0, u - 1.0) ** 2


def unit_price(item, inventory):
    """Exact engine price of one unit at this market inventory."""
    base, T, below, bt, above, at = PRICE[item]
    if inventory < 10000:
        price = base + bt * base / _shape(below, T, T) * _shape(below, 10000 - inventory, T)
    else:
        price = base - at * base / _shape(above, T, T) * _shape(above, inventory - 10000, T)
    return max(1, int(round(price)))


def town_eats_units(shops, item, step):
    c = 0
    if step % 4 == 0:
        for s in shops:
            if item in SHOPS.get(s, ()):
                c += 2 if len(SHOPS[s]) == 1 else 1
    if step % 24 == 0 and item != "FERTILIZER":
        c += 1
    return c


def trickle_dump(parent, start=600, gate="none", theta=0.4, min_frac=0.0):
    """Wrap ``parent`` (the agent before L's queue-order layer).
    gate: "none" (always), "clone" (opponent farm identical to ours) or
    "mirror" (opponent sold the same item in the same step in at least
    ``theta`` of our sale steps since day 20)."""
    report = {"dump_turns": 0, "dump_units": 0, "clone_steps": 0,
              "mirror_rate_x100": 0, "dump_errors": 0}
    state = {"step": -1, "meter": MirrorMeter()}

    def agent(observation, configuration=None):
        action = parent(observation, configuration)
        try:
            step = int(observation["step"])
            if step <= state["step"]:
                for k in report:
                    report[k] = 0
                state["meter"] = MirrorMeter()
            state["step"] = step
            if not isinstance(action, dict):
                return action
            meter = state["meter"]
            track = gate == "mirror" and step >= meter.since - 1
            if track:
                meter.observe(observation)
            if step < start or step >= 718:
                if track:
                    meter.remember(observation, projected_shed(observation, action),
                                   action.get("market") or [])
                return action
            market = action.get("market") or []
            stock = projected_shed(observation, action)
            fire = True
            if gate == "clone":
                fire = farms_identical(observation)
                report["clone_steps"] += fire
            elif gate == "mirror":
                fire = meter.rate() >= theta
                report["mirror_rate_x100"] = int(100 * meter.rate())
            new = market
            if fire:
                sells = _sells(market)
                shops = list(observation["town"]["unlocked_shops"])
                extra = {}
                for item, want in sells.items():
                    have = stock.get(item, 0)
                    if item in INPUTS or item not in PRODUCTS or want <= 0 or want >= have:
                        continue
                    if town_eats_after(shops, item, step):
                        continue
                    add = have - want
                    if min_frac > 0:
                        # stop where the next unit would fetch less than
                        # min_frac of this step's quote (our own damage)
                        inv = int(observation["market"]["inventory"][item])
                        quote = unit_price(item, inv)
                        add = 0
                        while (want + add < have and unit_price(item, inv + want + add)
                               >= max(2, min_frac * quote)):
                            add += 1
                    if add > 0:
                        extra[item] = add
                if extra:
                    new, done = [], set()
                    for o in market:
                        if (isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL"
                                and o[1] in extra and o[1] not in done):
                            new.append(["SELL", o[1], int(o[2]) + extra[o[1]]])
                            done.add(o[1])
                        else:
                            new.append(list(o) if isinstance(o, (list, tuple)) else o)
                    report["dump_turns"] += 1
                    report["dump_units"] += sum(extra.values())
                    action = dict(action, market=new)
            if track:
                meter.remember(observation, stock, new)
            return action
        except Exception:
            report["dump_errors"] += 1
            return action

    agent.telemetry = report
    return agent


def build():
    from stack.candidate_l import l_stack
    return l_stack(inner=lambda agent, env: trickle_dump(agent))


def build_gated():
    from stack.candidate_l import l_stack
    return l_stack(inner=lambda agent, env: trickle_dump(agent, gate="clone"))


def build_mirror():
    from stack.candidate_l import l_stack
    return l_stack(inner=lambda agent, env: trickle_dump(agent, gate="mirror", theta=0.4))


def build_mirror60():
    from stack.candidate_l import l_stack
    return l_stack(inner=lambda agent, env: trickle_dump(agent, gate="mirror", theta=0.6))
