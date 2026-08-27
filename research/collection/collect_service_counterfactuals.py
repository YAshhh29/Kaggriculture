"""Collect day-1 baseline-versus-paired service counterfactuals."""

from __future__ import annotations

import argparse
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from benchmark import load_agent_callable
from research.collection.collect_market_counterfactuals import (
    _joint_actions,
    _run_to_completion,
    _terminal_outcome,
    clone_for_counterfactual,
)
from policies.macro_policy import extract_macro_features
from policies.service_policy import (
    ARM_BASELINE,
    ARM_NAMES,
    SERVICE_ARMS,
    decide_service_arm,
)


ROOT = Path(__file__).resolve().parents[2]
SELECTION_DAY = 1
BUILTIN_OPPONENTS = {"pass", "random", "starter"}
DEFAULT_OPPONENTS = (
    "agents/experimental_deadline_tapered_wheat_agent.py",
    "agents/experimental_compact_macro_agent.py",
    "agents/experimental_adaptive_counter_agent.py",
    "agents/experimental_scale_agent.py",
)
Agent = Callable[[dict[str, Any]], dict[str, Any]]


def _utility(outcome: dict[str, Any]) -> float:
    result = str(outcome["result"])
    win_value = 1 if result == "win" else -1 if result == "loss" else 0
    margin = max(
        -200.0,
        min(200.0, float(outcome["terminal_margin"]) / 1000.0),
    )
    return 1000.0 * win_value + margin


def _arm_decision(
    observation: dict[str, Any],
    arm: int,
) -> dict[str, Any]:
    selected = (
        ARM_BASELINE
        if int(observation.get("day", 0)) < SELECTION_DAY
        else arm
    )
    return decide_service_arm(observation, selected)


def _opponent_agent(environment: Any, opponent: str) -> Agent:
    if opponent in BUILTIN_OPPONENTS:
        return environment.agents[opponent]
    return load_agent_callable((ROOT / opponent).resolve())


def collect_context(
    make: Any,
    opponent: str,
    seed: int,
    player: int,
) -> dict[str, Any]:
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    opponent_agent = _opponent_agent(environment, opponent)
    baseline_agent = lambda observation: _arm_decision(
        observation, ARM_BASELINE
    )
    while (
        not environment.done
        and int(environment.state[player].observation.day) < SELECTION_DAY
    ):
        environment.step(
            _joint_actions(
                environment,
                player,
                baseline_agent,
                opponent_agent,
            )
        )
    features = extract_macro_features(
        environment.state[player].observation
    )
    outcomes = {}
    for arm in SERVICE_ARMS:
        branch = clone_for_counterfactual(environment)
        controlled = lambda observation, arm=arm: _arm_decision(
            observation, arm
        )
        _run_to_completion(
            branch,
            player,
            controlled,
            opponent_agent,
        )
        outcome = _terminal_outcome(branch, player)
        outcome["utility"] = _utility(outcome)
        outcomes[str(arm)] = outcome
    label = max(
        SERVICE_ARMS,
        key=lambda arm: (
            outcomes[str(arm)]["utility"],
            outcomes[str(arm)]["terminal_margin"],
            -arm,
        ),
    )
    return {
        "opponent": opponent,
        "seed": seed,
        "player": player,
        "features": features,
        "outcomes": outcomes,
        "label": label,
    }


def _write_report(
    output: Path,
    metadata: dict[str, Any],
    records: list[dict[str, Any]],
    expected: int,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                **metadata,
                "complete": len(records) == expected,
                "records": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=140)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--opponent", action="append", dest="opponents")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    opponents = tuple(args.opponents or DEFAULT_OPPONENTS)
    contexts = [
        (opponent, seed, player)
        for opponent in opponents
        for seed in range(args.seed_start, args.seed_start + args.seed_count)
        for player in (0, 1)
    ]
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "simulator_version": "1.32.7",
        "selection_day": SELECTION_DAY,
        "seed_start": args.seed_start,
        "seed_count": args.seed_count,
        "opponents": list(opponents),
        "arms": {str(arm): ARM_NAMES[arm] for arm in SERVICE_ARMS},
    }
    records: list[dict[str, Any]] = []
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        keys = (
            "simulator_version",
            "selection_day",
            "seed_start",
            "seed_count",
            "opponents",
            "arms",
        )
        if all(existing.get(key) == metadata[key] for key in keys):
            records = list(existing.get("records", []))
    completed = {
        (record["opponent"], record["seed"], record["player"])
        for record in records
    }
    make = importlib.import_module("kaggle_environments").make
    for opponent, seed, player in contexts:
        if (opponent, seed, player) in completed:
            continue
        record = collect_context(make, opponent, seed, player)
        records.append(record)
        _write_report(args.output, metadata, records, len(contexts))
        print(
            f"opponent={opponent} seed={seed} player={player} "
            f"label={ARM_NAMES[int(record['label'])]}"
        )
    _write_report(args.output, metadata, records, len(contexts))
    print(f"Records: {len(records)}/{len(contexts)}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
