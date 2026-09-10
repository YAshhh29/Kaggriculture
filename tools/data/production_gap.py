"""Where does the output gap come from? Ask two hundred replays.

Candidate G banks around 66,000. The tapes it plays against bank around
147,000 off it and around 87,000 off each other. That gap has been
attributed to labour, to land, to the herd and to the market, mostly on
inference. This measures it.

For every elite tape and for G, replayed under identical conditions, it
counts what actually comes off the farm: units harvested per good, tiles
carrying a crop, animals standing, and the worker actions that produced
them. The point is to find which *quantity* differs, before guessing at
which decision causes it.

    python -m tools.data.production_gap --games 60
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")


def harvest_census(actions: list[dict[str, Any]], steps) -> dict[str, Any]:
    """What this farm harvested, planted and kept, over one game."""
    verbs: Counter[str] = Counter()
    harvested: Counter[str] = Counter()
    planted: Counter[str] = Counter()
    peak_tiles = 0
    peak_animals = 0
    hands: list[int] = []

    for step, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        observation = None
        if step < len(steps):
            for view in steps[step]:
                candidate = view.get("observation")
                if isinstance(candidate, dict) and candidate.get("farms"):
                    observation = candidate
                    break
        board = None
        if observation:
            farms = observation.get("farms") or []
            if farms and isinstance(farms[0], dict):
                farm = farms[0]
                board = farm.get("tiles") or []
                hands.append(len(farm.get("hands") or []))
                crops = sum(1 for row in board for tile in row
                            if isinstance(tile, dict)
                            and tile.get("kind") == "PLANT")
                animals = sum(1 for row in board for tile in row
                              if isinstance(tile, dict) and "animal" in tile)
                peak_tiles = max(peak_tiles, crops)
                peak_animals = max(peak_animals, animals)

        for unit_index, unit in enumerate(
                [action.get("farmer"), *(action.get("hands") or [])]):
            if not isinstance(unit, list) or not unit:
                continue
            verb = str(unit[0])
            verbs[verb] += 1
            if verb == "PLANT" and len(unit) > 1:
                planted[str(unit[1])] += 1
            if verb == "HARVEST" and board is not None:
                # What is standing on the tile this worker occupies.
                farms = (observation or {}).get("farms") or []
                farm = farms[0] if farms else {}
                units_here = [farm.get("farmer"), *(farm.get("hands") or [])]
                if unit_index < len(units_here):
                    pos = units_here[unit_index]
                    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        x, y = int(pos[0]), int(pos[1])
                        if 0 <= y < len(board) and 0 <= x < len(board[y]):
                            tile = board[y][x]
                            if isinstance(tile, dict):
                                got = int(tile.get("yield_units", 0) or 0)
                                if "animal" in tile:
                                    from rl.economics import ANIMALS
                                    good = ANIMALS[tile["animal"]]["product"]
                                    harvested[good] += got
                                elif tile.get("kind") == "PLANT":
                                    harvested[str(tile.get("crop"))] += got
    total = sum(verbs.values()) or 1
    moves = sum(verbs[d] for d in ("NORTH", "SOUTH", "EAST", "WEST"))
    return {
        "harvested": harvested,
        "planted": planted,
        "peak_tiles": peak_tiles,
        "peak_animals": peak_animals,
        "hands": statistics.mean(hands) if hands else 0.0,
        "turns": total,
        "move_share": moves / total,
        "pass_share": verbs.get("PASS", 0) / total,
        "verbs": verbs,
    }


def replay(actions):
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent

    agent = build_replay_agent(tuple(actions))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": 11}, debug=False)
    env.run([agent, agent])
    return env.steps


def ours(seed: int):
    from kaggle_environments import make

    import rl.candidate_g as G

    captured: list[dict[str, Any]] = []

    def watched(observation, *rest):
        action = G.agent(observation)
        captured.append(json.loads(json.dumps(action)))
        return action

    # Against a replayed tape, not against itself: running G on both
    # sides captures two agents' actions into one list and doubles every
    # count, which made the first reading of this table wrong by 2x.
    from tools.eval.measure_panel import resolve

    opponent = resolve(
        "clone:kaggle_cache/live_clones/live_106683123.json")
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([watched, opponent])
    return captured, env.steps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=60)
    parser.add_argument("--min-rating", type=float, default=2800.0)
    args = parser.parse_args()

    from tools.data.profile_tapes import INDEX, TAPES, load_tape

    rows = []
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists() or row["episode_id"] in seen:
            continue
        if (row.get("rating") or 0) < args.min_rating:
            continue
        seen.add(row["episode_id"])
        rows.append(path)
        if len(rows) >= args.games:
            break

    print(f"replaying {len(rows)} elite tapes ...", flush=True)
    elite = []
    for index, path in enumerate(rows):
        actions = load_tape(path)
        elite.append(harvest_census(actions, replay(actions)))
        if (index + 1) % 20 == 0:
            print(f"  {index + 1}/{len(rows)}", flush=True)

    captured, steps = ours(11)
    mine = harvest_census(captured, steps)

    def med(field, source=elite):
        return statistics.median([r[field] for r in source]) if source else 0

    print(f"\n{len(elite)} elite games vs Candidate G\n")
    print(f"{'':22s}{'G':>10}{'elite median':>15}")
    for field in ("peak_tiles", "peak_animals", "hands", "turns"):
        print(f"  {field:20s}{mine[field]:10.1f}{med(field):15.1f}")
    print(f"  {'move share':20s}{mine['move_share']:10.1%}"
          f"{med('move_share'):15.1%}")
    print(f"  {'pass share':20s}{mine['pass_share']:10.1%}"
          f"{med('pass_share'):15.1%}")

    print(f"\n  units harvested{'':7s}{'G':>10}{'elite median':>15}")
    for good in GOODS:
        theirs = statistics.median([r["harvested"].get(good, 0)
                                    for r in elite] or [0])
        print(f"  {good:20s}{mine['harvested'].get(good, 0):10d}{theirs:15.0f}")

    print(f"\n  PLANT actions{'':9s}{'G':>10}{'elite median':>15}")
    for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        theirs = statistics.median([r["planted"].get(crop, 0)
                                    for r in elite] or [0])
        print(f"  {crop:20s}{mine['planted'].get(crop, 0):10d}{theirs:15.0f}")

    work = Counter()
    for r in elite:
        for k, v in r["verbs"].items():
            work[k] += v / len(elite)
    print(f"\n  worker actions{'':8s}{'G':>10}{'elite mean':>15}")
    for verb in ("WATER", "HARVEST", "PLANT", "FEED", "CARE",
                 "COLLECT_FERTILIZER", "FERTILIZE", "PICKUP", "PLACE",
                 "BUILD_COOP", "BUILD_PASTURE", "DIG", "DROP"):
        print(f"  {verb:20s}{mine['verbs'].get(verb, 0):10d}"
              f"{work.get(verb, 0):15.0f}")


if __name__ == "__main__":
    main()
