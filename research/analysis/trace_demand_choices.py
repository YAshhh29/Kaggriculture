"""Trace locked crop and expansion-animal demand choices in direct matches."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from agents.experimental_demand_animal_agent import decide
from agents.experimental_demand_aware_agent import (
    ANIMAL_SELECTION_DAY,
    CROP_SELECTION_DAY,
    _ANIMAL_CHOICES,
    _CROP_CHOICES,
)
from benchmark import load_agent_callable
from policies.macro_policy import extract_macro_features


ROOT = Path(__file__).resolve().parents[2]


def trace_game(
    make: Any,
    opponent: str,
    seed: int,
    player: int,
    selection_only: bool = False,
) -> dict[str, Any]:
    snapshots: dict[str, Any] = {}
    _ANIMAL_CHOICES.clear()
    _CROP_CHOICES.clear()

    def traced(observation: dict[str, Any]) -> dict[str, Any]:
        day = int(observation.get("day", 0))
        hour = int(observation.get("hour", 0))
        action = decide(observation)
        if day == ANIMAL_SELECTION_DAY and hour == 0:
            snapshots["animal"] = {
                "choice": _ANIMAL_CHOICES.get(player),
                "shops": list(
                    observation.get("town", {}).get("unlocked_shops", [])
                ),
                "features": extract_macro_features(observation),
            }
        if day == CROP_SELECTION_DAY and hour == 0:
            snapshots["crop"] = {
                "choice": _CROP_CHOICES.get(player),
                "shops": list(
                    observation.get("town", {}).get("unlocked_shops", [])
                ),
            }
        return action

    opponent_agent = load_agent_callable((ROOT / opponent).resolve())
    agents: list[Any] = [traced, opponent_agent]
    if player == 1:
        agents.reverse()
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    if selection_only:
        while (
            not environment.done
            and "crop" not in snapshots
        ):
            environment.step(
                [
                    agent(state.observation)
                    for agent, state in zip(agents, environment.state)
                ]
            )
    else:
        environment.run(agents)
    final = environment.steps[-1]
    return {
        "seed": seed,
        "player": player,
        "snapshots": snapshots,
        "reward": (
            float(final[player].reward)
            if final[player].reward is not None
            else None
        ),
        "opponent_reward": (
            float(final[1 - player].reward)
            if final[1 - player].reward is not None
            else None
        ),
        "result": (
            "incomplete"
            if final[player].reward is None
            else
            "win"
            if final[player].reward > final[1 - player].reward
            else "loss"
            if final[player].reward < final[1 - player].reward
            else "tie"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("opponent")
    parser.add_argument("--seed-start", type=int, required=True)
    parser.add_argument("--seed-count", type=int, default=1)
    parser.add_argument("--selection-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    make = importlib.import_module("kaggle_environments").make
    report = {
        "opponent": args.opponent,
        "games": [
            trace_game(
                make,
                args.opponent,
                seed,
                player,
                args.selection_only,
            )
            for seed in range(args.seed_start, args.seed_start + args.seed_count)
            for player in (0, 1)
        ],
    }
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Demand choice trace written to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
