"""Compare control and candidate mechanisms on one captured live episode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agents.experimental_premium_throughput_agent import _crop_operations
from benchmark import load_agent_callable, load_simulator, run_game
from policies.macro_policy import extract_macro_features
from research.evaluation.evaluate_live_macro_arms import replay_agent
from research.evaluation.evaluate_live_macro_arms import (
    validate_control_reproduction,
)


ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "submissions" / "future-labor" / "main.py"


def trace_fertilizer_opportunities(
    agent: Any,
) -> tuple[
    Any,
    list[dict[str, Any]],
    list[dict[str, float]],
    list[dict[str, Any]],
]:
    """Wrap an agent and capture nearby strawberry service opportunities."""
    events: list[dict[str, Any]] = []
    lock_contexts: list[dict[str, float]] = []
    late_contexts: list[dict[str, Any]] = []

    def traced(observation: dict[str, Any]) -> dict[str, Any]:
        if (
            int(observation.get("day", 0)) == 6
            and int(observation.get("hour", 0)) == 0
        ):
            lock_contexts.append(extract_macro_features(observation))
        decision = agent(observation)
        player = int(observation["player"])
        farm = observation["farms"][player]
        positions = [
            tuple(farm["farmer"]),
            *(tuple(position) for position in farm.get("hands", [])),
        ]
        inventories = observation.get("private", {}).get("inventories", [])
        actions = [decision.get("farmer", ["PASS"])]
        actions.extend(decision.get("hands", []))
        actions.extend([["PASS"]] * (len(positions) - len(actions)))
        carriers = [
            worker
            for worker, inventory in enumerate(inventories[:len(positions)])
            if isinstance(inventory, dict)
            and int(inventory.get("FERTILIZER", 0)) > 0
        ]
        day = int(observation.get("day", 0))
        hour = int(observation.get("hour", 0))
        if (day, hour) in {(10, 12), (12, 12)}:
            premium_tiles = []
            for y, row in enumerate(farm.get("tiles", [])):
                for x, tile in enumerate(row):
                    if not isinstance(tile, dict) or tile.get("crop") not in {
                        "MELON",
                        "STRAWBERRY",
                    }:
                        continue
                    premium_tiles.append(
                        {
                            "target": [x, y],
                            "crop": tile["crop"],
                            "age": day - int(tile.get("planted_day", day)),
                            "watered": bool(tile.get("watered_today", False)),
                            "stress": int(
                                tile.get("consecutive_unwatered", 0)
                            ),
                            "yield_units": int(tile.get("yield_units", 0)),
                            "fertilized_until_day": int(
                                tile.get("fertilized_until_day", -1)
                            ),
                        }
                    )
            late_contexts.append(
                {
                    "day": day,
                    "hour": hour,
                    "unlocked_quadrants": list(
                        farm.get("unlocked_quadrants", [])
                    ),
                    "workers": [
                        {
                            "worker": worker,
                            "position": list(position),
                            "fertilizer": (
                                int(inventories[worker].get("FERTILIZER", 0))
                                if worker < len(inventories)
                                and isinstance(inventories[worker], dict)
                                else 0
                            ),
                            "action": actions[worker][0],
                        }
                        for worker, position in enumerate(positions)
                    ],
                    "premium_tiles": premium_tiles,
                }
            )
        if carriers:
            for y, row in enumerate(farm.get("tiles", [])):
                for x, tile in enumerate(row):
                    if not isinstance(tile, dict):
                        continue
                    if tile.get("crop") != "STRAWBERRY":
                        continue
                    operations = _crop_operations(day, tile)
                    if not {"FERTILIZE", "WATER"}.issubset(operations):
                        continue
                    target = (x, y)
                    carrier_rows = [
                        {
                            "worker": worker,
                            "distance": abs(positions[worker][0] - x)
                            + abs(positions[worker][1] - y),
                            "action": actions[worker][0],
                        }
                        for worker in carriers
                    ]
                    events.append(
                        {
                            "day": day,
                            "hour": int(observation.get("hour", 0)),
                            "target": [x, y],
                            "yield_units": int(tile.get("yield_units", 0)),
                            "water_anchors": [
                                worker
                                for worker, position in enumerate(positions)
                                if position == target
                                and actions[worker] == ["WATER"]
                            ],
                            "carriers": carrier_rows,
                        }
                    )
        return decision

    return traced, events, lock_contexts, late_contexts


def summarize_fertilizer_opportunities(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize carrier proximity without retaining a full replay."""
    minimum_distances = [
        min(carrier["distance"] for carrier in event["carriers"])
        for event in events
    ]
    idle_distances = [
        carrier["distance"]
        for event in events
        for carrier in event["carriers"]
        if carrier["action"] == "PASS"
    ]
    anchored = [event for event in events if event["water_anchors"]]
    return {
        "candidate_turns": len(events),
        "water_anchored_turns": len(anchored),
        "minimum_carrier_distance_counts": {
            str(distance): minimum_distances.count(distance)
            for distance in sorted(set(minimum_distances))
        },
        "idle_carrier_distance_counts": {
            str(distance): idle_distances.count(distance)
            for distance in sorted(set(idle_distances))
        },
        "near_idle_carrier_events": [
            event
            for event in events
            if any(
                carrier["action"] == "PASS"
                and carrier["distance"] <= 1
                for carrier in event["carriers"]
            )
        ],
        "near_water_anchor_events": [
            event
            for event in anchored
            if min(
                carrier["distance"] for carrier in event["carriers"]
            ) <= 2
        ],
    }


