"""Summarize production and service patterns in live Kaggle replays."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from statistics import fmean
from typing import Any

from benchmark import (
    analyze_livestock,
    analyze_route,
    count_actions,
    inventory_snapshot,
)
from research.collection.collect_live_replay_league import (
    _fetch_replay,
    _resolve_player,
)


SALE_ITEMS = (
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "EGG",
    "MILK",
    "WOOL",
    "FERTILIZER",
)


def _farm_snapshot(observation: dict[str, Any], player: int) -> dict[str, Any]:
    farm = observation["farms"][player]
    crops: Counter[str] = Counter()
    animals: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kind = str(tile.get("kind", "UNKNOWN"))
            kinds[kind] += 1
            if kind == "PLANT":
                crops[str(tile.get("crop", "UNKNOWN"))] += 1
            if tile.get("animal"):
                animals[str(tile["animal"])] += 1
    return {
        "money": int(farm.get("money", 0)),
        "hands": len(farm.get("hands", [])),
        "land": sum(kinds.values()),
        "weeds": kinds["WEED"],
        "crops": dict(sorted(crops.items())),
        "animals": dict(sorted(animals.items())),
        "inventory": inventory_snapshot(observation),
    }


def _player_metrics(
    replay: dict[str, Any],
    player: int,
) -> dict[str, Any]:
    actions = count_actions(replay["steps"], player)
    route = analyze_route(replay["steps"], player)
    livestock = analyze_livestock(replay["steps"], player)
    final_observation = replay["steps"][-1][player]["observation"]
    farmer_actions = actions["farmer"]
    hand_actions = actions["hands"]
    sold = actions["market_units"]
    fertilize_events = [
        {
            key: visit[key]
            for key in ("step", "day", "hour", "worker", "tile")
        }
        for visit in route["task_visits"]
        if visit["task"] == "FERTILIZE"
    ]
    return {
        "movement_turns": route["all_worker_movement_turns"],
        "task_visits": route["task_visit_count"],
        "mean_travel_turns_per_task": route[
            "mean_travel_turns_per_task"
        ],
        "cycles_planted": route["cycles_planted"],
        "cycles_harvested": route["cycles_harvested"],
        "cycles_weeded": route["cycles_weeded"],
        "cycles_unfinished": route["cycles_unfinished"],
        "missed_planting_day_water": route[
            "missed_planting_day_water_cycles"
        ],
        "harvested_units": route["harvested_units"],
        "mean_harvest_yield": route["mean_harvest_yield"],
        "fertilize_actions": (
            farmer_actions.get("FERTILIZE", 0)
            + hand_actions.get("FERTILIZE", 0)
        ),
        "fertilize_events": fertilize_events,
        "care_actions": (
            farmer_actions.get("CARE", 0)
            + hand_actions.get("CARE", 0)
        ),
        "feed_actions": (
            farmer_actions.get("FEED", 0)
            + hand_actions.get("FEED", 0)
        ),
        "sales": {
            item: sold.get(f"SELL:{item}", 0) for item in SALE_ITEMS
        },
        "livestock_losses": livestock["losses"],
        "total_livestock_losses": sum(livestock["losses"].values()),
        "maximum_animals": livestock["maximum_active"],
        "final": _farm_snapshot(final_observation, player),
    }


def analyze_record(
    record: dict[str, Any],
    team_name: str,
) -> dict[str, Any]:
    episode_id = int(record["episode_id"])
    replay = _fetch_replay(episode_id)
    player = _resolve_player(replay, "auto", team_name)
    if player != int(record["own_player"]):
        raise ValueError(f"Player mismatch for episode {episode_id}")
    if replay["rewards"] != record["expected_rewards"]:
        raise ValueError(f"Reward mismatch for episode {episode_id}")
    opponent = 1 - player
    own_reward = float(replay["rewards"][player])
    opponent_reward = float(replay["rewards"][opponent])
    day12 = record["decision_contexts"]["day12_hour12"]["features"]
    return {
        "episode_id": episode_id,
        "seed": int(record["seed"]),
        "own_player": player,
        "result": (
            "win"
            if own_reward > opponent_reward
            else "loss"
            if own_reward < opponent_reward
            else "tie"
        ),
        "reward": own_reward,
        "opponent_reward": opponent_reward,
        "margin": own_reward - opponent_reward,
        "day12": {
            "staging_distance": (
                2 if day12["price_strawberry"] > 1.30 else 0
            ),
            "price_strawberry": day12["price_strawberry"],
            "hands": day12["own_hands"],
            "pending_animal_service_per_worker": day12[
                "own_pending_animal_service_per_worker"
            ],
            "unfertilized_due_strawberries": day12[
                "own_unfertilized_due_strawberries"
            ],
            "carrier_distance": day12[
                "own_min_carrier_distance_to_due_strawberries"
            ],
        },
        "own": _player_metrics(replay, player),
        "opponent": _player_metrics(replay, opponent),
    }


def _mean(records: list[dict[str, Any]], path: tuple[str, ...]) -> float:
    if not records:
        return 0.0
    values: list[float] = []
    for record in records:
        value: Any = record
        for key in path:
            value = value.get(key, 0) if isinstance(value, dict) else 0
        values.append(float(value or 0))
    return round(fmean(values), 2)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    paths = {
        "reward": ("reward",),
        "margin": ("margin",),
        "movement_turns": ("own", "movement_turns"),
        "cycles_planted": ("own", "cycles_planted"),
        "cycles_harvested": ("own", "cycles_harvested"),
        "cycles_weeded": ("own", "cycles_weeded"),
        "cycles_unfinished": ("own", "cycles_unfinished"),
        "missed_planting_day_water": (
            "own",
            "missed_planting_day_water",
        ),
        "harvested_units": ("own", "harvested_units"),
        "fertilize_actions": ("own", "fertilize_actions"),
        "livestock_losses": ("own", "total_livestock_losses"),
        "final_money": ("own", "final", "money"),
    }
    for result in ("all", "win", "loss", "tie"):
        selected = (
            records
            if result == "all"
            else [record for record in records if record["result"] == result]
        )
        summary[result] = {
            "games": len(selected),
            **{
                name: _mean(selected, path)
                for name, path in paths.items()
            },
            "distance_two_games": sum(
                record["day12"]["staging_distance"] == 2
                for record in selected
            ),
            "sales": {
                item: _mean(selected, ("own", "sales", item))
                for item in SALE_ITEMS
            },
        }
    summary["sub_cap_applications"] = [
        {
            "episode_id": record["episode_id"],
            "result": record["result"],
            "margin": record["margin"],
            "applications": record["own"]["fertilize_actions"],
            "events": [
                f"{event['day']}:{event['hour']}"
                for event in record["own"]["fertilize_events"]
            ],
            "day12": record["day12"],
        }
        for record in records
        if record["own"]["fertilize_actions"] < 4
    ]
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--team-name", required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    analyze = partial(analyze_record, team_name=args.team_name)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        records = list(executor.map(analyze, dataset["records"]))
    records.sort(key=lambda record: int(record["episode_id"]))
    report = {
        "simulator_version": dataset["simulator_version"],
        "dataset": str(args.dataset),
        "summary": summarize(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
