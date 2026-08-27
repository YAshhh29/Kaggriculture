"""Convert a Kaggriculture replay into a transparent turn-by-turn audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


SEED_COSTS = {
    "WHEAT": 10,
    "CARROT": 20,
    "TOMATO": 50,
    "STRAWBERRY": 100,
    "MELON": 80,
}
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
SUPPORTED_CASH_ORDERS = {"BUY_SEED", "SELL"}
DEFAULT_MARKET_POLICY = [
    "sell shed wheat when its market price is at least 35",
    "sell shed wheat when holdings reach 72 units",
    "liquidate all remaining shed wheat from day 25 onward",
    "buy seeds needed to maintain six concurrent wheat crops",
    "stop seed buying and planting after day 24",
]


def build_audit(
    replay: dict[str, Any],
    player: int = 0,
    source_replay: str | None = None,
    agent_path: Path | None = None,
    market_policy: list[str] | None = None,
) -> dict[str, Any]:
    steps = replay.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise ValueError("Replay has no steps.")
    if player < 0 or player >= len(steps[0]):
        raise ValueError(f"Player index is out of range: {player}")

    configuration = replay.get("configuration", {})
    turns_per_day = int(configuration.get("turnsPerDay", 24))
    records = [_initial_record(steps[0][player], player)]
    transitions = [
        _transition_record(
            record_index,
            steps[record_index - 1][player],
            steps[record_index][player],
            player,
        )
        for record_index in range(1, len(steps))
    ]
    _annotate_movement_destinations(transitions)
    records.extend(transitions)

    final_states = steps[-1]
    opponent = 1 - player if len(final_states) == 2 else None
    final_state = final_states[player]
    opponent_reward = (
        final_states[opponent].get("reward")
        if opponent is not None
        else None
    )
    summary = summarize_audit(records, turns_per_day)
    final_reward = final_state.get("reward")
    result = _result(final_reward, opponent_reward, final_state.get("status"))

    metadata: dict[str, Any] = {
        "source_replay": source_replay,
        "environment": replay.get("name"),
        "simulator_version": replay.get("module_version")
        or replay.get("version"),
        "player": player,
        "opponent_player": opponent,
        "configuration": configuration,
        "replay_records": len(steps),
        "initial_state_records": 1,
        "executed_transitions": len(transitions),
        "record_index_range": [0, len(steps) - 1],
        "replay_semantics": (
            "Record 0 is initialized state. For record i > 0, its action "
            "transforms record i-1 observation into record i observation."
        ),
    }
    if agent_path is not None:
        metadata["agent_file"] = str(agent_path.resolve())
        metadata["agent_sha256"] = hashlib.sha256(
            agent_path.read_bytes()
        ).hexdigest()

    return {
        "metadata": metadata,
        "score": {
            "final_reward": final_reward,
            "opponent_reward": opponent_reward,
            "status": final_state.get("status"),
            "result": result,
        },
        "policy_under_audit": {
            "objective": "maximize banked coins at the end of the episode",
            "farmer_priority": [
                "rescue wheat with a missed watering day",
                "water all other unwatered wheat",
                "harvest mature wheat",
                "plant wheat while planting remains open",
                "pass",
            ],
            "market_policy": market_policy or DEFAULT_MARKET_POLICY,
        },
        "summary": summary,
        "daily_summaries": _daily_summaries(transitions, turns_per_day),
        "records": records,
    }


def _initial_record(state: dict[str, Any], player: int) -> dict[str, Any]:
    observation = state.get("observation", {})
    return {
        "record_index": 0,
        "record_type": "initialized_state",
        "observation_step": int(observation.get("step", 0)),
        "day": int(observation.get("day", 0)),
        "hour": int(observation.get("hour", 0)),
        "recorded_placeholder_action": state.get("action"),
        "state": _state_snapshot(observation, player),
    }


def _transition_record(
    record_index: int,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
    player: int,
) -> dict[str, Any]:
    before = before_state.get("observation", {})
    after = after_state.get("observation", {})
    action = after_state.get("action")
    action = action if isinstance(action, dict) else {}
    farmer_action = action.get("farmer", ["PASS"])
    operation = (
        str(farmer_action[0])
        if isinstance(farmer_action, list) and farmer_action
        else "PASS"
    )
    market_orders = action.get("market", [])
    market_orders = market_orders if isinstance(market_orders, list) else []

    before_snapshot = _state_snapshot(before, player)
    after_snapshot = _state_snapshot(after, player)
    before_farm = _farm(before, player)
    after_farm = _farm(after, player)
    before_position = _position(before_farm.get("farmer"))
    after_position = _position(after_farm.get("farmer"))
    before_tile = _tile_at(before_farm, before_position)
    after_tile = _tile_at(after_farm, after_position)
    changes = _board_changes(before_farm, after_farm)
    worker_actions = _worker_actions(
        action,
        before_farm,
        after_farm,
    )
    observed_changes = _observed_changes(before_farm, after_farm)

    cash = _cash_flow(
        before_snapshot,
        after_snapshot,
        market_orders,
        changes,
    )
    valid_task = _task_was_valid(operation, before_tile)

    return {
        "record_index": record_index,
        "record_type": "executed_transition",
        "decision_observation_step": int(before.get("step", record_index - 1)),
        "result_observation_step": int(after.get("step", record_index)),
        "day": int(before.get("day", 0)),
        "hour": int(before.get("hour", 0)),
        "farmer_action": farmer_action,
        "farmer_operation": operation,
        "hands_actions": action.get("hands", []),
        "worker_actions": worker_actions,
        "observed_changes": observed_changes,
        "market_orders": market_orders,
        "position_before": _list_position(before_position),
        "position_after": _list_position(after_position),
        "actual_movement_distance": _distance(
            before_position,
            after_position,
        ),
        "tile_before": _tile_snapshot(before_tile),
        "tile_after": _tile_snapshot(after_tile),
        "task_valid_from_pre_state": valid_task,
        "board_changes": changes,
        "cash_flow": cash,
        "state_before": before_snapshot,
        "state_after": after_snapshot,
        "next_observed_task": None,
    }


def _worker_actions(
    action: dict[str, Any],
    before_farm: dict[str, Any],
    after_farm: dict[str, Any],
) -> list[dict[str, Any]]:
    actions = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    before_positions = [
        before_farm.get("farmer"),
        *before_farm.get("hands", []),
    ]
    after_positions = [
        after_farm.get("farmer"),
        *after_farm.get("hands", []),
    ]
    records = []
    for index, worker_action in enumerate(actions):
        normalized = (
            worker_action
            if isinstance(worker_action, list) and worker_action
            else ["PASS"]
        )
        before_position = _position(
            before_positions[index] if index < len(before_positions) else None
        )
        after_position = _position(
            after_positions[index] if index < len(after_positions) else None
        )
        records.append(
            {
                "worker": "farmer" if index == 0 else f"hand_{index}",
                "action": normalized,
                "operation": str(normalized[0]),
                "position_before": _list_position(before_position),
                "position_after": _list_position(after_position),
            }
        )
    return records


def _observed_changes(
    before_farm: dict[str, Any],
    after_farm: dict[str, Any],
) -> dict[str, Any]:
    before_hands = len(before_farm.get("hands", []))
    after_hands = len(after_farm.get("hands", []))
    before_quadrants = set(before_farm.get("unlocked_quadrants", []))
    after_quadrants = set(after_farm.get("unlocked_quadrants", []))
    created_animals = []
    created_structures = []
    before_tiles = before_farm.get("tiles", [])
    after_tiles = after_farm.get("tiles", [])
    for y, after_row in enumerate(after_tiles):
        for x, after_tile in enumerate(after_row):
            before_tile = (
                before_tiles[y][x]
                if y < len(before_tiles) and x < len(before_tiles[y])
                else None
            )
            if not isinstance(after_tile, dict):
                continue
            after_animal = after_tile.get("animal")
            before_animal = (
                before_tile.get("animal")
                if isinstance(before_tile, dict)
                else None
            )
            if after_animal and after_animal != before_animal:
                created_animals.append(
                    {"animal": str(after_animal), "tile": [x, y]}
                )
            after_kind = after_tile.get("kind")
            before_kind = (
                before_tile.get("kind")
                if isinstance(before_tile, dict)
                else before_tile
            )
            if (
                after_kind in ("COOP", "PASTURE")
                and after_kind != before_kind
            ):
                created_structures.append(
                    {"structure": str(after_kind), "tile": [x, y]}
                )
    return {
        "hands_added": max(0, after_hands - before_hands),
        "hands_removed": max(0, before_hands - after_hands),
        "unlocked_quadrants": sorted(after_quadrants - before_quadrants),
        "created_animals": created_animals,
        "created_structures": created_structures,
    }


def _state_snapshot(
    observation: dict[str, Any],
    player: int,
) -> dict[str, Any]:
    farm = _farm(observation, player)
    private = observation.get("private", {})
    private = private if isinstance(private, dict) else {}
    market = observation.get("market", {})
    market = market if isinstance(market, dict) else {}
    prices = market.get("prices", {})
    inventory = market.get("inventory", {})
    return {
        "money": float(farm.get("money", 0)),
        "farmer": farm.get("farmer"),
        "wheat_seeds": _item_count(private.get("seeds"), "WHEAT"),
        "shed_wheat": _item_count(private.get("shed"), "WHEAT"),
        "carried_wheat": _carried_count(private, "WHEAT"),
        "planted_wheat": _count_plants(farm, "WHEAT"),
        "weeds": _count_kind(farm, "WEED"),
        "wheat_market_price": _item_count(prices, "WHEAT"),
        "wheat_market_inventory": _item_count(inventory, "WHEAT"),
        "unlocked_shops": list(
            observation.get("town", {}).get("unlocked_shops", [])
        ),
    }


def _cash_flow(
    before: dict[str, Any],
    after: dict[str, Any],
    orders: list[Any],
    changes: dict[str, Any],
) -> dict[str, Any]:
    operation_names = [
        str(order[0])
        for order in orders
        if isinstance(order, list) and order
    ]
    unsupported = sorted(set(operation_names) - SUPPORTED_CASH_ORDERS)
    planted_by_crop = Counter(
        change["after"].get("crop")
        for change in changes["created_plants"]
        if change["after"].get("crop")
    )

    purchased_seeds: dict[str, int] = {}
    seed_spend = 0
    for crop, cost in SEED_COSTS.items():
        before_count = before["wheat_seeds"] if crop == "WHEAT" else 0
        after_count = after["wheat_seeds"] if crop == "WHEAT" else 0
        purchased = max(0, after_count - before_count + planted_by_crop[crop])
        if purchased:
            purchased_seeds[crop] = purchased
            seed_spend += purchased * cost

    available_wheat = before["shed_wheat"]
    wheat_sold = 0
    for order in orders:
        if not (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "SELL"
            and order[1] == "WHEAT"
        ):
            continue
        sold = min(max(0, int(order[2])), available_wheat)
        wheat_sold += sold
        available_wheat -= sold

    net_delta = round(after["money"] - before["money"], 6)
    realized_sale_revenue = (
        round(net_delta + seed_spend, 6)
        if not unsupported
        else None
    )
    average_wheat_sale_price = (
        round(realized_sale_revenue / wheat_sold, 4)
        if realized_sale_revenue is not None and wheat_sold
        else None
    )
    return {
        "money_before": before["money"],
        "money_after": after["money"],
        "net_money_delta": net_delta,
        "successful_seed_purchases": purchased_seeds,
        "seed_spend": seed_spend,
        "wheat_units_sold": wheat_sold,
        "realized_sale_revenue": realized_sale_revenue,
        "average_wheat_sale_price": average_wheat_sale_price,
        "accounting_supported": not unsupported,
        "unsupported_orders": unsupported,
    }


def summarize_audit(
    records: list[dict[str, Any]],
    turns_per_day: int,
) -> dict[str, Any]:
    transitions = [
        record
        for record in records
        if record["record_type"] == "executed_transition"
    ]
    initial_money = records[0]["state"]["money"]
    final_money = transitions[-1]["state_after"]["money"]
    action_counts = Counter(
        record["farmer_operation"] for record in transitions
    )
    total_seed_spend = sum(
        record["cash_flow"]["seed_spend"] for record in transitions
    )
    total_sale_revenue = sum(
        record["cash_flow"]["realized_sale_revenue"] or 0
        for record in transitions
    )
    wheat_sold = sum(
        record["cash_flow"]["wheat_units_sold"] for record in transitions
    )
    sale_prices = [
        record["cash_flow"]["average_wheat_sale_price"]
        for record in transitions
        if record["cash_flow"]["average_wheat_sale_price"] is not None
    ]
    created_plants = sum(
        len(record["board_changes"]["created_plants"])
        for record in transitions
    )
    created_weeds = sum(
        len(record["board_changes"]["created_weeds"])
        for record in transitions
    )
    harvested_units = sum(
        _harvested_units(record) for record in transitions
    )
    supported = all(
        record["cash_flow"]["accounting_supported"]
        for record in transitions
    )
    expected_final_money = round(
        initial_money + total_sale_revenue - total_seed_spend,
        6,
    )

    return {
        "configured_turns_per_day": turns_per_day,
        "executed_transitions": len(transitions),
        "action_counts": dict(sorted(action_counts.items())),
        "initial_money": initial_money,
        "final_money": final_money,
        "net_profit": round(final_money - initial_money, 6),
        "successful_seed_spend": total_seed_spend,
        "realized_sale_revenue": round(total_sale_revenue, 6),
        "wheat_units_sold": wheat_sold,
        "weighted_average_wheat_sale_price": (
            round(total_sale_revenue / wheat_sold, 4)
            if wheat_sold
            else None
        ),
        "minimum_batch_average_sale_price": min(sale_prices, default=None),
        "maximum_batch_average_sale_price": max(sale_prices, default=None),
        "cash_accounting_supported": supported,
        "cash_reconciliation": {
            "formula": (
                "initial_money + realized_sale_revenue - seed_spend"
            ),
            "expected_final_money": expected_final_money,
            "observed_final_money": final_money,
            "difference": round(final_money - expected_final_money, 6),
        },
        "plants_created": created_plants,
        "weeds_created": created_weeds,
        "harvested_wheat_units": harvested_units,
        "final_state": transitions[-1]["state_after"],
    }


def _daily_summaries(
    transitions: list[dict[str, Any]],
    turns_per_day: int,
) -> list[dict[str, Any]]:
    days: list[dict[str, Any]] = []
    for day in range(30):
        rows = [record for record in transitions if record["day"] == day]
        if not rows:
            continue
        action_counts = Counter(row["farmer_operation"] for row in rows)
        sale_revenue = sum(
            row["cash_flow"]["realized_sale_revenue"] or 0
            for row in rows
        )
        seed_spend = sum(row["cash_flow"]["seed_spend"] for row in rows)
        sold = sum(row["cash_flow"]["wheat_units_sold"] for row in rows)
        days.append(
            {
                "day": day,
                "expected_turn_slots": turns_per_day,
                "executed_transitions": len(rows),
                "first_hour": rows[0]["hour"],
                "last_hour": rows[-1]["hour"],
                "money_start": rows[0]["state_before"]["money"],
                "money_end": rows[-1]["state_after"]["money"],
                "net_money_delta": round(
                    rows[-1]["state_after"]["money"]
                    - rows[0]["state_before"]["money"],
                    6,
                ),
                "realized_sale_revenue": round(sale_revenue, 6),
                "seed_spend": seed_spend,
                "wheat_units_sold": sold,
                "average_wheat_sale_price": (
                    round(sale_revenue / sold, 4) if sold else None
                ),
                "actions": dict(sorted(action_counts.items())),
                "weeds_created": sum(
                    len(row["board_changes"]["created_weeds"])
                    for row in rows
                ),
                "route": [
                    {
                        "record_index": row["record_index"],
                        "hour": row["hour"],
                        "operation": row["farmer_operation"],
                        "position": row["position_before"],
                    }
                    for row in rows
                    if row["farmer_operation"] != "PASS"
                ],
            }
        )
    return days


def _annotate_movement_destinations(records: list[dict[str, Any]]) -> None:
    for index, record in enumerate(records):
        if record["farmer_operation"] not in MOVE_ACTIONS:
            continue
        for later in records[index + 1:]:
            if later["day"] != record["day"]:
                break
            operation = later["farmer_operation"]
            if operation in MOVE_ACTIONS:
                continue
            if operation in TILE_TASK_ACTIONS:
                record["next_observed_task"] = {
                    "operation": operation,
                    "position": later["position_before"],
                    "record_index": later["record_index"],
                }
            break


def _board_changes(
    before_farm: dict[str, Any],
    after_farm: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    changes = {
        "created_plants": [],
        "removed_plants": [],
        "created_weeds": [],
    }
    before_tiles = before_farm.get("tiles", [])
    after_tiles = after_farm.get("tiles", [])
    for y, before_row in enumerate(before_tiles):
        if y >= len(after_tiles):
            continue
        for x, before_tile in enumerate(before_row):
            if x >= len(after_tiles[y]):
                continue
            after_tile = after_tiles[y][x]
            before_kind = _kind(before_tile)
            after_kind = _kind(after_tile)
            change = {
                "tile": [x, y],
                "before": _tile_snapshot(before_tile),
                "after": _tile_snapshot(after_tile),
            }
            if before_kind != "PLANT" and after_kind == "PLANT":
                changes["created_plants"].append(change)
            if before_kind == "PLANT" and after_kind != "PLANT":
                changes["removed_plants"].append(change)
            if before_kind != "WEED" and after_kind == "WEED":
                changes["created_weeds"].append(change)
    return changes


def _task_was_valid(operation: str, tile: Any) -> bool | None:
    if operation in MOVE_ACTIONS or operation == "PASS":
        return None
    if operation == "PLANT":
        return tile is None
    if operation == "WATER":
        return _kind(tile) == "PLANT" and not tile.get("watered_today", False)
    if operation == "HARVEST":
        return isinstance(tile, dict) and int(tile.get("yield_units", 0)) > 0
    return None


def _harvested_units(record: dict[str, Any]) -> int:
    if record["farmer_operation"] != "HARVEST":
        return 0
    tile = record["tile_before"]
    if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
        return 0
    return int(tile.get("yield_units", 0))


def _farm(observation: dict[str, Any], player: int) -> dict[str, Any]:
    farms = observation.get("farms", [])
    if isinstance(farms, list) and player < len(farms):
        farm = farms[player]
        return farm if isinstance(farm, dict) else {}
    return {}


def _tile_at(farm: dict[str, Any], position: tuple[int, int] | None) -> Any:
    if position is None:
        return None
    tiles = farm.get("tiles", [])
    x, y = position
    if not isinstance(tiles, list) or not (0 <= y < len(tiles)):
        return None
    row = tiles[y]
    if not isinstance(row, list) or not (0 <= x < len(row)):
        return None
    return row[x]


def _tile_snapshot(tile: Any) -> dict[str, Any] | str | None:
    if tile is None or isinstance(tile, str):
        return tile
    if not isinstance(tile, dict):
        return {"kind": type(tile).__name__}
    keys = (
        "kind",
        "crop",
        "animal",
        "planted_day",
        "placed_day",
        "yield_units",
        "watered_today",
        "consecutive_unwatered",
        "fertilized_until_day",
        "fed_today",
        "consecutive_unfed",
        "cared_today",
        "fertilizer_available",
        "pending_care_bonus",
    )
    return {key: tile[key] for key in keys if key in tile}


def _kind(tile: Any) -> str | None:
    if tile is None:
        return None
    if isinstance(tile, str):
        return tile
    if isinstance(tile, dict):
        return str(tile.get("kind"))
    return type(tile).__name__


def _position(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return int(value[0]), int(value[1])
    return None


def _list_position(position: tuple[int, int] | None) -> list[int] | None:
    return list(position) if position is not None else None


def _distance(
    before: tuple[int, int] | None,
    after: tuple[int, int] | None,
) -> int | None:
    if before is None or after is None:
        return None
    return abs(after[0] - before[0]) + abs(after[1] - before[1])


def _item_count(items: Any, item: str) -> int:
    return int(items.get(item, 0)) if isinstance(items, dict) else 0


def _carried_count(private: dict[str, Any], item: str) -> int:
    inventories = private.get("inventories", [])
    if not isinstance(inventories, list):
        return 0
    return sum(_item_count(inventory, item) for inventory in inventories)


def _count_plants(farm: dict[str, Any], crop: str) -> int:
    return sum(
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == crop
        for row in farm.get("tiles", [])
        for tile in row
    )


def _count_kind(farm: dict[str, Any], kind: str) -> int:
    return sum(
        isinstance(tile, dict) and tile.get("kind") == kind
        for row in farm.get("tiles", [])
        for tile in row
    )


def _result(
    reward: Any,
    opponent_reward: Any,
    status: Any,
) -> str:
    if status != "DONE" or reward is None or opponent_reward is None:
        return "error"
    if reward > opponent_reward:
        return "win"
    if reward < opponent_reward:
        return "loss"
    return "tie"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--player", type=int, default=0)
    parser.add_argument("--agent", type=Path, default=Path("main.py"))
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    replay = json.loads(args.replay.read_text(encoding="utf-8"))
    agent_path = args.agent if args.agent.is_file() else None
    audit = build_audit(
        replay,
        player=args.player,
        source_replay=str(args.replay.resolve()),
        agent_path=agent_path,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(audit, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = audit["summary"]
    print(f"Records: {audit['metadata']['replay_records']}")
    print(f"Transitions: {audit['metadata']['executed_transitions']}")
    print(f"Final score: {audit['score']['final_reward']}")
    print(f"Opponent score: {audit['score']['opponent_reward']}")
    print(f"Sale revenue: {summary['realized_sale_revenue']}")
    print(f"Seed spend: {summary['successful_seed_spend']}")
    print(
        "Average wheat sale price: "
        f"{summary['weighted_average_wheat_sale_price']}"
    )
    print(f"Cash reconciliation: {summary['cash_reconciliation']}")
    print(f"Audit written to {args.output}")


if __name__ == "__main__":
    main()
