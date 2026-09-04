"""Profile what an agent's economy actually does, from a replay.

Built to answer a comparative question rather than to score a candidate:
given replays of agents at very different skill levels, what *structurally*
differs about how they earn? Everything here is derived from the public
replay record -- units sold and the live market price at the moment of each
sale, worker action mix, hiring, land, livestock and crop choices -- so the
same profile can be computed for an elite player, for a mid-field opponent,
and for our own submissions, and compared directly.

Used by rl/GOAL.md section 9l.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


PRODUCTS = (
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
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
TASKS = {
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
    "PICKUP",
    "PLACE",
    "DROP",
}


def _obs(step: list[dict[str, Any]], side: int) -> dict[str, Any]:
    value = step[side].get("observation")
    if isinstance(value, dict) and value:
        return value
    other = step[1 - side].get("observation")
    return other if isinstance(other, dict) else {}


def profile(replay: dict[str, Any], side: int) -> dict[str, Any]:
    steps = replay["steps"]
    rewards = replay.get("rewards") or [0, 0]

    revenue: Counter[str] = Counter()
    units: Counter[str] = Counter()
    revenue_first_half = 0.0
    spend: Counter[str] = Counter()
    hires = 0
    land_buys = 0
    land_steps: list[int] = []
    animals_bought: Counter[str] = Counter()
    seeds_bought: Counter[str] = Counter()
    planted: Counter[str] = Counter()
    unit_ops: Counter[str] = Counter()
    move_turns = 0
    task_turns = 0
    pass_turns = 0

    for index, step in enumerate(steps):
        observation = _obs(step, side)
        prices = observation.get("market", {}).get("prices", {}) or {}
        action = step[side].get("action")
        if not isinstance(action, dict):
            continue

        for order in action.get("market") or []:
            if not (isinstance(order, list) and order):
                continue
            operation = str(order[0])
            if operation == "SELL" and len(order) >= 3:
                item = str(order[1])
                quantity = int(order[2])
                price = int(prices.get(item, 0))
                revenue[item] += price * quantity
                units[item] += quantity
                if index < len(steps) // 2:
                    revenue_first_half += price * quantity
            elif operation == "HIRE":
                hires += 1
            elif operation == "BUY_LAND":
                land_buys += 1
                land_steps.append(index)
            elif operation == "BUY_ANIMAL" and len(order) >= 3:
                animals_bought[str(order[1])] += int(order[2])
            elif operation == "BUY_SEED" and len(order) >= 3:
                seeds_bought[str(order[1])] += int(order[2])
            elif operation == "BUY_PRODUCT" and len(order) >= 3:
                spend[str(order[1])] += int(order[2])

        for unit_action in [action.get("farmer"), *(action.get("hands") or [])]:
            if not (isinstance(unit_action, list) and unit_action):
                continue
            operation = str(unit_action[0])
            unit_ops[operation] += 1
            if operation in MOVES:
                move_turns += 1
            elif operation in TASKS:
                task_turns += 1
            else:
                pass_turns += 1
            if operation == "PLANT" and len(unit_action) >= 2:
                planted[str(unit_action[1])] += 1

    final = _obs(steps[-1], side)
    farms = final.get("farms") or []
    farm = farms[side] if side < len(farms) and isinstance(farms[side], dict) else {}
    total_revenue = sum(revenue.values())

    return {
        "reward": float(rewards[side]) if side < len(rewards) else 0.0,
        "units_sold": dict(units),
        "revenue": {k: int(v) for k, v in revenue.items()},
        "total_sale_revenue": int(total_revenue),
        "mean_price": {
            item: round(revenue[item] / units[item], 1)
            for item in units
            if units[item]
        },
        "revenue_share": {
            item: round(revenue[item] / total_revenue, 3)
            for item in revenue
            if total_revenue
        },
        "first_half_revenue_share": (
            round(revenue_first_half / total_revenue, 3) if total_revenue else 0.0
        ),
        "hires": hires,
        "final_hands": len(farm.get("hands") or []),
        "land_buys": land_buys,
        "first_land_step": min(land_steps) if land_steps else None,
        "final_quadrants": len(farm.get("unlocked_quadrants") or []),
        "animals_bought": dict(animals_bought),
        "seeds_bought": dict(seeds_bought),
        "planted": dict(planted),
        "wheat_bought_for_feed": int(spend.get("WHEAT", 0)),
        "move_turns": move_turns,
        "task_turns": task_turns,
        "pass_turns": pass_turns,
        "utilisation": (
            round(task_turns / (move_turns + task_turns + pass_turns), 3)
            if (move_turns + task_turns + pass_turns)
            else 0.0
        ),
    }


def profile_file(path: Path) -> list[dict[str, Any]]:
    replay = json.loads(path.read_bytes())
    names = [
        str(agent.get("Name", ""))
        for agent in replay.get("info", {}).get("Agents", [])
    ]
    out = []
    for side, name in enumerate(names):
        row = profile(replay, side)
        row["team"] = name
        row["episode_id"] = replay.get("info", {}).get("EpisodeId")
        row["opponent"] = names[1 - side] if len(names) == 2 else None
        out.append(row)
    return out
