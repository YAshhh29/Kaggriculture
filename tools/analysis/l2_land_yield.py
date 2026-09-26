"""What each tile-day of land earns, by crop, from exact replays.

Land is nearly full (tools.analysis.l2_land_report), so the question becomes
what the full land holds. For the side under study this measures, per crop:
tile-days occupied (dusk census), units harvested (inventory gain on a
HARVEST that the engine applied), units sold and revenue (every committed
SELL unit, at the price the engine paid), seed spent, and so revenue per
occupied tile-day -- overall and for plants that were alive in the second
half (days 18-29) when the premium books have usually crashed.

    python -m tools.analysis.l2_land_yield --set L
    python -m tools.analysis.l2_land_yield --set top30
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

from tools.analysis.l2_land_fast import (CORPUS, corpus_record, live_paths,  # noqa: E402
                                         live_record, replay)

OUT = ROOT / "rl" / "data" / "l2" / "land"
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
SEED = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}


def one(seed, tp, side):
    from kaggle_environments.envs.kaggriculture import kaggriculture as E
    commit = E._commit_unit
    cur = {"farms": None, "t": 0}
    sold = defaultdict(lambda: [0, 0.0])          # item -> [units, revenue]
    sold_late = defaultdict(lambda: [0, 0.0])
    seeds = Counter()

    def cu(op, item, price, farm, *rest):
        ok = commit(op, item, price, farm, *rest)
        if ok and farm is cur["farms"][side]:
            if op == "SELL":
                sold[item][0] += 1
                sold[item][1] += price
                if cur["t"] >= 18 * 24:
                    sold_late[item][0] += 1
                    sold_late[item][1] += price
            elif op == "BUY_SEED":
                seeds[item] += 1
        return ok

    E._commit_unit = cu
    tile_days = Counter()
    tile_days_late = Counter()
    try:
        for t, g, acts in replay(seed, tp):
            cur["farms"] = g.obs.farms
            cur["t"] = t
            if t % 24 == 23:
                for row in g.obs.farms[side]["tiles"]:
                    for tile in row:
                        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                            tile_days[tile["crop"]] += 1
                            if t >= 18 * 24:
                                tile_days_late[tile["crop"]] += 1
                        elif isinstance(tile, dict) and tile.get("animal"):
                            tile_days[tile["animal"]] += 1
                            if t >= 18 * 24:
                                tile_days_late[tile["animal"]] += 1
    finally:
        E._commit_unit = commit
    return {"sold": {k: list(v) for k, v in sold.items()},
            "sold_late": {k: list(v) for k, v in sold_late.items()},
            "seeds": dict(seeds), "tile_days": dict(tile_days), "tile_days_late": dict(tile_days_late)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="L", choices=("L", "A", "top30"))
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    jobs = []
    if a.set in ("L", "A"):
        for p in live_paths(56582917 if a.set == "L" else 56571049):
            seed, side, tp, _ = live_record(p)
            jobs.append((seed, tp, side))
    else:
        for p in sorted(CORPUS.glob("ep*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            if int(r.get("team_rank") or 9999) <= 30:
                seed, seat, tp, _ = corpus_record(p)
                jobs.append((seed, tp, seat))
    if a.limit:
        jobs = jobs[:a.limit]
    rows = [one(*j) for j in jobs]
    n = len(rows)
    prod = {"WHEAT": "WHEAT", "CARROT": "CARROT", "TOMATO": "TOMATO", "STRAWBERRY": "STRAWBERRY",
            "MELON": "MELON", "GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
    lines = [f"[{a.set}] {n} games, per game means. revenue/tile-day = sales of the product / tile-days "
             "the crop or animal occupied (wheat sales exclude feed use; animals exclude wheat eaten)"]
    lines.append("  crop        tile-days  sold   revenue  avg$   seed$  rev/tile-day | days 18-29: tile-days sold avg$ rev/tile-day")
    for crop in CROPS + ("GOOSE", "COW", "SHEEP"):
        item = prod[crop]
        td = sum(r["tile_days"].get(crop, 0) for r in rows) / n
        u = sum(r["sold"].get(item, [0, 0])[0] for r in rows) / n
        rev = sum(r["sold"].get(item, [0, 0])[1] for r in rows) / n
        sd = sum(r["seeds"].get(crop, 0) for r in rows) / n * SEED.get(crop, 0)
        tdl = sum(r["tile_days_late"].get(crop, 0) for r in rows) / n
        ul = sum(r["sold_late"].get(item, [0, 0])[0] for r in rows) / n
        revl = sum(r["sold_late"].get(item, [0, 0])[1] for r in rows) / n
        lines.append(f"  {crop:11s} {td:9.0f} {u:5.0f} {rev:9,.0f} {rev / max(1, u):5.0f} {sd:7,.0f} "
                     f"{(rev - sd) / max(1, td):8.1f}     | {tdl:9.0f} {ul:5.0f} {revl / max(1, ul):5.0f} "
                     f"{revl / max(1, tdl):8.1f}")
    fert = sum(r["sold"].get("FERTILIZER", [0, 0])[1] for r in rows) / n
    fu = sum(r["sold"].get("FERTILIZER", [0, 0])[0] for r in rows) / n
    lines.append(f"  fertilizer sold {fu:.0f} units for {fert:,.0f} (avg {fert / max(1, fu):.0f})")
    text = "\n".join(lines)
    print(text)
    (OUT / f"yield_{a.set}.txt").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
