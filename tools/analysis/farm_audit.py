"""Everything the farm owns, grows, sells and throws away, in one run.

Counted at the engine, never inferred, and for both seats of the same
game so the figures have something to be measured against.

Four questions:

**What ground do we hold, and what is standing on it?** A daily census at
dusk: tiles owned, what occupies them, and how many are bare or weeds.
Ground bought and left empty is the most expensive thing a farm can own.

**What did we grow?** Units harvested per good, read at the tile.

**What price did we get, and was it the best available?** `_refresh_prices`
derives price from inventory alone -- there is no recovery with time:

    price = base +/- amp * shape(|inventory - I0|)

so a unit sold raises inventory permanently and the only thing that lowers
it again is the town eating. Selling faster than the town consumes is not
impatience, it is permanent damage to the book. The curves are steep and
uneven: wool loses 3.2 times base over 105 units and melon 3.6 over 300,
while wheat loses 0.2 over 400. So each sale is bucketed against base --
above base means we sold into scarcity the town created for us, and near
the floor means we were paying a worker to carry gravel.

**What went to waste?** Six ways to lose something already grown: ripe
crops rotting where they stand (`_decay_plants` takes a unit every other
step past `max_lifespan_step`), overflow binned at a full shed, produce
left unsold at the final bell, animals walking out at two unfed days, care
days wiped by an unfed production night, and waterings landing outside any
yield window, which the engine ignores entirely.

    python -m tools.analysis.farm_audit candidates.candidate_j:agent --tapes 4
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rl.replay_agent import build_replay_agent  # noqa: E402
from tools.eval.measure_panel import resolve  # noqa: E402

GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")
MOVES = ("NORTH", "SOUTH", "EAST", "WEST", "NORTHEAST", "NORTHWEST",
         "SOUTHEAST", "SOUTHWEST", "UP", "DOWN", "LEFT", "RIGHT")
BANDS = (("above base", 1.00), ("75-100%", 0.75), ("50-75%", 0.50),
         ("25-50%", 0.25), ("under 25%", 0.0))


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


class Audit:
    """One seat's whole book."""

    def __init__(self) -> None:
        self.grown: Counter = Counter()
        self.sold: Counter = Counter()
        self.revenue: Counter = Counter()
        self.bands: Counter = Counter()
        self.bought: Counter = Counter()
        self.spent = 0.0
        self.wages = 0.0
        self.land = 0.0
        self.rotted: Counter = Counter()
        self.binned: Counter = Counter()
        self.escaped = 0
        self.care_wiped = 0
        self.animal_overflow = 0
        self.dry_water: Counter = Counter()
        self.wet_water: Counter = Counter()
        self.manured: Counter = Counter()
        self.ops: Counter = Counter()
        self.days = 0
        self.owned = 0
        self.standing: Counter = Counter()
        self.bare = 0
        self.weeds = 0
        self.pens_empty = 0


def _census(farm, book: Audit) -> None:
    size = len(farm["tiles"])
    book.days += 1
    for y in range(size):
        for x in range(size):
            tile = farm["tiles"][y][x]
            if tile == "LOCKED":
                continue
            book.owned += 1
            if tile is None:
                book.bare += 1
            elif isinstance(tile, dict):
                kind = tile.get("kind")
                if "animal" in tile:
                    book.standing[str(tile["animal"])] += 1
                elif kind == "PLANT":
                    book.standing[str(tile.get("crop"))] += 1
                elif kind == "WEED":
                    book.weeds += 1
                elif kind in ("COOP", "PASTURE"):
                    book.pens_empty += 1


