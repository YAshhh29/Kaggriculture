"""Endgame market policies, scored exactly on our live ladder games.

Every policy is an order-rewrite layer on our seat (see l2_endgame_bench):
our unit actions and the opponent's tape stay as recorded, the layer only
changes WHEN and HOW MANY units our SELL orders move. Games are replayed from
a day-24 snapshot, so one policy over all 148 A/L games takes ~20 s.

On L's games the rewritten orders are passed through L's own queue-order
layer (stack.market_front.mf_reorder) again, as the L+layer agent would.

    python -m tools.analysis.l2_endgame_policies run shift_d25 final717 ...
    python -m tools.analysis.l2_endgame_policies list
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_endgame_bench import Game  # noqa: E402
from tools.analysis.l2_endgame_log import OUT, records  # noqa: E402

SNAP = 576
SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
         "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
         "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
         "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
         "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
            "WOOL", "FERTILIZER"]


def tick_units(shops, item, step):
    """Units of ``item`` the town removes after the market at ``step``."""
    c = 0
    if step % 4 == 0:
        for s in shops:
            if item in SHOPS.get(s, ()):
                c += 2 if len(SHOPS[s]) == 1 else 1
    if step % 24 == 0 and item != "FERTILIZER":
        c += 1
    return c


def _sells(action):
    out = {}
    for o in action.get("market") or []:
        if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
            try:
                out[o[1]] = out.get(o[1], 0) + max(0, int(o[2]))
            except (TypeError, ValueError):
                pass
    return out


def projected_shed(obs, action):
    """Shed after this step's unit actions, before the market (engine rules:
    DROP moves all of a shed-adjacent unit's goods, overflow destroyed;
    PLACE moves up to room; PICKUP removes)."""
    private = obs["private"]
    shed = {k: int(v) for k, v in private["shed"].items()}
    farm = obs["farms"][obs["player"]]
    positions = [farm["farmer"]] + list(farm["hands"])
    units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    invs = list(private["inventories"])
    adj = {(4, 4), (5, 4), (4, 5), (5, 5)}
    total = sum(shed.values())
    for i, act in enumerate(units[:len(positions)]):
        if not act or tuple(positions[i]) not in adj:
            continue
        inv = invs[i] if i < len(invs) else {}
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
        elif op == "PLACE" and len(act) >= 2 and act[1] not in ("COW", "SHEEP", "GOOSE"):
            n = int(act[2]) if len(act) >= 3 else 1
            take = min(max(0, n), int(inv.get(act[1], 0)), max(0, 100 - total))
            shed[act[1]] = shed.get(act[1], 0) + take
            total += take
    return shed


def rewrite_sells(action, parent, wanted):
    """Make the market sell ``wanted[item]`` units per item, touching only the
    items whose quantity changes (the parent's own orders, slots and splits
    are kept for the rest). Returns (new_action, placed) where placed[item]
    is what could actually be placed (a new item needs a free slot)."""
    changed = {i for i in set(parent) | set(wanted)
               if wanted.get(i, 0) != parent.get(i, 0)}
    if not changed:
        return action, dict(wanted)
    market = [list(o) if isinstance(o, list) else o for o in action.get("market") or []]
    placed = {i: parent.get(i, 0) for i in parent}
    for item in changed:
        target = wanted.get(item, 0)
        slots = [k for k, o in enumerate(market)
                 if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == item]
        have = parent.get(item, 0)
        if target < have:
            cut = have - target
            for k in reversed(slots):
                q = int(market[k][2])
                take = min(q, cut)
                market[k][2] = q - take
                cut -= take
                if market[k][2] <= 0:
                    market[k] = []
                if cut <= 0:
                    break
            placed[item] = target
        elif target > have:
            if slots:
                market[slots[0]][2] = int(market[slots[0]][2]) + (target - have)
                placed[item] = target
            else:
                free = next((k for k, o in enumerate(market) if o == [] or o is None), None)
                if free is not None:
                    market[free] = ["SELL", item, target]
                    placed[item] = target
                elif len(market) < 10:
                    market.append(["SELL", item, target])
                    placed[item] = target
                else:
                    placed[item] = have
    return dict(action, market=market), placed


class Layer:
    """Delay-only sell ledger. ``owed[item]`` = units the parent asked to sell
    that are still in our shed. Every step from ``start`` the release rule
    decides how many owed units to sell now (never more than owed: the parent
    keeps every unit it wanted for feed / fertilizer / planting). From
    ``final`` on, everything in the shed is sold."""

    def __init__(self, start=600, final=717):
        self.start = start
        self.final = final
        self.owed = {}
        self.report = {"held_units": 0, "released_units": 0, "turns": 0}

    def __call__(self, obs, action):
        t = obs["step"]
        if t < self.start or not isinstance(action, dict):
            return action
        stock = projected_shed(obs, action)
        parent = {}
        for i, q in _sells(action).items():
            parent[i] = min(q, stock.get(i, 0))
        for i in set(self.owed) | set(parent):
            self.owed[i] = min(stock.get(i, 0), self.owed.get(i, 0) + parent.get(i, 0))
        if t >= self.final:
            for i in PRODUCTS:
                if stock.get(i, 0) > 0:
                    self.owed[i] = stock[i]
        want = {}
        for i, q in self.owed.items():
            if q > 0:
                want[i] = q if t >= self.final else max(
                    0, min(q, self.release(obs, action, t, i, q, stock)))
        new, placed = rewrite_sells(action, parent, want)
        for i in list(self.owed):
            self.owed[i] -= placed.get(i, 0)
            if self.owed[i] <= 0:
                del self.owed[i]
        if new is not action:
            self.report["turns"] += 1
        return new

    def release(self, obs, action, t, item, owed, stock):
        return owed


class Shift(Layer):
    """Hold a sale placed on a consumption step (the market runs before the
    town eats) for items the town eats at that tick; release next step."""

    def __init__(self, start=600, items=None, final=717):
        super().__init__(start, final)
        self.items = set(items or PRODUCTS)

    def release(self, obs, action, t, item, owed, stock):
        if (t % 4 == 0 and t < self.final and item in self.items
                and tick_units(obs["town"]["unlocked_shops"], item, t) > 0):
            return 0
        return owed


class Final(Layer):
    """Hold every owed unit from ``start`` until ``final``."""

    def __init__(self, hold_from=712, sell_at=717, items=None):
        super().__init__(hold_from, sell_at)
        self.items = set(items or PRODUCTS)

    def release(self, obs, action, t, item, owed, stock):
        return owed if item not in self.items else 0


class Asap(Layer):
    """Sell non-input goods (everything but WHEAT / FERTILIZER) as soon as
    they are in the shed: the only rule here that sells EARLIER than the
    parent (inputs stay delay-only)."""

    def __call__(self, obs, action):
        t = obs["step"]
        if t < self.start or not isinstance(action, dict):
            return action
        stock = projected_shed(obs, action)
        for i in PRODUCTS:
            if i not in ("WHEAT", "FERTILIZER") and stock.get(i, 0) > 0:
                self.owed[i] = stock[i]
        return super().__call__(obs, action)


class FloorHold(Layer):
    """Do not sell a unit whose quote is at or below ``floor`` dollars
    (glut markets); held units go at the end."""

    def __init__(self, start=600, floor=3, final=717):
        super().__init__(start, final)
        self.floor = floor

    def release(self, obs, action, t, item, owed, stock):
        if t < self.final and obs["market"]["prices"].get(item, 0) <= self.floor:
            return 0
        return owed


POLICIES = {
    "identity": lambda: Layer(10**9),
    "ledger_same": lambda: Layer(600),
    "shift_d25": lambda: Shift(600),
    "shift_d27": lambda: Shift(648),
    "shift_d29": lambda: Shift(696),
    "final712_717": lambda: Final(712, 717),
    "final700_717": lambda: Final(700, 717),
    "final712_718": lambda: Final(712, 718),
    "asap_d25": lambda: Asap(600),
    "asap_d20": lambda: Asap(480),
    "floor3_d25": lambda: FloorHold(600, 3),
    "floor3_d27": lambda: FloorHold(648, 3),
}


def score(job):
    record, names = job
    from stack.market_front import mf_reorder
    g = Game(record)
    g.run(stop=SNAP, snap_at=(SNAP,))
    state, _ = g.run(start=SNAP)
    base = g.result(state)
    out = {"episode_id": record["episode_id"],
           "agent": {56571049: "A", 56582917: "L"}.get(record.get("submission"), "?"),
           "live": record["rewards"], "base": base, "policies": {}}
    for name in names:
        layer = POLICIES[name]()
        if out["agent"] == "L":
            inner = layer

            def layer(obs, action, inner=inner):
                new = inner(obs, action)
                if new is not action and isinstance(new, dict) and new.get("market"):
                    new = dict(new, market=mf_reorder(new["market"],
                                                      obs["market"]["inventory"]))
                return new
        state, _ = g.run(layer=layer, start=SNAP)
        res = g.result(state)
        private = state[g.side].observation.private
        res["left"] = int(sum(private["shed"].values()) + sum(
            v for inv in private["inventories"] for v in inv.values()))
        out["policies"][name] = res
    return out


def report(rows, names):
    for name in names:
        d_us, d_margin, flips_w, flips_l = [], [], 0, 0
        left = sum(r["policies"][name].get("left", 0) for r in rows)
        for r in rows:
            b, p = r["base"], r["policies"][name]
            d_us.append(p["us"] - b["us"])
            dm = (p["us"] - p["them"]) - (b["us"] - b["them"])
            d_margin.append(dm)
            won_b = b["us"] > b["them"]
            won_p = p["us"] > p["them"]
            flips_w += (not won_b) and won_p
            flips_l += won_b and not won_p
        for agent in ("A", "L", "all"):
            idx = [k for k, r in enumerate(rows) if agent == "all" or r["agent"] == agent]
            if not idx:
                continue
            dm = [d_margin[k] for k in idx]
            du = [d_us[k] for k in idx]
            print(f"  {name:16s} {agent:3s} n={len(idx):3d} margin {statistics.mean(dm):+7.0f} "
                  f"(med {statistics.median(dm):+6.0f}, better {sum(x > 0 for x in dm):3d}, "
                  f"worse {sum(x < 0 for x in dm):3d}) own {statistics.mean(du):+7.0f} "
                  f"worst {min(dm):+6.0f} best {max(dm):+6.0f}")
        print(f"  {'':16s}     results flipped: {flips_w} to wins, {flips_l} to losses; "
              f"units left unsold at the end (all games) {left}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run")
    p.add_argument("policies", nargs="+")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--label", default="")
    sub.add_parser("list")
    args = ap.parse_args()
    if args.command == "list":
        print("\n".join(POLICIES))
        return
    names = ["identity"] + [n for n in args.policies if n != "identity"]
    t0 = time.time()
    with Pool(args.workers) as pool:
        rows = pool.map(score, [(r, names) for r in records()])
    bad = [r["episode_id"] for r in rows if r["base"] != {"us": r["live"]["us"], "them": r["live"]["them"]}]
    print(f"{len(rows)} games in {time.time() - t0:.0f}s; base != live in {len(bad)}")
    report(rows, names)
    if args.label:
        path = OUT / "policies" / f"{args.label}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows), encoding="utf-8")
        print(f"saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Pre-emption experiments: sell our stock of an item one step BEFORE the
# opponent's sale of it. "oracle" knows the opponent's executed sales from the
# baseline replay (an upper bound for any predictor); "mirror" predicts them
# with our own parent's next-step orders (the ladder is full of copies).
class Preempt:
    def __init__(self, start=600, min_units=3, items=None, predictor=None,
                 exclude=("WHEAT", "FERTILIZER"), tick_guard=True):
        self.start = start
        self.min_units = min_units
        self.items = items
        self.predictor = predictor      # f(t, item) -> predicted opp units at t
        self.exclude = set(exclude)
        self.tick_guard = tick_guard

    def __call__(self, obs, action):
        t = obs["step"]
        if t < self.start or t >= 718 or not isinstance(action, dict):
            return action
        stock = projected_shed(obs, action)
        parent = {i: min(q, stock.get(i, 0)) for i, q in _sells(action).items()}
        want = dict(parent)
        shops = obs["town"]["unlocked_shops"]
        for i in PRODUCTS:
            if i in self.exclude or (self.items and i not in self.items):
                continue
            have = stock.get(i, 0)
            if have <= parent.get(i, 0):
                continue
            # selling now instead of after a tick gives up the tick's bounce
            if self.tick_guard and tick_units(shops, i, t) > 0:
                continue
            if self.predictor(t + 1, i) >= self.min_units:
                want[i] = have
        new, _ = rewrite_sells(action, parent, want)
        return new


def preempt_factory(kind, **kw):
    def build(game, base_sales):
        if kind == "oracle":
            opp = {}
            for step, who, op, item, price in base_sales:
                if who == 1 and op == "SELL":
                    opp[(step, item)] = opp.get((step, item), 0) + 1
            pred = lambda t, i: opp.get((t, i), 0)        # noqa: E731
        else:
            tape = game.ours

            def pred(t, i):
                a = tape[t + 1] if t + 1 < len(tape) else {}
                return sum(int(o[2]) for o in (a.get("market") or [])
                           if isinstance(o, list) and len(o) >= 3
                           and o[0] == "SELL" and o[1] == i)
        return Preempt(predictor=pred, **kw)
    return build


GAME_POLICIES = {
    "pre_oracle_d25": preempt_factory("oracle", start=600),
    "pre_oracle_d25_m8": preempt_factory("oracle", start=600, min_units=8),
    "pre_oracle_d25_notick": preempt_factory("oracle", start=600, tick_guard=False),
    "pre_mirror_d25": preempt_factory("mirror", start=600),
    "pre_mirror_d25_m8": preempt_factory("mirror", start=600, min_units=8),
}


def score_game_policies(job):
    record, names = job
    from stack.market_front import mf_reorder
    g = Game(record)
    base_sales = []
    g.run(stop=SNAP, snap_at=(SNAP,))
    state, _ = g.run(start=SNAP, sales=base_sales)
    base = g.result(state)
    out = {"episode_id": record["episode_id"],
           "agent": {56571049: "A", 56582917: "L"}.get(record.get("submission"), "?"),
           "live": record["rewards"], "base": base, "policies": {}}
    for name in names:
        if name == "identity":
            out["policies"][name] = dict(base, left=0)
            continue
        layer = GAME_POLICIES[name](g, base_sales)
        if out["agent"] == "L":
            inner = layer

            def layer(obs, action, inner=inner):
                new = inner(obs, action)
                if new is not action and isinstance(new, dict) and new.get("market"):
                    new = dict(new, market=mf_reorder(new["market"],
                                                      obs["market"]["inventory"]))
                return new
        state, _ = g.run(layer=layer, start=SNAP)
        res = g.result(state)
        private = state[g.side].observation.private
        res["left"] = int(sum(private["shed"].values()) + sum(
            v for inv in private["inventories"] for v in inv.values()))
        out["policies"][name] = res
    return out


def run_game_policies(names, workers=2, label=""):
    names = ["identity"] + [n for n in names if n != "identity"]
    t0 = time.time()
    with Pool(workers) as pool:
        rows = pool.map(score_game_policies, [(r, names) for r in records()])
    print(f"{len(rows)} games in {time.time() - t0:.0f}s")
    report(rows, names)
    if label:
        path = OUT / "policies" / f"{label}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows), encoding="utf-8")
    return rows


# ---------------------------------------------------------------------------
# Realistic dump rules: sell our whole stock of a non-input item now (tick-
# guarded) when an OBSERVABLE signal says the opponent is selling it. The
# opponent's past sales are what the live agent infers exactly from the
# market-inventory change (steep items, prices > 1); here they come from the
# replay log, which is the same number.
class Dump:
    def __init__(self, rule, start=600, exclude=("WHEAT", "FERTILIZER"),
                 tick_guard=True, min_stock=1):
        self.rule = rule
        self.start = start
        self.exclude = set(exclude)
        self.tick_guard = tick_guard
        self.min_stock = min_stock
        self.fired = 0

    def __call__(self, obs, action):
        t = obs["step"]
        if t < self.start or t >= 718 or not isinstance(action, dict):
            return action
        stock = projected_shed(obs, action)
        parent = {i: min(q, stock.get(i, 0)) for i, q in _sells(action).items()}
        want = dict(parent)
        shops = obs["town"]["unlocked_shops"]
        for i in PRODUCTS:
            if i in self.exclude:
                continue
            have = stock.get(i, 0)
            if have < self.min_stock or have <= parent.get(i, 0):
                continue
            if self.tick_guard and tick_units(shops, i, t) > 0:
                continue
            if self.rule(t, i, parent.get(i, 0), have, obs):
                want[i] = have
                self.fired += 1
        new, _ = rewrite_sells(action, parent, want)
        return new


def dump_factory(kind, **kw):
    def build(game, base_sales):
        opp = {}
        for step, who, op, item, price in base_sales:
            if who == 1 and op == "SELL" and price > 1:
                opp[(step, item)] = opp.get((step, item), 0) + 1
        past = lambda t, i, k=1: sum(opp.get((t - d, i), 0) for d in range(1, k + 1))  # noqa: E731
        rules = {
            "opp_last": lambda t, i, p, h, obs: past(t, i) >= 1,
            "opp_last2": lambda t, i, p, h, obs: past(t, i, 2) >= 1,
            "opp_last_and_us": lambda t, i, p, h, obs: past(t, i) >= 1 and p > 0,
            "us_trickle": lambda t, i, p, h, obs: p > 0,
            "opp_last3u": lambda t, i, p, h, obs: past(t, i) >= 3,
        }
        return Dump(rules[kind], **kw)
    return build


GAME_POLICIES.update({
    "dump_opp_last": dump_factory("opp_last"),
    "dump_opp_last2": dump_factory("opp_last2"),
    "dump_opp_last_and_us": dump_factory("opp_last_and_us"),
    "dump_us_trickle": dump_factory("us_trickle"),
    "dump_opp_last3u": dump_factory("opp_last3u"),
})


def _only(items):
    ex = tuple(i for i in PRODUCTS if i not in items)
    return ex


for _it in ("STRAWBERRY", "MILK", "WOOL", "CARROT", "EGG", "TOMATO"):
    GAME_POLICIES[f"dump_us_trickle_{_it.lower()}"] = dump_factory("us_trickle", exclude=_only((_it,)))
GAME_POLICIES["dump_us_trickle_d27"] = dump_factory("us_trickle", start=648)
GAME_POLICIES["dump_us_trickle_d20"] = dump_factory("us_trickle", start=480)
GAME_POLICIES["dump_us_trickle_notick"] = dump_factory("us_trickle", tick_guard=False)


# ---------------------------------------------------------------------------
# Night-overflow guard (a UNIT-action layer, outside the pure SELL-order
# scope): at hour 23 the night drop moves every carried unit into the shed and
# destroys what does not fit in 100. If this step's harvests would push shed +
# carried over 100, first sell more from the shed, then postpone harvests
# whose yield keeps on the tile overnight (animal products below the cap,
# ongoing crops below their cap) until it fits.
CROP = {"TOMATO": (8, 1, 4), "STRAWBERRY": (10, 2, 4)}   # first_yield, interval, max
HELD = {"GOOSE": 4, "COW": 6, "SHEEP": 6}
ANIMAL_FIRST = {"GOOSE": (4, 1), "COW": (8, 2), "SHEEP": (6, 3)}


def _deferrable(tile, day):
    """Yield units that can safely wait on this tile until tomorrow."""
    if not isinstance(tile, dict):
        return 0
    y = int(tile.get("yield_units", 0) or 0)
    if y <= 0:
        return 0
    if "animal" in tile:
        cap = HELD[tile["animal"]]
        first, interval = ANIMAL_FIRST[tile["animal"]]
        nxt = day + 1 - int(tile.get("placed_day", 0)) - first
        produces = nxt >= 0 and nxt % interval == 0
        gain = (1 + (1 if tile.get("cared_today") and tile.get("fed_today") else 0)) if produces else 0
        return y if y + gain <= cap else 0
    if tile.get("kind") == "PLANT" and tile.get("crop") in CROP:
        first, interval, cap = CROP[tile["crop"]]
        return y if y + 2 <= cap else 0
    return 0


class NightGuard:
    def __init__(self, start=480, last_day=28, sell_first=True):
        self.start = start
        self.last_day = last_day
        self.sell_first = sell_first
        self.deferred = 0

    def __call__(self, obs, action):
        t = obs["step"]
        if t < self.start or t % 24 != 23 or t // 24 > self.last_day or not isinstance(action, dict):
            return action
        farm = obs["farms"][obs["player"]]
        private = obs["private"]
        positions = [farm["farmer"]] + list(farm["hands"])
        units = [list(action.get("farmer") or ["PASS"])] + [list(u) for u in (action.get("hands") or [])]
        invs = list(private["inventories"])
        adj = {(4, 4), (5, 4), (4, 5), (5, 5)}
        stock = projected_shed(obs, action)
        carried = 0
        harvest = []
        for i, pos in enumerate(positions):
            inv = invs[i] if i < len(invs) else {}
            act = units[i] if i < len(units) else ["PASS"]
            n = sum(int(v) for v in inv.values())
            if act and tuple(pos) in adj and act[0] == "DROP":
                n = 0
            tile = farm["tiles"][pos[1]][pos[0]]
            if act and act[0] == "HARVEST" and isinstance(tile, dict):
                y = int(tile.get("yield_units", 0) or 0)
                n += y
                d = _deferrable(tile, t // 24)
                if d > 0:
                    harvest.append((i, d))
            elif act and act[0] == "COLLECT_FERTILIZER" and isinstance(tile, dict) and tile.get("fertilizer_available"):
                n += 1
            elif act and act[0] in ("FEED", "FERTILIZE"):
                n -= 1
            carried += max(0, n)
        sold = {}
        for o in action.get("market") or []:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold[o[1]] = sold.get(o[1], 0) + int(o[2])
        shed_after = sum(max(0, stock.get(k, 0) - min(sold.get(k, 0), stock.get(k, 0))) for k in stock)
        excess = shed_after + carried - 100
        if excess <= 0:
            return action
        new = dict(action)
        if self.sell_first:
            # sell remaining shed stock, most valuable first
            prices = obs["market"]["prices"]
            left = {k: stock.get(k, 0) - min(sold.get(k, 0), stock.get(k, 0)) for k in stock}
            want = {k: min(v, stock.get(k, 0)) for k, v in sold.items()}
            for k in sorted(left, key=lambda k: -int(prices.get(k, 0))):
                if excess <= 0:
                    break
                take = min(left[k], excess)
                if take > 0 and int(prices.get(k, 0)) >= 1:
                    want[k] = want.get(k, 0) + take
                    excess -= take
            new, _ = rewrite_sells(new, {k: min(v, stock.get(k, 0)) for k, v in sold.items()}, want)
        for i, d in sorted(harvest, key=lambda x: -x[1]):
            if excess <= 0:
                break
            units[i] = ["PASS"]
            excess -= d
            self.deferred += d
        new = dict(new, farmer=units[0], hands=units[1:])
        return new


GAME_POLICIES["night_guard"] = lambda game, base: NightGuard()
GAME_POLICIES["night_guard_nosell"] = lambda game, base: NightGuard(sell_first=False)


# Route-plan trigger: A's chassis replays a route tape chosen by the town's
# first two shops (route 2 for everyone from step 648). The plan tells when
# our parent -- and any copy of it -- will sell an item.
_PARENT_TABLES = {}


def _route_tables():
    if not _PARENT_TABLES:
        from stack.candidate_l import parent_namespace
        env, _ = parent_namespace()
        _PARENT_TABLES.update(routes=env["_ROUTES"], r108=env["_R108_SHOP_ROUTES"],
                              r110=env["_R110_OLD_SHOPS"], v92=env["_V92_TABLE"])
    return _PARENT_TABLES


def route_of(shops, step):
    tb = _route_tables()
    if step >= 648:
        return 2
    first = tuple(shops[:2])
    use_new = first.count("YARN_STORE") <= 0
    route = tb["r108"].get(first, 100) if use_new else tb["r110"].get(first, 0)
    return tb["v92"].get(first, route)


def planned_sells(shops, t, h):
    tb = _route_tables()
    out = {}
    for s in range(t + 1, min(719, t + h + 1)):
        tape = tb["routes"][route_of(shops, s)]
        a = tape[s] if s < len(tape) and isinstance(tape[s], dict) else {}
        for o in a.get("market") or []:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                out[o[1]] = out.get(o[1], 0) + int(o[2])
    return out


def route_factory(h, **kw):
    def build(game, base_sales):
        rule = lambda t, i, p, have, obs: planned_sells(obs["town"]["unlocked_shops"], t, h).get(i, 0) > 0  # noqa: E731
        return Dump(rule, **kw)
    return build


for _h in (1, 2, 4, 8):
    GAME_POLICIES[f"dump_route{_h}"] = route_factory(_h)


def band_records():
    """Faithful band games (2600-2700 teams, replay >= 90% of their real
    score) as bench records: our agent's seat is 1 - team seat."""
    from pathlib import Path as _P
    panels = [ROOT / "rl" / "data" / "band_panel" / "band_2600_2700_front.json",
              ROOT / "rl" / "data" / "band_panel" / "band_2600_2900.json"]
    games = ROOT / "arena" / "games"
    out, seen = [], set()
    for panel in panels:
        for r in json.loads(_P(panel).read_text(encoding="utf-8")):
            if (r.get("agent") in ("A", "L_front") and "ours" in r
                    and 2600 <= r["score"] < 2700 and r["theirs"] >= 0.9 * r["recorded"]
                    and r["game_id"] not in seen and (games / f"{r['game_id']}.json").exists()):
                seen.add(r["game_id"])
                g = json.loads((games / f"{r['game_id']}.json").read_text(encoding="utf-8"))
                ours = 1 - int(r["seat"])
                out.append({"episode_id": r["game_id"], "seed": g["seed"], "our_side": ours,
                            "our_actions_zlib_b64": g["tapes"][ours],
                            "opp_actions_zlib_b64": g["tapes"][1 - ours],
                            "rewards": {"us": float(g["rewards"][ours]),
                                        "them": float(g["rewards"][1 - ours])},
                            "submission": {"A": 56571049, "L_front": 56582917}[r["agent"]]})
    return out


