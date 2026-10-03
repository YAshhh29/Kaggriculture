"""The same yardstick trace_top_hire.py applies to the field, applied to us.

trace_top_hire.py found that even rank 1-5 teams have hands that take 5+
turns to do anything productive after spawning (32.6% of 334 hires across
25 tapes). That number is only useful paired with our own, measured the
same way, so decisions about COLD_START_RADIUS are made against the
field's actual bar rather than an assumption that 0% is achievable or
that any nonzero number is a problem.

    python -m tools.analysis.measure_hire_delay candidates.j_variant:agent --games 10
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.eval.measure_panel import resolve  # noqa: E402

MOVE = {"NORTH", "SOUTH", "EAST", "WEST"}


def study(spec: str, seed: int, seat: int) -> list[int]:
    from kaggle_environments import make

    mine = resolve(spec)
    players = [mine, "random"] if seat == 0 else ["random", mine]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run(players)

    out: list[int] = []
    prev_count = 0
    born_step: dict[int, int] = {}
    settled: set[int] = set()
    for index in range(len(env.steps) - 1):
        obs = env.steps[index][seat]["observation"]
        farm = (obs.get("farms") or [None, None])[seat]
        if not isinstance(farm, dict):
            continue
        hands = [tuple(farm.get("farmer") or (0, 0))]
        hands += [tuple(h) for h in (farm.get("hands") or [])]
        if len(hands) > prev_count:
            for idx in range(prev_count, len(hands)):
                born_step[idx] = index
        prev_count = len(hands)
        action = env.steps[index][seat].get("action") or {}
        acts = [action.get("farmer")] + list(action.get("hands") or [])
        for idx, act in enumerate(acts):
            if idx in settled or idx not in born_step:
                continue
            if not isinstance(act, list) or not act:
                continue
            op = act[0]
            if op in MOVE or op == "PASS":
                continue
            out.append(index - born_step[idx])
            settled.add(idx)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec")
    ap.add_argument("--games", type=int, default=10)
    args = ap.parse_args()

    rows: list[int] = []
    for seed in range(1, args.games + 1):
        rows.extend(study(args.spec, seed, seed % 2))

    total = len(rows)
    delays = Counter(rows)
    print(f"\n{total} hire-to-first-productive-action samples, "
          f"{args.games} games, {args.spec}\n")
    for turns in sorted(delays):
        n = delays[turns]
        print(f"  {turns:3d} turns after spawning: {n:4d} hands "
              f"({100 * n / total:4.1f}%)")
    slow = sum(1 for t in rows if t >= 5)
    print(f"\n{slow} / {total} ({100 * slow / total:.1f}%) took 5+ turns")
    print("field reference (top200_tapes, rank 1-5 and others): "
          "109/334 (32.6%)")


if __name__ == "__main__":
    main()
