"""What the census says about land: idle ground, idle hands, and infill room.

Reads rl/data/l2/land/census/<set>_ep*.json (tools.analysis.l2_land_census)
and prints, for each set:

1. the farm at dusk on chosen days: owned, empty, weed, planted by crop,
   animals, empty structures (medians), and per quadrant;
2. idle ground: owned tile-days empty or weed at dusk, by quadrant;
3. turnover: after a one-time crop leaves a tile, how long until the tile
   is used again (and how often never);
4. labour: every unit-turn judged by the engine -- moves, work, deliberate
   PASS, silent no-ops (by verb), and what the idle unit stood on;
5. infill room with perfect foresight: for each stretch where a tile sits
   empty or weedy, the best carrot / wheat crop that the idle turns (PASS or
   refused) of units already standing on that tile could have planted,
   watered and harvested before the tile's next real use. Yields follow the
   engine exactly (planting day counts as unwatered; +1 per watered day in
   the window; decay one unit per two steps after max lifespan).

    python -m tools.analysis.l2_land_report --sets L A top30
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_land_census import load_set, unpack  # noqa: E402

DAYS = (2, 5, 8, 11, 14, 17, 20, 23, 26, 29)
PLANTS = "wctsm"
ANIMALS = "GMS"
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
QUAD = {}
for _y in range(10):
    for _x in range(10):
        QUAD[_y * 10 + _x] = ("N" if _y < 5 else "S") + ("W" if _x < 5 else "E")
SHED_ADJ = {(4, 4), (5, 4), (4, 5), (5, 5)}
# crop: (max_yield_day, cap unfertilized, seed, base price)
CROPS = {"CARROT": (3, 3, 20, 35), "WHEAT": (4, 4, 10, 25)}


def med(xs):
    xs = list(xs)
    return statistics.median(xs) if xs else 0


def side_data(game: dict, which: str = "focus"):
    s = str(game["meta"][which])
    d = game["sides"][s]
    return unpack(d["timeline"]), unpack(d["units"])


# ---------------------------------------------------------------- 1. census
def census(games, which="focus"):
    rows = defaultdict(lambda: defaultdict(list))
    quad_rows = defaultdict(lambda: defaultdict(list))
    for g in games:
        tl, _ = side_data(g, which)
        for d in range(30):
            t = min(24 * d + 23, len(tl[0]) - 1)
            c = Counter(tl[i][t] for i in range(100))
            owned = 100 - c["#"]
            rows[d]["owned"].append(owned)
            rows[d]["empty"].append(c["."])
            rows[d]["weed"].append(c["x"])
            rows[d]["plants"].append(sum(c[k] for k in PLANTS))
            for k in PLANTS:
                rows[d][k].append(c[k])
            rows[d]["animals"].append(sum(c[k] for k in ANIMALS))
            rows[d]["structs"].append(c["O"] + c["P"])
            qc = defaultdict(Counter)
            for i in range(100):
                qc[QUAD[i]][tl[i][t]] += 1
            for q in ("NW", "NE", "SW", "SE"):
                owned_q = 25 - qc[q]["#"]
                quad_rows[d][q + "_owned"].append(owned_q)
                quad_rows[d][q + "_idle"].append(qc[q]["."] + qc[q]["x"])
                quad_rows[d][q + "_used"].append(owned_q - qc[q]["."] - qc[q]["x"])
    return rows, quad_rows


def print_census(name, games, which="focus"):
    rows, quad_rows = census(games, which)
    print(f"\n[{name}] farm at dusk, medians over {len(games)} games")
    print("  day owned empty weed plants  w  c  t  s  m animals structs | "
          "idle NW NE SW SE | used NW NE SW SE")
    for d in DAYS:
        r, q = rows[d], quad_rows[d]
        print(f"  {d:3d} {med(r['owned']):5.0f} {med(r['empty']):5.0f} {med(r['weed']):4.0f} "
              f"{med(r['plants']):6.0f} {med(r['w']):2.0f} {med(r['c']):2.0f} {med(r['t']):2.0f} "
              f"{med(r['s']):2.0f} {med(r['m']):2.0f} {med(r['animals']):7.0f} {med(r['structs']):7.0f} | "
              f"     {med(q['NW_idle']):2.0f} {med(q['NE_idle']):2.0f} {med(q['SW_idle']):2.0f} "
              f"{med(q['SE_idle']):2.0f} |      {med(q['NW_used']):2.0f} {med(q['NE_used']):2.0f} "
              f"{med(q['SW_used']):2.0f} {med(q['SE_used']):2.0f}")


# ---------------------------------------------------------------- 2. idle ground
def idle_ground(games, which="focus"):
    per_game = []
    for g in games:
        tl, _ = side_data(g, which)
        tot = Counter()
        for d in range(30):
            t = min(24 * d + 23, len(tl[0]) - 1)
            for i in range(100):
                c = tl[i][t]
                if c == "#":
                    continue
                tot["owned"] += 1
                if c in ".x":
                    tot["idle"] += 1
                    tot["idle_" + QUAD[i]] += 1
                    tot["empty" if c == "." else "weed"] += 1
                elif c in PLANTS:
                    tot["plant"] += 1
                elif c in ANIMALS:
                    tot["animal"] += 1
                else:
                    tot["struct"] += 1
        per_game.append(tot)
    return per_game


def print_idle(name, games, which="focus"):
    pg = idle_ground(games, which)
    keys = ("owned", "plant", "animal", "struct", "idle", "empty", "weed",
            "idle_NW", "idle_NE", "idle_SW", "idle_SE")
    print(f"\n[{name}] tile-days at dusk per game (median;mean)")
    print("  " + "  ".join(f"{k} {med(t[k] for t in pg):.0f};{statistics.mean(t[k] for t in pg):.0f}"
                           for k in keys))


# ---------------------------------------------------------------- 3. turnover
def turnover(games, which="focus"):
    gaps = []   # (prev, next, length_steps, start_step)
    for g in games:
        tl, _ = side_data(g, which)
        for i in range(100):
            s = tl[i]
            t = 1
            while t < len(s):
                if s[t] in ".x" and s[t - 1] in PLANTS:
                    prev = s[t - 1]
                    u = t
                    while u < len(s) and s[u] in ".x":
                        u += 1
                    nxt = s[u] if u < len(s) else "END"
                    gaps.append((prev, nxt, u - t, t))
                    t = u
                else:
                    t += 1
    return gaps


def print_turnover(name, games, which="focus"):
    gaps = turnover(games, which)
    n = max(1, len(games))
    reused = [g for g in gaps if g[1] != "END"]
    never = [g for g in gaps if g[1] == "END"]
    print(f"\n[{name}] after a crop leaves a tile: {len(gaps) / n:.1f} events/game, "
          f"reused {len(reused) / n:.1f}, never reused {len(never) / n:.1f}")
    buckets = Counter()
    lost = Counter()
    for prev, nxt, length, start in reused:
        b = ("<6h" if length < 6 else "<1d" if length < 24 else "1-2d" if length < 48
             else "2-3d" if length < 72 else "3-5d" if length < 120 else "5d+")
        buckets[b] += 1
        lost[b] += length / 24
    print("  gap before reuse: " + ", ".join(
        f"{b} {buckets[b] / n:.1f}/game ({lost[b] / n:.1f} tile-days)"
        for b in ("<6h", "<1d", "1-2d", "2-3d", "3-5d", "5d+")))
    never_days = sum(length for _, _, length, _ in never) / 24 / n
    print(f"  never reused: {never_days:.1f} tile-days/game; by start day: " + ", ".join(
        f"d{lo}-{lo + 4} {sum(1 for g in never if lo * 24 <= g[3] < (lo + 5) * 24) / n:.1f}"
        for lo in range(0, 30, 5)))
    nxt = Counter((p, q) for p, q, _, _ in reused)
    print("  crop -> next use (per game): " + ", ".join(
        f"{p}->{q} {c / n:.1f}" for (p, q), c in nxt.most_common(10)))


# ---------------------------------------------------------------- 4. labour
def labour(games, which="focus"):
    tot = Counter()
    noop_ops = Counter()
    idle_on = Counter()
    per_day_idle = defaultdict(list)
    for g in games:
        tl, units = side_data(g, which)
        day_idle = Counter()
        for t, row in enumerate(units):
            for op, applied, x, y in row:
                tot["unit_turns"] += 1
                base = op.split(":")[0]
                if base in MOVES:
                    tot["move" if applied else "move_fail"] += 1
                    continue
                if base == "PASS":
                    tot["pass"] += 1
                elif applied:
                    tot["work"] += 1
                    continue
                else:
                    tot["noop"] += 1
                    noop_ops[base] += 1
                day_idle[t // 24] += 1
                c = tl[y * 10 + x][t]
                key = ("shed-side" if (x, y) in SHED_ADJ and c in ".#" else
                       "empty" if c == "." else "weed" if c == "x" else "locked" if c == "#" else
                       "plant" if c in PLANTS else "animal" if c in ANIMALS else "structure")
                idle_on[key] += 1
        for d in range(30):
            per_day_idle[d].append(day_idle[d])
    return tot, noop_ops, idle_on, per_day_idle


def print_labour(name, games, which="focus"):
    tot, noop_ops, idle_on, per_day = labour(games, which)
    n = max(1, len(games))
    ut = max(1, tot["unit_turns"])
    print(f"\n[{name}] labour per game: {tot['unit_turns'] / n:.0f} unit-turns; "
          + ", ".join(f"{k} {tot[k] / n:.0f} ({tot[k] / ut:.1%})"
                      for k in ("move", "work", "pass", "noop", "move_fail")))
    print("  no-ops by verb/game: " + ", ".join(f"{k} {v / n:.1f}" for k, v in noop_ops.most_common(10)))
    print("  idle (pass+noop) standing on/game: " + ", ".join(
        f"{k} {v / n:.1f}" for k, v in idle_on.most_common()))
    print("  idle unit-turns per day (median): " + " ".join(
        f"{d}:{med(per_day[d]):.0f}" for d in range(0, 30, 2)))


# ---------------------------------------------------------------- 5. infill
def _crop_best(crop, plant_t, run_end, idle_by_day):
    """Best (units, harvest_step, n_actions) for a crop planted at plant_t.

    Same-day watering must come after the plant; a same-day harvest must
    come after that day's watering to count it.
    """
    myd, cap, _, _ = CROPS[crop]
    lo = (myd + 1) // 2
    d0 = plant_t // 24
    mls = (d0 + myd + 1) * 24
    first = [t for t in idle_by_day.get(d0, []) if t > plant_t]
    if not first:
        return 0, None, 0
    best = (0, None, 0)
    states = {(0, 1): 2}   # watered on d0 (age 0: no bonus); plant + water
    for d in range(d0 + 1, d0 + myd + 3):
        if d * 24 >= run_end:
            break
        turns = [t for t in idle_by_day.get(d, []) if t < run_end]
        age = d - d0
        new = {}
        for (streak, y), acts in states.items():
            if turns and age >= 2:
                h = turns[0]
                dec = 0 if h <= mls else (h - mls + 1) // 2
                if y - dec > best[0]:
                    best = (y - dec, h, acts + 1)
            if turns:
                y2 = min(cap, y + 1) if lo <= age <= myd else y
                if age >= 2 and len(turns) >= 2:
                    h = turns[1]
                    dec = 0 if h <= mls else (h - mls + 1) // 2
                    if y2 - dec > best[0]:
                        best = (y2 - dec, h, acts + 2)
                key = (0, y2)
                new[key] = min(new.get(key, 99), acts + 1)
            if streak + 1 < 2:
                key = (streak + 1, y)
                new[key] = min(new.get(key, 99), acts)
        states = new
        if not states:
            break
    return best


def idle_turns_by_tile(tl, units):
    idle = defaultdict(list)
    for t, row in enumerate(units):
        for op, applied, x, y in row:
            base = op.split(":")[0]
            if base in MOVES:
                continue
            c = tl[y * 10 + x][t]
            if c == "#":
                continue
            if base == "PASS" or not applied or (base == "DIG" and c == "x"):
                idle[y * 10 + x].append(t)
    return idle


def infill(games, which="focus", min_value=0.0):
    """Perfect-foresight infill opportunities per game."""
    out = []
    for g in games:
        tl, units = side_data(g, which)
        idle = idle_turns_by_tile(tl, units)
        res = {"carrot_units": 0, "carrot_value": 0.0, "wheat_units": 0, "wheat_value": 0.0,
               "carrot_crops": 0, "wheat_crops": 0, "actions": 0, "tiles": set(),
               "by_quad": Counter(), "by_day": Counter()}
        for i in range(100):
            s = tl[i]
            t = 0
            while t < len(s):
                if s[t] not in ".x":
                    t += 1
                    continue
                u = t
                while u < len(s) and s[u] in ".x":
                    u += 1
                run_end = u
                turns = sorted(x for x in idle[i] if t <= x < run_end)
                by_day = defaultdict(list)
                for x in turns:
                    by_day[x // 24].append(x)
                k = 0
                while k < len(turns):
                    p = turns[k]
                    if s[p] == "x" or p // 24 >= 28:
                        k += 1
                        continue
                    options = []
                    for crop in CROPS:
                        units_, h, acts = _crop_best(crop, p, run_end, by_day)
                        _, _, seed, price = CROPS[crop]
                        if h is not None and units_ > 0:
                            options.append((units_ * price - seed, crop, units_, h, acts))
                    if not options:
                        k += 1
                        continue
                    val, crop, units_, h, acts = max(options)
                    if val <= min_value:
                        k += 1
                        continue
                    key = crop.lower()
                    res[key + "_units"] += units_
                    res[key + "_value"] += val
                    res[key + "_crops"] += 1
                    res["actions"] += acts
                    res["tiles"].add(i)
                    res["by_quad"][QUAD[i]] += val
                    res["by_day"][p // 24] += val
                    k = next((j for j, x in enumerate(turns) if x > h), len(turns))
                t = u
        res["tiles"] = len(res["tiles"])
        res["episode"] = g["meta"]["episode_id"]
        out.append(res)
    return out


def print_infill(name, games, which="focus"):
    res = infill(games, which)
    n = max(1, len(res))
    val = [r["carrot_value"] + r["wheat_value"] for r in res]
    print(f"\n[{name}] infill with perfect foresight (base prices, seed paid): "
          f"median {med(val):,.0f}/game, mean {statistics.mean(val) if val else 0:,.0f}")
    print(f"  carrot crops {sum(r['carrot_crops'] for r in res) / n:.1f} "
          f"({sum(r['carrot_units'] for r in res) / n:.1f} units), wheat crops "
          f"{sum(r['wheat_crops'] for r in res) / n:.1f} ({sum(r['wheat_units'] for r in res) / n:.1f} units), "
          f"converted turns {sum(r['actions'] for r in res) / n:.1f}, tiles {sum(r['tiles'] for r in res) / n:.1f}")
    q = Counter()
    dd = Counter()
    for r in res:
        q.update(r["by_quad"])
        dd.update(r["by_day"])
    print("  value by quadrant/game: " + ", ".join(f"{k} {v / n:,.0f}" for k, v in q.most_common()))
    print("  value by planting day/game: " + " ".join(f"{d}:{dd[d] / n:,.0f}" for d in range(30) if dd[d]))
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sets", nargs="+", default=["L"])
    ap.add_argument("--other", action="store_true", help="also report the opponents' side")
    ap.add_argument("--only", default="", help="comma list: census,idle,turnover,labour,infill")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else {"census", "idle", "turnover", "labour", "infill"}
    for name in a.sets:
        games = load_set(name)
        views = [("focus", name)]
        if a.other:
            views.append(("other", name + " opponents"))
        for which, label in views:
            if "census" in only:
                print_census(label, games, which)
            if "idle" in only:
                print_idle(label, games, which)
            if "turnover" in only:
                print_turnover(label, games, which)
            if "labour" in only:
                print_labour(label, games, which)
            if "infill" in only:
                print_infill(label, games, which)


if __name__ == "__main__":
    main()