def run_band(names, workers=2, label=""):
    """Score policies on the faithful band games (both kinds of policies)."""
    names = ["identity"] + [n for n in names if n != "identity"]
    plain = [n for n in names if n in POLICIES]
    game = [n for n in names if n in GAME_POLICIES]
    recs = band_records()
    t0 = time.time()
    with Pool(workers) as pool:
        a = pool.map(score, [(r, plain) for r in recs]) if plain else []
        b = pool.map(score_game_policies, [(r, game) for r in recs]) if game else []
    rows = a or b
    if a and b:
        for x, y in zip(a, b):
            x["policies"].update(y["policies"])
    print(f"{len(rows)} band games in {time.time() - t0:.0f}s")
    report(rows, names)
    if label:
        path = OUT / "policies" / f"{label}.json"
        path.write_text(json.dumps(rows), encoding="utf-8")
    return rows


# Mirror-rate gate: fire the trickle dump only while the opponent has been
# selling the same items in the same steps as us. The live agent infers the
# opponent's sales exactly from the inventory change (steep items, price > 1);
# here they come from the base replay (the same numbers).
def mirror_gate_factory(theta, since=480, per_item=False, min_events=6):
    def build(game, base_sales):
        opp, ours = {}, {}
        for step, who, op, item, price in base_sales:
            if op == "SELL" and price > 1 and item not in ("WHEAT", "FERTILIZER"):
                d = opp if who == 1 else ours
                d[(step, item)] = d.get((step, item), 0) + 1
        # base_sales only cover steps >= SNAP; rates use steps since SNAP
        def rate(t, item):
            ev = [(s, i) for (s, i) in ours if s < t and s >= since and (not per_item or i == item)]
            if len(ev) < min_events:
                return 0.0
            return sum(1 for s, i in ev if (s, i) in opp) / len(ev)
        rule = lambda t, i, p, have, obs: p > 0 and rate(t, i) >= theta  # noqa: E731
        return Dump(rule)
    return build


