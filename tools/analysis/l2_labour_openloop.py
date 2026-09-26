"""First-order value of the in-place recycler, exactly, on our real games.

Replays each live game (both tapes on the seed) with our recorded commands
passed through rl.l2_labour.lb_recycle before the engine applies them. The
parent cannot react (it is a tape), so this isolates what the substitutions
themselves are worth: our money against the exact live money, plus the goods
the substitutions left unsold at the end (a tape cannot sell what it did not
expect to have), valued at the final price. The opponent's tape is also
fixed, so a changed market can make it drift; its money change is reported.

    python -m tools.analysis.l2_labour_openloop --submission 56582917 --label L
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
from rl.l2_labour import lb_recycle  # noqa: E402
from tools.analysis.l2_labour_replay import records, replay_record  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "labour"


class Recycle:
    def __init__(self, side):
        self.side = side
        self.tel = {}

    def before_step(self, state, step):
        o0 = state[0].observation
        obs = {"step": step, "player": self.side, "day": step // 24,
               "hour": step % 24, "farms": o0.farms,
               "private": state[self.side].observation.private,
               "market": o0.market, "town": o0.town}
        a = state[self.side].action
        if isinstance(a, dict):
            state[self.side].action = lb_recycle(obs, a, self.tel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", type=int, default=56582917)
    ap.add_argument("--label", default="L")
    args = ap.parse_args()
    rows = []
    tel = Counter()
    for p, r in records(args.submission):
        side = int(r["our_side"])
        obs = Recycle(side)
        got, state, _ = replay_record(r, obs)
        final_prices = state[0].observation.market["prices"]
        held = Counter(state[side].observation.private["shed"])
        for inv in state[side].observation.private["inventories"]:
            held.update(inv)
        leftover = sum(n * final_prices.get(k, 0) for k, n in held.items()
                       if k in final_prices and n > 0)
        tel.update(obs.tel)
        rows.append({"episode_id": r["episode_id"], "live": r["rewards"],
                     "got": got, "d_us": got["us"] - r["rewards"]["us"],
                     "d_them": got["them"] - r["rewards"]["them"],
                     "leftover": leftover, "tel": obs.tel,
                     "won_live": r["rewards"]["us"] > r["rewards"]["them"],
                     "won": got["us"] > got["them"]})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"openloop_{args.label}.json").write_text(json.dumps(rows), encoding="utf-8")
    n = len(rows)
    d = [x["d_us"] for x in rows]
    dm = [x["d_us"] - x["d_them"] for x in rows]
    print(f"open-loop recycler on {args.label}: {n} games")
    print(f"  our money change: mean {statistics.mean(d):+.0f}, median {statistics.median(d):+.0f}, "
          f"higher {sum(v > 0 for v in d)}, lower {sum(v < 0 for v in d)}, same {sum(v == 0 for v in d)}")
    print(f"  margin change: mean {statistics.mean(dm):+.0f}, median {statistics.median(dm):+.0f}; "
          f"opponent money change mean {statistics.mean(x['d_them'] for x in rows):+.0f}")
    print(f"  unsold goods at the end (final price): mean {statistics.mean(x['leftover'] for x in rows):.0f}")
    print(f"  wins live {sum(x['won_live'] for x in rows)} -> {sum(x['won'] for x in rows)}")
    print("  substitutions per game: " + ", ".join(f"{k} {v / n:.1f}" for k, v in sorted(tel.items())))


if __name__ == "__main__":
    main()
