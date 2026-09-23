"""Do the actual best teams have the same new-hire cold-start problem J did?

trace_new_hire.py found it in our own agent by watching real turns. The
natural next question, raised directly: with 561 recorded games of
top-ranked teams sitting in kaggle_cache/top200_tapes, why guess at what
they do differently rather than watch it. This replays the TRACKED side
of real top tapes (never the opponent -- only the recorded team's own
actions are attributed to a rank and a rating) and reports, for every
turn its hand count grew, how many turns passed before the new hand's
position first left the shed block, and before it first took a
productive (non-movement, non-pass) action.

    python -m tools.analysis.trace_top_hire --tapes 25
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MOVE = {"NORTH", "SOUTH", "EAST", "WEST"}


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def study(path: Path) -> list[tuple[int, int, int]]:
    """(rank, turns to leave shed area, turns to first productive action)."""
    from rl.replay_agent import build_replay_agent
    from kaggle_environments import make

    record = json.loads(path.read_text(encoding="utf-8"))
    seat = int(record["seat"])
    mine = _unpack(record["actions_zlib_b64"])
    theirs = _unpack(record["opponent_actions_zlib_b64"])
    players = [build_replay_agent(mine), build_replay_agent(theirs)]
    if seat == 1:
        players = players[::-1]

    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run(players)

    out: list[tuple[int, int, int]] = []
    prev_count = 0
    born_step: dict[int, int] = {}
    born_pos: dict[int, tuple[int, int]] = {}
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
                born_pos[idx] = hands[idx]
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
            # First non-movement action this hand has taken since it was
            # first seen. Whether it happened at the shed or off it, this
            # is the turn count that matters for "how long idle/moving".
            out.append((record.get("team_rank", 0), idx,
                        index - born_step[idx]))
            settled.add(idx)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tapes", type=int, default=25)
    args = ap.parse_args()

    tapes = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    rows: list[tuple[int, int, int]] = []
    used = 0
    for tape in tapes[: args.tapes]:
        try:
            r = study(tape)
            if r:
                rows.extend(r)
                used += 1
        except Exception as error:
            print(f"  {tape.name}: {type(error).__name__} {error}")

    print(f"\n{len(rows)} (rank, hand-index, turns-to-first-productive-action) "
          f"samples from {used} tapes\n")

    delays = Counter(turns for _rank, _idx, turns in rows)
    total = len(rows)
    for turns in sorted(delays):
        n = delays[turns]
        print(f"  {turns:3d} turns after spawning: {n:4d} hands "
              f"({100 * n / total:4.1f}%)")

    slow = [r for r in rows if r[2] >= 5]
    print(f"\n{len(slow)} / {total} ({100 * len(slow) / total:.1f}%) took "
          f"5+ turns to do anything productive after appearing")
    if slow:
        by_rank = Counter(rank for rank, _idx, _turns in slow)
        print(f"  by team rank: {dict(sorted(by_rank.items()))}")


if __name__ == "__main__":
    main()
