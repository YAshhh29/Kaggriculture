"""Market math with the engine's own price function.

  1. every curve: price at offsets from I0, the $1-floor inventory, hinge knees
  2. slope: dollars per unit moved, at I0 and at the inventories our real
     games actually held on days 5 / 15 / 25 (rl/data/l2/econ/summary.json)
  3. price impact: revenue and slippage of selling n units at once
  4. slot order: selling n units in an earlier slot than the opponent's m units,
     the same slot (lockstep), or a later one
  5. town demand: units per shop per day, expected season demand per product
     under uniform shop draws, and the price a shop tick adds per unit sold
     after it rather than before it
  6. buying wheat: cost of n units at typical inventories

All prices come from kaggriculture.market_price, and every multi-unit sale
applies the engine's rule that a sale at $1 does not add inventory.

    python -m tools.analysis.l2_econ_market [--group A+L]
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations_with_replacement  # noqa: F401
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import kaggle_environments.envs.kaggriculture.kaggriculture as E  # noqa: E402

SUMMARY = ROOT / "rl" / "data" / "l2" / "econ" / "summary.json"
OUT = ROOT / "rl" / "data" / "l2" / "econ" / "market.json"
I0 = 10000
price = E.market_price


def sell_run(item, inv, n):
    """Revenue of n units sold one at a time from inventory inv; returns (revenue, inv after)."""
    rev = 0
    for _ in range(n):
        p = price(item, inv)
        rev += p
        if p > 1:
            inv += 1
    return rev, inv


def lockstep(item, inv, n_us, n_them):
    """Both players selling the same item in the same slot, one unit each per round."""
    us = them = 0
    a, b = n_us, n_them
    while a > 0 or b > 0:
        p = price(item, inv)
        added = 0
        if a > 0:
            us += p
            a -= 1
            added += p > 1
        if b > 0:
            them += p
            b -= 1
            added += p > 1
        inv += added
    return us, them


def floor_inventory(item):
    x = I0
    while price(item, x) > 1:
        x += 1
        if x > I0 + 100000:
            return None
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="A+L")
    args = ap.parse_args()
    S = json.loads(SUMMARY.read_text(encoding="utf-8"))[args.group] if SUMMARY.exists() else None
    out = {}

    # 1. Curves.
    offs = [-900, -600, -400, -200, -100, -50, 0, 50, 100, 200, 400, 600]
    print("1. PRICE CURVES: price at inventory I0+offset (I0=10000), and where the $1 floor starts")
    print(f"{'item':11s} {'T':>4s} " + " ".join(f"{o:>+6d}" for o in offs) + "  floor at I0+")
    curves = {}
    for it in E.PRODUCTS:
        T = E.MARKET_PARAMS[it]["T"]
        fl = floor_inventory(it)
        row = [price(it, I0 + o) for o in offs]
        curves[it] = {"T": T, "prices": dict(zip(offs, row)), "floor_offset": fl - I0 if fl else None}
        print(f"{it:11s} {T:4d} " + " ".join(f"{p:6d}" for p in row) + f"  {fl - I0 if fl else '-':>6}")
    out["curves"] = curves

    print("\n   Hinge knees (carrot, tomato, egg): calm to I0-T, then a quadratic runaway")
    for it in ("CARROT", "TOMATO", "EGG"):
        T = E.MARKET_PARAMS[it]["T"]
        pts = [(m, price(it, I0 - int(m * T))) for m in (0.5, 1.0, 1.25, 1.5, 2.0)]
        print(f"   {it:7s} T={T}: " + ", ".join(f"I0-{m}T -> ${p}" for m, p in pts))

    # 2. Slopes at typical inventories.
    print("\n2. SLOPE: $ change for the next unit sold (price(inv) - price(inv+1)), at I0 and at the median"
          " inventory our real games held on the morning of day 5 / 15 / 25")
    slopes = {}
    for it in E.PRODUCTS:
        cells = [f"I0: {price(it, I0 - 1) - price(it, I0):+d}/{price(it, I0) - price(it, I0 + 1):+d}"]
        row = {}
        if S:
            for d in (5, 15, 25):
                inv = int(S["prices"][it][d]["inv50"])
                p0 = price(it, inv)
                # Average slope over the next 10 units (rounding makes single steps 0 or 1).
                p10 = price(it, inv + 10)
                row[d] = {"inv": inv, "price": p0, "per_unit": (p0 - p10) / 10}
                cells.append(f"d{d} inv {inv - I0:+5d} ${p0:<4d} {(p0 - p10) / 10:5.2f}/unit")
        slopes[it] = row
        print(f"   {it:11s} " + " | ".join(cells))
    out["slopes"] = slopes

    # 3. Price impact of selling n at once.
    print("\n3. PRICE IMPACT: selling n units in one go (average $/unit, and the loss versus n x the"
          " opening quote), at the day-15 and day-25 median inventories")
    impact = {}
    for it in E.PRODUCTS:
        row = {}
        cells = []
        for d in (15, 25):
            inv = int(S["prices"][it][d]["inv50"]) if S else I0
            q0 = price(it, inv)
            for n in (10, 40, 80):
                rev, _ = sell_run(it, inv, n)
                row[f"d{d}_n{n}"] = {"avg": rev / n, "loss": q0 * n - rev}
                cells.append(f"d{d} n{n}: {rev / n:6.1f} (-{q0 * n - rev:,.0f})")
        impact[it] = row
        print(f"   {it:11s} " + "  ".join(cells))
    out["impact"] = impact

    # 4. Slot order.
    print("\n4. SLOT ORDER: our revenue for n units when the opponent sells m units of the same item"
          " in an EARLIER slot / the SAME slot (lockstep) / a LATER slot; day-15 median inventory")
    slot = {}
    for it in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
        inv = int(S["prices"][it][15]["inv50"]) if S else I0
        cells = []
        row = {}
        for n in (10, 20, 40):
            m = n
            first, _ = sell_run(it, inv, n)
            _, after = sell_run(it, inv, m)
            second, _ = sell_run(it, after, n)
            same, _ = lockstep(it, inv, n, m)
            row[n] = {"first": first, "same": same, "second": second}
            cells.append(f"n=m={n}: {first:,}/{same:,}/{second:,} (edge {first - second:,})")
        slot[it] = row
        print(f"   {it:11s} inv {inv - I0:+5d}: " + "  ".join(cells))
    out["slot"] = slot

    # 5. Town demand.
    print("\n5. TOWN DEMAND per product: units/day per shop instance (6 ticks/day; single-product shops"
          " eat 2 per tick) + 1/day town centre (not fertilizer)")
    rate = {it: {} for it in E.PRODUCTS}
    for shop, items in E.SHOPS.items():
        for it in items:
            rate[it][shop] = 6 * (2 if len(items) == 1 else 1)
    # Expected consumption under uniform draws: shop k live from day 3k to day 29 (6 ticks/day).
    shop_days = sum(30 - 3 * k for k in range(1, 9))
    demand = {}
    for it in E.PRODUCTS:
        per_draw = sum(rate[it].values()) / len(E.SHOPS)
        centre = 0 if it == "FERTILIZER" else 30
        season = centre + shop_days * per_draw
        demand[it] = {"per_shop": rate[it], "per_draw_per_day": per_draw, "season_expected": season,
                      "T": E.MARKET_PARAMS[it]["T"]}
        print(f"   {it:11s} shops {rate[it] or '-'}; expected +{per_draw:.2f}/day per unlock; expected season"
              f" demand {season:6.0f} (T={E.MARKET_PARAMS[it]['T']})")
    print(f"   (8 unlocks live from days 3,6,...,24 give {shop_days} shop-days; day 29 still has all 6 ticks)")
    out["demand"] = demand

    print("\n   A shop tick runs AFTER the market at hours 0,4,...,20. Selling on the turn after a tick"
          " instead of on the tick turn gains, per unit, the tick's drain x the slope:")
    for it in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "EGG", "MILK", "WOOL"):
        inv = int(S["prices"][it][15]["inv50"]) if S else I0
        cells = []
        for k in (1, 2, 3):
            drain = k * max(rate[it].values()) // 6
            cells.append(f"{k} shop(s): +${price(it, inv - drain) - price(it, inv)}")
        print(f"   {it:11s} at day-15 median inventory: " + ", ".join(cells))

    if S:
        print("\n   Measured in our games (median inventory vs I0 on the morning of each day):")
        for it in E.PRODUCTS:
            rows = S["prices"][it]
            print(f"   {it:11s} " + " ".join(f"d{d}:{int(rows[d]['inv50']) - I0:+d}" for d in (3, 6, 9, 12, 15, 18, 21, 24, 27, 29)))

    # 6. Buying wheat.
    print("\n6. BUYING WHEAT: cost of n units bought at once (buy quoted at post-buy inventory)")
    for d in (5, 15, 25):
        inv = int(S["prices"]["WHEAT"][d]["inv50"]) if S else I0
        cells = []
        for n in (10, 30, 60, 100):
            cost = sum(price("WHEAT", inv - 1 - k) for k in range(n))
            cells.append(f"n{n}: {cost:,} ({cost / n:.1f}/u)")
        print(f"   day {d} inv {inv - I0:+d} (quote {price('WHEAT', inv - 1)}): " + ", ".join(cells))

    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
