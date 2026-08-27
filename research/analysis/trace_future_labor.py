"""Trace public day-start workload and labor decisions for one agent."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from agents.experimental_center_out_agent import _crop_operations
from benchmark import load_agent_callable, load_simulator


ROOT = Path(__file__).resolve().parents[2]


def _public_counts(farm: dict[str, Any]) -> tuple[Counter[str], Counter[str]]:
    crops: Counter[str] = Counter()
    animals: Counter[str] = Counter()
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                crops[str(tile.get("crop"))] += 1
            animal = str(tile.get("animal", ""))
            if animal in {"GOOSE", "COW", "SHEEP"}:
                animals[animal] += 1
    return crops, animals


def trace_game(
    make: Any,
    agent_path: Path,
    opponent_path: Path,
    seed: int,
    player: int,
) -> dict[str, Any]:
    snapshots = []
    agent = load_agent_callable(agent_path)
    opponent = load_agent_callable(opponent_path)

    def traced(observation: dict[str, Any]) -> dict[str, Any]:
        action = agent(observation)
        day = int(observation.get("day", 0))
        hour = int(observation.get("hour", 0))
        if hour != 0:
            return action
        own = observation["farms"][player]
        other = observation["farms"][1 - player]
        own_crops, own_animals = _public_counts(own)
        other_crops, other_animals = _public_counts(other)
        due: Counter[str] = Counter()
        for row in own.get("tiles", []):
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    due.update(_crop_operations(day, tile))
        snapshots.append(
            {
                "day": day,
                "money": int(own.get("money", 0)),
                "opponent_money": int(other.get("money", 0)),
                "hands_before_hiring": len(own.get("hands", [])),
                "hire_orders": sum(
                    order == ["HIRE"]
                    for order in action.get("market", [])
                ),
                "crops": dict(sorted(own_crops.items())),
                "opponent_crops": dict(sorted(other_crops.items())),
                "animals": dict(sorted(own_animals.items())),
                "opponent_animals": dict(sorted(other_animals.items())),
                "due_crop_operations": dict(sorted(due.items())),
                "shops": list(
                    observation.get("town", {}).get("unlocked_shops", [])
                ),
            }
        )
        return action

    agents = [traced, opponent]
    if player == 1:
        agents.reverse()
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    environment.run(agents)
    final = environment.steps[-1]
    return {
        "seed": seed,
        "player": player,
        "reward": final[player].reward,
        "opponent_reward": final[1 - player].reward,
        "snapshots": snapshots,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", required=True)
    parser.add_argument("--player", type=int, choices=(0, 1), default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    make, simulator_version = load_simulator()
    report = {
        "simulator_version": simulator_version,
        "agent": str(args.agent),
        "opponent": str(args.opponent),
        "games": [
            trace_game(
                make,
                args.agent.resolve(),
                args.opponent.resolve(),
                seed,
                args.player,
            )
            for seed in args.seed
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Future labor trace written to {args.output}")


if __name__ == "__main__":
    main()