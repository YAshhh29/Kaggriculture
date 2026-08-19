"""Benchmark a Kaggriculture agent over seeds and player positions."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
AgentInput = str | Callable[[dict[str, Any]], dict[str, Any]]
MOVE_ACTIONS = {"NORTH", "SOUTH", "EAST", "WEST"}
TILE_TASK_ACTIONS = {
    "PLANT",
    "WATER",
    "HARVEST",
    "FERTILIZE",
    "DIG",
    "BUILD_COOP",
    "BUILD_PASTURE",
    "FEED",
    "CARE",
    "COLLECT_FERTILIZER",
}


def classify_result(
    agent_reward: float | None,
    opponent_reward: float | None,
    agent_status: str,
    opponent_status: str,
) -> str:
    if (
        agent_status != "DONE"
        or opponent_status != "DONE"
        or agent_reward is None
        or opponent_reward is None
    ):
        return "error"
    if agent_reward > opponent_reward:
        return "win"
    if agent_reward < opponent_reward:
        return "loss"
    return "tie"


def count_actions(
    replay_steps: list[list[dict[str, Any]]],
    agent_player: int,
) -> dict[str, dict[str, int]]:
    farmer_counts: Counter[str] = Counter()
    hand_counts: Counter[str] = Counter()
    market_counts: Counter[str] = Counter()
    market_units: Counter[str] = Counter()

    for step in replay_steps:
        action = step[agent_player].get("action")
        if not isinstance(action, dict):
            continue

        farmer_action = action.get("farmer")
        if isinstance(farmer_action, list) and farmer_action:
            farmer_counts[str(farmer_action[0])] += 1

        hands_actions = action.get("hands", [])
        if isinstance(hands_actions, list):
            for hand_action in hands_actions:
                if isinstance(hand_action, list) and hand_action:
                    hand_counts[str(hand_action[0])] += 1

        market_orders = action.get("market", [])
        if isinstance(market_orders, list):
            for order in market_orders:
                if isinstance(order, list) and order:
                    operation = str(order[0])
                    market_counts[operation] += 1
                    if len(order) >= 3 and isinstance(order[2], int):
                        item = str(order[1])
                        market_units[f"{operation}:{item}"] += order[2]

    return {
        "farmer": dict(sorted(farmer_counts.items())),
        "hands": dict(sorted(hand_counts.items())),
        "market": dict(sorted(market_counts.items())),
        "market_units": dict(sorted(market_units.items())),
    }


def analyze_route(
    replay_steps: list[list[dict[str, Any]]],
    agent_player: int,
    turns_per_day: int = 24,
) -> dict[str, Any]:
    task_visits: list[dict[str, Any]] = []
    crop_cycles: list[dict[str, Any]] = []
    active_cycles: dict[tuple[int, int], dict[str, Any]] = {}
    pending_harvests: list[dict[str, Any]] = []
    routes_by_day: dict[str, list[dict[str, Any]]] = {}
    tile_task_counts: Counter[str] = Counter()
    movement_turns = 0
    hand_movement_turns = 0
    travel_since_task: dict[int, int] = {}
    current_day: int | None = None

    for replay_index in range(1, len(replay_steps)):
        states = replay_steps[replay_index]
        state = states[agent_player]
        previous_state = replay_steps[replay_index - 1][agent_player]
        observation = previous_state.get("observation", {})
        post_observation = state.get("observation", {})
        day = int(observation.get("day", 0))
        hour = int(observation.get("hour", 0))
        step = int(observation.get("step", replay_index - 1))
        farm = _observed_farm(observation, agent_player)

        if current_day != day:
            current_day = day
            travel_since_task = {}

        action = state.get("action")
        if not isinstance(action, dict):
            continue
        unit_positions = [farm.get("farmer"), *farm.get("hands", [])]
        unit_actions = [action.get("farmer"), *action.get("hands", [])]
        for unit_index, unit_position in enumerate(unit_positions):
            position = _position(unit_position)
            unit_action = (
                unit_actions[unit_index]
                if unit_index < len(unit_actions)
                else ["PASS"]
            )
            operation = (
                str(unit_action[0])
                if isinstance(unit_action, list) and unit_action
                else "PASS"
            )
            travel_since_task.setdefault(unit_index, 0)

            if operation in MOVE_ACTIONS:
                if unit_index == 0:
                    movement_turns += 1
                else:
                    hand_movement_turns += 1
                travel_since_task[unit_index] += 1
            elif operation in TILE_TASK_ACTIONS and position is not None:
                tile_before = _tile_at(farm, position)
                visit = {
                    "step": step,
                    "day": day,
                    "hour": hour,
                    "worker": (
                        "farmer" if unit_index == 0 else f"hand_{unit_index}"
                    ),
                    "task": operation,
                    "tile": list(position),
                    "travel_turns": travel_since_task[unit_index],
                }
                task_visits.append(visit)
                routes_by_day.setdefault(str(day), []).append(visit)
                tile_task_counts[
                    f"{position[0]},{position[1]}:{operation}"
                ] += 1
                travel_since_task[unit_index] = 0
                _record_crop_task(
                    operation,
                    unit_action,
                    tile_before,
                    position,
                    step,
                    day,
                    hour,
                    turns_per_day,
                    active_cycles,
                    crop_cycles,
                    pending_harvests,
                )

        _match_wheat_sales(
            action.get("market"),
            observation,
            step,
            pending_harvests,
        )

        post_day = int(post_observation.get("day", day))
        post_hour = int(post_observation.get("hour", hour))
        post_step = int(post_observation.get("step", step + 1))
        post_farm = _observed_farm(post_observation, agent_player)
        _mark_lost_cycles(
            active_cycles,
            crop_cycles,
            post_farm,
            post_step,
            post_day,
            post_hour,
        )

    for cycle in active_cycles.values():
        cycle["status"] = "unfinished"
        _finish_cycle(cycle)
        crop_cycles.append(cycle)

    travel_turns = [visit["travel_turns"] for visit in task_visits]
    completed = [
        cycle for cycle in crop_cycles if cycle["status"] == "harvested"
    ]
    harvested_units = sum(cycle.get("harvest_units", 0) for cycle in completed)
    sold_units = sum(cycle.get("sold_units", 0) for cycle in completed)
    sale_delay_unit_turns = sum(
        cycle.get("sale_delay_unit_turns", 0) for cycle in completed
    )

    return {
        "movement_turns": movement_turns,
        "hand_movement_turns": hand_movement_turns,
        "all_worker_movement_turns": movement_turns + hand_movement_turns,
        "task_visit_count": len(task_visits),
        "travel_turns_to_tasks": sum(travel_turns),
        "mean_travel_turns_per_task": _mean(travel_turns),
        "max_travel_turns_to_task": max(travel_turns, default=0),
        "tile_task_counts": dict(sorted(tile_task_counts.items())),
        "routes_by_day": routes_by_day,
        "task_visits": task_visits,
        "crop_cycles": crop_cycles,
        "cycles_planted": len(crop_cycles),
        "cycles_harvested": len(completed),
        "cycles_weeded": sum(
            cycle["status"] == "weeded" for cycle in crop_cycles
        ),
        "cycles_unfinished": sum(
            cycle["status"] == "unfinished" for cycle in crop_cycles
        ),
        "same_day_watered_cycles": sum(
            cycle.get("watered_on_planting_day", False)
            for cycle in crop_cycles
        ),
        "missed_planting_day_water_cycles": sum(
            not cycle.get("watered_on_planting_day", False)
            for cycle in crop_cycles
        ),
        "harvested_units": harvested_units,
        "matched_sold_units": sold_units,
        "unmatched_harvested_units": harvested_units - sold_units,
        "mean_harvest_yield": _mean(
            [cycle.get("harvest_units", 0) for cycle in completed]
        ),
        "mean_plant_to_harvest_turns": _mean(
            [cycle["plant_to_harvest_turns"] for cycle in completed]
        ),
        "mean_harvest_to_shed_turns": _mean(
            [cycle["harvest_to_shed_turns"] for cycle in completed]
        ),
        "mean_harvest_to_sale_turns": (
            round(sale_delay_unit_turns / sold_units, 2)
            if sold_units
            else None
        ),
    }


def analyze_livestock(
    replay_steps: list[list[dict[str, Any]]],
    agent_player: int,
) -> dict[str, Any]:
    placements: Counter[str] = Counter()
    losses: Counter[str] = Counter()
    maximum_active: Counter[str] = Counter()
    placement_events: list[dict[str, Any]] = []
    loss_events: list[dict[str, Any]] = []
    final_active: Counter[str] = Counter()

    for replay_index, states in enumerate(replay_steps):
        observation = states[agent_player].get("observation", {})
        farm = _observed_farm(observation, agent_player)
        active: Counter[str] = Counter()
        for row in farm.get("tiles", []):
            for tile in row:
                if isinstance(tile, dict) and tile.get("animal"):
                    active[str(tile["animal"])] += 1
        for animal, quantity in active.items():
            maximum_active[animal] = max(maximum_active[animal], quantity)
        final_active = active

        if replay_index == 0:
            continue
        previous_observation = replay_steps[replay_index - 1][agent_player].get(
            "observation", {}
        )
        previous_farm = _observed_farm(previous_observation, agent_player)
        previous_tiles = previous_farm.get("tiles", [])
        current_tiles = farm.get("tiles", [])
        for y, row in enumerate(current_tiles):
            for x, tile in enumerate(row):
                previous_tile = (
                    previous_tiles[y][x]
                    if y < len(previous_tiles) and x < len(previous_tiles[y])
                    else None
                )
                previous_animal = (
                    str(previous_tile.get("animal"))
                    if isinstance(previous_tile, dict)
                    and previous_tile.get("animal")
                    else None
                )
                current_animal = (
                    str(tile.get("animal"))
                    if isinstance(tile, dict) and tile.get("animal")
                    else None
                )
                if current_animal and current_animal != previous_animal:
                    placements[current_animal] += 1
                    placement_events.append(
                        {
                            "step": int(observation.get("step", replay_index)),
                            "day": int(observation.get("day", 0)),
                            "hour": int(observation.get("hour", 0)),
                            "animal": current_animal,
                            "tile": [x, y],
                        }
                    )
                if previous_animal and current_animal != previous_animal:
                    losses[previous_animal] += 1
                    loss_events.append(
                        {
                            "step": int(observation.get("step", replay_index)),
                            "day": int(observation.get("day", 0)),
                            "hour": int(observation.get("hour", 0)),
                            "animal": previous_animal,
                            "tile": [x, y],
                        }
                    )

    return {
        "placements": dict(sorted(placements.items())),
        "losses": dict(sorted(losses.items())),
        "maximum_active": dict(sorted(maximum_active.items())),
        "final_active": dict(sorted(final_active.items())),
        "placement_events": placement_events,
        "loss_events": loss_events,
    }


def _observed_farm(
    observation: dict[str, Any],
    agent_player: int,
) -> dict[str, Any]:
    farms = observation.get("farms", [])
    if isinstance(farms, list) and agent_player < len(farms):
        farm = farms[agent_player]
        return farm if isinstance(farm, dict) else {}
    return {}


def _position(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return int(value[0]), int(value[1])
    return None


def _tile_at(
    farm: dict[str, Any],
    position: tuple[int, int],
) -> Any:
    tiles = farm.get("tiles", [])
    x, y = position
    if not isinstance(tiles, list) or not (0 <= y < len(tiles)):
        return None
    row = tiles[y]
    if not isinstance(row, list) or not (0 <= x < len(row)):
        return None
    return row[x]


def _mark_lost_cycles(
    active_cycles: dict[tuple[int, int], dict[str, Any]],
    crop_cycles: list[dict[str, Any]],
    farm: dict[str, Any],
    step: int,
    day: int,
    hour: int,
) -> None:
    for position, cycle in list(active_cycles.items()):
        tile = _tile_at(farm, position)
        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            cycle.update(
                {
                    "status": "weeded",
                    "ended_step": step,
                    "ended_day": day,
                    "ended_hour": hour,
                }
            )
            _finish_cycle(cycle)
            crop_cycles.append(cycle)
            del active_cycles[position]


def _record_crop_task(
    operation: str,
    farmer_action: list[Any],
    tile_before: Any,
    position: tuple[int, int],
    step: int,
    day: int,
    hour: int,
    turns_per_day: int,
    active_cycles: dict[tuple[int, int], dict[str, Any]],
    crop_cycles: list[dict[str, Any]],
    pending_harvests: list[dict[str, Any]],
) -> None:
    if operation == "PLANT" and len(farmer_action) >= 2:
        active_cycles[position] = {
            "crop": str(farmer_action[1]),
            "tile": list(position),
            "planted_step": step,
            "planted_day": day,
            "planted_hour": hour,
            "waterings": [],
            "status": "growing",
            "sold_units": 0,
            "sale_delay_unit_turns": 0,
        }
        return

    cycle = active_cycles.get(position)
    if operation == "WATER" and cycle is not None:
        cycle["waterings"].append(
            {"step": step, "day": day, "hour": hour}
        )
        return

    if operation != "HARVEST" or not isinstance(tile_before, dict):
        return
    if tile_before.get("kind") != "PLANT":
        return

    if cycle is None:
        planted_day = int(tile_before.get("planted_day", day))
        cycle = {
            "crop": str(tile_before.get("crop", "UNKNOWN")),
            "tile": list(position),
            "planted_step": planted_day * turns_per_day,
            "planted_day": planted_day,
            "planted_hour": None,
            "waterings": [],
            "status": "growing",
            "sold_units": 0,
            "sale_delay_unit_turns": 0,
        }

    harvest_units = int(tile_before.get("yield_units", 0))
    inferred_shed_step = (day + 1) * turns_per_day
    cycle.update(
        {
            "status": "harvested",
            "harvest_step": step,
            "harvest_day": day,
            "harvest_hour": hour,
            "harvest_units": harvest_units,
            "plant_to_harvest_turns": step - cycle["planted_step"],
            "inferred_shed_step": inferred_shed_step,
            "harvest_to_shed_turns": inferred_shed_step - step,
        }
    )
    _finish_cycle(cycle)
    crop_cycles.append(cycle)
    active_cycles.pop(position, None)
    if harvest_units > 0:
        pending_harvests.append(
            {
                "cycle": cycle,
                "harvest_step": step,
                "remaining": harvest_units,
            }
        )


def _finish_cycle(cycle: dict[str, Any]) -> None:
    planting_day = cycle["planted_day"]
    planting_day_waterings = [
        watering
        for watering in cycle.get("waterings", [])
        if watering["day"] == planting_day
    ]
    cycle["watered_on_planting_day"] = bool(planting_day_waterings)
    cycle["plant_to_first_water_turns"] = (
        planting_day_waterings[0]["step"] - cycle["planted_step"]
        if planting_day_waterings
        else None
    )
    if cycle.get("status") == "harvested":
        cycle["unsold_units"] = (
            cycle.get("harvest_units", 0) - cycle.get("sold_units", 0)
        )


def _match_wheat_sales(
    market_orders: Any,
    observation: dict[str, Any],
    sale_step: int,
    pending_harvests: list[dict[str, Any]],
) -> None:
    if not isinstance(market_orders, list):
        return
    private = observation.get("private", {})
    shed = private.get("shed", {}) if isinstance(private, dict) else {}
    available = int(shed.get("WHEAT", 0)) if isinstance(shed, dict) else 0

    for order in market_orders:
        if not (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "SELL"
            and order[1] == "WHEAT"
        ):
            continue
        units_to_match = min(int(order[2]), available)
        available -= units_to_match
        while units_to_match > 0 and pending_harvests:
            batch = pending_harvests[0]
            matched = min(units_to_match, batch["remaining"])
            cycle = batch["cycle"]
            delay = sale_step - batch["harvest_step"]
            cycle["sold_units"] += matched
            cycle["sale_delay_unit_turns"] += matched * delay
            cycle.setdefault("first_sale_step", sale_step)
            cycle["last_sale_step"] = sale_step
            cycle["unsold_units"] = cycle["harvest_units"] - cycle["sold_units"]
            batch["remaining"] -= matched
            units_to_match -= matched
            if batch["remaining"] == 0:
                pending_harvests.pop(0)


def _mean(values: list[int]) -> float | None:
    return round(fmean(values), 2) if values else None


def inventory_snapshot(observation: dict[str, Any]) -> dict[str, dict[str, int]]:
    private = observation.get("private", {})
    carried: Counter[str] = Counter()
    inventories = private.get("inventories", [])
    if isinstance(inventories, list):
        for inventory in inventories:
            if isinstance(inventory, dict):
                carried.update(_positive_items(inventory))

    return {
        "shed": _positive_items(private.get("shed", {})),
        "carried": dict(sorted(carried.items())),
        "seeds": _positive_items(private.get("seeds", {})),
    }


def _positive_items(items: Any) -> dict[str, int]:
    if not isinstance(items, dict):
        return {}
    return {
        str(item): int(quantity)
        for item, quantity in sorted(items.items())
        if isinstance(quantity, (int, float)) and quantity > 0
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [
        record for record in records if record["result"] != "error"
    ]
    wins = sum(record["result"] == "win" for record in records)
    losses = sum(record["result"] == "loss" for record in records)
    ties = sum(record["result"] == "tie" for record in records)
    errors = sum(record["result"] == "error" for record in records)

    agent_rewards = [
        float(record["agent_reward"])
        for record in completed
    ]
    opponent_rewards = [
        float(record["opponent_reward"])
        for record in completed
    ]
    margins = [
        agent_reward - opponent_reward
        for agent_reward, opponent_reward in zip(
            agent_rewards,
            opponent_rewards,
            strict=True,
        )
    ]

    summary: dict[str, Any] = {
        "games": len(records),
        "completed": len(completed),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "errors": errors,
        "win_rate": _rate(wins, len(completed)),
        "score_rate": _rate(wins + 0.5 * ties, len(completed)),
        "agent_actions": _sum_action_counts(records),
        "route_analysis": _sum_route_analysis(records),
        "livestock_analysis": _sum_livestock_analysis(records),
        "final_inventory_totals": _sum_final_inventory(records),
        "by_player": {
            str(player): _result_counts(
                [
                    record
                    for record in records
                    if record["agent_player"] == player
                ]
            )
            for player in (0, 1)
        },
    }
    summary.update(_reward_stats(agent_rewards, opponent_rewards, margins))
    return summary


def _rate(numerator: float, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _result_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "games": len(records),
        "wins": sum(record["result"] == "win" for record in records),
        "losses": sum(record["result"] == "loss" for record in records),
        "ties": sum(record["result"] == "tie" for record in records),
        "errors": sum(record["result"] == "error" for record in records),
    }


def _reward_stats(
    agent_rewards: list[float],
    opponent_rewards: list[float],
    margins: list[float],
) -> dict[str, float | None]:
    if not agent_rewards:
        return {
            "mean_agent_coins": None,
            "min_agent_coins": None,
            "max_agent_coins": None,
            "mean_opponent_coins": None,
            "mean_margin": None,
        }
    return {
        "mean_agent_coins": round(fmean(agent_rewards), 2),
        "min_agent_coins": min(agent_rewards),
        "max_agent_coins": max(agent_rewards),
        "mean_opponent_coins": round(fmean(opponent_rewards), 2),
        "mean_margin": round(fmean(margins), 2),
    }


def _sum_action_counts(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    totals: dict[str, Counter[str]] = {
        "farmer": Counter(),
        "hands": Counter(),
        "market": Counter(),
        "market_units": Counter(),
    }
    for record in records:
        actions = record.get("agent_actions", {})
        for category in totals:
            totals[category].update(actions.get(category, {}))
    return {
        category: dict(sorted(counts.items()))
        for category, counts in totals.items()
    }


def _sum_final_inventory(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    totals: dict[str, Counter[str]] = {
        "shed": Counter(),
        "carried": Counter(),
        "seeds": Counter(),
    }
    for record in records:
        inventory = record.get("final_inventory", {})
        for location in totals:
            totals[location].update(inventory.get(location, {}))
    return {
        location: dict(sorted(items.items()))
        for location, items in totals.items()
    }


def _sum_route_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    analyses = [
        record["route_analysis"]
        for record in records
        if isinstance(record.get("route_analysis"), dict)
    ]
    tile_tasks: Counter[str] = Counter()
    for analysis in analyses:
        tile_tasks.update(analysis.get("tile_task_counts", {}))

    harvested_units = sum(
        analysis.get("harvested_units", 0) for analysis in analyses
    )
    sold_units = sum(
        analysis.get("matched_sold_units", 0) for analysis in analyses
    )
    weighted_sale_delay = 0.0
    for analysis in analyses:
        delay = analysis.get("mean_harvest_to_sale_turns")
        units = analysis.get("matched_sold_units", 0)
        if delay is not None:
            weighted_sale_delay += delay * units

    return {
        "games": len(analyses),
        "movement_turns": sum(
            analysis.get("movement_turns", 0) for analysis in analyses
        ),
        "hand_movement_turns": sum(
            analysis.get("hand_movement_turns", 0)
            for analysis in analyses
        ),
        "all_worker_movement_turns": sum(
            analysis.get("all_worker_movement_turns", 0)
            for analysis in analyses
        ),
        "task_visit_count": sum(
            analysis.get("task_visit_count", 0) for analysis in analyses
        ),
        "travel_turns_to_tasks": sum(
            analysis.get("travel_turns_to_tasks", 0) for analysis in analyses
        ),
        "max_travel_turns_to_task": max(
            (
                analysis.get("max_travel_turns_to_task", 0)
                for analysis in analyses
            ),
            default=0,
        ),
        "cycles_planted": sum(
            analysis.get("cycles_planted", 0) for analysis in analyses
        ),
        "cycles_harvested": sum(
            analysis.get("cycles_harvested", 0) for analysis in analyses
        ),
        "cycles_weeded": sum(
            analysis.get("cycles_weeded", 0) for analysis in analyses
        ),
        "cycles_unfinished": sum(
            analysis.get("cycles_unfinished", 0) for analysis in analyses
        ),
        "same_day_watered_cycles": sum(
            analysis.get("same_day_watered_cycles", 0)
            for analysis in analyses
        ),
        "missed_planting_day_water_cycles": sum(
            analysis.get("missed_planting_day_water_cycles", 0)
            for analysis in analyses
        ),
        "harvested_units": harvested_units,
        "matched_sold_units": sold_units,
        "unmatched_harvested_units": harvested_units - sold_units,
        "mean_harvest_to_sale_turns": (
            round(weighted_sale_delay / sold_units, 2)
            if sold_units
            else None
        ),
        "tile_task_counts": dict(sorted(tile_tasks.items())),
    }


def run_game(
    make: Any,
    agent_input: AgentInput,
    opponent: str,
    episode_steps: int,
    seed: int,
    agent_player: int,
) -> dict[str, Any]:
    agents: list[Any] = [agent_input, opponent]
    if agent_player == 1:
        agents.reverse()

    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": episode_steps, "seed": seed},
        debug=False,
    )
    environment.run(agents)
    replay = environment.toJSON()
    final_states = replay["steps"][-1]
    opponent_player = 1 - agent_player
    agent_state = final_states[agent_player]
    opponent_state = final_states[opponent_player]

    agent_reward = agent_state.get("reward")
    opponent_reward = opponent_state.get("reward")
    agent_status = str(agent_state.get("status"))
    opponent_status = str(opponent_state.get("status"))

    return {
        "seed": seed,
        "agent_player": agent_player,
        "agent_reward": agent_reward,
        "opponent_reward": opponent_reward,
        "agent_status": agent_status,
        "opponent_status": opponent_status,
        "result": classify_result(
            agent_reward,
            opponent_reward,
            agent_status,
            opponent_status,
        ),
        "agent_actions": count_actions(replay["steps"], agent_player),
        "route_analysis": analyze_route(
            replay["steps"],
            agent_player,
            int(replay.get("configuration", {}).get("turnsPerDay", 24)),
        ),
        "livestock_analysis": analyze_livestock(
            replay["steps"],
            agent_player,
        ),
        "final_inventory": inventory_snapshot(
            agent_state.get("observation", {})
        ),
    }


def _sum_livestock_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    placements: Counter[str] = Counter()
    losses: Counter[str] = Counter()
    maximum_active: Counter[str] = Counter()
    pre_endgame_losses: Counter[str] = Counter()
    for record in records:
        analysis = record.get("livestock_analysis", {})
        placements.update(analysis.get("placements", {}))
        losses.update(analysis.get("losses", {}))
        pre_endgame_losses.update(
            event["animal"]
            for event in analysis.get("loss_events", [])
            if int(event.get("day", 0)) < 29
        )
        for animal, quantity in analysis.get("maximum_active", {}).items():
            maximum_active[animal] = max(maximum_active[animal], quantity)
    return {
        "placements": dict(sorted(placements.items())),
        "losses": dict(sorted(losses.items())),
        "pre_endgame_losses": dict(sorted(pre_endgame_losses.items())),
        "maximum_active": dict(sorted(maximum_active.items())),
        "final_active": {
            animal: sum(
                int(record.get("livestock_analysis", {})
                    .get("final_active", {})
                    .get(animal, 0))
                for record in records
            )
            for animal in sorted(
                {
                    animal
                    for record in records
                    for animal in record.get("livestock_analysis", {})
                    .get("final_active", {})
                }
            )
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent",
        type=Path,
        default=PROJECT_ROOT / "main.py",
        help="agent file to benchmark (default: main.py)",
    )
    parser.add_argument(
        "--opponent",
        default="starter",
        help="built-in opponent or agent file (default: starter)",
    )
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument(
        "--target-wheat-tiles",
        type=int,
        help="locally evaluate this wheat target through agent.decide",
    )
    parser.add_argument(
        "--target-daily-hands",
        type=int,
        help="locally evaluate this daily hand target through agent.decide",
    )
    parser.add_argument(
        "--care-enabled",
        action="store_true",
        help="locally evaluate animal CARE through agent.decide",
    )
    parser.add_argument("--target-cows", type=int)
    parser.add_argument("--target-sheep", type=int)
    parser.add_argument(
        "--feed-daily",
        action="store_true",
        help="locally feed active animals every service day",
    )
    parser.add_argument("--target-extra-land", type=int)
    parser.add_argument(
        "--adaptive-hands",
        action="store_true",
        help="use the replay-grounded daily workforce schedule",
    )
    parser.add_argument(
        "--last-planting-day",
        type=int,
        help="locally stop seed buying and planting after this day",
    )
    parser.add_argument(
        "--harvest-watered-current-first",
        action="store_true",
        help="locally harvest a mature watered current tile before moving",
    )
    parser.add_argument("--minimum-wheat-sale-price", type=int)
    parser.add_argument("--maximum-wheat-holdings", type=int)
    parser.add_argument("--wheat-liquidation-day", type=int)
    parser.add_argument(
        "--one-position",
        action="store_true",
        help="run only as player 0 instead of testing both positions",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional JSON output path",
    )
    return parser.parse_args()


def load_simulator() -> tuple[Any, str]:
    try:
        package = importlib.import_module("kaggle_environments")
    except ModuleNotFoundError as error:
        raise SystemExit(
            "kaggle-environments is not installed. See README.md."
        ) from error
    return package.make, str(package.__version__)


def load_parameterized_agent(
    agent_path: Path,
    parameters: dict[str, Any],
) -> AgentInput:
    agent_digest = hashlib.sha256(agent_path.read_bytes()).hexdigest()
    module_name = f"benchmark_agent_{agent_digest}"
    spec = importlib.util.spec_from_file_location(module_name, agent_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load agent module: {agent_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    decision_function = getattr(module, "decide", None)
    if not callable(decision_function):
        raise SystemExit(
            "--target-wheat-tiles requires the agent file to define decide()"
        )

    def parameterized_agent(observation: dict[str, Any]) -> dict[str, Any]:
        return decision_function(observation, **parameters)

    return parameterized_agent


def load_agent_callable(agent_path: Path) -> AgentInput:
    agent_digest = hashlib.sha256(agent_path.read_bytes()).hexdigest()
    module_name = f"benchmark_opponent_{agent_digest}"
    spec = importlib.util.spec_from_file_location(module_name, agent_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load opponent module: {agent_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    opponent_agent = getattr(module, "agent", None)
    if not callable(opponent_agent):
        raise SystemExit(f"Opponent file does not define agent(): {agent_path}")
    return opponent_agent


def default_output_path(args: argparse.Namespace) -> Path:
    final_seed = args.seed_start + args.seed_count - 1
    target = (
        f"-wheat-{args.target_wheat_tiles}"
        if args.target_wheat_tiles is not None
        else ""
    )
    cutoff = (
        f"-plant-through-{args.last_planting_day}"
        if args.last_planting_day is not None
        else ""
    )
    finish_tile = (
        "-finish-tile"
        if args.harvest_watered_current_first
        else ""
    )
    selling = (
        f"-sell-{args.minimum_wheat_sale_price}"
        f"-cap-{args.maximum_wheat_holdings}"
        f"-liquidate-{args.wheat_liquidation_day}"
        if args.minimum_wheat_sale_price is not None
        else ""
    )
    filename = (
        f"{args.agent.stem}-vs-{args.opponent}-"
        f"seeds-{args.seed_start}-{final_seed}"
        f"{target}{cutoff}{finish_tile}{selling}.json"
    )
    return PROJECT_ROOT / "artifacts" / "benchmarks" / filename


def print_summary(summary: dict[str, Any]) -> None:
    print("\nSummary")
    print(
        "  W/L/T/E: "
        f"{summary['wins']}/{summary['losses']}/"
        f"{summary['ties']}/{summary['errors']}"
    )
    print(f"  Win rate: {summary['win_rate']}")
    print(f"  Score rate: {summary['score_rate']}")
    print(f"  Mean coins: {summary['mean_agent_coins']}")
    print(f"  Mean opponent coins: {summary['mean_opponent_coins']}")
    print(f"  Mean margin: {summary['mean_margin']}")


def write_report(
    output_path: Path,
    metadata: dict[str, Any],
    records: list[dict[str, Any]],
    expected_games: int,
) -> dict[str, Any]:
    report = {
        **metadata,
        "complete": len(records) == expected_games,
        "summary": summarize(records),
        "games": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    args = parse_args()
    if args.seed_count < 1:
        raise SystemExit("--seed-count must be at least 1")
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")
    if args.target_wheat_tiles is not None and args.target_wheat_tiles < 1:
        raise SystemExit("--target-wheat-tiles must be at least 1")
    if args.target_daily_hands is not None and args.target_daily_hands < 0:
        raise SystemExit("--target-daily-hands cannot be negative")
    if args.target_cows is not None and args.target_cows < 0:
        raise SystemExit("--target-cows cannot be negative")
    if args.target_sheep is not None and args.target_sheep < 0:
        raise SystemExit("--target-sheep cannot be negative")
    if args.target_extra_land is not None and not (
        0 <= args.target_extra_land <= 3
    ):
        raise SystemExit("--target-extra-land must be between 0 and 3")
    if args.last_planting_day is not None and args.last_planting_day < 0:
        raise SystemExit("--last-planting-day cannot be negative")
    if (
        args.minimum_wheat_sale_price is not None
        and args.minimum_wheat_sale_price < 1
    ):
        raise SystemExit("--minimum-wheat-sale-price must be at least 1")
    if args.maximum_wheat_holdings is not None and not (
        1 <= args.maximum_wheat_holdings <= 100
    ):
        raise SystemExit("--maximum-wheat-holdings must be between 1 and 100")
    if args.wheat_liquidation_day is not None and not (
        0 <= args.wheat_liquidation_day <= 29
    ):
        raise SystemExit("--wheat-liquidation-day must be between 0 and 29")

    agent_path = args.agent.resolve()
    if not agent_path.is_file():
        raise SystemExit(f"Agent file does not exist: {agent_path}")

    make, simulator_version = load_simulator()
    agent_input: AgentInput = str(agent_path)
    opponent_input = args.opponent
    opponent_path = Path(args.opponent)
    if args.opponent not in ("pass", "random", "starter"):
        opponent_path = opponent_path.resolve()
        if not opponent_path.is_file():
            raise SystemExit(f"Opponent file does not exist: {opponent_path}")
        opponent_input = load_agent_callable(opponent_path)
    parameters: dict[str, Any] = {}
    if args.target_wheat_tiles is not None:
        parameters["target_wheat_tiles"] = args.target_wheat_tiles
    if args.target_daily_hands is not None:
        parameters["target_daily_hands"] = args.target_daily_hands
    if args.care_enabled:
        parameters["care_enabled"] = True
    if args.target_cows is not None:
        parameters["target_cows"] = args.target_cows
    if args.target_sheep is not None:
        parameters["target_sheep"] = args.target_sheep
    if args.feed_daily:
        parameters["feed_daily"] = True
    if args.target_extra_land is not None:
        parameters["target_extra_land"] = args.target_extra_land
    if args.adaptive_hands:
        parameters["adaptive_hands"] = True
    if args.last_planting_day is not None:
        parameters["last_planting_day"] = args.last_planting_day
    if args.harvest_watered_current_first:
        parameters["harvest_watered_current_first"] = True
    if args.minimum_wheat_sale_price is not None:
        parameters["minimum_wheat_sale_price"] = args.minimum_wheat_sale_price
    if args.maximum_wheat_holdings is not None:
        parameters["maximum_wheat_holdings"] = args.maximum_wheat_holdings
    if args.wheat_liquidation_day is not None:
        parameters["wheat_liquidation_day"] = args.wheat_liquidation_day
    if parameters:
        agent_input = load_parameterized_agent(agent_path, parameters)

    players = (0,) if args.one_position else (0, 1)
    expected_games = args.seed_count * len(players)
    output_path = args.output or default_output_path(args)
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent": str(agent_path),
        "agent_sha256": hashlib.sha256(agent_path.read_bytes()).hexdigest(),
        "opponent": args.opponent,
        "episode_steps": args.steps,
        "seed_start": args.seed_start,
        "seed_count": args.seed_count,
        "positions": list(players),
        "parameters": parameters,
        "simulator_version": simulator_version,
    }
    records: list[dict[str, Any]] = []
    report: dict[str, Any] = {}

    for seed in range(args.seed_start, args.seed_start + args.seed_count):
        for agent_player in players:
            record = run_game(
                make,
                agent_input,
                opponent_input,
                args.steps,
                seed,
                agent_player,
            )
            records.append(record)
            print(
                f"seed={seed:>3} player={agent_player} "
                f"result={record['result']:<5} "
                f"coins={record['agent_reward']} "
                f"opponent={record['opponent_reward']}"
            )
            report = write_report(
                output_path,
                metadata,
                records,
                expected_games,
            )

    print_summary(report["summary"])
    print(f"  Report: {output_path}")


if __name__ == "__main__":
    main()
