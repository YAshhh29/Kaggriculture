"""L2 out-farm candidates on top of Agent L (rl.candidate_l.l_stack).

Controlled V219 decisions, used to measure what the day-18 tomato project is
worth game by game on the live replays:

    v219_on   L, but V219 fires whenever its physical preconditions hold
              (exactly NW/NE/SW owned, SE still locked, >= 12,000 cash, no
              tomato anywhere, no later land/tomato on the route) -- the
              shop-count and tomato-price tests are dropped;
    v219_off  L, but V219 never fires.

    python -m tools.analysis.l2_outfarm_counter --factory rl.l2_outfarm:v219_on --label v219on --losses
"""

from __future__ import annotations

from rl.candidate_l import l_stack


def _v219_physical(env):
    """Agent A's own V219 qualification minus the shop-count and price tests."""
    impl = env["_IMPL"]

    def qualifies(obs, native):
        farm = obs["farms"][obs["player"]]
        if len(farm["tiles"]) != 10 or set(farm["unlocked_quadrants"]) != {"NW", "NE", "SW"}:
            return False
        if farm["money"] < 12000:
            return False
        if any(farm["tiles"][y][x] != "LOCKED" for y in (5, 6) for x in range(5, 10)):
            return False
        if obs["private"]["seeds"].get("TOMATO", 0) or obs["private"]["shed"].get("TOMATO", 0):
            return False
        if any(isinstance(t, dict) and t.get("crop") == "TOMATO" for row in farm["tiles"] for t in row):
            return False
        for tape in impl.chassis.routes.values():
            for a in tape[432:719]:
                if any(o and o[0] == "BUY_LAND" for o in a.get("market", [])):
                    return False
                if any(c == ["PLANT", "TOMATO"] for c in [a.get("farmer")] + a.get("hands", [])):
                    return False
        return True

    return qualifies


def _patch_gate(gate_factory):
    def inner(agent, env):
        env["_v219_qualifies"] = gate_factory(env)
        return agent
    return inner


def v219_on():
    return l_stack(inner=_patch_gate(_v219_physical))


# ---------------------------------------------------------------------------
# Forecast tomato gate. V219 decides once, at step 432, and its 80 tomatoes are
# sold on days 26-29 into the tomato shortfall of that moment. The project
# costs ~8,000 (SE land 4,000, seeds 500, crew wages ~3,100, fertilizer), so it
# pays only when the day-26 shortfall is about 250 or more ($97+/unit alone).
# Nobody sells tomatoes before day 18 unless they grow them, so the shortfall
# path is nearly deterministic: every PIZZA_SHOP / FARMERS_MARKET instance eats
# 6 a day and the town centre 1. The forecast subtracts the rival's standing
# tomato plants (visible on its farm; about 6 units each reach the market).
TOMATO_SHOPS = ("PIZZA_SHOP", "FARMERS_MARKET")
FORECAST_THRESHOLD = 250
UNITS_PER_RIVAL_PLANT = 6


def tomato_forecast(obs) -> float:
    """Tomato shortfall expected at the start of day 26, seen from step 432."""
    day = int(obs["step"]) // 24
    short = 10000 - int(obs["market"]["inventory"]["TOMATO"])
    shops = sum(s in TOMATO_SHOPS for s in obs["town"]["unlocked_shops"])
    rival = obs["farms"][1 - int(obs["player"])]
    plants = sum(1 for row in rival["tiles"] for t in row
                 if isinstance(t, dict) and t.get("crop") == "TOMATO"
                 and int(t.get("planted_day", day)) + 11 >= day)
    return short + (26 - day) * (6 * shops + 1) - UNITS_PER_RIVAL_PLANT * plants


