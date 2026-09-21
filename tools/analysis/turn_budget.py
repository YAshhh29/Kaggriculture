"""Where every worker-turn goes, ours against a top-200 team's.

A farm gets `hands x 24` turns a day and nothing else. Coins come from what
those turns were spent on, so this counts every single one at
`_apply_unit_action` -- the eight compass moves, the passes, and each real
job -- for both seats of the same game.

The two numbers to read first are the share spent walking and the share
spent passing. A turn spent walking is a turn not spent watering, and a
hired hand is rented for the whole day whether it works or idles, so a high
pass share means the farm is paying for labour it has no work for.

    python -m tools.analysis.turn_budget rl.candidate_j:agent --tapes 3
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

from rl.replay_agent import build_replay_agent  # noqa: E402
from tools.eval.measure_panel import resolve  # noqa: E402

MOVES = ("NORTH", "SOUTH", "EAST", "WEST",
         "NORTHEAST", "NORTHWEST", "SOUTHEAST", "SOUTHWEST",
         "UP", "DOWN", "LEFT", "RIGHT")


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def run(spec: str, tape: Path) -> tuple[Counter, Counter, float, float]:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    record = json.loads(tape.read_text(encoding="utf-8"))
    opponent = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    books = (Counter(), Counter())
    # When the crew stands idle. A pass at dawn is a hand with nothing in
    # reach; a pass at dusk is the closing logic switching jobs off.
    idle_hour = (Counter(), Counter())
    clock = [0]
    # How far a worker walks between one piece of work and the next. A farm
    # whose jobs sit next to each other pays one step a job; a farm that
    # sends the same hand across the board pays five.
    runs = (Counter(), Counter())
    walking = ({}, {})
    steps_taken = ({}, {})
    # Where the work actually is. The shed occupies the four centre tiles,
    # so distance from centre is distance from the one place every hand
    # starts its morning and every sale has to pass through.
    places = (Counter(), Counter())
    # Steps actually taken between two jobs against the straight-line
    # distance between them. Anything above one is a detour: a hand that
    # set off for one tile, was re-aimed at another, and paid for both.
    last = ({}, {})
    detour = ([0, 0], [0, 0])
    seat_of: dict[int, int] = {}
    raw_unit = engine._apply_unit_action

    def unit(farm, private, idx, action, board_size, day, turns_per_day,
             shed_capacity=100):
        seat = seat_of.get(id(farm))
        if seat is not None:
            op = action[0] if isinstance(action, list) and action else "NONE"
            books[seat]["WALK" if op in MOVES else str(op)] += 1
            if op == "PASS":
                idle_hour[seat][clock[0]] += 1
            if op in MOVES:
                walking[seat][idx] = walking[seat].get(idx, 0) + 1
                steps_taken[seat][idx] = steps_taken[seat].get(idx, 0) + 1
            elif op != "PASS":
                runs[seat][min(walking[seat].pop(idx, 0), 9)] += 1
                where = (farm["farmer"] if idx == 0
                         else (farm["hands"][idx - 1]
                               if idx - 1 < len(farm["hands"]) else None))
                if where is not None:
                    reach = max(abs(int(where[0]) - 4), abs(int(where[1]) - 4))
                    places[seat][min(reach, 6)] += 1
                    spot = (int(where[0]), int(where[1]))
                    was = last[seat].get(idx)
                    took = steps_taken[seat].pop(idx, 0)
                    if was is not None and took > 0:
                        straight = max(abs(spot[0] - was[0]),
                                       abs(spot[1] - was[1]))
                        detour[seat][0] += took
                        detour[seat][1] += straight
                    last[seat][idx] = spot
        return raw_unit(farm, private, idx, action, board_size, day,
                        turns_per_day, shed_capacity)

    raw_interpreter = env.interpreter

    def interpreter(state, e):
        clock[0] = int(state[0].observation.get("step", 0)) % 24
        seat_of.clear()
        seat_of.update({id(farm): seat for seat, farm
                        in enumerate(state[0].observation.farms)})
        return raw_interpreter(state, e)

    engine._apply_unit_action = unit
    env.interpreter = interpreter
    try:
        env.run([resolve(spec), opponent])
    finally:
        engine._apply_unit_action = raw_unit
    final = env.steps[-1]
    return (books[0], books[1], runs[0], runs[1], places[0], places[1],
            detour[0], detour[1], idle_hour[0], idle_hour[1],
            float(final[0].get("reward") or 0.0),
            float(final[1].get("reward") or 0.0))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--tapes", type=int, default=3)
    args = parser.parse_args()

    tapes = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    ours, theirs = Counter(), Counter()
    our_runs, their_runs = Counter(), Counter()
    our_where, their_where = Counter(), Counter()
    our_detour, their_detour = [0, 0], [0, 0]
    our_idle, their_idle = Counter(), Counter()
    scores = [0.0, 0.0]
    for tape in tapes[: args.tapes]:
        (mine, yours, mine_runs, your_runs, mine_where, your_where,
         mine_detour, your_detour, mine_idle, your_idle,
         a, b) = run(args.spec, tape)
        our_idle.update(mine_idle)
        their_idle.update(your_idle)
        for pair, total in ((mine_detour, our_detour),
                            (your_detour, their_detour)):
            total[0] += pair[0]
            total[1] += pair[1]
        our_where.update(mine_where)
        their_where.update(your_where)
        ours.update(mine)
        theirs.update(yours)
        our_runs.update(mine_runs)
        their_runs.update(your_runs)
        scores[0] += a
        scores[1] += b

    games = max(1, args.tapes)
    total_ours = max(1, sum(ours.values()))
    total_theirs = max(1, sum(theirs.values()))
    print(f"\n{args.spec}: the turn budget over {games} games "
          f"({scores[0] / games:,.0f} to {scores[1] / games:,.0f} a game)\n")
    print(f"  turns taken: {total_ours:,} against {total_theirs:,}\n")
    print(f"  {'action':22s} {'ours':>8s} {'share':>7s} "
          f"{'theirs':>8s} {'share':>7s} {'gap':>8s}")
    for op in sorted(set(ours) | set(theirs),
                     key=lambda k: -(theirs.get(k, 0) / total_theirs)):
        a, b = ours.get(op, 0), theirs.get(op, 0)
        share_a, share_b = a / total_ours, b / total_theirs
        print(f"  {op:22s} {a:8d} {share_a:6.1%} {b:8d} {share_b:6.1%} "
              f"{share_b - share_a:+7.1%}")

    work_ours = total_ours - ours["WALK"] - ours["PASS"]
    work_theirs = total_theirs - theirs["WALK"] - theirs["PASS"]
    print(f"\n  turns that did something: {work_ours / total_ours:.1%} "
          f"against {work_theirs / total_theirs:.1%}")
    print(f"  coins per working turn: {scores[0] / max(1, work_ours):,.1f} "
          f"against {scores[1] / max(1, work_theirs):,.1f}")

    jobs_ours = max(1, sum(our_runs.values()))
    jobs_theirs = max(1, sum(their_runs.values()))
    mean_ours = sum(k * v for k, v in our_runs.items()) / jobs_ours
    mean_theirs = sum(k * v for k, v in their_runs.items()) / jobs_theirs
    print(f"\n  steps walked to reach a job: {mean_ours:.2f} against "
          f"{mean_theirs:.2f}\n")
    print(f"  {'steps':>7s} {'ours':>8s} {'share':>7s} {'theirs':>8s} "
          f"{'share':>7s}")
    for steps in range(10):
        a, b = our_runs.get(steps, 0), their_runs.get(steps, 0)
        label = "9+" if steps == 9 else str(steps)
        print(f"  {label:>7s} {a:8d} {a / jobs_ours:6.1%} {b:8d} "
              f"{b / jobs_theirs:6.1%}")

    here = max(1, sum(our_where.values()))
    there = max(1, sum(their_where.values()))
    mean_here = sum(k * v for k, v in our_where.items()) / here
    mean_there = sum(k * v for k, v in their_where.items()) / there
    print(f"\n  rings from the shed where the work happens "
          f"(mean {mean_here:.2f} against {mean_there:.2f}):\n")
    print(f"  {'ring':>7s} {'ours':>8s} {'share':>7s} {'theirs':>8s} "
          f"{'share':>7s}")
    for ring in range(7):
        a, b = our_where.get(ring, 0), their_where.get(ring, 0)
        label = "6+" if ring == 6 else str(ring)
        print(f"  {label:>7s} {a:8d} {a / here:6.1%} {b:8d} {b / there:6.1%}")

    print("\n  idle turns by hour of the day:")
    for block in range(0, 24, 4):
        a = sum(our_idle.get(h, 0) for h in range(block, block + 4))
        b = sum(their_idle.get(h, 0) for h in range(block, block + 4))
        print(f"    hours {block:2d}-{block + 3:2d}  {a:6d} {b:6d}")

    for name, pair in (("ours", our_detour), ("theirs", their_detour)):
        if pair[1]:
            print(f"  {name}: {pair[0]:,} steps walked to cover "
                  f"{pair[1]:,} of distance -- {pair[0] / pair[1]:.2f}x")


if __name__ == "__main__":
    main()

