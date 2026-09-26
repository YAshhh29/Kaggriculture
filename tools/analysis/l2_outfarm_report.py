"""Out-farm autopsy, part 2: where each big loss's coins went, us against them.

Reads the books written by tools.analysis.l2_outfarm_replay and prints, per
game: the town, money by day, the exact accounting of the final gap (sales by
item, seed / animal / product purchases, wages, land -- final money is 3,000
plus these, so the rows sum to the gap), the census of both farms, harvest and
fertilizer use, and sales by phase.

    python -m tools.analysis.l2_outfarm_report
    python -m tools.analysis.l2_outfarm_report --episodes 113751067
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "rl" / "data" / "l2" / "outfarm"
PHASES = (("d0-14", 0, 15), ("d15-24", 15, 25), ("d25-29", 25, 30))
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")
ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
DAYS = (2, 5, 8, 11, 14, 17, 20, 23, 26, 29)


def phase_of(step: int) -> str:
    return next(p for p, lo, hi in PHASES if lo <= step // 24 < hi)


def flows(book: dict) -> Counter:
    """Money in and out by source; sums to final money - 3000."""
    out: Counter = Counter()
    for step, item, price in book["sales"]:
        out["sell " + item] += price
    for step, op, item, price in book["buys"]:
        key = {"BUY_SEED": "seed ", "BUY_ANIMAL": "animal ", "BUY_PRODUCT": "buy "}[op] + item
        out[key] -= price
    for step, cost in book["hires"]:
        out["wages"] -= cost
    for step, cost, q in book["land"]:
        out["land"] -= cost
    return out


def sales_by_phase(book: dict) -> dict:
    out = defaultdict(lambda: [0, 0.0])
    for step, item, price in book["sales"]:
        cell = out[(item, phase_of(step))]
        cell[0] += 1
        cell[1] += price
    return out


def harvest_stats(book: dict) -> dict:
    out = {}
    for crop in CROPS:
        rows = [h for h in book["harvest"] if h[1] == crop]
        if not rows:
            continue
        units = sum(h[2] for h in rows)
        fert = [h for h in rows if h[3]]
        out[crop] = {"harvests": len(rows), "units": units,
                     "per": units / len(rows), "fert_share": len(fert) / len(rows),
                     "fert_units": sum(h[2] for h in fert)}
    for product in ("EGG", "MILK", "WOOL"):
        rows = [h for h in book["harvest"] if h[1] == product]
        if rows:
            out[product] = {"harvests": len(rows), "units": sum(h[2] for h in rows)}
    return out


def report(game: dict) -> list[str]:
    side = game["our_side"]
    us, them = game["books"][side], game["books"][1 - side]
    lines = []
    margin = game["live"]["us"] - game["live"]["them"]
    shops6 = game["shops_by_day"].get("6") or game["shops_by_day"].get(6)
    lines.append(f"\n=== ep{game['episode_id']} vs {game['opponent']} "
                 f"({'A' if game['submission'] == 56571049 else 'L'}, seat {side}) "
                 f"final {game['live']['us']:,.0f} vs {game['live']['them']:,.0f} = {margin:+,.0f}")
    lines.append(f"  town at day 6: {shops6}; final: {game['town']}")
    # money by day
    row = []
    for d in DAYS:
        cu, ct = us["census"].get(str(d)), them["census"].get(str(d))
        if cu and ct:
            row.append(f"d{d}:{cu['money'] - ct['money']:+,.0f}")
    lines.append("  cash gap (us-them) at dusk: " + " ".join(row))
    # accounting
    fu, ft = flows(us), flows(them)
    keys = sorted(set(fu) | set(ft), key=lambda k: -abs(fu.get(k, 0) - ft.get(k, 0)))
    lines.append("  accounting (us - them), largest first:")
    parts = []
    for k in keys:
        d = fu.get(k, 0) - ft.get(k, 0)
        if abs(d) >= 50:
            parts.append(f"{k} {d:+,.0f} ({fu.get(k, 0):,.0f}/{ft.get(k, 0):,.0f})")
    for i in range(0, len(parts), 4):
        lines.append("    " + " | ".join(parts[i:i + 4]))
    lines.append(f"    check: sum {sum(fu.values()) - sum(ft.values()):+,.0f} vs margin {margin:+,.0f}")
    # census
    lines.append("  census at dusk (us/them): day | quads | hands | " +
                 " ".join(c[:4] for c in CROPS) + " | goose cow sheep | weeds bare pens")
    for d in DAYS:
        cu, ct = us["census"].get(str(d)), them["census"].get(str(d))
        if not (cu and ct):
            continue
        crops = " ".join(f"{cu['plants'].get(c, 0)}/{ct['plants'].get(c, 0)}" for c in CROPS)
        anim = " ".join(f"{cu['animals'].get(a, 0)}/{ct['animals'].get(a, 0)}" for a in ANIMALS)
        hu, ht = us["hands_peak"].get(str(d), 0), them["hands_peak"].get(str(d), 0)
        lines.append(f"    {d:2d} | {len(cu['quadrants'])}/{len(ct['quadrants'])} | {hu}/{ht} | "
                     f"{crops} | {anim} | {cu['weeds']}/{ct['weeds']} {cu['bare']}/{ct['bare']} "
                     f"{cu['pens']}/{ct['pens']}")
    land_u = [(s // 24, q) for s, c, q in us["land"]]
    land_t = [(s // 24, q) for s, c, q in them["land"]]
    lines.append(f"  land bought (day, quadrant): us {land_u}  them {land_t}")
    # plantings by crop and phase
    pu, pt = Counter(), Counter()
    for s, crop, x, y in us["plant"]:
        pu[(crop, phase_of(s))] += 1
    for s, crop, x, y in them["plant"]:
        pt[(crop, phase_of(s))] += 1
    cells = []
    for crop in CROPS:
        for p, _, _ in PHASES:
            if pu[(crop, p)] or pt[(crop, p)]:
                cells.append(f"{crop[:4]} {p} {pu[(crop, p)]}/{pt[(crop, p)]}")
    lines.append("  plantings (us/them): " + "; ".join(cells))
    # harvest
    hu, ht = harvest_stats(us), harvest_stats(them)
    cells = []
    for k in list(CROPS) + ["EGG", "MILK", "WOOL"]:
        a, b = hu.get(k), ht.get(k)
        if not (a or b):
            continue
        a = a or {"harvests": 0, "units": 0}
        b = b or {"harvests": 0, "units": 0}
        extra = ""
        if k in CROPS:
            extra = (f" per {a.get('per', 0):.2f}/{b.get('per', 0):.2f}"
                     f" fert {a.get('fert_share', 0):.0%}/{b.get('fert_share', 0):.0%}")
        cells.append(f"{k[:5]} units {a['units']}/{b['units']} (n {a['harvests']}/{b['harvests']}{extra})")
    for c in cells:
        lines.append("  harvest: " + c)
    fz_u = Counter(f[1] for f in us["fertilize"])
    fz_t = Counter(f[1] for f in them["fertilize"])
    col_u, col_t = sum(us["collect"].values()), sum(them["collect"].values())
    lines.append(f"  FERTILIZE applied (us/them): {dict(fz_u)} / {dict(fz_t)}; "
                 f"collected {col_u}/{col_t}; fed {sum(us['feed'].values())}/{sum(them['feed'].values())}; "
                 f"cared {sum(us['care'].values())}/{sum(them['care'].values())}")
    wu = [sum(v[i] for v in us["water"].values()) for i in range(3)]
    wt = [sum(v[i] for v in them["water"].values()) for i in range(3)]
    lines.append(f"  waterings no-gain/+1/+2 (us | them): {wu} | {wt}")
    # sales by phase
    su, st = sales_by_phase(us), sales_by_phase(them)
    lines.append("  sales by phase (units us/them, revenue us-them):")
    for item in ITEMS:
        cells = []
        for p, _, _ in PHASES:
            a, b = su.get((item, p), [0, 0]), st.get((item, p), [0, 0])
            if a[0] or b[0]:
                cells.append(f"{p} {a[0]}/{b[0]} {a[1] - b[1]:+,.0f}")
        if cells:
            lines.append(f"    {item:10s} " + " | ".join(cells))
    # purchases
    bu, bt = Counter(), Counter()
    for s, op, item, price in us["buys"]:
        bu[(op, item)] += 1
    for s, op, item, price in them["buys"]:
        bt[(op, item)] += 1
    cells = [f"{op.replace('BUY_', '')} {item} {bu[(op, item)]}/{bt[(op, item)]}"
             for op, item in sorted(set(bu) | set(bt))]
    lines.append("  purchases (units us/them): " + "; ".join(cells))
    hires_u = Counter(s // 24 for s, c in us["hires"])
    hires_t = Counter(s // 24 for s, c in them["hires"])
    lines.append(f"  wages total {sum(c for s, c in us['hires']):,.0f}/{sum(c for s, c in them['hires']):,.0f}; "
                 f"hires per day us {[hires_u.get(d, 0) for d in range(30)]}")
    lines.append(f"  {'':34s}them {[hires_t.get(d, 0) for d in range(30)]}")
    ru, rt = Counter(), Counter()
    for s, crop, n in us["rot"]:
        ru[crop] += n
    for s, crop, n in them["rot"]:
        rt[crop] += n
    lines.append(f"  rot {dict(ru)} / {dict(rt)}; binned {us['binned']} / {them['binned']}; "
                 f"escaped {len(us['escaped'])}/{len(them['escaped'])}")
    pl_u = Counter(p[1] for p in us["place"])
    pl_t = Counter(p[1] for p in them["place"])
    lines.append(f"  animals placed {dict(pl_u)} / {dict(pl_t)}; "
                 f"first placements us {[(s // 24, a) for s, a, x, y in us['place'][:3]]} "
                 f"them {[(s // 24, a) for s, a, x, y in them['place'][:3]]}")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--episodes", type=int, nargs="*", default=[])
    args = ap.parse_args()
    paths = sorted((OUT / "books").glob("ep*.json"))
    if args.episodes:
        paths = [p for p in paths if int(p.stem[2:]) in set(args.episodes)]
    games = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    games.sort(key=lambda g: g["live"]["us"] - g["live"]["them"])
    for g in games:
        print("\n".join(report(g)))


if __name__ == "__main__":
    main()