def run(spec: str, tape: Path, crops: dict, animals: dict,
        params: dict) -> tuple[Audit, Audit, float, float]:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    record = json.loads(tape.read_text(encoding="utf-8"))
    opponent = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    books = (Audit(), Audit())
    by_farm: dict[int, int] = {}
    by_private: dict[int, int] = {}
    raw = {name: getattr(engine, name) for name in (
        "_commit_unit", "_apply_unit_action", "_decay_plants",
        "_drop_inventories_to_shed", "_daily_refresh_animals",
        "_do_hire", "_do_buy_land", "_end_of_day")}

    def seat_farm(farm):
        seat = by_farm.get(id(farm))
        return books[seat] if seat is not None else None

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        ok = raw["_commit_unit"](op, item, price, farm, private, market,
                                 shed_capacity)
        book = seat_farm(farm)
        if book is None or not ok:
            return ok
        if op == "SELL":
            book.sold[item] += 1
            book.revenue[item] += float(price)
            base = float(params[item]["base"])
            for label, edge in BANDS:
                if price >= base * edge:
                    book.bands[(item, label)] += 1
                    break
        else:
            book.bought[str(op) + ":" + str(item)] += 1
            book.spent += float(price)
        return ok

    def unit(farm, private, idx, action, board_size, day, turns_per_day,
             shed_capacity=100):
        book = seat_farm(farm)
        op = action[0] if isinstance(action, list) and action else "NONE"
        if book is None:
            return raw["_apply_unit_action"](farm, private, idx, action,
                                             board_size, day, turns_per_day,
                                             shed_capacity)
        book.ops["WALK" if op in MOVES else op] += 1
        where = (farm["farmer"] if idx == 0
                 else (farm["hands"][idx - 1]
                       if idx - 1 < len(farm["hands"]) else None))
        standing = None
        if where is not None:
            tile = farm["tiles"][int(where[1])][int(where[0])]
            standing = dict(tile) if isinstance(tile, dict) else None
        result = raw["_apply_unit_action"](farm, private, idx, action,
                                          board_size, day, turns_per_day,
                                          shed_capacity)
        if standing is None or standing.get("kind") != "PLANT":
            if standing is not None and op == "HARVEST" and "animal" in standing:
                took = int(standing.get("yield_units", 0) or 0)
                if took > 0:
                    book.grown[animals[standing["animal"]]["product"]] += took
            return result
        crop = str(standing.get("crop", ""))
        spec_c = crops.get(crop)
        if spec_c is None:
            return result
        age = day - int(standing.get("planted_day", day))
        if op == "HARVEST":
            took = int(standing.get("yield_units", 0) or 0)
            if took > 0:
                book.grown[crop] += took
        elif op == "FERTILIZE":
            book.manured[crop] += 1
        elif op == "WATER" and not standing.get("watered_today"):
            if spec_c["ongoing"]:
                since = (day + 1) - int(standing.get("planted_day", day)) \
                    - spec_c["first_yield_day"]
                due = since >= 0 and since % max(1, spec_c["interval"]) == 0
                (book.wet_water if due else book.dry_water)[crop] += 1
            else:
                start = (spec_c["max_yield_day"] + 1) // 2
                if start <= age <= spec_c["max_yield_day"]:
                    book.wet_water[crop] += 1
                else:
                    book.dry_water[crop] += 1
        return result

    def decay(farm, step):
        book = seat_farm(farm)
        if book is None:
            return raw["_decay_plants"](farm, step)
        size = len(farm["tiles"])
        before = {}
        for y in range(size):
            for x in range(size):
                tile = farm["tiles"][y][x]
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    before[(x, y)] = (str(tile.get("crop")),
                                      int(tile.get("yield_units", 0) or 0))
        result = raw["_decay_plants"](farm, step)
        for (x, y), (crop, was) in before.items():
            tile = farm["tiles"][y][x]
            now = (int(tile.get("yield_units", 0) or 0)
                   if isinstance(tile, dict) and tile.get("kind") == "PLANT"
                   else 0)
            if was > now:
                book.rotted[crop] += was - now
        return result

    def drop(private, capacity):
        seat = by_private.get(id(private))
        if seat is None:
            return raw["_drop_inventories_to_shed"](private, capacity)
        book = books[seat]
        carried: Counter = Counter()
        for bag in private["inventories"]:
            carried.update({k: int(v) for k, v in bag.items()})
        before = sum(private["shed"].values())
        result = raw["_drop_inventories_to_shed"](private, capacity)
        lost = sum(carried.values()) - (sum(private["shed"].values()) - before)
        for item, n in carried.most_common():
            if lost <= 0:
                break
            take = min(n, lost)
            book.binned[item] += take
            lost -= take
        return result

    def refresh_animals(farm, day):
        book = seat_farm(farm)
        if book is None:
            return raw["_daily_refresh_animals"](farm, day)
        size = len(farm["tiles"])
        before = {}
        for y in range(size):
            for x in range(size):
                tile = farm["tiles"][y][x]
                if isinstance(tile, dict) and "animal" in tile:
                    before[(x, y)] = dict(tile)
        result = raw["_daily_refresh_animals"](farm, day)
        for (x, y), was in before.items():
            now = farm["tiles"][y][x]
            kind = animals[was["animal"]]
            if not (isinstance(now, dict) and "animal" in now):
                book.escaped += 1
                continue
            since = (day + 1) - was["placed_day"] - kind["first_yield_day"]
            if since < 0 or since % kind["interval"] != 0:
                continue
            pending = int(was.get("pending_care_bonus", 0) or 0)
            if not was["fed_today"]:
                book.care_wiped += pending
                continue
            wanted = int(was["yield_units"]) + 1 + pending
            if wanted > kind["max_held"]:
                book.animal_overflow += wanted - kind["max_held"]
        return result

    def hire(farm, private, board_size, mult=1):
        before = float(farm["money"])
        result = raw["_do_hire"](farm, private, board_size, mult)
        book = seat_farm(farm)
        if book is not None:
            book.wages += before - float(farm["money"])
        return result

    def buy_land(farm, board_size):
        before = float(farm["money"])
        result = raw["_do_buy_land"](farm, board_size)
        book = seat_farm(farm)
        if book is not None:
            book.land += before - float(farm["money"])
        return result

    def end_of_day(state, env_, day):
        result = raw["_end_of_day"](state, env_, day)
        for seat, farm in enumerate(state[0].observation.farms):
            _census(farm, books[seat])
        return result

    raw_interpreter = env.interpreter

    def interpreter(state, e):
        by_farm.clear()
        by_private.clear()
        by_farm.update({id(f): s for s, f
                        in enumerate(state[0].observation.farms)})
        by_private.update({id(st.observation.private): s
                           for s, st in enumerate(state)})
        return raw_interpreter(state, e)

    engine._commit_unit = commit
    engine._apply_unit_action = unit
    engine._decay_plants = decay
    engine._drop_inventories_to_shed = drop
    engine._daily_refresh_animals = refresh_animals
    engine._do_hire = hire
    engine._do_buy_land = buy_land
    engine._end_of_day = end_of_day
    env.interpreter = interpreter
    try:
        env.run([resolve(spec), opponent])
    finally:
        for name, fn in raw.items():
            setattr(engine, name, fn)

    final = env.steps[-1]
    shed = (final[0]["observation"].get("private") or {}).get("shed") or {}
    for item, n in shed.items():
        if item in GOODS and int(n) > 0:
            books[0].binned["UNSOLD:" + item] += int(n)
    return (books[0], books[1],
            float(final[0].get("reward") or 0.0),
            float(final[1].get("reward") or 0.0))


