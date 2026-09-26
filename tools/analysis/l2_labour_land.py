"""Empty land on our farm at nightfall, from exact replays of our live games.

Counts, per game, unlocked tiles that are empty (None) at the end of each
day, by quadrant, and the runs of consecutive empty nights: a tile empty for
five or more nights in a row could carry a 4-day wheat cycle that never
collides with the tape's own plantings. Context for what a layer with spare
labour could grow; it does not say the labour exists where the land is.

    python -m tools.analysis.l2_labour_land --submission 56582917 --label L
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.l2_labour_replay import records, replay_record  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "labour"


def quad(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


class Land:
    def __init__(self, side):
        self.side = side
        self.nights = {}

    def end_of_day(self, state, env, day, apply):
        tiles = state[0].observation.farms[self.side]["tiles"]
        self.nights[day] = [[("L" if t == "LOCKED" else "." if t is None else
                              "W" if isinstance(t, dict) and t.get("kind") == "WEED"
                              else "X") for t in row] for row in tiles]
        return apply()


def one(record):
    side = int(record["our_side"])
    land = Land(side)
    replay_record(record, land)
    empty_q = Counter()
    runs5 = runs5_days = 0
    for y in range(10):
        for x in range(10):
            run = 0
            for day in range(29):
                c = land.nights[day][y][x]
                if c == ".":
                    empty_q[quad(x, y)] += 1
                    run += 1
                else:
                    if run >= 5:
                        runs5 += 1
                        runs5_days += run
                    run = 0
            if run >= 5:
                runs5 += 1
                runs5_days += run
    unlocked = Counter()
    for day in range(29):
        for y in range(10):
            for x in range(10):
                if land.nights[day][y][x] != "L":
                    unlocked[quad(x, y)] += 1
    return {"episode_id": record["episode_id"], "empty": dict(empty_q),
            "unlocked": dict(unlocked), "runs5": runs5, "runs5_days": runs5_days}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", type=int, default=56582917)
    ap.add_argument("--label", default="L")
    args = ap.parse_args()
    games = [one(r) for _, r in records(args.submission)]
    (OUT / f"land_{args.label}.json").write_text(json.dumps(games), encoding="utf-8")
    n = len(games)
    print(f"land {args.label}: {n} games (nights 0-28)")
    for q in ("NW", "NE", "SW", "SE"):
        e = statistics.mean(g["empty"].get(q, 0) for g in games)
        u = statistics.mean(g["unlocked"].get(q, 0) for g in games)
        print(f"  {q}: unlocked tile-nights {u:6.0f}, empty {e:6.0f} ({e / max(1, u):.0%})")
    print(f"  runs of >=5 empty nights per game: {statistics.mean(g['runs5'] for g in games):.1f} "
          f"covering {statistics.mean(g['runs5_days'] for g in games):.0f} tile-nights")


if __name__ == "__main__":
    main()
