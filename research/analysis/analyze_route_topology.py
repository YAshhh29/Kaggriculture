"""Summarize worker route stability and task locality in a replay."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import fmean
from typing import Any

from benchmark import MOVE_ACTIONS, TILE_TASK_ACTIONS
from research.collection.collect_live_replay_league import _resolve_player


def _quadrant(position: tuple[int, int], board_size: int) -> str:
    x, y = position
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def analyze_route_topology(
    replay: dict[str, Any],
    player: int,
) -> dict[str, Any]:
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))
    workers: dict[int, dict[str, Any]] = {}
    for record_index in range(1, len(replay["steps"])):
        before = replay["steps"][record_index - 1][player]["observation"]
        state = replay["steps"][record_index][player]
        farm = before["farms"][player]
        action = state.get("action") or {}
        positions = [farm["farmer"], *farm.get("hands", [])]
        actions = [action.get("farmer"), *action.get("hands", [])]
        day = int(before.get("day", 0))
        for worker, position_value in enumerate(positions):
            position = (int(position_value[0]), int(position_value[1]))
            worker_action = (
                actions[worker]
                if worker < len(actions)
                and isinstance(actions[worker], list)
                and actions[worker]
                else ["PASS"]
            )
            operation = str(worker_action[0])
            row = workers.setdefault(
                worker,
                {
                    "actions": Counter(),
                    "task_tiles": Counter(),
                    "task_quadrants": Counter(),
                    "daily_task_quadrants": {},
                    "quadrant_switches": 0,
                    "last_task_quadrant": None,
                },
            )
            row["actions"][operation] += 1
            if operation not in TILE_TASK_ACTIONS:
                continue
            tile_key = f"{position[0]},{position[1]}"
            quadrant = _quadrant(position, board_size)
            row["task_tiles"][tile_key] += 1
            row["task_quadrants"][quadrant] += 1
            daily_quadrants = row["daily_task_quadrants"].setdefault(
                day,
                Counter(),
            )
            daily_quadrants[quadrant] += 1
            if (
                row["last_task_quadrant"] is not None
                and row["last_task_quadrant"] != quadrant
            ):
                row["quadrant_switches"] += 1
            row["last_task_quadrant"] = quadrant

    compact_workers = []
    for worker, row in sorted(workers.items()):
        actions = row["actions"]
        task_count = sum(row["task_quadrants"].values())
        move_count = sum(actions[operation] for operation in MOVE_ACTIONS)
        compact_workers.append(
            {
                "worker": worker,
                "tasks": task_count,
                "moves": move_count,
                "passes": actions["PASS"],
                "moves_per_task": (
                    round(move_count / task_count, 3) if task_count else None
                ),
                "quadrant_switches": row["quadrant_switches"],
                "task_quadrants": dict(sorted(row["task_quadrants"].items())),
                "top_task_tiles": [
                    {"tile": tile, "tasks": count}
                    for tile, count in row["task_tiles"].most_common(10)
                ],
                "daily_primary_quadrant": {
                    str(day): counts.most_common(1)[0][0]
                    for day, counts in sorted(
                        row["daily_task_quadrants"].items()
                    )
                },
            }
        )
    task_counts = [row["tasks"] for row in compact_workers]
    move_rates = [
        row["moves_per_task"]
        for row in compact_workers
        if row["moves_per_task"] is not None
    ]
    return {
        "workers": compact_workers,
        "summary": {
            "workers_seen": len(compact_workers),
            "mean_tasks_per_worker": round(fmean(task_counts), 2),
            "mean_moves_per_task_by_worker": round(fmean(move_rates), 3),
            "total_quadrant_switches": sum(
                row["quadrant_switches"] for row in compact_workers
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    identity = parser.add_mutually_exclusive_group(required=True)
    identity.add_argument("--team-name")
    identity.add_argument("--player", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    replay = json.loads(args.replay.read_text(encoding="utf-8"))
    player = (
        int(args.player)
        if args.player is not None
        else _resolve_player(replay, "auto", args.team_name)
    )
    report = {
        "episode_id": replay.get("info", {}).get("EpisodeId"),
        "team_name": args.team_name,
        "player": player,
        **analyze_route_topology(replay, player),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
