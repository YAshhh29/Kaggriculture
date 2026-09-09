"""Turn by turn, our farm against the top of the ladder's.

Every comparison this project has made is a final score. A final score
says an agent is behind; it does not say *when* it fell behind or what it
was doing at the time, and it cannot be acted on.

This walks a game step by step and records the same quantities for our
agent and for the elite corpus at the same turns: money, the farm that
money bought, and what has been sold so far. Elite state is recovered by
replaying each captured tape in the simulator, so both sides are measured
on identical machinery.

Read the columns as a build order. If the corpus has eleven animals at
turn 120 and we have four, the fix is at turn 120 and not in the endgame.

    python -m tools.eval.telemetry_grid rl.candidate_g:agent --until 120
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.data.profile_tapes import INDEX, TAPES, load_tape  # noqa: E402

GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")
FIELDS = ("money", "hands", "animals", "planted", "pens", "quadrants",
          "sold_units", "sold_value")


def farm_state(step: list[dict[str, Any]], side: int) -> dict[str, Any] | None:
    for view in step:
        observation = view.get("observation")
        if not (isinstance(observation, dict) and observation.get("farms")):
            continue
        farms = observation["farms"]
        if side >= len(farms) or not isinstance(farms[side], dict):
            return None
        farm = farms[side]
        animals = planted = pens = 0
        for row in farm.get("tiles") or []:
            for tile in row:
                if not isinstance(tile, dict):
                    continue
                if "animal" in tile:
                    animals += 1
                elif tile.get("kind") == "PLANT":
                    planted += 1
                elif tile.get("kind") in ("COOP", "PASTURE"):
                    pens += 1
        return {
            "money": float(farm.get("money", 0) or 0),
            "hands": len(farm.get("hands") or []),
            "animals": animals,
            "planted": planted,
            "pens": pens,
            "quadrants": len(farm.get("unlocked_quadrants") or []),
            "market": (observation.get("market") or {}).get("inventory") or {},
        }
    return None


def walk(steps, actions_of_side: int, marks: tuple[int, ...]
        ) -> dict[int, dict[str, Any]]:
    """State at each mark, plus cumulative sales up to that point.

    Sale quantities in a tape are *requests*, not fills: the engine clamps
    every SELL to what the shed actually holds, and the strong agents ask
    for far more than they have. Counting the request made the corpus look
    as though it sold 145 wheat on day one out of a shed that starts
    empty. So each order is clamped here the same way the engine clamps
    it, against the shed in that step's own observation.
    """
    sold: Counter[str] = Counter()
    out: dict[int, dict[str, Any]] = {}
    for step_index, step in enumerate(steps):
        if actions_of_side < len(step):
            view = step[actions_of_side]
            observation = view.get("observation") or {}
            shed = dict(((observation.get("private") or {}).get("shed")) or {})
            action = view.get("action")
            if isinstance(action, dict):
                for order in action.get("market") or []:
                    if (isinstance(order, list) and len(order) > 2
                            and order[0] == "SELL"):
                        try:
                            good = str(order[1])
                            fill = min(int(order[2]),
                                       int(shed.get(good, 0) or 0))
                        except (TypeError, ValueError):
                            continue
                        if fill > 0:
                            sold[good] += fill
                            shed[good] = int(shed.get(good, 0)) - fill
        if step_index in marks:
            state = farm_state(step, actions_of_side)
            if state is None:
                continue
            state["sold_units"] = sum(sold.values())
            state["sold"] = dict(sold)
            out[step_index] = state
    return out


def elite_grids(marks: tuple[int, ...], games: int, min_rating: float
                ) -> list[dict[int, dict[str, Any]]]:
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent

    grids = []
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists() or row["episode_id"] in seen:
            continue
        if (row.get("rating") or 0) < min_rating:
            continue
        seen.add(row["episode_id"])
        actions = load_tape(path)
        agent = build_replay_agent(tuple(actions))
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": 11},
                   debug=False)
        env.run([agent, agent])
        grids.append(walk(env.steps, 0, marks))
        if len(grids) >= games:
            break
    return grids


def our_grid(spec: str, marks: tuple[int, ...], seed: int
             ) -> dict[int, dict[str, Any]]:
    from kaggle_environments import make

    from tools.eval.measure_panel import resolve

    inner = resolve(spec)
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([inner, inner])
    return walk(env.steps, 0, marks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--until", type=int, default=720)
    parser.add_argument("--every", type=int, default=24)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--min-rating", type=float, default=2700.0)
    args = parser.parse_args()

    marks = tuple(range(0, min(args.until, 719) + 1, args.every))
    print(f"replaying {args.games} elite tapes ...", flush=True)
    elite = elite_grids(marks, args.games, args.min_rating)
    mine = our_grid(args.spec, marks, args.seed)
    print(f"{len(elite)} elite games, ours = {args.spec}\n")

    def med(mark: int, field: str) -> float:
        vals = [g[mark][field] for g in elite
                if mark in g and field in g[mark]]
        return statistics.median(vals) if vals else 0.0

    head = f"  {'turn':>5} {'day':>4} | "
    for field in ("money", "hands", "animals", "planted", "pens", "sold_units"):
        head += f"{field[:9]:>10}"
    print(head)
    print(f"  {'':>5} {'':>4} |   ours / elite  (gap)")
    for mark in marks:
        if mark not in mine:
            continue
        row = f"  {mark:>5} {mark // 24:>4} | "
        for field in ("money", "hands", "animals", "planted", "pens",
                      "sold_units"):
            ours = mine[mark].get(field, 0)
            theirs = med(mark, field)
            row += f"{ours:>5.0f}/{theirs:<4.0f}"
        print(row)

    print("\n  cumulative units sold by good")
    print(f"  {'turn':>5} | " + "".join(f"{g[:4]:>11}" for g in GOODS))
    for mark in marks:
        if mark not in mine:
            continue
        row = f"  {mark:>5} | "
        for good in GOODS:
            ours = mine[mark]["sold"].get(good, 0)
            theirs = statistics.median(
                [g[mark]["sold"].get(good, 0) for g in elite if mark in g]
                or [0]
            )
            row += f"{ours:>5.0f}/{theirs:<5.0f}"
        print(row)


if __name__ == "__main__":
    main()