def _merge(source: Audit, total: Audit) -> None:
    for name in ("grown", "sold", "revenue", "bands", "bought", "rotted",
                 "binned", "dry_water", "wet_water", "manured", "ops",
                 "standing"):
        getattr(total, name).update(getattr(source, name))
    for name in ("spent", "wages", "land", "escaped", "care_wiped",
                 "animal_overflow", "days", "owned", "bare", "weeds",
                 "pens_empty"):
        setattr(total, name, getattr(total, name) + getattr(source, name))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--tapes", type=int, default=4)
    args = parser.parse_args()

    from kaggle_environments.envs.kaggriculture.kaggriculture import (
        ANIMALS, CROPS, MARKET_PARAMS)
    from candidates.demand import demand_rate

    tapes = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    ours, theirs = Audit(), Audit()
    scores = [0.0, 0.0]
    towns: list[dict] = []
    for tape in tapes[: args.tapes]:
        mine, yours, a, b = run(args.spec, tape, CROPS, ANIMALS, MARKET_PARAMS)
        _merge(mine, ours)
        _merge(yours, theirs)
        scores[0] += a
        scores[1] += b
    games = max(1, args.tapes)

    print(f"\n{args.spec}: the whole farm, {games} games, per game\n")
    print(f"  finished with {scores[0] / games:,.0f} against "
          f"{scores[1] / games:,.0f}\n")

    # --- the ground ---
    print("  THE GROUND, averaged over every dusk")
    print(f"    {'':22s} {'ours':>8s} {'theirs':>8s}")
    for label, a, b in (
            ("tiles owned", ours.owned / max(1, ours.days),
             theirs.owned / max(1, theirs.days)),
            ("bare", ours.bare / max(1, ours.days),
             theirs.bare / max(1, theirs.days)),
            ("weeds", ours.weeds / max(1, ours.days),
             theirs.weeds / max(1, theirs.days)),
            ("empty pens", ours.pens_empty / max(1, ours.days),
             theirs.pens_empty / max(1, theirs.days))):
        print(f"    {label:22s} {a:8.1f} {b:8.1f}")
    print(f"\n    {'standing on it':22s} {'ours':>8s} {'theirs':>8s}")
    for what in sorted(set(ours.standing) | set(theirs.standing)):
        print(f"    {what:22s} "
              f"{ours.standing.get(what, 0) / max(1, ours.days):8.1f} "
              f"{theirs.standing.get(what, 0) / max(1, theirs.days):8.1f}")
    used = (ours.owned - ours.bare - ours.weeds) / max(1, ours.days)
    used_them = ((theirs.owned - theirs.bare - theirs.weeds)
                 / max(1, theirs.days))
    print(f"\n    working {used:.1f} of {ours.owned / max(1, ours.days):.1f} "
          f"tiles ({used / max(1, ours.owned / max(1, ours.days)):.0%}), "
          f"they work {used_them:.1f} "
          f"({used_them / max(1, theirs.owned / max(1, theirs.days)):.0%})")

    # --- what we grew and what we got for it ---
    print("\n  GROWN, SOLD, AND WHAT THE MARKET PAID")
    print(f"    {'good':11s} {'grown':>6s} {'sold':>6s} {'coins':>9s} "
          f"{'/unit':>7s} {'base':>5s} {'vs base':>8s} | {'their /unit':>11s}")
    for item in GOODS:
        grown = ours.grown.get(item, 0)
        sold = ours.sold.get(item, 0)
        coins = ours.revenue.get(item, 0.0)
        base = float(MARKET_PARAMS[item]["base"])
        each = coins / max(1, sold)
        t_each = (theirs.revenue.get(item, 0.0)
                  / max(1, theirs.sold.get(item, 0)))
        print(f"    {item:11s} {grown / games:6.0f} {sold / games:6.0f} "
              f"{coins / games:9,.0f} {each:7.1f} {base:5.0f} "
              f"{each / base - 1:+7.0%} | {t_each:11.1f}")

    print("\n  EVERY SALE, BUCKETED AGAINST BASE PRICE")
    print(f"    {'good':11s} " + " ".join(f"{label:>10s}"
                                          for label, _ in BANDS))
    for item in GOODS:
        row = [ours.bands.get((item, label), 0) for label, _ in BANDS]
        if not sum(row):
            continue
        print(f"    {item:11s} " + " ".join(f"{n / games:10.0f}" for n in row))

    # --- waste ---
    print("\n  WHAT WENT TO WASTE")
    unsold = sum(v for k, v in ours.binned.items() if k.startswith("UNSOLD:"))
    binned = sum(v for k, v in ours.binned.items()
                 if not k.startswith("UNSOLD:"))
    t_unsold = sum(v for k, v in theirs.binned.items()
                   if k.startswith("UNSOLD:"))
    t_binned = sum(v for k, v in theirs.binned.items()
                   if not k.startswith("UNSOLD:"))
    print(f"    {'':34s} {'ours':>8s} {'theirs':>8s}")
    for label, a, b in (
            ("rotted where it stood", sum(ours.rotted.values()),
             sum(theirs.rotted.values())),
            ("binned at a full shed", binned, t_binned),
            ("left in the shed at the bell", unsold, t_unsold),
            ("animals walked out", ours.escaped, theirs.escaped),
            ("care days wiped unfed", ours.care_wiped, theirs.care_wiped),
            ("produce lost, animal full", ours.animal_overflow,
             theirs.animal_overflow),
            ("waterings outside any window", sum(ours.dry_water.values()),
             sum(theirs.dry_water.values()))):
        print(f"    {label:34s} {a / games:8.1f} {b / games:8.1f}")
    if ours.rotted:
        print("\n    rotted, by crop: " + ", ".join(
            f"{k} {v / games:.0f}" for k, v in ours.rotted.most_common(5)))

    # --- the demand the town actually had ---
    print("\n  WHAT THE TOWN COULD ABSORB, AGAINST WHAT WE SOLD IT")
    print(f"    {'good':11s} {'town wanted':>12s} {'we sold':>9s} "
          f"{'over/under':>11s}")
    for item in GOODS:
        want = sum(t.get(item, 0.0) for t in towns) if towns else 0.0
        sold = ours.sold.get(item, 0) / games
        print(f"    {item:11s} {want:12.0f} {sold:9.0f} "
              f"{sold - want:+11.0f}" if want else
              f"    {item:11s} {'-':>12s} {sold:9.0f} {'-':>11s}")

    print("\n  THE TURN BUDGET")
    total = max(1, sum(ours.ops.values()))
    t_total = max(1, sum(theirs.ops.values()))
    for op, n in ours.ops.most_common():
        print(f"    {op:22s} {n / games:8.0f} {n / total:6.1%} "
              f"{theirs.ops.get(op, 0) / t_total:6.1%}")


if __name__ == "__main__":
    main()
