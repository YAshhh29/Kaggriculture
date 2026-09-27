# ---- BEGIN l2_shadow (Agent L2 candidate layer: opponent shadow) ----
# Opponent shadow.
#
# Many ladder opponents run a program we have byte for byte (Agent A is a
# verbatim public build; a large share of the 2000-2130 ladder are exact copies
# of it). The program is deterministic given its observation stream, so a
# fresh instance of it, fed each turn the observation the opponent is being
# given, returns exactly the action the opponent is about to play -- before we
# commit ours.
#
# The opponent's observation is the public state we see (both farms, market,
# town, clock) plus their private state (shed, seeds, per-unit inventories),
# which we do not see. It starts empty and is carried forward by simulating
# each turn with an exact copy of the engine's rules: our own action (known),
# their predicted action, both farms and the market. Every turn the simulated
# result is checked against what we then observe (their money, their workers,
# their tiles, the market inventory); the first mismatch retires the shadow for
# the rest of the game, and the layer then passes the inner agent's action
# through untouched.
#
# While the shadow is in sync, the layer knows the opponent's exact market
# queue for the current turn and re-orders our own priced orders (never their
# quantities) to maximise our revenue minus theirs under the engine's slot-by-
# slot, unit-by-unit lockstep, instead of assuming the rival uses our parent's
# slots.

import copy as _sh_copy
import itertools as _sh_it
import json as _sh_json
import math as _sh_math
import time as _sh_time