def _forecast_gate(threshold=FORECAST_THRESHOLD):
    def factory(env):
        physical = _v219_physical(env)
        report = env.setdefault("_L2_TOMATO_REPORT", {"forecast26": 0, "gate_fired": 0})

        def qualifies(obs, native):
            if not physical(obs, native):
                return False
            if obs["market"]["prices"]["TOMATO"] < 70:
                return False
            f = tomato_forecast(obs)
            report["forecast26"] = int(f)
            ok = f >= threshold
            report["gate_fired"] = int(ok)
            return ok
        return qualifies
    return factory


def fgate():
    return l_stack(inner=_patch_gate(_forecast_gate()))


def v219_off():
    return l_stack(inner=_patch_gate(lambda env: (lambda obs, native: False)))


# ---------------------------------------------------------------------------
# Lot selling. In near-mirror games both farms hold the same lots on the same
# steps, and the parent often sells a lot a few units per step. A rival that
# sells the whole lot in the same slot takes the undamaged prices and leaves
# the parent selling into the damage (episode 113664678, step 636: 18
# strawberries each; the rival sold 18 at 68->30, the parent 3 per step and
# its last 15 at 36->14). This layer only enlarges the parent's own SELL of an
# item to the whole projected shed stock of that item; it never adds a sale the
# parent did not make, never touches WHEAT or FERTILIZER (feed and inputs),
# and leaves the parent's timing alone.
LOT_ITEMS = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
BASE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
        "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}
PRODUCER = {"EGG": "GOOSE", "MILK": "COW", "WOOL": "SHEEP"}


def _rival_producers(obs) -> set:
    """Items the rival can put on the market: crops standing, animals kept."""
    try:
        farm = obs["farms"][1 - int(obs["player"])]
    except (KeyError, IndexError, TypeError):
        return set(LOT_ITEMS)
    out = set()
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict):
                if t.get("kind") == "PLANT":
                    out.add(t.get("crop"))
                elif "animal" in t:
                    out.update(k for k, v in PRODUCER.items() if v == t["animal"])
    return out


def lot_wrap(parent, env, theta=0.0, min_step=96, items=LOT_ITEMS, rival_only=False):
    report = {"lot_turns": 0, "lot_units": 0, "lot_errors": 0}
    farm_view = env["FarmView"]
    projected = env["projected_shed"]

    def lot_agent(observation, configuration=None):
        action = parent(observation, configuration)
        try:
            step = int(observation["step"])
            market = action.get("market") if isinstance(action, dict) else None
            if not market or step < min_step or step >= 718:
                return action
            if not any(o and o[0] == "SELL" and len(o) >= 3 and o[1] in items for o in market):
                return action
            stock = projected(action, farm_view(observation))
            prices = observation["market"]["prices"]
            rivals = _rival_producers(observation) if rival_only else None
            committed: dict = {}
            new, extra = [], 0
            for o in market:
                if o and o[0] == "SELL" and len(o) >= 3 and o[1] in items:
                    item, q = o[1], max(0, int(o[2]))
                    have = int(stock.get(item, 0)) - committed.get(item, 0)
                    if (0 < q < have and int(prices.get(item, 0)) >= theta * BASE[item]
                            and (rivals is None or item in rivals)):
                        extra += have - q
                        o = ["SELL", item, have]
                        q = have
                    committed[item] = committed.get(item, 0) + q
                new.append(o)
            if extra:
                report["lot_turns"] += 1
                report["lot_units"] += extra
                action = dict(action, market=new)
        except Exception:
            report["lot_errors"] += 1
        return action

    lot_agent.telemetry = report
    return lot_agent


def lot():
    return l_stack(inner=lambda agent, env: lot_wrap(agent, env))


def lot50():
    return l_stack(inner=lambda agent, env: lot_wrap(agent, env, theta=0.5))


def lot_rival():
    return l_stack(inner=lambda agent, env: lot_wrap(agent, env, rival_only=True))


def fgate_lot():
    def inner(agent, env):
        env["_v219_qualifies"] = _forecast_gate()(env)
        return lot_wrap(agent, env)
    return l_stack(inner=inner)
