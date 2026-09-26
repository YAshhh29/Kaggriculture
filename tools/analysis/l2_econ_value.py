"""Value per tile-day and per labour action for every crop and animal.

Every yield below is measured by running the stock engine (through
tools/analysis/l2_econ_sim.Sim) on one tile with an exact schedule of
PLANT / WATER / FERTILIZE / HARVEST / DIG or FEED / CARE / COLLECT / HARVEST
actions, so the numbers are the engine's, not a formula's. Each schedule's
output is then priced three ways: at base price, and at the prices our real
ladder games actually paid in the middle (days 10-19) and late (days 20-29)
game, read from rl/data/l2/econ/summary.json (tools/analysis/l2_econ_report).

Also prints: the marginal cost of the n-th hand against the value of a
hand-day, land break-even by purchase day, and the wheat feed bill.

    python -m tools.analysis.l2_econ_value [--group A+L]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import kaggle_environments.envs.kaggriculture.kaggriculture as E  # noqa: E402
from tools.analysis.l2_econ_sim import Sim  # noqa: E402

SUMMARY = ROOT / "rl" / "data" / "l2" / "econ" / "summary.json"
OUT = ROOT / "rl" / "data" / "l2" / "econ" / "value.json"
X, Y = 4, 4   # the farmer respawns here every morning, so no walking is needed


def P(a):
    return {"farmer": a, "hands": [], "market": []}


# ---------------------------------------------------------------------------
# Crops
CROP_PLANS = [
    # name, crop, water days, fertilize days, harvest days, dig day
    ("wheat, harvest age 2", "WHEAT", [0, 2], [], [2], None),
    ("wheat, harvest age 3", "WHEAT", [0, 2, 3], [], [3], None),
    ("wheat, harvest age 4", "WHEAT", [0, 2, 3, 4], [], [4], None),
    ("wheat, age 2 + fert", "WHEAT", [0, 2], [2], [2], None),
    ("wheat, age 3 + fert", "WHEAT", [0, 2, 3], [2], [3], None),
    ("wheat, age 4 + fert", "WHEAT", [0, 2, 3, 4], [2], [4], None),
    ("carrot, harvest age 2", "CARROT", [0, 2], [], [2], None),
    ("carrot, harvest age 3", "CARROT", [0, 2, 3], [], [3], None),
    ("carrot, age 2 + fert", "CARROT", [0, 2], [2], [2], None),
    ("carrot, age 3 + fert", "CARROT", [0, 2, 3], [2], [3], None),
    ("melon, harvest age 10", "MELON", [0, 2, 4, 6, 7, 8, 9, 10], [], [10], None),
    ("melon, age 10 + fert at 6", "MELON", [0, 2, 4, 6, 7, 8], [6], [10], None),
    ("tomato, survival water", "TOMATO", [0, 2, 4, 6, 8, 10], [], [11], 11),
    ("tomato + 1 fert (d7)", "TOMATO", [0, 2, 4, 6, 7, 8, 9], [7], [9, 11], 11),
    ("tomato + 2 fert (d7,d10)", "TOMATO", [0, 2, 4, 6, 7, 8, 9, 10], [7, 10], [9, 11], 11),
    ("strawberry, survival water", "STRAWBERRY", [0, 2, 4, 6, 8, 10, 12, 14], [], [16], 16),
    ("strawberry + 2 fert (d9,d13)", "STRAWBERRY", [0, 2, 4, 6, 8, 9, 11, 13, 15], [9, 13], [12, 16], 16),
]


def run_crop(crop, water, fert, harvest, dig):
    s = Sim()
    s.put_plant(0, X, Y, crop, 0)
    last = max(harvest + ([dig] if dig is not None else []))
    got = actions = 0
    for d in range(last + 1):
        s.to_day(d)
        s.private(0)["inventories"][0]["FERTILIZER"] = 1
        todo = []
        if d in fert:
            todo.append(["FERTILIZE"])
        if d in water:
            todo.append(["WATER"])
        if d in harvest:
            todo.append(["HARVEST"])
        if d == dig:
            todo.append(["DIG"])
        for a in todo:
            before = s.private(0)["inventories"][0].get(crop, 0)
            s.step(P(a))
            actions += 1
            if a == ["HARVEST"]:
                got += s.private(0)["inventories"][0].get(crop, 0) - before
    return got, actions + 1, last   # +1 for the PLANT


# ---------------------------------------------------------------------------
# Animals: steady state measured over nights 12..23 of an animal placed day 0.
ANIMAL_MODES = [
    ("fed + cared daily", 1, True),
    ("fed daily, no care", 1, False),
    ("fed every other day, no care", 2, False),
]
HARVEST_EVERY = {"GOOSE": 2, "COW": 4, "SHEEP": 3}


def run_animal(animal, feed_every, care, start=12, end=24):
    """Production is counted as it is credited on the tile each night
    (morning yield minus the previous evening's), so harvest timing and
    window edges do not distort the rate; units lost to max_held are lost."""
    s = Sim()
    s.put_animal(0, X, Y, animal, 0)
    units = first_day = 0
    acts = {"FEED": 0, "CARE": 0, "COLLECT_FERTILIZER": 0, "HARVEST": 0}
    fert = wheat = 0
    evening = None
    for d in range(end + 1):
        s.to_day(d)
        inv = s.private(0)["inventories"][0]
        inv["WHEAT"] = 1
        t = s.tile(0, X, Y)
        if "animal" not in t:
            return None
        if evening is not None and d > start:
            units += t["yield_units"] - evening
        if t["yield_units"] and not first_day:
            first_day = d
        todo = []
        if t["yield_units"] and (d % HARVEST_EVERY[animal] == 0 or t["yield_units"] >= E.ANIMALS[animal]["max_held"] - 1):
            todo.append("HARVEST")
        if d % feed_every == 0:
            todo.append("FEED")
        if care:
            todo.append("CARE")
        if t["fertilizer_available"]:
            todo.append("COLLECT_FERTILIZER")
        for a in todo:
            s.step(P([a]))
            if start <= d < end:
                acts[a] += 1
                fert += a == "COLLECT_FERTILIZER"
                wheat += a == "FEED"
        evening = s.tile(0, X, Y)["yield_units"]
    days = nights = end - start   # 12 nights: a multiple of every production interval
    return {"units_per_day": units / nights, "fert_per_day": fert / days, "wheat_per_day": wheat / days,
            "actions_per_day": sum(acts.values()) / days,
            "acts": {k: v / days for k, v in acts.items()}, "first_harvest_day": first_day}


# ---------------------------------------------------------------------------
def prices(group):
    """base, mid (d10-19) and late (d20-29) prices from our real games."""
    S = json.loads(SUMMARY.read_text(encoding="utf-8"))[group]
    out = {"base": {it: E.market_price(it, 10000) for it in E.PRODUCTS}, "mid": {}, "late": {},
           "buy_wheat": {}, "vwap": {}}
    out["morning_mid"], out["morning_late"], out["source"] = {}, {}, {}
    for it in E.PRODUCTS:
        rows = S["prices"][it]
        out["morning_mid"][it] = sum(r["p50"] for r in rows[10:20]) / 10
        out["morning_late"][it] = sum(r["p50"] for r in rows[20:30]) / 10
        ph = S["sales_us"][it]["by_phase"]
        out["vwap"][it] = ph
        for col, key, morning in (("mid", "d10-19", "morning_mid"), ("late", "d20-29", "morning_late")):
            if ph.get(key) is not None:
                out[col][it] = ph[key]
                out["source"][(it, col).__str__()] = "our realised VWAP"
            else:
                out[col][it] = out[morning][it]
                out["source"][(it, col).__str__()] = "median morning price"
    out["buy_wheat"] = S["sales_us"]["WHEAT"]["buy_vwap"]
    return out, S


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="A+L")
    args = ap.parse_args()
    pr, S = prices(args.group)
    L = S["labour_us"]
    turns_per_useful = L["actions_per_game"] / L["useful"]
    out = {"group": args.group, "prices": pr, "crops": [], "animals": [], "turns_per_useful": turns_per_useful}

    print(f"Prices used ({args.group}): 'mid'/'late' = our realised VWAP in days 10-19 / 20-29 where we sold"
          f" that item then, else the mean of the daily median morning price (shown too)")
    for it in E.PRODUCTS:
        print(f"  {it:11s} base {pr['base'][it]:4d}  mid {pr['mid'][it]:6.1f}  late {pr['late'][it]:6.1f}"
              f"   morning median mid {pr['morning_mid'][it]:6.1f} late {pr['morning_late'][it]:6.1f}")
    print(f"  wheat bought at {pr['buy_wheat']:.1f} on average; turns per useful action in our games "
          f"{turns_per_useful:.2f}")

    print("\nCROPS (one tile, engine-measured). 'actions' = field actions only (plant, water, fertilize,"
          " harvest, dig); fert valued at its sale price in each column")
    print(f"{'schedule':32s} {'units':>5s} {'days':>4s} {'acts':>4s} {'fert':>4s} | "
          f"{'base $/tile-day':>15s} {'$/act':>6s} | {'mid $/t-d':>9s} {'$/act':>6s} | {'late $/t-d':>10s} {'$/act':>6s}")
    for name, crop, water, fert, harvest, dig in CROP_PLANS:
        units, acts, days = run_crop(crop, water, fert, harvest, dig)
        row = {"name": name, "crop": crop, "units": units, "days": days, "actions": acts, "fert": len(fert)}
        cells = []
        for col in ("base", "mid", "late"):
            p = pr[col]
            net = units * p[crop] - E.CROPS[crop]["seed"] - len(fert) * p["FERTILIZER"]
            row[col] = {"net": net, "per_tile_day": net / days, "per_action": net / acts}
            cells.append(f"{net / days:9.1f} {net / acts:6.1f}")
        out["crops"].append(row)
        print(f"{name:32s} {units:5d} {days:4d} {acts:4d} {len(fert):4d} | {cells[0]:>22s} | {cells[1]} | {cells[2]:>17s}")

    print("\nANIMALS, steady state over nights 12-23 (engine-measured), per animal-day; wheat valued at the price"
          " we bought it, fertilizer at its sale price")
    print(f"{'animal / mode':40s} {'units':>5s} {'fert':>4s} {'wheat':>5s} {'acts':>5s} | {'base $/day':>10s} {'$/act':>6s}"
          f" | {'mid $/day':>9s} {'$/act':>6s} | {'late $/day':>10s} {'$/act':>6s}")
    for animal in E.ANIMALS:
        prod = E.ANIMALS[animal]["product"]
        for mode, every, care in ANIMAL_MODES:
            r = run_animal(animal, every, care)
            if r is None:
                print(f"{animal} {mode}: escaped")
                continue
            row = {"animal": animal, "mode": mode, **r}
            cells = []
            for col in ("base", "mid", "late"):
                p = pr[col]
                wheat_price = p["WHEAT"] if col == "base" else pr["buy_wheat"]
                net = r["units_per_day"] * p[prod] + r["fert_per_day"] * p["FERTILIZER"] - r["wheat_per_day"] * wheat_price
                row[col] = {"net_per_day": net, "per_action": net / r["actions_per_day"]}
                cells.append(f"{net:9.1f} {net / r['actions_per_day']:6.1f}")
            out["animals"].append(row)
            print(f"{animal + ' / ' + mode:40s} {r['units_per_day']:5.2f} {r['fert_per_day']:4.2f} {r['wheat_per_day']:5.2f}"
                  f" {r['actions_per_day']:5.2f} | {cells[0]:>17s} | {cells[1]} | {cells[2]:>17s}"
                  f"   (first harvest day {r['first_harvest_day']})")
        cost = E.ANIMALS[animal]["cost"]
        print(f"   {animal} costs {cost}; first production {E.ANIMALS[animal]['first_yield_day']} days after placing")

    # Animal payback by placement day (full care from placement; nights P..28 exist).
    print("\nANIMAL PAYBACK by placement day P (fed + cared daily from placement, fertilizer collected and sold,"
          " wheat bought; the day-29 night never runs, so nights P..28 are all an animal gets)")
    payback = {}
    for animal in E.ANIMALS:
        prod_by_night = []
        s2 = Sim()
        s2.put_animal(0, X, Y, animal, 0)
        for d in range(1, 30):
            s2.to_day(d - 1)
            s2.private(0)["inventories"][0]["WHEAT"] = 1
            s2.step(P(["FEED"]))
            s2.step(P(["CARE"]))
            s2.to_day(d)
            prod_by_night.append(s2.tile(0, X, Y)["yield_units"])
            s2.step(P(["HARVEST"]))
        prod = E.ANIMALS[animal]["product"]
        rows = {}
        for col in ("base", "mid", "late"):
            p = pr[col]
            wheat_price = p["WHEAT"] if col == "base" else pr["buy_wheat"]
            last_ok = None
            for p0 in range(0, 29):
                nights = 29 - p0
                units = sum(prod_by_night[:nights])
                net = units * p[prod] + nights * (p["FERTILIZER"] - wheat_price) - E.ANIMALS[animal]["cost"]
                if net > 0:
                    last_ok = p0
            rows[col] = last_ok
        payback[animal] = {"prod_by_night": prod_by_night, "last_paying_day": rows}
        print(f"   {animal:6s} units credited per night from placement: {prod_by_night[:12]}...;"
              f" latest paying placement day: base {rows['base']}, mid prices {rows['mid']}, late prices {rows['late']}")
    out["payback"] = payback

    # Hands.
    print("\nHANDS: the n-th hire of a day costs fib(n); a hand hired at hour 0 acts on hours 1-23 (23 turns;"
          " 22 on day 29).")
    useful_share = 1 / turns_per_useful
    print(f"In our games {useful_share:.0%} of unit turns are useful (not a move, PASS or ignored).")
    print(f"{'hand':>4s} {'cost':>5s} {'cum':>6s} {'$/turn':>7s} {'$/useful act':>13s}")
    cum = 0
    hands = []
    for n in range(1, 17):
        c = E._hire_cost(n - 1)
        cum += c
        per_turn = c / 23
        per_useful = per_turn * turns_per_useful
        hands.append({"n": n, "cost": c, "cum": cum, "per_turn": per_turn, "per_useful": per_useful})
        print(f"{n:4d} {c:5d} {cum:6d} {per_turn:7.2f} {per_useful:13.2f}")
    out["hands"] = hands

    # Value of a hand-day.
    net = S["results"]["median_us"] - 3000
    print(f"\nOur median game nets {net:,.0f} over {L['useful']:.0f} useful actions = "
          f"{net / L['useful']:.1f} per useful action ({net / L['actions_per_game']:.1f} per unit turn).")
    out["net_per_useful"] = net / L["useful"]

    # Land.
    print("\nLAND break-even: net needed per tile-day to repay the quadrant, if all 25 tiles are worked from"
          " the purchase day to day 29 (weeds and walking ignored)")
    best = {r["name"]: r for r in out["crops"]}
    w = best["wheat, harvest age 4"]
    print(f"{'day':>4s} " + " ".join(f"{q:>14s}" for q in ("NE $1000", "SW $2000", "SE $4000")))
    land = []
    for d in range(0, 27, 2):
        tile_days = 25 * (29 - d)
        cells = [c / tile_days for c in E.LAND_PRICES]
        land.append({"day": d, "need": cells})
        print(f"{d:4d} " + " ".join(f"{c:14.1f}" for c in cells))
    out["land"] = land
    print(f"   compare: wheat (age-4 cycle) nets {w['base']['per_tile_day']:.1f}/tile-day at base, "
          f"{w['mid']['per_tile_day']:.1f} mid-game, {w['late']['per_tile_day']:.1f} late, before labour;"
          f" it needs {w['actions'] / w['days']:.2f} field actions per tile-day")

    # Feed.
    print(f"\nFEED: each fed animal eats 1 wheat per FEED. At the {pr['buy_wheat']:.1f} we paid, a daily-fed animal"
          f" costs {pr['buy_wheat']:.1f}/day; a home-grown wheat tile yields 1 wheat/tile-day (age-4 cycle),"
          f" so a self-fed animal occupies about 2 tiles.")
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
