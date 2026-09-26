"""What each crop cycle actually earned in our real games, by planting day.

From the replay ledgers (tools/analysis/l2_econ_replay.py): every plant our
side put in the ground, with its waterings, fertilizer and harvests. Each
harvested unit is valued at the same game's morning price of that item on the
day after the harvest (when the parent typically sells it), which is close to
what the unit fetched; seed and fertilizer (at that day's fertilizer price)
are subtracted. Output: cycles per game, units, value per cycle, per tile-day
and per field action, by planting-day bucket, for our side and the opponent.

Also counts late wheat cycles left unfertilized while fertilizer was being
sold cheaply the same days.

    python -m tools.analysis.l2_econ_cycles
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import kaggle_environments.envs.kaggriculture.kaggriculture as E  # noqa: E402

GAMES = ROOT / "rl" / "data" / "l2" / "econ" / "games"
OUT = ROOT / "rl" / "data" / "l2" / "econ" / "cycles.json"
BUCKETS = ((0, 4), (5, 9), (10, 14), (15, 19), (20, 24), (25, 29))


def morning(g, item, day):
    day = min(max(day, 0), 29)
    if day == 0:
        return E.market_price(item, 10000)
    return E.market_price(item, g["inv_path"][item][day * 24 - 1])


def main() -> None:
    games = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(GAMES.glob("ep*.json"))]
    n = len(games)
    out = {}
    for who in ("us", "them"):
        rows = defaultdict(list)
        late_unfert = []
        late_fert_sold = []
        for g in games:
            p = g["our_side"] if who == "us" else 1 - g["our_side"]
            side = g["sides"][p]
            lu = 0
            for c in side["plants"]:
                crop = c["crop"]
                d0 = c["day"]
                units = sum(h[1] for h in c["harvest"])
                value = sum(h[1] * morning(g, crop, d0 + h[0] + 1) for h in c["harvest"])
                fert_cost = sum(morning(g, "FERTILIZER", d0 + a) for a in c["fert"])
                net = value - E.CROPS[crop]["seed"] - fert_cost
                last = max([h[0] for h in c["harvest"]] or [0])
                days = max(1, last)
                acts = 1 + len(c["water"]) + len(c["fert"]) + len(c["harvest"]) + (
                    1 if E.CROPS[crop]["ongoing"] else 0)
                b = next(f"d{lo}-{hi}" for lo, hi in BUCKETS if lo <= d0 <= hi)
                rows[(crop, b)].append((units, net, days, acts))
                if crop == "WHEAT" and d0 >= 17 and not c["fert"] and c["harvest"]:
                    lu += 1
            late_unfert.append(lu)
            late_fert_sold.append(sum(1 for pl, step, op, item, price in g["market_log"]
                                      if pl == p and op == "SELL" and item == "FERTILIZER" and step >= 20 * 24))
        table = {}
        print(f"\n== {who}: per planting-day bucket (value = units x next-morning price - seed - fertilizer)")
        print(f"{'crop':10s} {'bucket':7s} {'cyc/game':>8s} {'units':>6s} {'net/cycle':>9s} {'$/tile-day':>10s} {'$/action':>8s}")
        for crop in E.CROPS:
            for lo, hi in BUCKETS:
                b = f"d{lo}-{hi}"
                r = rows.get((crop, b))
                if not r:
                    continue
                units = statistics.mean(x[0] for x in r)
                net = statistics.mean(x[1] for x in r)
                ptd = sum(x[1] for x in r) / sum(x[2] for x in r)
                pa = sum(x[1] for x in r) / sum(x[3] for x in r)
                table[f"{crop}|{b}"] = {"cycles_per_game": len(r) / n, "units": units, "net": net,
                                        "per_tile_day": ptd, "per_action": pa}
                print(f"{crop:10s} {b:7s} {len(r) / n:8.1f} {units:6.2f} {net:9.0f} {ptd:10.1f} {pa:8.1f}")
        print(f"late wheat cycles (planted day >= 17) harvested without fertilizer: "
              f"{statistics.mean(late_unfert):.1f}/game; fertilizer sold on days 20-29: "
              f"{statistics.mean(late_fert_sold):.1f}/game")
        out[who] = {"table": table, "late_unfert_wheat": statistics.mean(late_unfert),
                    "late_fert_sold": statistics.mean(late_fert_sold)}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
