"""Compare candidate-C source, package, and simulator actions."""

from __future__ import annotations

import argparse
import copy
import importlib
from pathlib import Path
from typing import Any

from candidates.candidate_c import agent as source_agent
from benchmark import load_agent_callable


def validate(package: Path, seed: int) -> None:
    make = importlib.import_module("kaggle_environments").make
    package_agent = load_agent_callable(package)
    mismatches: list[dict[str, Any]] = []
    decisions = 0
    expected_decisions = 0
    for player in (0, 1):
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
        expected_decisions += len(replay["steps"]) - 1
        for record_index in range(1, len(replay["steps"])):
            observation = replay["steps"][record_index - 1][player][
                "observation"
            ]
            observation = copy.deepcopy(observation)
            observation["step"] = record_index - 1
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
    print(f"Decisions compared: {decisions}/{expected_decisions}")
    print(f"Mismatches: {len(mismatches)}")
    if mismatches:
        for mismatch in mismatches:
            print(mismatch)
        raise SystemExit("Candidate C equivalence failed")
    if decisions != expected_decisions:
        raise SystemExit("Candidate C equivalence stopped early")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--seed", type=int, default=230)
    args = parser.parse_args()
    validate(args.package, args.seed)


if __name__ == "__main__":
    main()
