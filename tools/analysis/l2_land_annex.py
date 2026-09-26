"""What would the idle SE rows earn as extra tomatoes in V219 games?

When V219 fires (day 18) it buys SE and plants rows 5-6 only; rows 7-9
(15 tiles) stay empty to the end. The only crop dear enough to pay the
13th/14th hand those rows would need is tomato: in L's V219 games the book
reaches $85-336 on days 26-29.

For each real V219 game (exact replay) this takes our real tomato sales
(step, units) and asks what k extra tiles would have earned if their crop
were sold alongside ours, in the same steps, pro rata (8 tomatoes a tile
fertilized, 4 unfertilized): each extra unit is priced by the engine's price
function at the inventory it would really have met (our earlier extra units
stay in the book: the town eats a fixed count per tick whatever the price).
Our original units lose value too (they sell into the extra supply), and so
does the opponent -- both are reported. Costs: seed, the fertilizer V219
uses (2 units a tile) at that game's day-24/27 quote, and labour at the
Fibonacci price of the hire index the extra hand would really have had
(the game's own hires that day + 1), for the worker-days in --worker-days.

    python -m tools.analysis.l2_land_annex --tiles 5 10
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_land_fast import live_paths, live_record, replay  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "land"


def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def game_book(seed, tp, side):
    """Our/their tomato sale events and the day's hire counts, from the exact replay."""
    from kaggle_environments.envs.kaggriculture import kaggriculture as E
    commit = E._commit_unit
    cur = {"farms": None, "t": 0}
    events = []   # (t, who, price, inv_before)

    def cu(op, item, price, farm, private, market, *rest):
        inv = market["inventory"].get(item, 0)
        ok = commit(op, item, price, farm, private, market, *rest)
        if ok and op == "SELL" and item == "TOMATO":
            who = 0 if farm is cur["farms"][side] else 1
            events.append((cur["t"], who, price, inv))
        return ok

    E._commit_unit = cu
    se_day = None
    hires = {}
    fert = {}
    town = {}
    try:
        for t, g, acts in replay(seed, tp):
            cur["farms"] = g.obs.farms
            cur["t"] = t
            f = g.obs.farms[side]
            if se_day is None and "SE" in f["unlocked_quadrants"]:
                se_day = t / 24
            d = t // 24
            hires[d] = max(hires.get(d, 0), int(f["hires_today"]))
            if t % 24 == 12:
                fert[d] = g.obs.market["prices"]["FERTILIZER"]
    finally:
        E._commit_unit = commit
    return se_day, events, hires, fert


def annex_value(events, extra_ratio, price_fn):
    """Revenue change for us and them when each of our sale units comes with
    `extra_ratio` more units (fractional carry), sold right after it."""
    shift = 0          # extra units already in the book
    carry = 0.0
    us_base = us_new = them_base = them_new = 0.0
    extra_units = 0
    for t, who, price, inv in events:
        new_price = price_fn(inv + shift)
        if who == 0:
            us_base += price
            us_new += new_price
            carry += extra_ratio
            while carry >= 1.0:
                p = price_fn(inv + shift + 1)
                us_new += p
                if p > 1:
                    shift += 1
                extra_units += 1
                carry -= 1.0
        else:
            them_base += price
            them_new += new_price
    return us_new - us_base, them_new - them_base, extra_units


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tiles", type=int, nargs="+", default=[5, 10, 15])
    ap.add_argument("--per-tile", type=int, default=8, help="tomatoes per extra tile (8 fertilized, 4 not)")
    ap.add_argument("--worker-days", type=int, nargs="+", default=[18, 20, 22, 24, 26, 27, 28, 29],
                    help="days an extra hand is hired (one hand per 5 tiles)")
    a = ap.parse_args()
    from kaggle_environments.envs.kaggriculture.kaggriculture import market_price

    def pf(inv):
        return market_price("TOMATO", inv)

    games = []
    for p in live_paths(56582917):
        seed, side, tp, r = live_record(p)
        se_day, events, hires, fert = game_book(seed, tp, side)
        if se_day is None or not (17.5 < se_day < 18.5):
            continue
        games.append((r, events, hires, fert))
    lines = [f"{len(games)} V219 games among L's live games; {a.per_tile} tomatoes per extra tile; "
             f"extra hands on days {a.worker_days} (one per 5 tiles)"]
    for k in a.tiles:
        rows = []
        for r, events, hires, fert in games:
            ours = sum(1 for e in events if e[1] == 0)
            if not ours:
                continue
            ratio = k * a.per_tile / ours
            d_us, d_them, units = annex_value(events, ratio, pf)
            n_hands = -(-k // 5)
            labour = sum(fib(hires.get(d, 12) + j) for d in a.worker_days for j in range(n_hands))
            fert_cost = 2 * k * (statistics.mean([fert.get(24, 100), fert.get(27, 100)]) + 2) if a.per_tile > 4 else 0
            seeds = 50 * k
            net = d_us - labour - fert_cost - seeds
            rows.append({"ep": r["episode_id"], "d_us": d_us, "d_them": d_them, "units": units,
                         "labour": labour, "fert": fert_cost, "seeds": seeds, "net": net,
                         "net_margin": net - d_them, "avg": d_us / max(1, units)})
        nets = [x["net"] for x in rows]
        lines.append(f"\n  +{k} tiles: our revenue change median {statistics.median(x['d_us'] for x in rows):+,.0f} "
                     f"(extra units {statistics.median(x['units'] for x in rows):.0f}, net of the price hit on our own "
                     f"80: {statistics.median(x['avg'] for x in rows):.0f}/unit); costs: labour "
                     f"{statistics.median(x['labour'] for x in rows):,.0f}, fertilizer "
                     f"{statistics.median(x['fert'] for x in rows):,.0f}, seed {rows[0]['seeds']:,.0f}")
        lines.append(f"    own net per V219 game: median {statistics.median(nets):+,.0f}, mean {statistics.mean(nets):+,.0f}, "
                     f"positive in {sum(n > 0 for n in nets)}/{len(nets)}; opponent's tomato revenue change "
                     f"median {statistics.median(x['d_them'] for x in rows):+,.0f}; margin net mean "
                     f"{statistics.mean(x['net_margin'] for x in rows):+,.0f}")
        lines.append("    per game (own net): " + ", ".join(f"{x['net']:+,.0f}" for x in sorted(rows, key=lambda x: x['net'])))
    text = "\n".join(lines)
    print(text)
    (OUT / "annex_value.txt").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