def compact(record: dict[str, Any]) -> dict[str, Any]:
    route = record["route_analysis"]
    livestock = record["livestock_analysis"]
    return {
        "reward": record["agent_reward"],
        "opponent_reward": record["opponent_reward"],
        "result": record["result"],
        "actions": record["agent_actions"],
        "route": {
            key: route.get(key)
            for key in (
                "all_worker_movement_turns",
                "task_visit_count",
                "travel_turns_to_tasks",
                "max_travel_turns_to_task",
                "cycles_planted",
                "cycles_harvested",
                "cycles_weeded",
                "cycles_unfinished",
                "harvested_units",
            )
        },
        "livestock": {
            "placements": livestock.get("placements", {}),
            "losses": livestock.get("losses", {}),
            "pre_endgame_losses": livestock.get("pre_endgame_losses", {}),
            "maximum_active": livestock.get("maximum_active", {}),
        },
        "final_inventory": record["final_inventory"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("episode_id", type=int)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.dataset.read_text(encoding="utf-8"))["records"]
    source = next(
        record
        for record in records
        if int(record["episode_id"]) == args.episode_id
    )
    make, simulator_version = load_simulator()
    opponent = replay_agent(source["opponent_actions"])
    agents = {
        "control": load_agent_callable(CONTROL),
        "candidate": load_agent_callable(args.candidate.resolve()),
    }
    results = {}
    for name, agent in agents.items():
        traced_agent, events, lock_contexts, late_contexts = (
            trace_fertilizer_opportunities(agent)
        )
        results[name] = compact(
            run_game(
                make,
                traced_agent,
                opponent,
                720,
                int(source["seed"]),
                int(source["own_player"]),
            ),
        )
        results[name]["fertilizer_opportunities"] = (
            summarize_fertilizer_opportunities(events)
        )
        results[name]["day6_lock_context"] = lock_contexts[0]
        results[name]["late_decision_contexts"] = late_contexts
    validate_control_reproduction(
        source,
        float(results["control"]["reward"]),
        float(results["control"]["opponent_reward"]),
    )
    report = {
        "simulator_version": simulator_version,
        "episode_id": args.episode_id,
        "seed": source["seed"],
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Control: {results['control']['reward']} / "
        f"Candidate: {results['candidate']['reward']}"
    )
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
