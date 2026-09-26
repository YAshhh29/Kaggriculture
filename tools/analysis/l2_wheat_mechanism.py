"""How the 2600-2700 teams use wheat and fertilizer, and what of it fits L's schedule.

Reads the exact traces written by tools/analysis/l2_wheat_runs.py (each
team's real game, and Agent A in the team's seat against the same recorded
opponent) and prints:

1. timing of every wheat FERTILIZE: plant age, and whether the same unit
   waters that plant right after (the F->W pair), per game, team vs A;
2. families: lineage near-copies (>= 90% identical unit commands on days
   0-9) vs other programmes - wheat, fertilizer, crew, purchases, money;
3. the money edge of the team over A in the same seat, by ledger line;
4. wheat round trips: when they are placed relative to the town's 4-step
   draw and what they earn per unit;
5. the free turns on A's own schedule that a zero-hire, zero-purchase layer
   could use: age-1 waterings, idle turns on young wheat, collectors that
   water young wheat while carrying fertilizer, and how often an extra turn
   can be absorbed after the watering or freed before it.

    python -m tools.analysis.l2_wheat_mechanism
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_wheat_report import load, metrics, similarity  # noqa: E402
from tools.analysis.l2_wheat_runs import faithful_games  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "wheat"
SHED = {(4, 4), (5, 4), (4, 5), (5, 5)}
MOVES = ("NORTH", "SOUTH", "EAST", "WEST")


def med(v):
    return statistics.median(v) if v else 0.0


def mean(v):
    return statistics.mean(v) if v else 0.0


def carried_series(ev):
    fl = defaultdict(list)
    for t, idx, x, y, animal, ok in ev["collect"]:
        if ok:
            fl[(t // 24, idx)].append((t, +1))
    for t, idx, item, n in ev["pickup"]:
        if item == "FERTILIZER":
            fl[(t // 24, idx)].append((t, +n))
    for t, idx, lost in ev["shed_in"]:
        if lost.get("FERTILIZER"):
            fl[(t // 24, idx)].append((t, -lost["FERTILIZER"]))
    for e in ev["fert"]:
        if e[6]:
            fl[(e[0] // 24, e[1])].append((e[0], -1))
    return fl


def carried_at(fl, t, idx):
    return sum(d for tt, d in fl.get((t // 24, idx), []) if tt < t)


def lifetimes(ev):
    """(x, y) -> [t_plant, t_harvest, birth_day, [fert steps], (harvest age, units)]."""
    out = defaultdict(list)
    cur = {}
    evs = ([(e[0], 0, "P", e) for e in ev["plant"] if e[2] == "WHEAT"]
           + [(e[0], 2, "H", e) for e in ev["harvest"] if e[2] == "WHEAT"]
           + [(e[0], 1, "F", e) for e in ev["fert"] if e[4] == "WHEAT" and e[6]])
    for t, _, kind, e in sorted(evs, key=lambda r: (r[0], r[1])):
        if kind == "P":
            cur[(e[3], e[4])] = [t, None, t // 24, [], None]
        elif kind == "F":
            p = cur.get((e[2], e[3]))
            if p:
                p[3].append(t)
        else:
            p = cur.pop((e[3], e[4]), None)
            if p:
                p[1], p[4] = t, (e[5], e[6])
                out[(e[3], e[4])].append(p)
    return out


def fert_timing(d):
    ev = d["events"]
    water = defaultdict(list)
    for w in ev["water"]:
        if w[2] == "WHEAT":
            water[(w[3], w[4], w[0] // 24)].append((w[0], w[1]))
    out = Counter()
    for e in ev["fert"]:
        t, idx, x, y, target, age, ok = e[:7]
        if not ok or target != "WHEAT":
            continue
        ws = water.get((x, y, t // 24), [])
        if any(wt < t for wt, wu in ws):
            kind = "after that day's watering"
        elif any(t < wt <= t + 2 and wu == idx for wt, wu in ws):
            kind = "F->W same unit"
        elif any(t < wt for wt, wu in ws):
            kind = "watered later by another unit"
        else:
            kind = "no watering that day"
        out[f"age {age}: {kind}"] += 1
    return out


def round_trips(d):
    buys, sells = defaultdict(lambda: [0, 0.0]), defaultdict(lambda: [0, 0.0])
    for t, s, op, item, n, tot in d["market"]:
        if item != "WHEAT" or int(s) != d["seat"]:
            continue
        cell = buys if op == "BUY_PRODUCT" else sells if op == "SELL" else None
        if cell is not None:
            cell[int(t)][0] += n
            cell[int(t)][1] += tot
    units, pnl, mod = 0, 0.0, Counter()
    for t in sorted(buys):
        if t < 24:
            continue
        b_n, b_c = buys[t]
        for dt in (0, 1):
            s_n, s_r = sells.get(t + dt, [0, 0.0])
            m = min(b_n, s_n)
            if m <= 0 or b_n <= 0:
                continue
            pnl += m * (s_r / s_n - b_c / b_n)
            units += m
            mod[t % 4] += m
            sells[t + dt] = [s_n - m, s_r - m * s_r / s_n]
            b_c -= m * b_c / b_n
            b_n -= m
    return units, pnl, mod


def free_turns(d):
    """Free or cheap turns on A's own schedule, days 10-28, one slot per plant."""
    ev, ops = d["events"], d["ops"]
    fl, lt = carried_series(ev), lifetimes(ev)
    wat = {(w[0], w[1]): w for w in ev["water"]}
    coll = {(e[0], e[1]) for e in ev["collect"] if e[5]}
    succ = set(coll)
    for key in ("water", "harvest", "plant", "care", "dig"):
        succ |= {(e[0], e[1]) for e in ev[key]}
    succ |= {(e[0], e[1]) for e in ev["fert"] if e[6]}
    succ |= {(e[0], e[1]) for e in ev["feed"] if e[5]}
    succ |= {(e[0], e[1]) for e in ev["pickup"]} | {(e[0], e[1]) for e in ev["shed_in"]}
    c = Counter()
    used = set()
    for k in range(240, 700):
        day = k // 24
        for u, op, x, y in ops[k]:
            w = wat.get((k, u))
            car = carried_at(fl, k, u)
            slot = None
            if op == "WATER" and w and w[2] == "WHEAT" and w[5] == 1 and not w[8]:
                slot = "age-1 watering"
            elif op == "PASS":
                for p in lt.get((x, y), []):
                    if p[0] < k < p[1] and not any(ft < k for ft in p[3]) and day - p[2] <= 3:
                        slot = "idle on young wheat"
                        break
            if slot:
                pl = next((p for p in lt.get((x, y), []) if p[0] < k <= p[1]), None)
                if pl and (x, y, pl[0]) not in used:
                    used.add((x, y, pl[0]))
                    c[f"{slot}"] += 1
                    c[f"{slot}, fertilizer in hand"] += car > 0
            if op == "WATER" and w and w[2] == "WHEAT" and not w[8] and w[5] == 2 and car > 0:
                c["collector waters unfertilized age-2 wheat"] += 1
                after = before = None
                for kk in range(k + 1, (day + 1) * 24):
                    o = next((o for o in ops[kk] if o[0] == u), None)
                    if o is None:
                        break
                    opn = o[1].split(":")[0]
                    if opn == "PASS" or (opn not in MOVES and (kk, u) not in succ):
                        after = kk
                        break
                for kk in range(k - 1, day * 24 - 1, -1):
                    o = next((o for o in ops[kk] if o[0] == u), None)
                    if o is None:
                        break
                    opn = o[1].split(":")[0]
                    if opn == "PASS" or (opn not in MOVES and (kk, u) not in succ):
                        before = "idle or no-op"
                        break
                    if opn == "COLLECT_FERTILIZER" and (kk, u) in coll and car >= 2:
                        before = "COLLECT while carrying >= 2"
                        break
                c["  ... an idle turn later the same day (insert after)"] += after is not None
                if before:
                    c[f"  ... a skippable command earlier: {before}"] += 1
    return c


