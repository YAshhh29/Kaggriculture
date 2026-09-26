"""Idle stretches of units already paid for, from the census.

Hands are dismissed every night and the farmer respawns at the shed, so a
unit whose remaining actions today are all idle (PASS or refused by the
engine) can be borrowed for the rest of the day without desynchronising any
later day of the route. Mid-day idle stretches can be borrowed too if the
unit is back on its square before the route needs it.

For each set: per day, the unit-turns in idle tails (to hour 23) and in
mid-day stretches of at least --min turns, and how far the borrowed units
stand from the idle ground (empty/weed tiles and, separately, SE rows 7-9).

    python -m tools.analysis.l2_land_tails --sets L top30
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_land_census import load_set  # noqa: E402
from tools.analysis.l2_land_report import MOVES, side_data  # noqa: E402


def med(xs):
    xs = list(xs)
    return statistics.median(xs) if xs else 0


def unit_days(tl, units):
    """{(day, unit): [(t, idle, x, y)]}"""
    out = defaultdict(list)
    for t, row in enumerate(units):
        for u, (op, applied, x, y) in enumerate(row):
            base = op.split(":")[0]
            idle = base == "PASS" or (base not in MOVES and not applied)
            out[(t // 24, u)].append((t, idle, x, y))
    return out


def tails(games, which="focus", min_gap=6):
    per_day_tail = defaultdict(list)
    per_day_gap = defaultdict(list)
    tail_units = defaultdict(list)
    for g in games:
        tl, units = side_data(g, which)
        ud = unit_days(tl, units)
        day_tail = defaultdict(int)
        day_gap = defaultdict(int)
        day_units = defaultdict(int)
        for (d, u), seq in ud.items():
            seq.sort()
            # tail: trailing idle turns, only if the unit exists to hour 23
            k = len(seq)
            while k > 0 and seq[k - 1][1]:
                k -= 1
            tail = len(seq) - k
            if seq and seq[-1][0] % 24 == 23 and tail > 0:
                day_tail[d] += tail
                if tail >= 8:
                    day_units[d] += 1
            # mid-day stretches
            run = 0
            for j in range(k):
                if seq[j][1]:
                    run += 1
                else:
                    if run >= min_gap:
                        day_gap[d] += run
                    run = 0
        for d in range(30):
            per_day_tail[d].append(day_tail[d])
            per_day_gap[d].append(day_gap[d])
            tail_units[d].append(day_units[d])
    return per_day_tail, per_day_gap, tail_units


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", nargs="+", default=["L", "top30"])
    ap.add_argument("--min", type=int, default=6)
    a = ap.parse_args()
    for name in a.sets:
        games = load_set(name)
        pt, pg, tu = tails(games, "focus", a.min)
        print(f"\n[{name}] idle unit-turns per day (median over {len(games)} games): "
              f"tail to hour 23 | mid-day stretches >= {a.min} | units with tail >= 8")
        print("  day: " + " ".join(f"{d:>4d}" for d in range(30)))
        print("  tail " + " ".join(f"{med(pt[d]):4.0f}" for d in range(30)))
        print("  gaps " + " ".join(f"{med(pg[d]):4.0f}" for d in range(30)))
        print("  u>=8 " + " ".join(f"{med(tu[d]):4.0f}" for d in range(30)))
        print(f"  per game: tails {sum(statistics.mean(pt[d]) for d in range(30)):.0f}, "
              f"stretches {sum(statistics.mean(pg[d]) for d in range(30)):.0f} unit-turns")


if __name__ == "__main__":
    main()
