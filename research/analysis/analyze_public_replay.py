"""Summarize workforce, land, crop, animal, and market strategy in a replay."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ANIMAL_PRODUCTS = {
    "GOOSE": "EGG",
    "COW": "MILK",
    "SHEEP": "WOOL",
}


def _position(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return int(value[0]), int(value[1])
    return None


def _tile_at(
    farm: dict[str, Any],
    position: tuple[int, int] | None,
) -> Any:
    if position is None:
        return None
    x, y = position
    tiles = farm.get("tiles", [])
    if not isinstance(tiles, list) or not (0 <= y < len(tiles)):
        return None
    row = tiles[y]
    if not isinstance(row, list) or not (0 <= x < len(row)):
        return None
    return row[x]


def _farm(observation: dict[str, Any], player: int) -> dict[str, Any]:
    farms = observation.get("farms", [])
    if isinstance(farms, list) and player < len(farms):
        farm = farms[player]
        return farm if isinstance(farm, dict) else {}
    return {}


def _board_counts(farm: dict[str, Any]) -> dict[str, Counter[str]]:
    counts = {
        "crops": Counter(),
        "animals": Counter(),
        "structures": Counter(),
        "weeds": Counter(),
    }
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                counts["crops"][str(tile.get("crop", "UNKNOWN"))] += 1
            if tile.get("animal"):
                counts["animals"][str(tile["animal"])] += 1
            if tile.get("kind") in ("COOP", "PASTURE"):
                counts["structures"][str(tile["kind"])] += 1
            if tile.get("kind") == "WEED":
                counts["weeds"]["WEED"] += 1
    return counts


def _tile_signature(tile: Any) -> tuple[Any, ...]:
    if not isinstance(tile, dict):
        return (tile,)
    return (
        tile.get("kind"),
        tile.get("crop"),
        tile.get("planted_day"),
        tile.get("animal"),
        tile.get("placed_day"),
    )


def _target_for_action(action: list[Any], tile: Any) -> str | None:
    operation = str(action[0])
    if operation in ("PLANT", "PLACE", "PICKUP") and len(action) >= 2:
        return str(action[1])
    if not isinstance(tile, dict):
        return None
    if operation == "HARVEST":
        if tile.get("kind") == "PLANT":
            return str(tile.get("crop", "UNKNOWN"))
        animal = tile.get("animal")
        return ANIMAL_PRODUCTS.get(str(animal), str(animal))
    if operation in ("FEED", "CARE", "COLLECT_FERTILIZER"):
        return str(tile.get("animal", "UNKNOWN"))
    if operation == "FERTILIZE":
        return str(tile.get("crop", "UNKNOWN"))
    return None


def _positive_items(items: Any) -> dict[str, int]:
    if not isinstance(items, dict):
        return {}
    return {
        str(item): int(quantity)
        for item, quantity in sorted(items.items())
        if isinstance(quantity, (int, float)) and quantity > 0
    }


def _final_inventory(observation: dict[str, Any]) -> dict[str, Any]:
    private = observation.get("private", {})
    carried: Counter[str] = Counter()
    for inventory in private.get("inventories", []):
        carried.update(_positive_items(inventory))
    return {
        "shed": _positive_items(private.get("shed", {})),
        "carried": dict(sorted(carried.items())),
        "seeds": _positive_items(private.get("seeds", {})),
    }


def _team_names(replay: dict[str, Any], players: int) -> list[str]:
    info = replay.get("info", {})
    names = info.get("TeamNames") or []
    return [
        str(names[player]) if player < len(names) else f"player_{player}"
        for player in range(players)
    ]


def analyze_player(
    replay: dict[str, Any],
    player: int,
    team_name: str,
) -> dict[str, Any]:
    steps = replay["steps"]
    configuration = replay.get("configuration", {})
    turns_per_day = int(configuration.get("turnsPerDay", 24))
    board_size = int(configuration.get("boardSize", 10))
    quadrant_tiles = (board_size // 2) ** 2
    action_counts = {
        "farmer": Counter(),
        "hands": Counter(),
        "all_workers": Counter(),
    }
    daily_action_counts: dict[int, Counter[str]] = {}
    targeted_actions: Counter[str] = Counter()
    harvest_ages: Counter[str] = Counter()
    market_orders: Counter[str] = Counter()
    market_units: Counter[str] = Counter()
    daily_hires: Counter[int] = Counter()
    land_purchases: list[dict[str, int]] = []
    animal_purchase_events: list[dict[str, Any]] = []
    structure_events: list[dict[str, Any]] = []
    successful_plants: Counter[str] = Counter()
    successful_plants_by_day: dict[int, Counter[str]] = {}
    successful_animals: Counter[str] = Counter()
    lost_animals: Counter[str] = Counter()
    first_crop_step: dict[str, int] = {}
    first_animal_step: dict[str, int] = {}
    day_start_bank: dict[int, float] = {}
    maximum_board = {
        "crops": Counter(),
        "animals": Counter(),
        "structures": Counter(),
        "weeds": Counter(),
    }
    maximum_concurrent_board = Counter()
    peak_productive_utilization: dict[str, Any] = {}
    daily_peak_productive: dict[int, dict[str, Any]] = {}
    tile_turns = Counter()
    maximum_hands = 0
    market_order_entries_per_turn = 0

    for record_index in range(1, len(steps)):
        state = steps[record_index][player]
        before = steps[record_index - 1][player].get("observation", {})
        after = state.get("observation", {})
        before_farm = _farm(before, player)
        after_farm = _farm(after, player)
        day = int(before.get("day", (record_index - 1) // turns_per_day))
        hour = int(before.get("hour", (record_index - 1) % turns_per_day))
        decision_step = int(before.get("step", record_index - 1))
        if hour == 0 and day not in day_start_bank:
            day_start_bank[day] = float(before_farm.get("money", 0))

        action = state.get("action")
        action = action if isinstance(action, dict) else {}
        unit_actions = [action.get("farmer"), *action.get("hands", [])]
        positions = [
            before_farm.get("farmer"),
            *before_farm.get("hands", []),
        ]
        for unit_index, unit_action in enumerate(unit_actions):
            if not isinstance(unit_action, list) or not unit_action:
                continue
            operation = str(unit_action[0])
            category = "farmer" if unit_index == 0 else "hands"
            action_counts[category][operation] += 1
            action_counts["all_workers"][operation] += 1
            daily_action_counts.setdefault(day, Counter())[operation] += 1
            position = _position(
                positions[unit_index]
                if unit_index < len(positions)
                else None
            )
            target = _target_for_action(
                unit_action,
                _tile_at(before_farm, position),
            )
            if target is not None:
                targeted_actions[f"{operation}:{target}"] += 1
            tile = _tile_at(before_farm, position)
            if (
                operation == "HARVEST"
                and isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and isinstance(tile.get("planted_day"), int)
            ):
                harvest_ages[
                    f"{tile.get('crop', 'UNKNOWN')}:{day - tile['planted_day']}"
                ] += 1

        orders = action.get("market", [])
        orders = orders if isinstance(orders, list) else []
        market_order_entries_per_turn = max(
            market_order_entries_per_turn,
            len(orders),
        )
        for order in orders:
            if not isinstance(order, list) or not order:
                continue
            operation = str(order[0])
            market_orders[operation] += 1
            if operation == "HIRE":
                daily_hires[day] += 1
            if operation == "BUY_LAND":
                land_purchases.append(
                    {"step": decision_step, "day": day, "hour": hour}
                )
            if len(order) >= 3:
                item = str(order[1])
                quantity = int(order[2])
                market_units[f"{operation}:{item}"] += quantity
                if operation == "BUY_ANIMAL":
                    animal_purchase_events.append(
                        {
                            "step": decision_step,
                            "day": day,
                            "hour": hour,
                            "animal": item,
                            "quantity": quantity,
                        }
                    )

        before_tiles = before_farm.get("tiles", [])
        after_tiles = after_farm.get("tiles", [])
        for y, after_row in enumerate(after_tiles):
            for x, after_tile in enumerate(after_row):
                before_tile = (
                    before_tiles[y][x]
                    if y < len(before_tiles) and x < len(before_tiles[y])
                    else None
                )
                if _tile_signature(before_tile) == _tile_signature(after_tile):
                    continue
                if isinstance(after_tile, dict):
                    if after_tile.get("kind") == "PLANT":
                        crop = str(after_tile.get("crop", "UNKNOWN"))
                        successful_plants[crop] += 1
                        successful_plants_by_day.setdefault(
                            day,
                            Counter(),
                        )[crop] += 1
                        first_crop_step.setdefault(crop, decision_step)
                    animal = after_tile.get("animal")
                    if animal and not (
                        isinstance(before_tile, dict)
                        and before_tile.get("animal") == animal
                    ):
                        animal = str(animal)
                        successful_animals[animal] += 1
                        first_animal_step.setdefault(animal, decision_step)
                    if (
                        before_tile is None
                        and after_tile.get("kind") in ("COOP", "PASTURE")
                    ):
                        structure_events.append(
                            {
                                "step": decision_step,
                                "day": day,
                                "hour": hour,
                                "structure": str(after_tile["kind"]),
                                "tile": [x, y],
                            }
                        )
                if (
                    isinstance(before_tile, dict)
                    and before_tile.get("animal")
                    and not (
                        isinstance(after_tile, dict)
                        and after_tile.get("animal")
                    )
                ):
                    lost_animals[str(before_tile["animal"])] += 1

        counts = _board_counts(after_farm)
        for category, values in counts.items():
            for item, quantity in values.items():
                maximum_board[category][item] = max(
                    maximum_board[category][item],
                    quantity,
                )
        concurrent = {
            category: sum(values.values())
            for category, values in counts.items()
        }
        productive_tiles = concurrent["crops"] + concurrent["structures"]
        unlocked_quadrants = after_farm.get("unlocked_quadrants", [])
        owned_tiles = quadrant_tiles * len(unlocked_quadrants)
        utilization = productive_tiles / owned_tiles if owned_tiles else 0.0
        snapshot = {
            "step": decision_step,
            "day": day,
            "hour": hour,
            **concurrent,
            "productive_tiles": productive_tiles,
            "owned_tiles": owned_tiles,
            "productive_utilization": round(utilization, 4),
        }
        for category, quantity in concurrent.items():
            maximum_concurrent_board[category] = max(
                maximum_concurrent_board[category],
                quantity,
            )
        maximum_concurrent_board["productive_tiles"] = max(
            maximum_concurrent_board["productive_tiles"],
            productive_tiles,
        )
        if (
            not peak_productive_utilization
            or utilization
            > peak_productive_utilization["productive_utilization"]
        ):
            peak_productive_utilization = snapshot
        if (
            day not in daily_peak_productive
            or productive_tiles
            > daily_peak_productive[day]["productive_tiles"]
        ):
            daily_peak_productive[day] = snapshot
        tile_turns.update(
            {
                "crops": concurrent["crops"],
                "animals": concurrent["animals"],
                "structures": concurrent["structures"],
                "weeds": concurrent["weeds"],
                "productive_tiles": productive_tiles,
                "owned_tiles": owned_tiles,
            }
        )
        maximum_hands = max(
            maximum_hands,
            len(after_farm.get("hands", [])),
        )

    final_state = steps[-1][player]
    final_observation = final_state.get("observation", {})
    final_farm = _farm(final_observation, player)
    final_board = _board_counts(final_farm)
    terminal_reward = final_state.get("reward")
    actions_by_day = []
    for day in sorted(daily_action_counts):
        counts = daily_action_counts[day]
        worker_actions = sum(counts.values())
        passes = counts["PASS"]
        actions_by_day.append(
            {
                "day": day,
                "worker_actions": worker_actions,
                "passes": passes,
                "pass_rate": round(passes / worker_actions, 4)
                if worker_actions
                else 0.0,
                "counts": dict(sorted(counts.items())),
            }
        )
    return {
        "player": player,
        "team_name": team_name,
        "reward": terminal_reward,
        "status": final_state.get("status"),
        "action_counts": {
            category: dict(sorted(values.items()))
            for category, values in action_counts.items()
        },
        "actions_by_day": actions_by_day,
        "targeted_actions": dict(sorted(targeted_actions.items())),
        "crop_harvest_ages": dict(sorted(harvest_ages.items())),
        "market_order_counts": dict(sorted(market_orders.items())),
        "market_units_requested": dict(sorted(market_units.items())),
        "maximum_market_order_entries_in_turn": market_order_entries_per_turn,
        "workforce": {
            "hires": sum(daily_hires.values()),
            "hires_by_day": {
                str(day): daily_hires[day]
                for day in sorted(daily_hires)
            },
            "maximum_simultaneous_hands": maximum_hands,
        },
        "land_purchases": land_purchases,
        "animal_purchase_events": animal_purchase_events,
        "successful_board_transitions": {
            "plants": dict(sorted(successful_plants.items())),
            "plants_by_day": {
                str(day): dict(sorted(counts.items()))
                for day, counts in sorted(successful_plants_by_day.items())
            },
            "animal_placements": dict(sorted(successful_animals.items())),
            "animal_losses": dict(sorted(lost_animals.items())),
            "structures": structure_events,
            "first_crop_step": dict(sorted(first_crop_step.items())),
            "first_animal_step": dict(sorted(first_animal_step.items())),
        },
        "maximum_board_counts": {
            category: dict(sorted(values.items()))
            for category, values in maximum_board.items()
        },
        "board_utilization": {
            "maximum_concurrent_counts": dict(
                sorted(maximum_concurrent_board.items())
            ),
            "peak_productive_utilization": peak_productive_utilization,
            "daily_peak_productive_tiles": [
                daily_peak_productive[day]
                for day in sorted(daily_peak_productive)
            ],
            "tile_days": {
                category: round(quantity / turns_per_day, 2)
                for category, quantity in sorted(tile_turns.items())
            },
            "season_productive_capacity_utilization": round(
                tile_turns["productive_tiles"] / tile_turns["owned_tiles"],
                4,
            ) if tile_turns["owned_tiles"] else 0.0,
        },
        "bank_at_day_start": [
            {"day": day, "money": day_start_bank[day]}
            for day in sorted(day_start_bank)
        ],
        "terminal": {
            "money": float(final_farm.get("money", 0)),
            "unlocked_quadrants": final_farm.get("unlocked_quadrants", []),
            "board_counts": {
                category: dict(sorted(values.items()))
                for category, values in final_board.items()
            },
            "inventory": _final_inventory(final_observation),
        },
    }


def analyze_replay(replay: dict[str, Any]) -> dict[str, Any]:
    steps = replay.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise ValueError("Replay has no steps")
    players = len(steps[0])
    names = _team_names(replay, players)
    analyses = [
        analyze_player(replay, player, names[player])
        for player in range(players)
    ]
    return {
        "metadata": {
            "environment": replay.get("name"),
            "simulator_version": replay.get("module_version"),
            "episode_id": replay.get("info", {}).get("EpisodeId"),
            "seed": replay.get("info", {}).get("seed"),
            "records": len(steps),
            "teams": names,
            "rewards": replay.get("rewards"),
        },
        "players": analyses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    replay = json.loads(args.replay.read_text(encoding="utf-8"))
    analysis = analyze_replay(replay)
    output = args.output or args.replay.with_name(
        args.replay.stem.replace("-replay", "-strategy") + ".json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(f"Strategy analysis written to {output}")


if __name__ == "__main__":
    main()