def main() -> None:
    games = faithful_games()
    rows = []
    for g in games:
        ep = int(g["episode"])
        team, ours = load(ep, "team"), load(ep, "A")
        if team is None or ours is None:
            continue
        rows.append((g, team, ours))
    n = len(rows)
    summary: dict = {"games": n}
    print(f"{n} faithful 2600-2700 games; team = the team's real game, A = Agent A in its seat\n")

    print("1. wheat FERTILIZE timing, per game (team / A)")
    ft, fa = Counter(), Counter()
    for g, team, ours in rows:
        ft.update(fert_timing(team))
        fa.update(fert_timing(ours))
    for k in sorted(set(ft) | set(fa)):
        print(f"   {k:44s} {ft[k] / n:5.1f} / {fa[k] / n:5.1f}")
    summary["fert_timing_per_game"] = {k: [ft[k] / n, fa[k] / n] for k in sorted(set(ft) | set(fa))}

    print("\n2. families (team minus A in the same seat; mean / median)")
    fam = {}
    for g, team, ours in rows:
        s = similarity(team, ours)["same_units"]
        mt, mo = metrics(team), metrics(ours)
        key = "lineage near-copies" if s >= 0.9 else "other programmes"
        fam.setdefault(key, []).append((mt, mo))
    summary["families"] = {}
    for key, lst in fam.items():
        cols = {
            "wheat units": [a["wheat_units"] - b["wheat_units"] for a, b in lst],
            "wheat fertilizations": [a["fert_applied"].get("WHEAT", 0) - b["fert_applied"].get("WHEAT", 0) for a, b in lst],
            "fertilizer collected": [a["collected"] - b["collected"] for a, b in lst],
            "hires": [a["hires"] - b["hires"] for a, b in lst],
            "fertilizer bought": [a["market"].get("BUY_PRODUCT|FERTILIZER", [0, 0])[0]
                                  - b["market"].get("BUY_PRODUCT|FERTILIZER", [0, 0])[0] for a, b in lst],
            "final money": [a["reward"] - b["reward"] for a, b in lst],
        }
        print(f"   {key} ({len(lst)} games): " + "; ".join(
            f"{k} {mean(v):+.1f}/{med(v):+.1f}" for k, v in cols.items()))
        summary["families"][key] = {k: [mean(v), med(v)] for k, v in cols.items()} | {"games": len(lst)}

    print("\n3. money edge of the team over A in the same seat, by ledger line (mean / median)")
    per = defaultdict(list)
    pairs = [(metrics(team), metrics(ours)) for g, team, ours in rows]
    keys = sorted({k for mt, mo in pairs for k in set(mt["ledger"]) | set(mo["ledger"])})
    for mt, mo in pairs:
        for k in keys:
            per[k].append(mt["ledger"].get(k, 0) - mo["ledger"].get(k, 0))
        per["final money"].append(mt["reward"] - mo["reward"])
    for k in sorted(per, key=lambda k: -abs(mean(per[k]))):
        print(f"   {k:22s} {mean(per[k]):+9,.0f} {med(per[k]):+9,.0f}")
    summary["ledger_edge"] = {k: [mean(v), med(v)] for k, v in per.items()}

    print("\n4. wheat round trips (bought and sold within one step, after day 0)")
    for label, idx in (("team", 1), ("A", 2)):
        units, pnl, mods = [], [], Counter()
        for row in rows:
            u, p, m = round_trips(row[idx])
            units.append(u)
            pnl.append(p)
            mods.update(m)
        heavy = [(u, p) for u, p in zip(units, pnl) if u > 100]
        per100 = 100 * sum(p for u, p in heavy) / max(1, sum(u for u, p in heavy))
        print(f"   {label}: units/game mean {mean(units):.0f} median {med(units):.0f}; P&L/game mean "
              f"{mean(pnl):+.0f}; {len(heavy)} games > 100 units earning ${per100:.1f} per 100 units; "
              f"buy step % 4: {dict(sorted(mods.items()))}")
        summary[f"round_trips_{label}"] = {"units_mean": mean(units), "pnl_mean": mean(pnl),
                                           "heavy_games": len(heavy), "per100": per100,
                                           "buy_step_mod4": dict(mods)}

    print("\n5. free or cheap turns on A's own schedule (days 10-28), per game")
    ft5 = Counter()
    for g, team, ours in rows:
        ft5.update(free_turns(ours))
    for k, v in ft5.items():
        print(f"   {k:62s} {v / n:5.1f}")
    summary["free_turns_per_game"] = {k: v / n for k, v in ft5.items()}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mechanism_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"\nsaved {(OUT / 'mechanism_summary.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