for _th in (0.4, 0.5, 0.6, 0.7):
    GAME_POLICIES[f"dump_mirror{int(_th * 100)}"] = mirror_gate_factory(_th)
    GAME_POLICIES[f"dump_mirror{int(_th * 100)}_item"] = mirror_gate_factory(_th, per_item=True, min_events=3)


# The shipped layer itself (stack/l2_endgame.py), driven by the recorded parent
# actions, so its own opponent-sales inference and gate are what gets scored.
def module_factory(**kw):
    def build(game, base_sales):
        from stack.l2_endgame import trickle_dump
        holder = {}
        inner = trickle_dump(lambda obs, cfg=None: holder["a"], **kw)

        def layer(obs, action):
            holder["a"] = action
            return inner(obs, None)
        layer.telemetry = inner.telemetry
        return layer
    return build


GAME_POLICIES["module_none"] = module_factory(gate="none")
GAME_POLICIES["module_mirror40"] = module_factory(gate="mirror", theta=0.4)
GAME_POLICIES["module_mirror60"] = module_factory(gate="mirror", theta=0.6)
GAME_POLICIES["module_clone"] = module_factory(gate="clone")
for _f in (0.3, 0.5, 0.7):
    GAME_POLICIES[f"module_mirror40_cap{int(_f * 100)}"] = module_factory(gate="mirror", theta=0.4, min_frac=_f)
    GAME_POLICIES[f"module_none_cap{int(_f * 100)}"] = module_factory(gate="none", min_frac=_f)


def active_factory(theta=0.4, back=2, since=480, min_events=6):
    """Mirror-gated dump that also fires while an item is in an active
    selling spell of our parent (sold in the last ``back`` steps)."""
    def build(game, base_sales):
        opp, ours = {}, {}
        for step, who, op, item, price in base_sales:
            if op == "SELL" and price > 1 and item not in ("WHEAT", "FERTILIZER"):
                d = opp if who == 1 else ours
                d[(step, item)] = d.get((step, item), 0) + 1

        def rate(t):
            ev = [(s, i) for (s, i) in ours if since <= s < t]
            if len(ev) < min_events:
                return 0.0
            return sum(1 for k in ev if k in opp) / len(ev)

        def rule(t, i, p, have, obs):
            if rate(t) < theta:
                return False
            return p > 0 or any(ours.get((t - d, i), 0) > 0 for d in range(1, back + 1))
        return Dump(rule)
    return build


GAME_POLICIES["dump_active1_m40"] = active_factory(back=1)
GAME_POLICIES["dump_active2_m40"] = active_factory(back=2)
GAME_POLICIES["dump_active4_m40"] = active_factory(back=4)
