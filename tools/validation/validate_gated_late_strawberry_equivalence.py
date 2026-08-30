"""Compare gated late-strawberry source, package, and simulator actions."""

from __future__ import annotations

import argparse
import copy
import importlib
from pathlib import Path
from typing import Any

from agents.experimental_demand_aware_agent import (
    _ANIMAL_CHOICES,
    _CROP_CHOICES,
)
from agents.experimental_future_labor_agent import _LABOR_CHOICES
from agents.experimental_guarded_colocated_crop_service_agent import (
    _CROP_SERVICE_CHOICES,
)
from agents.experimental_idle_value_fertilizer_agent import (
    _APPLICATION_COUNTS,
)
from agents.experimental_late_value_fertilizer_agent import (
    _FERTILIZER_CHOICES,
)
from agents.experimental_learned_service_agent import _SELECTED_ARMS
from agents.experimental_tiered_late_strawberry_agent import (
    _LATE_STRAWBERRY_CHOICES,
    agent as source_agent,
)
from agents.experimental_tiered_value_fertilizer_agent import (
    _STAGING_DISTANCES,
)
from benchmark import load_agent_callable


CACHE_NAMES = (
    "_ANIMAL_CHOICES",
    "_CROP_CHOICES",
    "_LABOR_CHOICES",
    "_SELECTED_ARMS",
    "_CROP_SERVICE_CHOICES",
    "_FERTILIZER_CHOICES",
    "_APPLICATION_COUNTS",
    "_STAGING_DISTANCES",
    "_LATE_STRAWBERRY_CHOICES",
)
SOURCE_CACHES = (
    _ANIMAL_CHOICES,
    _CROP_CHOICES,
    _LABOR_CHOICES,
    _SELECTED_ARMS,
    _CROP_SERVICE_CHOICES,
    _FERTILIZER_CHOICES,
    _APPLICATION_COUNTS,
    _STAGING_DISTANCES,
    _LATE_STRAWBERRY_CHOICES,
)


def _reset_source() -> None:
    for cache in SOURCE_CACHES:
        cache.clear()


def _reset_package(package_agent: Any) -> None:
    namespace = package_agent.__globals__
    for name in CACHE_NAMES:
        cache = namespace.get(name)
        if isinstance(cache, dict):
            cache.clear()


def validate(package: Path, seed: int) -> None:
    make = importlib.import_module("kaggle_environments").make
    package_agent = load_agent_callable(package)
    mismatches: list[dict[str, Any]] = []
    decisions = 0
    expected_decisions = 0
    for player in (0, 1):
        _reset_source()
        _reset_package(package_agent)
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
        _reset_source()
        _reset_package(package_agent)
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
    print(f"Decisions compared: {decisions}/{expected_decisions}")
    print(f"Mismatches: {len(mismatches)}")
    if mismatches:
        for mismatch in mismatches:
            print(mismatch)
        raise SystemExit(
            "Gated late-strawberry source/package equivalence failed"
        )
    if decisions != expected_decisions:
        raise SystemExit("Gated late-strawberry equivalence stopped early")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--seed", type=int, default=223)
    args = parser.parse_args()
    validate(args.package, args.seed)


if __name__ == "__main__":
    main()
