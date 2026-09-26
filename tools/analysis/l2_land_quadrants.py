"""When each quadrant is bought, how fast it is put to use, and what idles.

From the census timelines (tools.analysis.l2_land_census): per game and
quadrant, the unlock step, the tile-days between unlock and each tile's first
use, the tile-days idle afterwards (split mid-game / after the last harvest),
and how the idle ground is distributed across games (is it a few games with a
whole quadrant idle, or a little everywhere?).

    python -m tools.analysis.l2_land_quadrants --sets L A top30
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_land_census import load_set  # noqa: E402
from tools.analysis.l2_land_report import QUAD, side_data  # noqa: E402


def med(xs):
    xs = list(xs)
    return statistics.median(xs) if xs else 0


def quad_stats(game, which="focus"):
    tl, _ = side_data(game, which)
    n = len(tl[0])
    out = {}
    for q in ("NE", "SW", "SE"):
        idx = [i for i in range(100) if QUAD[i] == q]
        unlock = next((t for t in range(n) if tl[idx[0]][t] != "#"), None)
        if unlock is None:
            out[q] = None
            continue
        lag = []
        idle_mid = 0
        idle_end = 0
        for i in idx:
            s = tl[i]
            first = next((t for t in range(unlock, n) if s[t] not in ".x#"), n)
            lag.append((first - unlock) / 24)
            last_use = max((t for t in range(n) if s[t] not in ".x#"), default=unlock)
            for t in range(first, n):
                if s[t] in ".x":
                    if t < last_use:
                        idle_mid += 1
                    else:
                        idle_end += 1
        out[q] = {"unlock_day": unlock / 24, "lag_days_sum": sum(lag),
                  "lag_median": med(lag), "never_used": sum(1 for x in lag if x >= (n - unlock) / 24),
                  "idle_mid_days": idle_mid / 24, "idle_end_days": idle_end / 24}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", nargs="+", default=["L", "top30"])
    a = ap.parse_args()
    for name in a.sets:
        games = load_set(name)
        rows = [quad_stats(g) for g in games]
        print(f"\n[{name}] {len(games)} games")
        for q in ("NE", "SW", "SE"):
            got = [r[q] for r in rows if r[q]]
            if not got:
                print(f"  {q}: never bought")
                continue
            print(f"  {q}: bought in {len(got)}/{len(rows)} games, unlock day median "
                  f"{med(x['unlock_day'] for x in got):.2f} (days "
                  f"{Counter(int(x['unlock_day']) for x in got).most_common(6)}); "
                  f"tile-days before first use: median {med(x['lag_days_sum'] for x in got):.1f}, "
                  f"mean {statistics.mean(x['lag_days_sum'] for x in got):.1f}; "
                  f"tiles never used: mean {statistics.mean(x['never_used'] for x in got):.1f}; "
                  f"idle between uses {statistics.mean(x['idle_mid_days'] for x in got):.1f}, "
                  f"after last use {statistics.mean(x['idle_end_days'] for x in got):.1f} tile-days")
            if q == "SE":
                worst = sorted(((x["lag_days_sum"], g["meta"]["episode_id"], x["unlock_day"], x["never_used"])
                                for x, g in zip([r[q] for r in rows], games) if x), reverse=True)[:8]
                print("    most SE ground idle before use (tile-days, episode, unlock day, never used): "
                      + "; ".join(f"{a_:.0f} ep{b} d{c:.1f} {d}" for a_, b, c, d in worst))


if __name__ == "__main__":
    main()