# ---------------------------------------------------------------------------
# Engine replica (kaggle_environments/envs/kaggriculture/kaggriculture.py).
# ---------------------------------------------------------------------------
_SH_CROPS = {
    "WHEAT": {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT": {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO": {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON": {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
_SH_ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW": {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
_SH_PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
_SH_I0 = 10000
_SH_PARAMS = {
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
_SH_SHOPS = {
    "BAKERY": ["EGG", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
_SH_CENTER = [p for p in _SH_PRODUCTS if p != "FERTILIZER"]
_SH_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_SH_LAND_ORDER = ["NE", "SW", "SE"]
_SH_LAND_PRICES = [1000, 2000, 4000]
_SH_BOARD = 10
_SH_TPD = 24
_SH_CAP = 100


def _sh_shape(func, x, T):
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return _sh_math.sqrt(x)
    if func == "log":
        return _sh_math.log(1.0 + x)
    if func == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def sh_price(item, inventory):
    base, T, below, bt, above, at = _SH_PARAMS[item]
    if inventory < _SH_I0:
        amp = bt * base / _sh_shape(below, T, T)
        price = base + amp * _sh_shape(below, _SH_I0 - inventory, T)
    else:
        amp = at * base / _sh_shape(above, T, T)
        price = base - amp * _sh_shape(above, inventory - _SH_I0, T)
    return max(1, int(round(price)))


def _sh_quadrant(x, y):
    half = _SH_BOARD // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


_SH_ACCESS = [(4, 4), (5, 4), (4, 5), (5, 5)]


def _sh_default_spawn():
    for tile in _SH_ACCESS:
        if _sh_quadrant(tile[0], tile[1]) == "NW":
            return tile
    return (0, 0)


def _sh_new_plant(crop, day):
    cd = _SH_CROPS[crop]
    return {"kind": "PLANT", "crop": crop, "planted_day": day, "watered_today": False,
            "consecutive_unwatered": 1, "yield_units": 0 if cd["ongoing"] else 1,
            "max_lifespan_step": (-1 if cd["ongoing"] else (day + cd["max_yield_day"] + 1) * _SH_TPD),
            "fertilized_until_day": -1}


def _sh_new_animal(animal, day):
    return {"kind": _SH_ANIMALS[animal]["structure"], "animal": animal, "placed_day": day,
            "yield_units": 0, "consecutive_unfed": 0, "fed_today": False, "cared_today": False,
            "fertilizer_available": False, "pending_care_bonus": 0}


def _sh_inv_add(inv, item, n=1):
    inv[item] = inv.get(item, 0) + n


def _sh_inv_take(inv, item, n=1):
    if inv.get(item, 0) < n:
        return False
    inv[item] -= n
    if inv[item] == 0:
        del inv[item]
    return True


def _sh_unit(farm, private, idx, action, day):
    """engine._apply_unit_action (board 10, 24 turns, shed 100)."""
    if not isinstance(action, list) or not action:
        return
    op = action[0]
    if idx == 0:
        pos = farm["farmer"]
    else:
        pos = farm["hands"][idx - 1] if idx - 1 < len(farm["hands"]) else None
    if pos is None:
        return
    fx, fy = pos[0], pos[1]
    while len(private["inventories"]) <= idx:
        private["inventories"].append({})
    inv = private["inventories"][idx]
    if op in _SH_MOVES:
        dx, dy = _SH_MOVES[op]
        nx, ny = fx + dx, fy + dy
        if not (0 <= nx < _SH_BOARD and 0 <= ny < _SH_BOARD):
            return
        if idx == 0:
            farm["farmer"] = [nx, ny]
        else:
            farm["hands"][idx - 1] = [nx, ny]
        return
    if op == "PASS":
        return
    tile = farm["tiles"][fy][fx]
    adjacent = (fx, fy) in _SH_ACCESS
    if op == "DROP":
        if not adjacent:
            return
        shed = private["shed"]
        for item, n in list(inv.items()):
            if n <= 0:
                del inv[item]
                continue
            room = max(0, _SH_CAP - sum(shed.values()))
            take = min(n, room)
            if take > 0:
                shed[item] = shed.get(item, 0) + take
            del inv[item]
        return
    if op == "PICKUP":
        if not adjacent or len(action) < 2:
            return
        item = action[1]
        n = int(action[2]) if len(action) >= 3 else 1
        if n <= 0:
            return
        n = min(n, private["shed"].get(item, 0))
        if n <= 0:
            return
        private["shed"][item] -= n
        _sh_inv_add(inv, item, n)
        return
    if op == "PLACE":
        if len(action) < 2:
            return
        item = action[1]
        if (item in _SH_ANIMALS and isinstance(tile, dict)
                and tile.get("kind") == _SH_ANIMALS[item]["structure"] and "animal" not in tile):
            if _sh_inv_take(inv, item, 1):
                farm["tiles"][fy][fx] = _sh_new_animal(item, day)
            return
        if adjacent:
            n = int(action[2]) if len(action) >= 3 else 1
            if n <= 0:
                return
            n = min(n, inv.get(item, 0))
            if n <= 0:
                return
            room = max(0, _SH_CAP - sum(private["shed"].values()))
            n = min(n, room)
            if n <= 0:
                return
            inv[item] -= n
            if inv[item] == 0:
                del inv[item]
            private["shed"][item] = private["shed"].get(item, 0) + n
        return
    if tile == "LOCKED":
        return
    if op == "PLANT":
        if len(action) < 2:
            return
        crop = action[1]
        if crop not in _SH_CROPS or tile is not None:
            return
        if private["seeds"].get(crop, 0) <= 0:
            return
        private["seeds"][crop] -= 1
        farm["tiles"][fy][fx] = _sh_new_plant(crop, day)
        return
    if op == "WATER":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT") or tile["watered_today"]:
            return
        tile["watered_today"] = True
        cd = _SH_CROPS[tile["crop"]]
        if not cd["ongoing"]:
            age = day - tile["planted_day"]
            if (cd["max_yield_day"] + 1) // 2 <= age <= cd["max_yield_day"]:
                bonus = 2 if tile["fertilized_until_day"] >= day else 1
                tile["yield_units"] = min(cd["max_yield"], tile["yield_units"] + bonus)
        return
    if op == "HARVEST":
        if not isinstance(tile, dict) or tile.get("yield_units", 0) <= 0:
            return
        if tile.get("kind") == "PLANT":
            cd = _SH_CROPS[tile["crop"]]
            if day - tile["planted_day"] < cd["first_yield_day"]:
                return
            units = tile["yield_units"]
            tile["yield_units"] = 0
            _sh_inv_add(inv, tile["crop"], units)
            if not cd["ongoing"]:
                farm["tiles"][fy][fx] = None
        elif "animal" in tile:
            units = tile["yield_units"]
            tile["yield_units"] = 0
            _sh_inv_add(inv, _SH_ANIMALS[tile["animal"]]["product"], units)
        return
    if op == "FERTILIZE":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return
        if not _sh_inv_take(inv, "FERTILIZER", 1):
            return
        tile["fertilized_until_day"] = max(tile.get("fertilized_until_day", -1), day + 2)
        return
    if op == "DIG":
        if tile is None or (isinstance(tile, dict) and "animal" in tile):
            return
        farm["tiles"][fy][fx] = None
        return
    if op == "BUILD_COOP":
        if tile is None:
            farm["tiles"][fy][fx] = {"kind": "COOP"}
        return
    if op == "BUILD_PASTURE":
        if tile is None:
            farm["tiles"][fy][fx] = {"kind": "PASTURE"}
        return
    if op == "FEED":
        if not (isinstance(tile, dict) and "animal" in tile) or tile["fed_today"]:
            return
        if not _sh_inv_take(inv, "WHEAT", 1):
            return
        tile["fed_today"] = True
        return
    if op == "COLLECT_FERTILIZER":
        if not (isinstance(tile, dict) and "animal" in tile) or not tile["fertilizer_available"]:
            return
        tile["fertilizer_available"] = False
        _sh_inv_add(inv, "FERTILIZER", 1)
        return
    if op == "CARE":
        if not (isinstance(tile, dict) and "animal" in tile) or tile["cared_today"]:
            return
        tile["cared_today"] = True
        return


def sh_units(farm, private, action, day):
    """The interpreter's per-player unit phase, including the atomic PLANT rule."""
    action = action if isinstance(action, dict) else {}
    farmer = action.get("farmer", ["PASS"])
    hands = action.get("hands", [])
    if not isinstance(hands, list):
        hands = []
    demand = {}
    for a in [farmer, *hands]:
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
            demand[a[1]] = demand.get(a[1], 0) + 1
    seeds = private.get("seeds", {})
    blocked = {c for c, n in demand.items() if n > seeds.get(c, 0)}

    def allowed(a):
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT" and a[1] in blocked:
            return ["PASS"]
        return a
    _sh_unit(farm, private, 0, allowed(farmer), day)
    for i, a in enumerate(hands):
        _sh_unit(farm, private, i + 1, allowed(a), day)


def _sh_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _sh_spawn_hand(farm):
    occ = {t: 0 for t in _SH_ACCESS}
    for p in [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]:
        if p in occ:
            occ[p] += 1
    best = sorted(occ.items(), key=lambda kv: (kv[1], _SH_ACCESS.index(kv[0])))
    return list(best[0][0])


def _sh_parse(order):
    if not isinstance(order, list) or not order:
        return None
    op = order[0]
    if op in ("HIRE", "BUY_LAND"):
        return {"type": op}
    if op in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"):
        if len(order) < 3:
            return None
        try:
            n = int(order[2])
        except (TypeError, ValueError):
            return None
        if n <= 0:
            return None
        return {"type": op, "item": order[1], "remaining": n}
    return None


def _sh_commit(op, item, price, farm, private, inventory):
    if op == "SELL":
        if private["shed"].get(item, 0) <= 0:
            return False
        private["shed"][item] -= 1
        farm["money"] += price
        if price > 1:
            inventory[item] += 1
        return True
    if op == "BUY_PRODUCT":
        if farm["money"] < price or sum(private["shed"].values()) >= _SH_CAP:
            return False
        farm["money"] -= price
        private["shed"][item] = private["shed"].get(item, 0) + 1
        inventory[item] -= 1
        return True
    if op == "BUY_SEED":
        if farm["money"] < price:
            return False
        farm["money"] -= price
        private["seeds"][item] = private["seeds"].get(item, 0) + 1
        return True
    if op == "BUY_ANIMAL":
        if farm["money"] < price or sum(private["shed"].values()) >= _SH_CAP:
            return False
        farm["money"] -= price
        private["shed"][item] = private["shed"].get(item, 0) + 1
        return True
    return False


def sh_market(farms, privates, queues, inventory, log=None):
    """engine._process_market on plain dicts. `log` collects (slot, player, op, item, price)."""
    queues = [list(q)[:10] if isinstance(q, list) else [] for q in queues]
    for i in range(max((len(q) for q in queues), default=0)):
        states = [(_sh_parse(q[i]) if i < len(q) else None) for q in queues]
        for p, st in enumerate(states):
            if st is None:
                continue
            if st["type"] == "HIRE":
                farm = farms[p]
                cost = _sh_fib(farm["hires_today"])
                if farm["money"] >= cost:
                    farm["money"] -= cost
                    farm["hires_today"] += 1
                    farm["hands"].append(_sh_spawn_hand(farm))
                    privates[p]["inventories"].append({})
                states[p] = None
            elif st["type"] == "BUY_LAND":
                farm = farms[p]
                extra = len(farm["unlocked_quadrants"]) - 1
                if extra < len(_SH_LAND_ORDER) and farm["money"] >= _SH_LAND_PRICES[extra]:
                    farm["money"] -= _SH_LAND_PRICES[extra]
                    quad = _SH_LAND_ORDER[extra]
                    farm["unlocked_quadrants"].append(quad)
                    for y in range(_SH_BOARD):
                        for x in range(_SH_BOARD):
                            if _sh_quadrant(x, y) == quad and farm["tiles"][y][x] == "LOCKED":
                                farm["tiles"][y][x] = None
                states[p] = None
        guard = 0
        while True:
            guard += 1
            if guard >= 100000:
                break
            quoted = [None, None]
            for p, st in enumerate(states):
                if st is None or st["remaining"] <= 0:
                    continue
                op, item = st["type"], st["item"]
                if op == "SELL" and item in _SH_PARAMS:
                    quoted[p] = (op, item, sh_price(item, inventory[item]), st)
                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                    quoted[p] = (op, item, sh_price(item, inventory[item] - 1), st)
                elif op == "BUY_SEED" and item in _SH_CROPS:
                    quoted[p] = (op, item, _SH_CROPS[item]["seed"], st)
                elif op == "BUY_ANIMAL" and item in _SH_ANIMALS:
                    quoted[p] = (op, item, _SH_ANIMALS[item]["cost"], st)
                else:
                    states[p] = None
            if quoted[0] is None and quoted[1] is None:
                break
            committed = False
            for p, q in enumerate(quoted):
                if q is None:
                    continue
                op, item, price, st = q
                if _sh_commit(op, item, price, farms[p], privates[p], inventory):
                    st["remaining"] -= 1
                    committed = True
                    if log is not None:
                        log.append((i, p, op, item, price))
                else:
                    states[p] = None
            if not committed:
                break


def sh_town(inventory, shops, step):
    if step % 4 == 0:
        for shop in shops:
            products = _SH_SHOPS[shop]
            mult = 2 if len(products) == 1 else 1
            for item in products:
                inventory[item] -= mult
    if step % 24 == 0:
        for item in _SH_CENTER:
            inventory[item] -= 1


def _sh_decay(farm, step):
    for y in range(_SH_BOARD):
        for x in range(_SH_BOARD):
            tile = farm["tiles"][y][x]
            if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
                continue
            mls = tile["max_lifespan_step"]
            if mls < 0 or step < mls or (step - mls) % 2 != 0:
                continue
            tile["yield_units"] -= 1
            if tile["yield_units"] <= 0:
                farm["tiles"][y][x] = {"kind": "WEED"}


def _sh_refresh_plants(farm, day):
    nd = day + 1
    for y in range(_SH_BOARD):
        for x in range(_SH_BOARD):
            tile = farm["tiles"][y][x]
            if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
                continue
            watered = tile["watered_today"]
            tile["consecutive_unwatered"] = 0 if watered else tile["consecutive_unwatered"] + 1
            tile["watered_today"] = False
            if tile["consecutive_unwatered"] >= 2:
                farm["tiles"][y][x] = {"kind": "WEED"}
                continue
            cd = _SH_CROPS[tile["crop"]]
            if not cd["ongoing"]:
                continue
            since = nd - tile["planted_day"] - cd["first_yield_day"]
            if since < 0 or since % cd["interval"] != 0:
                continue
            count = since // cd["interval"] + 1
            if count > cd["max_yield"]:
                continue
            fert = watered and tile.get("fertilized_until_day", -1) >= day
            tile["yield_units"] = min(cd["max_yield"], tile["yield_units"] + (2 if fert else 1))
            if count == cd["max_yield"]:
                tile["max_lifespan_step"] = (nd + 1) * _SH_TPD


def _sh_refresh_animals(farm, day):
    nd = day + 1
    for y in range(_SH_BOARD):
        for x in range(_SH_BOARD):
            tile = farm["tiles"][y][x]
            if not (isinstance(tile, dict) and "animal" in tile):
                continue
            tile["consecutive_unfed"] = 0 if tile["fed_today"] else tile["consecutive_unfed"] + 1
            if tile["consecutive_unfed"] >= 2:
                farm["tiles"][y][x] = {"kind": _SH_ANIMALS[tile["animal"]]["structure"]}
                continue
            a = _SH_ANIMALS[tile["animal"]]
            since = nd - tile["placed_day"] - a["first_yield_day"]
            if since >= 0 and since % a["interval"] == 0:
                bonus = tile.pop("pending_care_bonus", 0) if tile["fed_today"] else 0
                tile["yield_units"] = min(a["max_held"], tile["yield_units"] + 1 + bonus)
                tile["pending_care_bonus"] = 0
            if tile["cared_today"] and tile["fed_today"]:
                tile["pending_care_bonus"] = tile.get("pending_care_bonus", 0) + 1
            tile["fertilizer_available"] = True
            tile["fed_today"] = False
            tile["cared_today"] = False


def _sh_night_drop(private):
    shed = private["shed"]
    for inv in private["inventories"]:
        for item, n in list(inv.items()):
            if n <= 0:
                del inv[item]
                continue
            room = max(0, _SH_CAP - sum(shed.values()))
            take = min(n, room)
            if take > 0:
                shed[item] = shed.get(item, 0) + take
            del inv[item]
    private["inventories"] = [{}]


def sh_transition(farms, privates, market_inventory, shops, actions, step, log=None):
    """One engine step on copies (weeds and shop unlocks, which need the hidden
    seed, are not simulated). Returns (farms, privates, inventory)."""
    farms = _sh_copy.deepcopy(farms)
    privates = _sh_copy.deepcopy(privates)
    inventory = dict(market_inventory)
    day = step // _SH_TPD
    for p in (0, 1):
        sh_units(farms[p], privates[p], actions[p], day)
    queues = [(a.get("market", []) if isinstance(a, dict) else []) for a in actions]
    sh_market(farms, privates, queues, inventory, log)
    sh_town(inventory, shops, step)
    for farm in farms:
        _sh_decay(farm, step)
    if (step + 1) % _SH_TPD == 0:
        for p in (0, 1):
            _sh_refresh_plants(farms[p], day)
            _sh_refresh_animals(farms[p], day)
            _sh_night_drop(privates[p])
            farms[p]["farmer"] = list(_sh_default_spawn())
            farms[p]["hands"] = []
            farms[p]["hires_today"] = 0
    return farms, privates, inventory


def sh_new_private():
    return {"shed": {item: 0 for item in _SH_PRODUCTS + list(_SH_ANIMALS)},
            "seeds": {crop: 0 for crop in _SH_CROPS}, "inventories": [{}]}


def _sh_tiles_match(pred, seen, night):
    for y in range(_SH_BOARD):
        for x in range(_SH_BOARD):
            a, b = pred[y][x], seen[y][x]
            if a == b:
                continue
            if night and a is None and isinstance(b, dict) and b.get("kind") == "WEED":
                continue          # a weed spawned at the day-end refresh
            return False
    return True


def sh_farm_match(pred, seen, night):
    """Everything public about one farm that its owner's actions determine."""
    if float(pred["money"]) != float(seen["money"]):
        return "money"
    if list(pred["farmer"]) != list(seen["farmer"]):
        return "farmer"
    if [list(h) for h in pred["hands"]] != [list(h) for h in seen["hands"]]:
        return "hands"
    if list(pred["unlocked_quadrants"]) != list(seen["unlocked_quadrants"]):
        return "quadrants"
    if int(pred.get("hires_today", 0)) != int(seen.get("hires_today", 0)):
        return "hires"
    if not _sh_tiles_match(pred["tiles"], seen["tiles"], night):
        return "tiles"
    return None


# ---------------------------------------------------------------------------
# Market queue: exact lockstep margin and the best permutation of our orders.
# ---------------------------------------------------------------------------
_SH_PRICED = ("SELL", "BUY_PRODUCT")


def sh_lockstep_margin(ours, theirs, inventory, stock_ours, stock_theirs):
    """Our revenue minus theirs from the priced orders of one turn, per the
    engine's slot-by-slot unit lockstep (money assumed sufficient for buys).
    Returns (margin, our_revenue, their_revenue)."""
    inv = dict(inventory)
    stock = [dict(stock_ours), dict(stock_theirs)]
    rev = [0.0, 0.0]
    queues = [ours, theirs]
    for i in range(max(len(ours), len(theirs))):
        rem = [None, None]
        for p in (0, 1):
            if i < len(queues[p]):
                o = queues[p][i]
                if isinstance(o, list) and len(o) >= 3 and o[0] in _SH_PRICED and o[1] in _SH_PARAMS:
                    try:
                        n = int(o[2])
                    except (TypeError, ValueError):
                        n = 0
                    if n > 0 and (o[0] == "SELL" or o[1] in ("WHEAT", "FERTILIZER")):
                        rem[p] = [o[0], o[1], n]
        while rem[0] is not None or rem[1] is not None:
            quoted = [None, None]
            for p in (0, 1):
                r = rem[p]
                if r is None:
                    continue
                if r[2] <= 0:
                    rem[p] = None
                    continue
                if r[0] == "SELL":
                    if stock[p].get(r[1], 0) <= 0:
                        rem[p] = None
                        continue
                    quoted[p] = sh_price(r[1], inv[r[1]])
                else:
                    quoted[p] = sh_price(r[1], inv[r[1]] - 1)
            if quoted[0] is None and quoted[1] is None:
                break
            for p in (0, 1):
                if quoted[p] is None:
                    continue
                r = rem[p]
                price = quoted[p]
                if r[0] == "SELL":
                    stock[p][r[1]] -= 1
                    rev[p] += price
                    if price > 1:
                        inv[r[1]] += 1
                else:
                    stock[p][r[1]] = stock[p].get(r[1], 0) + 1
                    rev[p] -= price
                    inv[r[1]] -= 1
                r[2] -= 1
    return rev[0] - rev[1], rev[0], rev[1]


# Exhaustive search costs one full lockstep simulation per permutation: 5,040
# for seven orders took ~3 s on the day-27 sell-off turn (Kaggle allows 1 s per
# turn plus a 60 s reserve). Above this many orders the search switches to an
# exact assignment solve.
_SH_EXHAUSTIVE_MAX = 5


def _sh_best_order_assign(priced, other, theirs, inventory, stock_ours, stock_theirs,
                          base, fallback):
    """Exact best order when every priced order is for a different item.

    The lockstep simulation keeps items separate (per-item stock and market
    inventory; money is not simulated), so an item's revenue depends only on
    which slot our order for it takes relative to the opponent's orders.
    margin(order) = margin(no priced orders) + sum over items of gain(item, slot),
    which makes the search an assignment problem: n*n single-item simulations,
    then a subset DP over (items placed, next slot) -- about 10^4 steps for 10
    orders instead of 10! simulations. Ties keep the lowest item index.
    """
    n = len(priced)
    hole = ["PASS_SLOT"]                     # a non-priced placeholder occupying a slot
    empty = sh_lockstep_margin([], theirs, inventory, stock_ours, stock_theirs)[0]
    gain = [[sh_lockstep_margin([hole] * k + [priced[j]], theirs, inventory,
                                stock_ours, stock_theirs)[0] - empty
             for k in range(n)] for j in range(n)]
    size = 1 << n
    neg = float("-inf")
    dp = [neg] * size
    choice = [-1] * size
    dp[0] = 0.0
    for mask in range(size):
        if dp[mask] == neg:
            continue
        k = bin(mask).count("1")
        if k >= n:
            continue
        for j in range(n):
            if mask & (1 << j):
                continue
            nxt = mask | (1 << j)
            val = dp[mask] + gain[j][k]
            if val > dp[nxt] + 1e-9:
                dp[nxt] = val
                choice[nxt] = j
    order, mask = [], size - 1
    while mask:
        j = choice[mask]
        order.append(j)
        mask &= ~(1 << j)
    order.reverse()
    best_val = empty + dp[size - 1]
    if best_val <= base + 1e-9:
        return fallback, 0.0
    return [priced[j] for j in order] + other, best_val - base


def sh_best_order(ours, theirs, inventory, stock_ours, stock_theirs, max_perm=5040):
    """Permute our priced orders (quantities unchanged) to maximise the lockstep
    margin against the opponent's known queue; non-priced orders keep their
    relative order behind the priced ones (like market_front). Returns
    (new_queue, gain) with gain >= 0 against our queue as given."""
    orders = [o for o in (ours or []) if o]
    priced = [o for o in orders if isinstance(o, list) and len(o) >= 3 and o[0] in _SH_PRICED]
    other = [o for o in orders if not (isinstance(o, list) and len(o) >= 3 and o[0] in _SH_PRICED)]
    base = sh_lockstep_margin(list(ours or []), theirs, inventory, stock_ours, stock_theirs)[0]
    if len(priced) < 1:
        return list(ours or []), 0.0
    items = [o[1] for o in priced]
    if len(priced) > _SH_EXHAUSTIVE_MAX and len(set(items)) == len(items):
        return _sh_best_order_assign(priced, other, theirs, inventory, stock_ours,
                                     stock_theirs, base, list(ours or []))
    if len(priced) > _SH_EXHAUSTIVE_MAX:
        max_perm = min(max_perm, 120)   # repeated items: bounded, deterministic search
    best, best_val = None, base
    seen = set()
    count = 0
    for perm in _sh_it.permutations(range(len(priced))):
        key = tuple(_sh_json.dumps(priced[j]) for j in perm)
        if key in seen:
            continue
        seen.add(key)
        count += 1
        if count > max_perm:
            break
        cand = [priced[j] for j in perm] + other
        val = sh_lockstep_margin(cand, theirs, inventory, stock_ours, stock_theirs)[0]
        if val > best_val + 1e-9:
            best, best_val = cand, val
    if best is None:
        return list(ours or []), 0.0
    return best, best_val - base


# ---------------------------------------------------------------------------
# Cloning a program instance's state (for one-turn-ahead predictions).
# A's mutable state is its module-level containers plus the Chassis object in
# _IMPL's closure; its route tapes are constant after the first turn and are
# shared by reference, never copied.
# ---------------------------------------------------------------------------
import collections as _sh_coll
import types as _sh_types

_SH_SHARED = ("_ROUTES", "_PIPE_RAW", "_R108_SHOP_ROUTES", "_PLANNER_NS", "__builtins__")
_SH_CHASSIS_SHARED = ("routes", "router", "cfg")
_SH_BIG = 50000          # bytes pickled: containers this large are constant tables


def _sh_size(v):
    import pickle
    try:
        return len(pickle.dumps(v, protocol=4))
    except Exception:
        return -1


def _sh_is_stateobj(v):
    return (hasattr(v, "__dict__") and not isinstance(
        v, (_sh_types.FunctionType, _sh_types.ModuleType, type, _sh_types.BuiltinFunctionType,
            _sh_types.MethodType)))


def sh_clone_plan(env):
    """Which globals hold state (copied by value each clone) and which are
    constant tables (shared by reference). Computed once per program, on a
    namespace that has already played its first turn."""
    names, shared = [], []
    for k, v in env.items():
        if k.startswith("__"):
            continue
        if isinstance(v, (dict, list, set, _sh_coll.deque)):
            size = _sh_size(v)
            if k in _SH_SHARED or size > _SH_BIG or (size < 0 and isinstance(v, dict)
                                                     and any(callable(x) for x in v.values())):
                shared.append(k)
            else:
                names.append(k)
    objs = []                      # state objects held in function closures (A: the Chassis)
    seen = set()
    for k, v in env.items():
        if isinstance(v, _sh_types.FunctionType):
            for c in (v.__closure__ or ()):
                try:
                    o = c.cell_contents
                except ValueError:
                    continue
                if _sh_is_stateobj(o) and id(o) not in seen:
                    seen.add(id(o))
                    attrs = [a for a, x in vars(o).items()
                             if not callable(x) and a not in _SH_CHASSIS_SHARED and _sh_size(x) <= _SH_BIG]
                    objs.append((k, attrs))
    return {"names": names, "shared": shared, "objs": objs}


def _sh_closure_obj(env, fname):
    f = env.get(fname)
    for c in (getattr(f, "__closure__", None) or ()):
        try:
            o = c.cell_contents
        except ValueError:
            continue
        if _sh_is_stateobj(o):
            return o
    return None


def sh_clone_into(src, dst, plan=None):
    """Make namespace `dst` (a second instance of the same program) continue
    exactly where `src` is: copy every state container by value in one
    deepcopy (aliasing preserved), rebind it in `dst`, share constant tables."""
    plan = plan or sh_clone_plan(src)
    objs_src = [(_sh_closure_obj(src, f), _sh_closure_obj(dst, f), attrs) for f, attrs in plan["objs"]]
    values = [src[k] for k in plan["names"]]
    obj_vals = [{a: getattr(o, a) for a in attrs if hasattr(o, a)} for o, _, attrs in objs_src if o is not None]
    copied_values, copied_objs = _sh_copy.deepcopy((values, obj_vals))
    for k, v in zip(plan["names"], copied_values):
        dst[k] = v
    for k in plan["shared"]:
        dst[k] = src[k]
    i = 0
    for o_src, o_dst, attrs in objs_src:
        if o_src is None:
            continue
        vals = copied_objs[i]
        i += 1
        if o_dst is None:
            continue
        for a, x in vars(o_src).items():   # large constant tables: share; callables: keep dst's own
            if a not in vals and not callable(x):
                setattr(o_dst, a, x)
        for a, x in vals.items():
            setattr(o_dst, a, x)
    return plan


# ---------------------------------------------------------------------------
# The shadow: a fresh instance of a known program fed the opponent's view.
# ---------------------------------------------------------------------------
def _sh_plain(x):
    return _sh_json.loads(_sh_json.dumps(x))


_SH_PLAIN_CACHE = {"key": None, "val": None}
_SH_VERIFY_CACHE = {}   # one turn's shared engine steps (see OpponentShadow._verify)
_SH_PREV_CACHE = {}     # one turn's shared decoded public state (see observe)


def _sh_plain_public(obs):
    """JSON copies of the public parts of this turn's observation, shared by
    every shadow (callers must not mutate them)."""
    key = (id(obs), int(obs["step"]))
    if _SH_PLAIN_CACHE["key"] != key:
        _SH_PLAIN_CACHE["key"] = key
        _SH_PLAIN_CACHE["val"] = {"farms": _sh_json.dumps(obs["farms"]), "market": _sh_json.dumps(obs["market"]),
                                  "town": _sh_json.dumps(obs["town"]), "private": _sh_json.dumps(obs["private"])}
    return _SH_PLAIN_CACHE["val"]


def _sh_norm(action):
    a = action if isinstance(action, dict) else {}
    return {"farmer": list(a.get("farmer") or ["PASS"]),
            "hands": [list(h) for h in (a.get("hands") or [])],
            "market": [list(o) if isinstance(o, (list, tuple)) else o for o in (a.get("market") or [])]}


class OpponentShadow:
    """Track one candidate program against the opponent, turn by turn.

    observe(own_obs, cfg) must be called at the start of every one of our
    turns (from step 0), and record_own_action(action) with the action we
    actually return. After observe(), .pred is the opponent's predicted action
    for this turn and .in_sync says whether every past prediction matched.
    lookahead(obs, cfg, our_action) predicts their NEXT action given ours,
    from a clone of the shadow (the shadow itself is never disturbed).
    """

    def __init__(self, program="A", seat=None, factory=None, lookahead=False):
        self.program = program
        self.factory = factory
        self.wants_lookahead = lookahead
        self.env = self.agent = None
        self.env2 = self.agent2 = None
        self.clone_plan = None
        self.seat = seat
        self.in_sync = False
        self.pred = None
        self.prev = None           # (public obs dict, own private, opp private, step)
        self.own_action = None
        self.opp_private = None
        self.last_step = -1
        self.stats = {}
        self._clear_stats()

    def _clear_stats(self):
        self.stats = {"turns": 0, "sync_turns": 0, "lost_at": None, "lost_reason": None,
                      "ms": 0.0, "own_model_miss": 0, "errors": 0, "lookaheads": 0,
                      "lookahead_ms": 0.0}

    def _fresh(self):
        if self.factory is not None:
            return self.factory()
        from rl.candidate_l import parent_namespace
        return parent_namespace()

    def reset(self, seat, lookahead=False):
        self.seat = seat
        self.env, self.agent = self._fresh()
        if lookahead and self.env2 is None:
            self.env2, self.agent2 = self._fresh()   # pay the exec cost on turn 0
        self.in_sync = True
        self.opp_private = sh_new_private()
        self.prev = None
        self.own_action = None
        self.pred = None
        self._clear_stats()

    def _lose(self, step, reason):
        if self.in_sync:
            self.in_sync = False
            self.stats["lost_at"] = step
            self.stats["lost_reason"] = reason
            self.env = self.env2 = self.agent2 = None
            self.clone_plan = None
            self.agent = False          # retired: not None, so observe() does not restart it

    def _verify(self, obs):
        """Simulate last turn with our action and the predicted one; compare."""
        pub, own_priv, opp_priv, step = self.prev
        me = self.seat
        opp = 1 - me
        privates = [None, None]
        privates[me], privates[opp] = own_priv, opp_priv
        actions = [None, None]
        actions[me], actions[opp] = self.own_action or {}, self.pred or {}
        # Shadows that tracked the same opponent state and predicted the same
        # move run the identical engine step (in the opening every lineage
        # program does): simulate it once per turn and share the result
        # read-only (sh_transition copies its inputs; the tracked private
        # state below is copied per shadow).
        key = (step, me, _sh_json.dumps(opp_priv, sort_keys=True),
               _sh_json.dumps(self.pred or {}, sort_keys=True),
               _sh_json.dumps(self.own_action or {}, sort_keys=True))
        if _SH_VERIFY_CACHE.get("step") != step:
            _SH_VERIFY_CACHE.clear()
            _SH_VERIFY_CACHE["step"] = step
        hit = _SH_VERIFY_CACHE.get(key)
        if hit is None:
            hit = sh_transition(pub["farms"], privates, pub["market"]["inventory"],
                                pub["town"]["unlocked_shops"], actions, step)
            _SH_VERIFY_CACHE[key] = hit
        farms, privs, inv = hit
        night = (step + 1) % _SH_TPD == 0
        seen = obs["farms"]
        own_bad = sh_farm_match(farms[me], seen[me], night)
        if own_bad is None and privs[me]["shed"] != obs["private"]["shed"]:
            own_bad = "own shed"
        if own_bad is not None:
            self.stats["own_model_miss"] += 1
            return f"own model: {own_bad}"
        bad = sh_farm_match(farms[opp], seen[opp], night)
        if bad is not None:
            return bad
        if {k: int(v) for k, v in inv.items()} != {k: int(v) for k, v in obs["market"]["inventory"].items()}:
            return "market"
        self.opp_private = _sh_plain(privs[opp])     # own copy: the result may be shared
        return None

    def view_for(self, obs):
        step = int(obs["step"])
        pub = _sh_plain_public(obs)
        return {"remainingOverageTime": 60, "step": step, "player": 1 - self.seat,
                "farms": _sh_json.loads(pub["farms"]), "private": _sh_plain(self.opp_private),
                "market": _sh_json.loads(pub["market"]), "town": _sh_json.loads(pub["town"]),
                "day": int(obs.get("day", step // 24)), "hour": int(obs.get("hour", step % 24))}

    def observe(self, obs, cfg=None):
        step = int(obs["step"])
        seat = int(obs["player"])
        if step == 0 or self.agent is None or step <= self.last_step:
            self.reset(seat, self.wants_lookahead)
            if step != 0:
                self._lose(step, "started late")
        self.last_step = step
        self.stats["turns"] += 1
        started = _sh_time.perf_counter()
        try:
            if self.in_sync and self.prev is not None:
                if self.prev[3] != step - 1:
                    self._lose(step, "skipped turn")
                else:
                    reason = self._verify(obs)
                    if reason is not None:
                        self._lose(step, reason)
            if self.in_sync:
                self.pred = _sh_norm(self.agent(self.view_for(obs), cfg))
                self.stats["sync_turns"] += 1
                # The public part and our own private state are the same for
                # every shadow this turn and only ever read (sh_transition
                # copies them), so they are decoded once per turn and shared.
                if _SH_PREV_CACHE.get("step") != step or _SH_PREV_CACHE.get("id") != id(obs):
                    pub = _sh_plain_public(obs)
                    _SH_PREV_CACHE.update(step=step, id=id(obs), val=(
                        {"farms": _sh_json.loads(pub["farms"]), "market": _sh_json.loads(pub["market"]),
                         "town": _sh_json.loads(pub["town"])}, _sh_json.loads(pub["private"])))
                shared_pub, shared_own = _SH_PREV_CACHE["val"]
                self.prev = (shared_pub, shared_own, _sh_copy.deepcopy(self.opp_private), step)
            else:
                self.pred = None
        except Exception as error:  # a shadow must never break the real agent
            self.stats["errors"] += 1
            self._lose(step, f"error {type(error).__name__}: {error}")
            self.pred = None
        self.stats["ms"] += (_sh_time.perf_counter() - started) * 1000.0
        return {"step": step, "in_sync": self.in_sync, "pred": self.pred}

    def lookahead(self, obs, cfg, our_action):
        """Their predicted action NEXT turn if we play `our_action` now, plus
        the simulated state it was computed on. None across a day boundary
        (weeds and shop draws come from the hidden seed) or out of sync."""
        step = int(obs["step"])
        if not self.in_sync or self.pred is None or (step + 1) % _SH_TPD == 0 or step >= 718:
            return None
        started = _sh_time.perf_counter()
        me, opp = self.seat, 1 - self.seat
        privates = [None, None]
        privates[me], privates[opp] = _sh_plain(obs["private"]), self.opp_private
        actions = [None, None]
        actions[me], actions[opp] = _sh_norm(our_action), self.pred
        farms, privs, inv = sh_transition(_sh_plain(obs["farms"]), privates, obs["market"]["inventory"],
                                          list(obs["town"]["unlocked_shops"]), actions, step)
        view = {"remainingOverageTime": 60, "step": step + 1, "player": opp,
                "farms": _sh_plain(farms), "private": _sh_plain(privs[opp]),
                "market": {"inventory": {k: int(v) for k, v in inv.items()},
                           "prices": {k: sh_price(k, int(v)) for k, v in inv.items()}},
                "town": _sh_plain(obs["town"]), "day": (step + 1) // _SH_TPD,
                "hour": (step + 1) % _SH_TPD}
        if self.env2 is None:
            self.env2, self.agent2 = self._fresh()
        if self.clone_plan is None:
            self.clone_plan = sh_clone_plan(self.env)
        sh_clone_into(self.env, self.env2, self.clone_plan)
        pred_next = _sh_norm(self.agent2(view, cfg))
        self.stats["lookaheads"] += 1
        self.stats["lookahead_ms"] += (_sh_time.perf_counter() - started) * 1000.0
        return {"pred": pred_next, "farms": farms, "privates": privs, "inventory": inv}

    def record_own_action(self, action):
        self.own_action = _sh_norm(action)

    def summary(self):
        out = dict(self.stats)
        out["ms_per_turn"] = round(out["ms"] / max(1, out["turns"]), 2)
        return out
# ---- END l2_shadow (core) ----


# ---------------------------------------------------------------------------
# Per-item valuation across turns (slot-by-slot, unit-by-unit lockstep).
# ---------------------------------------------------------------------------
_SH_CASH = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")


def sh_item_orders(market, item, stock):
    """Effective (slot, op, units) of one item in a queue, given the player's
    stock of it at market time (bought units can fund later sells)."""
    out = []
    left = int(stock)
    for slot, o in enumerate((market or [])[:10]):
        if not (isinstance(o, list) and len(o) >= 3 and o[1] == item):
            continue
        try:
            n = int(o[2])
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        if o[0] == "SELL":
            n = min(n, left)
            left -= n
            if n > 0:
                out.append((slot, "SELL", n))
        elif o[0] == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
            left += n
            out.append((slot, "BUY_PRODUCT", n))
    return out


def sh_item_path(item, inv0, turns):
    """turns: [(ours, theirs, consumption_after)], orders as (slot, op, units).
    Returns (our revenue, their revenue) for this item."""
    inv = int(inv0)
    rev = [0.0, 0.0]
    for ours, theirs, cons in turns:
        slots = sorted({s for s, _, _ in ours} | {s for s, _, _ in theirs})
        for s in slots:
            rem = [None, None]
            for p, orders in enumerate((ours, theirs)):
                q = [(op, n) for sl, op, n in orders if sl == s]
                if q:
                    rem[p] = [q[0][0], sum(n for _, n in q)]
            while any(r is not None and r[1] > 0 for r in rem):
                quote = [None, None]
                for p in (0, 1):
                    r = rem[p]
                    if r is not None and r[1] > 0:
                        quote[p] = sh_price(item, inv if r[0] == "SELL" else inv - 1)
                for p in (0, 1):
                    if quote[p] is None:
                        continue
                    r = rem[p]
                    if r[0] == "SELL":
                        rev[p] += quote[p]
                        if quote[p] > 1:
                            inv += 1
                    else:
                        rev[p] -= quote[p]
                        inv -= 1
                    r[1] -= 1
        inv -= cons
    return rev[0], rev[1]


def sh_consumption(shops, step, item):
    n = 0
    if step % 4 == 0:
        for shop in shops:
            products = _SH_SHOPS[shop]
            if item in products:
                n += 2 if len(products) == 1 else 1
    if step % 24 == 0 and item != "FERTILIZER":
        n += 1
    return n


# ---------------------------------------------------------------------------
# The layer: wraps the finished agent (l_stack(outer=...)).
# ---------------------------------------------------------------------------
def _sh_stock_at_market(farm, private, action, day):
    f = _sh_copy.deepcopy(farm)
    p = _sh_copy.deepcopy(private)
    sh_units(f, p, action, day)
    return p["shed"]


_SH_DEFAULTS = {
    "reorder": True,        # exact best permutation of our priced orders vs their queue
    "min_gain": 1.0,        # coins; below this keep the inner agent's queue
    "early": False,         # sell ahead of the opponent's predicted next-turn sale
    "early_min_gain": 5.0,  # coins of two-turn margin
    "early_items": _SH_CASH,
    "early_from": 96,       # never touch the scripted opening
    "early_budget_ms": 150,  # stop evaluating further items past this
    "early_max_items": 2,    # items evaluated per turn (each costs 1-2 lookaheads)
    # Several library programs can be in sync at once (near-twins such as
    # statma's submit and race variants). When True, early sales also run
    # while every in-sync program predicts the same move (L4); when False,
    # only with exactly one in sync (L2/L3 as tested).
    "early_when_agree": False,
}


def _sh_add_sell(market, item, n):
    market = [list(o) if isinstance(o, (list, tuple)) else o for o in (market or [])]
    for o in market:
        if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == item:
            o[2] = int(o[2]) + n
            return market
    for i, o in enumerate(market):
        if not o:                   # reuse an empty slot
            market[i] = ["SELL", item, n]
            return market
    if len(market) >= 10:
        return None
    market.append(["SELL", item, n])
    return market


def shadow_wrap(inner, programs=("A",), factories=None, **settings):
    cfg_layer = dict(_SH_DEFAULTS)
    cfg_layer.update(settings)
    factories = factories or {}
    shadows = [OpponentShadow(program=p, factory=factories.get(p) or (sh_program_factory(p) if len(programs) > 1 else None),
                              lookahead=bool(cfg_layer["early"]) and len(programs) == 1)
               for p in programs]
    report = {"shadow_sync_turns": 0, "shadow_lost": 0, "shadow_reorders": 0,
              "shadow_reorder_gain": 0.0, "shadow_errors": 0, "shadow_ms": 0.0,
              "shadow_turns": 0, "early_sales": 0, "early_units": 0,
              "early_pred_gain": 0.0, "early_rejected_react": 0, "shadow_max_ms": 0.0,
              "early_budget_stops": 0, "shadow_slow_turns": 0, "shadow_disagree_turns": 0,
              "shadow_insync_programs": 0, "early_multi_skips": 0}
    state = {"last_step": -1}
    events = []

    def reorder(observation, action, live, day):
        seat = int(observation["player"])
        ours = _sh_stock_at_market(observation["farms"][seat], observation["private"], action, day)
        theirs = _sh_stock_at_market(observation["farms"][1 - seat], live.opp_private, live.pred, day)
        new, gain = sh_best_order(action.get("market") or [], live.pred.get("market") or [],
                                  observation["market"]["inventory"], ours, theirs)
        return new, gain, ours, theirs

    def early(observation, configuration, action, live, step, ours, theirs):
        """Sell now what the opponent is about to sell next turn."""
        seat = int(observation["player"])
        day = step // 24
        market = action.get("market") or []
        free = {}
        for item in cfg_layer["early_items"]:
            sold = sum(n for _, op, n in sh_item_orders(market, item, ours.get(item, 0)) if op == "SELL")
            h = int(ours.get(item, 0)) - sold
            if h > 0 and sh_price(item, int(observation["market"]["inventory"][item])) > 1:
                free[item] = h
        if not free:
            return action
        look = live.lookahead(observation, configuration, action)
        if look is None:
            return action
        nxt = look["pred"]
        opp = 1 - seat
        next_day = (step + 1) // 24
        their_next_stock = _sh_stock_at_market(look["farms"][opp], look["privates"][opp], nxt, next_day)
        shops = list(observation["town"]["unlocked_shops"])
        inv0 = observation["market"]["inventory"]
        budget_end = _sh_time.perf_counter() + cfg_layer["early_budget_ms"] / 1000.0
        tried = 0
        for item, h in sorted(free.items(), key=lambda kv: -sh_price(kv[0], int(inv0[kv[0]])) * kv[1]):
            if _sh_time.perf_counter() > budget_end or tried >= cfg_layer["early_max_items"]:
                report["early_budget_stops"] += 1
                break
            theirs_next = sh_item_orders(nxt.get("market"), item, their_next_stock.get(item, 0))
            if not any(op == "SELL" for _, op, _ in theirs_next):
                continue
            tried += 1
            q_next = sum(n for _, op, n in theirs_next if op == "SELL")
            slot_next = min(s for s, op, _ in theirs_next if op == "SELL")
            cons = sh_consumption(shops, step, item)
            theirs_now = sh_item_orders(live.pred.get("market"), item, theirs.get(item, 0))
            ours_now = sh_item_orders(market, item, ours.get(item, 0))
            best = None
            for m in sorted({h, min(h, q_next)}):
                if m <= 0:
                    continue
                new_market = _sh_add_sell(market, item, m)
                if new_market is None:
                    continue
                cand = dict(action, market=new_market)
                if cfg_layer["reorder"]:
                    cm, _, _, _ = reorder(observation, cand, live, day)
                    cand = dict(cand, market=cm)
                ours_early = sh_item_orders(cand["market"], item, ours.get(item, 0))
                hold = sh_item_path(item, inv0[item], [(ours_now, theirs_now, cons),
                                                         ([(slot_next, "SELL", m)], theirs_next, 0)])
                look2 = live.lookahead(observation, configuration, cand)
                if look2 is None:
                    continue
                nxt2 = look2["pred"]
                stock2 = _sh_stock_at_market(look2["farms"][opp], look2["privates"][opp], nxt2, next_day)
                theirs_next2 = sh_item_orders(nxt2.get("market"), item, stock2.get(item, 0))
                if not any(op == "SELL" for _, op, _ in theirs_next2):
                    report["early_rejected_react"] += 1
                    continue
                early_rev = sh_item_path(item, inv0[item], [(ours_early, theirs_now, cons),
                                                              ([], theirs_next2, 0)])
                gain = (early_rev[0] - early_rev[1]) - (hold[0] - hold[1])
                if best is None or gain > best[0]:
                    best = (gain, m, cand)
            if best is not None and best[0] >= cfg_layer["early_min_gain"]:
                action = best[2]
                if len(events) < 400:
                    events.append({"t": step, "item": item, "units": best[1], "free": h,
                                   "their_next": q_next, "pred_gain": round(best[0], 1),
                                   "price": sh_price(item, int(inv0[item]))})
                report["early_sales"] += 1
                report["early_units"] += best[1]
                report["early_pred_gain"] += best[0]
                return action          # one item per turn: the next turn re-plans
        return action

    def shadow_agent(observation, configuration=None):
        step = int(observation.get("step", 0))
        if step == 0 or step <= state["last_step"]:
            for k in report:
                report[k] = 0.0 if isinstance(report[k], float) else 0
            del events[:]
        state["last_step"] = step
        started = _sh_time.perf_counter()
        live = None
        insync = []
        for sh in shadows:
            try:
                info = sh.observe(observation, configuration)
                if info["in_sync"] and sh.pred is not None:
                    insync.append(sh)
            except Exception:
                report["shadow_errors"] += 1
        if insync:
            if all(sh.pred == insync[0].pred for sh in insync[1:]):
                live = insync[0]
            else:
                report["shadow_disagree_turns"] += 1
        report["shadow_insync_programs"] = len(insync)
        action = inner(observation, configuration)
        try:
            if live is not None and live.pred is not None and isinstance(action, dict):
                report["shadow_sync_turns"] += 1
                day = step // 24
                seat = int(observation["player"])
                ours = _sh_stock_at_market(observation["farms"][seat], observation["private"], action, day)
                theirs = _sh_stock_at_market(observation["farms"][1 - seat], live.opp_private, live.pred, day)
                if cfg_layer["reorder"] and action.get("market"):
                    new, gain, _, _ = reorder(observation, action, live, day)
                    if gain >= cfg_layer["min_gain"]:
                        action = dict(action, market=new)
                        report["shadow_reorders"] += 1
                        report["shadow_reorder_gain"] += gain
                if cfg_layer["early"] and step >= cfg_layer["early_from"]:
                    if len(insync) == 1 or (cfg_layer["early_when_agree"] and live is not None):
                        action = early(observation, configuration, action, live, step, ours, theirs)
                    else:
                        report["early_multi_skips"] += 1
        except Exception:
            report["shadow_errors"] += 1
        for sh in shadows:
            try:
                sh.record_own_action(action)
            except Exception:
                report["shadow_errors"] += 1
        report["shadow_lost"] = sum(1 for sh in shadows if sh.stats.get("lost_at") is not None)
        report["shadow_turns"] += 1
        took = (_sh_time.perf_counter() - started) * 1000.0
        report["shadow_ms"] += took
        if step > 0:
            report["shadow_max_ms"] = max(report["shadow_max_ms"], took)
            report["shadow_slow_turns"] += took > 300.0
        return action

    shadow_agent.telemetry = report
    shadow_agent.shadows = shadows
    shadow_agent.events = events
    return shadow_agent



# ---------------------------------------------------------------------------
# Program library. Each entry is a program that ladder opponents run byte for
# byte (measured on our live games, rl/data/l2/shadow/opponent_programs.json).
# Programs found identical to one already listed are left out (nb_guru_master_v3,
# nb_tetsutani_demand and nb_tetsutani_mirror play exactly as A;
# nb_leoprovorov_forecast as nb_arsgorynich_herdsafe_v3; nb_tschinkel_2945 as
# nb_nihilistic_robust on the games seen).
# ---------------------------------------------------------------------------
SH_LIBRARY = ("A", "nb_arsgorynich_herdsafe_v3", "nb_haideptry_2965", "nb_guru_master_v4",
              "nb_dmitrii_herdsafe_2700", "nb_nihilistic_robust", "nb_tschinkel_metav4_v13",
              "nb_ahmed_v55")


_SH_CODE = {}      # compiled sources, once per process


def sh_program_factory(name):
    """Local factory: a fresh (namespace, entry) for a library program. A
    packaged submission must exec embedded verbatim sources instead."""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if name == "A":
        path = os.path.join(root, "submissions", "agent-a", "main.py")
    else:
        path = os.path.join(root, "rl", "public", name + ".py")

    def make():
        code = _SH_CODE.get(path)
        if code is None:
            with open(path, encoding="utf-8") as fh:
                code = _SH_CODE[path] = compile(fh.read(), path, "exec")
        env = {} if name == "A" else {"__name__": "shadow_" + name, "__file__": path}
        exec(code, env)
        if name == "A":            # exactly rl.candidate_l.parent_namespace
            return env, [v for v in env.values() if callable(v)][-1]
        if "NAMESPACE" in env and "KAGGLE_ENTRY" in env:   # wrapper that execs the real main.py
            return env["NAMESPACE"], env["KAGGLE_ENTRY"]
        return env["agent"].__globals__, env["agent"]
    return make

def _l_with(**settings):
    from rl.candidate_l import l_stack
    return l_stack(outer=lambda agent: shadow_wrap(agent, **settings))


def build():
    """L2 candidate: Agent L plus the opponent shadow (exact reorder only)."""
    return _l_with(reorder=True, early=False)


def build_early():
    """Agent L plus the shadow's one-turn-ahead early sales (no reorder)."""
    return _l_with(reorder=False, early=True)


def build_both():
    return _l_with(reorder=True, early=True)


def build_library_early():
    """Agent L plus early sales against any exact copy of a library program."""
    return _l_with(programs=SH_LIBRARY, reorder=False, early=True)


def build_observe():
    """Agent L with the shadow running but never acting (identical play; cost and sync telemetry)."""
    return _l_with(reorder=False, early=False)
# ---- END l2_shadow ----
