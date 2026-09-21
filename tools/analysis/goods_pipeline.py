"""Where do the harvested goods go, counted at source.

The failure grid says the candidate sells 0.44 units for every unit a
top-200 team sells. Inferring that from shed deltas does not work: the
shed receives the day's deposits and pays out the day's sales in the same
step, so a net delta hides both. So this hooks the engine itself --
`_commit_unit`, which is the single place a unit is ever sold, bought or
refused, and `_drop_inventories_to_shed`, which is the single place a unit
is ever silently binned.

What it separates:

    sold        units the market actually took, with the coins they paid
    refused     a unit the engine would not commit. The first refusal
                aborts the whole order (`order_states[p] = None`), so a
                refused unit costs every unit behind it too
    binned      overflow thrown away because the shed was already at 100
    left        still in the shed when the game ends, worth nothing

Note the shed holds livestock as well as goods, so a herd of seventeen is
seventeen fewer slots for produce, and a full shed makes BUY_PRODUCT and
BUY_ANIMAL fail outright rather than queue.

    python -m tools.analysis.goods_pipeline rl.candidate_j:agent --tapes 3
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import zlib
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rl.replay_agent import build_replay_agent  # noqa: E402
from tools.eval.measure_panel import resolve  # noqa: E402

GOODS = ("WHEAT", "CARROT", "TOMATO", "MELON", "STRAWBERRY",
         "EGG", "MILK", "WOOL", "FERTILIZER")


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def _held(observation: dict[str, Any]) -> Counter:
    bag: Counter = Counter()
    for unit in (observation.get("private") or {}).get("inventories") or []:
        bag.update({k: int(v) for k, v in (unit or {}).items() if k in GOODS})
    return bag


_HOOKED = ("_commit_unit", "_drop_inventories_to_shed",
           "_process_market", "_end_of_day", "_apply_unit_action")
_PRISTINE: dict | None = None


class Ledger:
    """Counts every unit the engine commits, refuses or bins, for one seat."""

    def __init__(self) -> None:
        self.sold: Counter = Counter()
        self.revenue: Counter = Counter()
        self.bought: Counter = Counter()
        self.spent = 0.0
        self.refused: Counter = Counter()
        self.binned: Counter = Counter()
        self.dumped: Counter = Counter()
        self.grown: Counter = Counter()
        self.fed = 0
        self.cared = 0
        self.planted: Counter = Counter()
        self.seats: dict[int, int] = {}
        self.other: "Ledger | None" = None

    def _book(self, key: int) -> "Ledger | None":
        seat = self.seats.get(key)
        if seat == 0:
            return self
        if seat == 1:
            return self.other
        return None

    def _record(self, op, item, price, ok) -> None:
        if not ok:
            self.refused[str(op) + ":" + str(item)] += 1
        elif op == "SELL":
            self.sold[item] += 1
            self.revenue[item] += float(price)
        else:
            self.bought[str(op) + ":" + str(item)] += 1
            self.spent += float(price)

    def install(self, engine) -> None:
        """Wrap the engine, from its pristine functions every time.

        Wrapping an already-wrapped engine leaves the previous game's
        ledger in the call chain, still counting; the older rows then grow
        while later games play, and a good can end up "sold" more often
        than it was ever grown. So the originals are kept once and every
        install starts from them.
        """
        global _PRISTINE
        if _PRISTINE is None:
            _PRISTINE = {name: getattr(engine, name) for name in _HOOKED}
        for name, function in _PRISTINE.items():
            setattr(engine, name, function)

        raw_commit = engine._commit_unit
        raw_drop = engine._drop_inventories_to_shed

        def commit(op, item, price, farm, private, market, shed_capacity=100):
            ok = raw_commit(op, item, price, farm, private, market,
                            shed_capacity)
            book = self._book(id(private))
            if book is None:
                return ok
            if book is not self:
                return book._record(op, item, price, ok) or ok
            if not ok:
                self.refused[str(op) + ":" + str(item)] += 1
            elif op == "SELL":
                self.sold[item] += 1
                self.revenue[item] += float(price)
            else:
                self.bought[str(op) + ":" + str(item)] += 1
                self.spent += float(price)
            return ok

        def drop(private, capacity):
            book = self._book(id(private))
            if book is None:
                return raw_drop(private, capacity)
            carried: Counter = Counter()
            for inventory in private["inventories"]:
                carried.update({k: int(v) for k, v in inventory.items()})
            before = sum(private["shed"].values())
            result = raw_drop(private, capacity)
            lost = sum(carried.values()) - (
                sum(private["shed"].values()) - before)
            if lost > 0:
                # The engine drops in inventory order, so the tail is what
                # goes; attribute the loss across what was being carried.
                for item, n in carried.most_common():
                    take = min(n, lost)
                    book.binned[item] += take
                    lost -= take
                    if lost <= 0:
                        break
            return result

        raw_unit = engine._apply_unit_action

        def unit(farm, private, idx, action, board_size, day, turns_per_day,
                 shed_capacity=100):
            book = self._book(id(private))
            op = action[0] if isinstance(action, list) and action else None
            if book is not None and op in ("HARVEST", "COLLECT_FERTILIZER"):
                # Production has to be read at the tile. Counting it as a
                # rise in what the crew carries also counts every PICKUP
                # from the shed, which made wheat look four times the crop
                # it is -- the same units fetched, carried and fetched again.
                bags = private["inventories"]
                was = dict(bags[idx]) if idx < len(bags) else {}
                result = raw_unit(farm, private, idx, action, board_size, day,
                                  turns_per_day, shed_capacity)
                now = bags[idx] if idx < len(bags) else {}
                for item, n in now.items():
                    if n > was.get(item, 0):
                        book.grown[item] += n - was.get(item, 0)
                return result
            if book is not None and op == "CARE":
                book.cared += 1
            if book is not None and op == "PLANT" and len(action) > 1:
                book.planted[action[1]] += 1
            if book is None or op not in ("DROP", "FEED"):
                return raw_unit(farm, private, idx, action, board_size, day,
                                turns_per_day, shed_capacity)
            bags = private["inventories"]
            inventory = dict(bags[idx]) if idx < len(bags) else {}
            before = sum(private["shed"].values())
            result = raw_unit(farm, private, idx, action, board_size, day,
                              turns_per_day, shed_capacity)
            if op == "FEED":
                bags = private["inventories"]
                after = bags[idx].get("WHEAT", 0) if idx < len(bags) else 0
                if inventory.get("WHEAT", 0) > after:
                    book.fed += 1
                return result
            # DROP bins whatever did not fit: the engine deletes the entry
            # from the inventory whether or not the shed had room for it.
            lost = sum(inventory.values()) - (
                sum(private["shed"].values()) - before)
            for item, n in sorted(inventory.items(), key=lambda kv: -kv[1]):
                if lost <= 0:
                    break
                take = min(n, lost)
                book.dumped[item] += take
                lost -= take
            return result

        raw_market = engine._process_market
        raw_endday = engine._end_of_day

        def register(state) -> None:
            # `env.run` resets the environment, so any identity captured
            # outside points at a dead dict. The engine hands us the live
            # state here, so the seats are re-learnt every step.
            self.seats = {id(s.observation.private): seat
                          for seat, s in enumerate(state)}

        def market(state, env):
            register(state)
            return raw_market(state, env)

        def end_of_day(state, env, day):
            register(state)
            return raw_endday(state, env, day)

        engine._apply_unit_action = unit
        engine._commit_unit = commit
        engine._drop_inventories_to_shed = drop
        engine._process_market = market
        engine._end_of_day = end_of_day


def run(spec: str, tape: Path) -> dict[str, Any]:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    record = json.loads(tape.read_text(encoding="utf-8"))
    opponent = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    ledger = Ledger()
    ledger.other = Ledger()
    ledger.install(engine)
    # `_apply_unit_action` runs before the market and after the day rolls
    # over, and the environment rebuilds the observation wrapper each step,
    # so a seat identity learnt inside either of those hooks is already
    # stale by the time a worker acts. The interpreter is the one place
    # that sees the live state at the top of every step.
    raw_interpreter = env.interpreter

    def interpreter(state, e):
        ledger.seats = {id(s.observation.private): seat
                        for seat, s in enumerate(state)}
        return raw_interpreter(state, e)

    env.interpreter = interpreter
    env.run([resolve(spec), opponent])

    harvested: Counter = Counter()
    orders_issued = 0
    carried_at_dusk = 0
    for index in range(1, len(env.steps)):
        before = env.steps[index - 1][0]["observation"]
        after = env.steps[index][0]["observation"]
        action = env.steps[index - 1][0].get("action") or {}
        orders_issued += len(action.get("market") or [])
        grew = _held(after) - _held(before)
        harvested += Counter({k: v for k, v in grew.items() if v > 0})
        if index % 24 == 0:
            carried_at_dusk += sum(_held(before).values())

    shed = (env.steps[-1][0]["observation"].get("private") or {}).get("shed") or {}
    return {
        "tape": tape.name,
        "ours": float(env.steps[-1][0].get("reward") or 0.0),
        "theirs": float(env.steps[-1][1].get("reward") or 0.0),
        "harvested": sum(ledger.grown.values()),
        "sold": sum(ledger.sold.values()),
        "revenue": sum(ledger.revenue.values()),
        "refused": sum(ledger.refused.values()),
        "binned": sum(ledger.binned.values()),
        "carried": carried_at_dusk,
        "left": sum(int(v) for k, v in shed.items() if k in GOODS),
        "orders": orders_issued,
        "by_sold": ledger.sold,
        "by_revenue": ledger.revenue,
        "by_refused": ledger.refused,
        "by_binned": ledger.binned,
        "by_dumped": ledger.dumped,
        "fed": ledger.fed,
        "their_fed": ledger.other.fed,
        "their_dumped": ledger.other.dumped,
        "by_harvested": ledger.grown,
        "their_grown": ledger.other.grown,
        "cared": ledger.cared,
        "their_cared": ledger.other.cared,
        "planted": ledger.planted,
        "their_planted": ledger.other.planted,
        "their_sold": ledger.other.sold,
        "their_revenue": ledger.other.revenue,
        "their_refused": ledger.other.refused,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--tapes", type=int, default=3)
    args = parser.parse_args()

    tapes = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    rows = [run(args.spec, tape) for tape in tapes[: args.tapes]]

    print("\n" + args.spec + ": where the goods go, "
          + str(len(rows)) + " games\n")
    print(f"  {'game':20s} {'ours':>9s} {'theirs':>9s} {'grown':>6s} "
          f"{'sold':>6s} {'revenue':>10s} {'refused':>8s} {'binned':>7s} "
          f"{'left':>5s}")
    for row in rows:
        print(f"  {row['tape'][:20]:20s} {row['ours']:9,.0f} "
              f"{row['theirs']:9,.0f} {row['harvested']:6d} {row['sold']:6d} "
              f"{row['revenue']:10,.0f} {row['refused']:8d} "
              f"{row['binned']:7d} {row['left']:5d}")

    grown = sum(r["harvested"] for r in rows)
    print(f"\n  grown {grown}, sold {sum(r['sold'] for r in rows)}, "
          f"binned at the shed {sum(r['binned'] for r in rows)}, "
          f"left in the shed {sum(r['left'] for r in rows)}")
    print(f"  refused units {sum(r['refused'] for r in rows)} across "
          f"{sum(r['orders'] for r in rows)} orders -- each refusal also "
          f"kills every unit behind it in that order")

    revenue: Counter = Counter()
    for row in rows:
        revenue.update(row["by_revenue"])
    print("\n  revenue by good (the whole point):")
    for item, coins in revenue.most_common():
        units = sum(r["by_sold"].get(item, 0) for r in rows)
        grew = sum(r["by_harvested"].get(item, 0) for r in rows)
        print(f"    {item:12s} {units:5d} sold of {grew:5d} grown  "
              f"{coins:10,.0f} coins  {coins / max(1, units):7,.1f}/unit")

    refused: Counter = Counter()
    binned_by: Counter = Counter()
    for row in rows:
        refused.update(row["by_refused"])
        binned_by.update(row["by_binned"])
    if refused:
        print("\n  refusals, most common first:")
        for what, n in refused.most_common(8):
            print(f"    {what:24s} {n:5d}")
    if binned_by:
        print("\n  binned at the shed door:")
        for what, n in binned_by.most_common(6):
            print(f"    {what:24s} {n:5d}")

    # The two sinks that never reach the market: wheat eaten by the flock,
    # and anything a worker drops when the shed is already at capacity --
    # `DROP` deletes the inventory entry whether or not there was room.
    dumped: Counter = Counter()
    their_dumped: Counter = Counter()
    for row in rows:
        dumped.update(row["by_dumped"])
        their_dumped.update(row["their_dumped"])
    print(f"\n  eaten as feed: {sum(r['fed'] for r in rows)} wheat, "
          f"against {sum(r['their_fed'] for r in rows)} for them")
    print(f"  dropped onto a full shed and lost: {sum(dumped.values())} "
          f"units, against {sum(their_dumped.values())} for them")
    for what, n in dumped.most_common(6):
        print(f"    {what:24s} {n:5d} lost, {their_dumped.get(what, 0):5d} "
              f"for them")

    # Where the labour actually went: what was sown, and whether the
    # animals got the care bonus that doubles a production day.
    sown: Counter = Counter()
    their_sown: Counter = Counter()
    for row in rows:
        sown.update(row["planted"])
        their_sown.update(row["their_planted"])
    print(f"\n  cared for animals {sum(r['cared'] for r in rows)} times, "
          f"against {sum(r['their_cared'] for r in rows)} for them")
    print(f"  seeds put in the ground, ours against theirs:")
    for crop in sorted(set(sown) | set(their_sown),
                       key=lambda c: -their_sown.get(c, 0)):
        print(f"    {crop:12s} {sown.get(crop, 0):5d} {their_sown.get(crop, 0):7d}")

    # The same ledger for the seat opposite, so the mix is judged against a
    # top-200 team playing the same seed rather than against an opinion.
    theirs: Counter = Counter()
    their_units: Counter = Counter()
    for row in rows:
        theirs.update(row["their_revenue"])
        their_units.update(row["their_sold"])
    ours_total = sum(revenue.values())
    their_total = sum(theirs.values())
    print(f"\n  the same game from the other side: they took "
          f"{their_total:,.0f} coins to our {ours_total:,.0f}\n")
    print(f"    {'good':12s} {'our units':>10s} {'their units':>12s} "
          f"{'our coins':>11s} {'their coins':>12s} {'gap':>11s}")
    for item in sorted(set(revenue) | set(theirs),
                       key=lambda k: theirs.get(k, 0) - revenue.get(k, 0),
                       reverse=True):
        gap = theirs.get(item, 0) - revenue.get(item, 0)
        print(f"    {item:12s} {sum(r['by_sold'].get(item, 0) for r in rows):10d} "
              f"{their_units.get(item, 0):12d} {revenue.get(item, 0):11,.0f} "
              f"{theirs.get(item, 0):12,.0f} {gap:+11,.0f}")


if __name__ == "__main__":
    main()
