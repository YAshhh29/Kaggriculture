"""How the top of the ladder spends a worker's day.

Replays recorded games with BOTH sides as they were played, which
reproduces the original result exactly, and watches one worker at a time:
where it goes, how far it walks between one job and the next, and how much
of the standing crop it actually waters.

The question is narrow and it is the one that decides a farm's output. A
tile's yield IS its waterings -- wheat gains a unit for every watering
inside its window, doubled if the tile is manured, and an ongoing crop pays
two units only on a day it was watered. A farm that waters half as often
grows half as much on the same ground.

    python -m tools.analysis.how_they_walk --tapes 8
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

MOVES = ("NORTH", "SOUTH", "EAST", "WEST")


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def study(path: Path, spec: str | None = None) -> dict | None:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    from rl.replay_agent import build_replay_agent

    record = json.loads(path.read_text(encoding="utf-8"))
    both = record.get("both_actions_zlib_b64") or record.get("actions_zlib_b64")
    if spec:
        from tools.eval.measure_panel import resolve
        mine = resolve(spec)
    else:
        mine = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    other = record.get("opponent_actions_zlib_b64")
    rival = build_replay_agent(_unpack(other)) if other else "random"
    seat = int(record.get("seat", 0) or 0)

    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    book = {"ops": Counter(), "runs": Counter(), "walked": 0, "straight": 0,
            "jobs": 0, "plant_days": 0, "watered_days": 0,
            "visits_per_tile": Counter()}
    seat_of: dict[int, int] = {}
    walking: dict[int, int] = {}
    last: dict[int, tuple[int, int]] = {}
    raw_unit = engine._apply_unit_action
    raw_day = engine._end_of_day

    def unit(farm, private, idx, action, board_size, day, turns_per_day,
             shed_capacity=100):
        if seat_of.get(id(farm)) != seat:
            return raw_unit(farm, private, idx, action, board_size, day,
                            turns_per_day, shed_capacity)
        op = action[0] if isinstance(action, list) and action else "NONE"
        book["ops"]["WALK" if op in MOVES else op] += 1
        where = (farm["farmer"] if idx == 0
                 else (farm["hands"][idx - 1]
                       if idx - 1 < len(farm["hands"]) else None))
        if op in MOVES:
            walking[idx] = walking.get(idx, 0) + 1
        elif op != "PASS" and where is not None:
            spot = (int(where[0]), int(where[1]))
            took = walking.pop(idx, 0)
            book["runs"][min(took, 9)] += 1
            book["jobs"] += 1
            book["visits_per_tile"][spot] += 1
            was = last.get(idx)
            if was is not None:
                book["walked"] += took
                book["straight"] += abs(spot[0] - was[0]) + abs(spot[1] - was[1])
            last[idx] = spot
        return raw_unit(farm, private, idx, action, board_size, day,
                        turns_per_day, shed_capacity)

    def end_of_day(state, env_, day):
        farm = state[0].observation.farms[seat]
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    book["plant_days"] += 1
                    if tile.get("watered_today"):
                        book["watered_days"] += 1
        return raw_day(state, env_, day)

    raw_interpreter = env.interpreter

    def interpreter(state, e):
        seat_of.clear()
        seat_of.update({id(f): s for s, f
                        in enumerate(state[0].observation.farms)})
        return raw_interpreter(state, e)

    engine._apply_unit_action = unit
    engine._end_of_day = end_of_day
    env.interpreter = interpreter
    try:
        env.run([mine, rival] if seat == 0 else [rival, mine])
    finally:
        engine._apply_unit_action = raw_unit
        engine._end_of_day = raw_day

    got = float(env.state[seat].reward or 0)
    want = float(record["rewards"]["them"])
    total = max(1, sum(book["ops"].values()))
    return {
        "team": (spec.split(":")[0].split(".")[-1] if spec
                 else record.get("source_team")),
        "rating": record.get("team_score"),
        "faithful": abs(got - want) < 1.0, "score": got, "recorded": want,
        "walk": book["ops"]["WALK"] / total,
        "pass": book["ops"]["PASS"] / total,
        "water": book["ops"]["WATER"] / total,
        "steps_per_job": book["walked"] / max(1, book["jobs"]),
        "detour": book["walked"] / max(1, book["straight"]),
        "watered_share": book["watered_days"] / max(1, book["plant_days"]),
        "tiles_touched": len(book["visits_per_tile"]),
        "visits_each": (sum(book["visits_per_tile"].values())
                        / max(1, len(book["visits_per_tile"]))),
        "runs": book["runs"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tapes", type=int, default=8)
    parser.add_argument("--agent", default=None,
                        help="play this agent in the strong team's seat "
                             "instead of replaying its tape")
    args = parser.parse_args()

    files = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    scored = []
    for path in files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if record.get("won") and record.get("opponent_actions_zlib_b64"):
            scored.append((float(record.get("team_score") or 0), path))
    scored.sort(reverse=True)
    if not scored:
        # Fall back to the strongest won games even without the rival tape.
        for path in files:
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if record.get("won"):
                scored.append((float(record.get("team_score") or 0), path))
        scored.sort(reverse=True)

    rows = []
    for rating, path in scored[: args.tapes]:
        try:
            row = study(path, args.agent)
        except Exception as error:
            print(f"  {path.name}: {type(error).__name__} {error}")
            continue
        if row:
            rows.append(row)

    print(f"\nHow the strongest teams spend a worker-turn "
          f"({len(rows)} games)\n")
    print(f"  {'team':18s} {'rated':>7s} {'ok':>3s} {'walk':>6s} {'pass':>6s} "
          f"{'water':>6s} {'steps/job':>10s} {'detour':>7s} "
          f"{'crop watered':>13s} {'tiles':>6s}")
    for row in rows:
        print(f"  {str(row['team'])[:18]:18s} {row['rating']:7.0f} "
              f"{'Y' if row['faithful'] else 'n':>3s} {row['walk']:6.1%} "
              f"{row['pass']:6.1%} {row['water']:6.1%} "
              f"{row['steps_per_job']:10.2f} {row['detour']:7.2f} "
              f"{row['watered_share']:13.1%} {row['tiles_touched']:6d}")

    if rows:
        n = len(rows)
        print(f"\n  average: walk {sum(r['walk'] for r in rows)/n:.1%}, "
              f"water {sum(r['water'] for r in rows)/n:.1%}, "
              f"{sum(r['steps_per_job'] for r in rows)/n:.2f} steps a job, "
              f"{sum(r['watered_share'] for r in rows)/n:.1%} of standing "
              f"crop watered each day")
        runs: Counter = Counter()
        for row in rows:
            runs.update(row["runs"])
        total = max(1, sum(runs.values()))
        print(f"\n  steps walked to reach a job:")
        for steps in range(10):
            label = "9+" if steps == 9 else str(steps)
            print(f"    {label:>3s} {runs.get(steps,0)/total:6.1%}")


if __name__ == "__main__":
    main()
