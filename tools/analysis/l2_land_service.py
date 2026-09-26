"""Idle turns that stood on work nobody did: free fixes without moving anyone.

Replays each game exactly (tools.analysis.l2_land_fast) and, at every
night's refresh, reads the side's tiles before the engine resets them:
animals fed / cared / fertilizer still uncollected, plants watered or not.
Each miss is matched against the idle unit-turns (PASS, or refused by the
engine) that stood on that very tile earlier that day -- a fix that needs no
movement and no new hand, so it cannot desynchronise the route.

Also counts production clipped at an animal's holding cap and PLANT/BUILD
refusals, and what an idle unit on an empty tile held in seeds.

    python -m tools.analysis.l2_land_service --set L
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

from tools.analysis.l2_land_census import classify  # noqa: E402
from tools.analysis.l2_land_fast import (CORPUS, corpus_record, live_paths,  # noqa: E402
                                         live_record, replay)

OUT = ROOT / "rl" / "data" / "l2" / "land"
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
ANIMALS = {"GOOSE": ("EGG", 4, 4, 1, 50), "COW": ("MILK", 6, 8, 2, 160), "SHEEP": ("WOOL", 6, 6, 3, 200)}
PLANT_WINDOW = {"WHEAT": (2, 4), "CARROT": (2, 3), "MELON": (6, 12)}


def one_game(seed, tapes, side):
    from kaggle_environments.envs.kaggriculture import kaggriculture as E
    nights = {}
    orig = E._daily_refresh_animals
    state = {"farm_obj": None}

    def hook(farm, day):
        if farm is state["farm_obj"]:
            snap = {}
            for y in range(10):
                for x in range(10):
                    t = farm["tiles"][y][x]
                    if isinstance(t, dict) and (t.get("animal") or t.get("kind") == "PLANT"):
                        snap[(x, y)] = dict(t)
            nights[day] = snap
        return orig(farm, day)

    E._daily_refresh_animals = hook
    # plants are refreshed before animals in _end_of_day, so snapshot them first
    orig_p = E._daily_refresh_plants

    def hook_p(farm, current_day, tpd):
        if farm is state["farm_obj"]:
            snapp = {}
            for y in range(10):
                for x in range(10):
                    t = farm["tiles"][y][x]
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        snapp[(x, y)] = dict(t)
            nights[("p", current_day)] = snapp
        return orig_p(farm, current_day, tpd)

    E._daily_refresh_plants = hook_p
    idle = defaultdict(list)     # (day, x, y) -> [(t, unit, op, inventory)]
    seeds_seen = Counter()
    try:
        for t, g, acts in replay(seed, tapes):
            farm = g.obs.farms[side]
            state["farm_obj"] = farm
            if acts is None:
                break
            priv = g.private(side)
            rows = classify(E, farm, priv, acts[side], t // 24)
            for u, (op, applied, x, y) in enumerate(rows):
                base = op.split(":")[0]
                if base in MOVES:
                    continue
                if base == "PASS" or not applied:
                    inv = priv["inventories"][u] if u < len(priv["inventories"]) else {}
                    idle[(t // 24, x, y)].append((t, u, op, dict(inv)))
                    if farm["tiles"][y][x] is None:
                        seeds_seen[tuple(sorted((k, v) for k, v in priv["seeds"].items() if v))] += 1
    finally:
        E._daily_refresh_animals = orig
        E._daily_refresh_plants = orig_p
    res = Counter()
    for day, snap in nights.items():
        if isinstance(day, tuple):
            continue
        for (x, y), tile in snap.items():
            if not tile.get("animal"):
                continue
            product, cap, first, interval, base = ANIMALS[tile["animal"]]
            here = idle.get((day, x, y), [])
            res["animal_days"] += 1
            fed = tile.get("fed_today")
            if not fed:
                res["unfed"] += 1
                if any("WHEAT" in inv for _, _, _, inv in here):
                    res["unfed_fixable_holding_wheat"] += 1
            if fed and not tile.get("cared_today"):
                res["fed_not_cared"] += 1
                if here:
                    res["care_fixable"] += 1
                    res["care_fixable_value"] += base
            if tile.get("fertilizer_available"):
                res["fert_uncollected"] += 1
                if here:
                    res["fert_fixable"] += 1
            since = day + 1 - int(tile.get("placed_day", 99)) - first
            if since >= 0 and since % interval == 0:
                prod = 1 + (int(tile.get("pending_care_bonus", 0) or 0) if fed else 0)
                clipped = max(0, int(tile.get("yield_units", 0)) + prod - cap)
                if clipped:
                    res["clipped_units"] += clipped
                    res["clipped_value"] += clipped * base
                    if here:
                        res["clipped_fixable_units"] += clipped
    for key, snap in nights.items():
        if not isinstance(key, tuple):
            continue
        day = key[1]
        for (x, y), tile in snap.items():
            crop = tile.get("crop")
            here = idle.get((day, x, y), [])
            if not tile.get("watered_today"):
                res["plant_unwatered"] += 1
                if int(tile.get("consecutive_unwatered", 0)) + 1 >= 2:
                    res["plant_died"] += 1
                    if here:
                        res["plant_died_fixable"] += 1
                w = PLANT_WINDOW.get(crop)
                age = day - int(tile.get("planted_day", 0))
                if w and w[0] <= age <= w[1] and day < int(tile.get("max_lifespan_step", 10 ** 9)) // 24:
                    res["window_missed"] += 1
                    if here:
                        res["window_missed_fixable"] += 1
    return res, seeds_seen


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
    tot = []
    seeds = Counter()
    for seed, tp, side in jobs:
        r, s = one_game(seed, tp, side)
        tot.append(r)
        seeds.update(s)
    keys = sorted({k for r in tot for k in r})
    n = len(tot)
    lines = [f"[{a.set}] {n} games; per game mean (median)"]
    for k in keys:
        vals = [r[k] for r in tot]
        lines.append(f"  {k:32s} {statistics.mean(vals):9.1f} ({statistics.median(vals):.0f})")
    lines.append("  seeds held when a unit idled on an empty tile (top): "
                 + "; ".join(f"{dict(k)} x{v}" for k, v in seeds.most_common(5)))
    text = "\n".join(lines)
    print(text)
    (OUT / f"service_{a.set}.txt").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
