"""Compare learned-service source, package, and simulator actions."""

from __future__ import annotations

import argparse
import copy
import importlib
from pathlib import Path
from typing import Any

from benchmark import load_agent_callable
from agents.experimental_learned_service_agent import (
    _SELECTED_ARMS,
    agent as source_agent,
)


def validate(package: Path, seed: int) -> None:
    make = importlib.import_module("kaggle_environments").make
    package_agent = load_agent_callable(package)
    mismatches: list[dict[str, Any]] = []
    decisions = 0

    for player in (0, 1):
        _SELECTED_ARMS.clear()
        agents: list[Any] = [source_agent, "starter"]
        if player == 1:
            agents.reverse()
        environment = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        environment.run(agents)
        replay = environment.toJSON()
        _SELECTED_ARMS.clear()
        for record_index in range(1, len(replay["steps"])):
            observation = replay["steps"][record_index - 1][player][
                "observation"
            ]
            actual = replay["steps"][record_index][player].get("action")
            source = source_agent(copy.deepcopy(observation))
            packaged = package_agent(copy.deepcopy(observation))
            decisions += 1
            if source == packaged == actual:
                continue
            mismatches.append(
                {
                    "player": player,
                    "record": record_index,
                    "source": source,
                    "packaged": packaged,
                    "actual": actual,
                }
            )
            if len(mismatches) >= 5:
                break

    print(f"Decisions compared: {decisions}")
    print(f"Mismatches: {len(mismatches)}")
    if mismatches:
        for mismatch in mismatches:
            print(mismatch)
        raise SystemExit("Learned service source/package equivalence failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--seed", type=int, default=186)
    args = parser.parse_args()
    validate(args.package, args.seed)


if __name__ == "__main__":
    main()
