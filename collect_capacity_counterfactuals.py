"""Collect paired outcomes for day-4 throughput policy templates."""

from __future__ import annotations

import argparse
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark import load_agent_callable
from policies.capacity_policy import (
    ARM_NAMES,
    ARM_STRAWBERRY,
    CAPACITY_ARMS,
    decide_capacity_arm,
)
from policies.macro_policy import extract_macro_features


ROOT = Path(__file__).resolve().parent
SELECTION_DAY = 4
DEFAULT_OPPONENTS = (
    "agents/experimental_compact_macro_agent.py",
    "agents/experimental_adaptive_counter_agent.py",
    "agents/experimental_center_out_agent.py",
    "agents/experimental_lifecycle_agent.py",
    "agents/experimental_scale_agent.py",
    "agents/experimental_investment_agent.py",
)


def _utility(agent_reward: float, opponent_reward: float) -> float:
    outcome = 1 if agent_reward > opponent_reward else -1
    if agent_reward == opponent_reward:
        outcome = 0
    margin = max(
        -200.0,
        min(200.0, (agent_reward - opponent_reward) / 1000.0),
    )
    return 1000.0 * outcome + margin


def _arm_decision(
    observation: dict[str, Any],
    arm: int,
) -> dict[str, Any]:
    if int(observation.get("day", 0)) < SELECTION_DAY:
        return decide_capacity_arm(observation, ARM_STRAWBERRY)
    return decide_capacity_arm(observation, arm)


def _run_arm(
    make: Any,
    *,
    arm: int,
    opponent: str,
    seed: int,
    player: int,
) -> dict[str, Any]:
    snapshot: dict[str, float] | None = None

    def capacity_agent(observation: dict[str, Any]) -> dict[str, Any]:
        nonlocal snapshot
        if (
            snapshot is None
            and int(observation.get("day", 0)) == SELECTION_DAY
            and int(observation.get("hour", 0)) == 0
        ):
            snapshot = extract_macro_features(observation)
        return _arm_decision(observation, arm)

    opponent_input = (
        opponent
        if opponent == "starter"
        else load_agent_callable((ROOT / opponent).resolve())
    )
    agents: list[Any] = [capacity_agent, opponent_input]
    if player == 1:
        agents.reverse()
    environment = make(
        "kaggriculture",
        configuration={
            "episodeSteps": 720,
            "seed": seed,
            "runTimeout": 10_000,
        },
        debug=False,
    )
    environment.run(agents)
    final = environment.steps[-1]
    opponent_player = 1 - player
    status = str(final[player].status)
    opponent_status = str(final[opponent_player].status)
    if status != "DONE" or opponent_status != "DONE":
        raise RuntimeError(
            f"Incomplete capacity game: {status}/{opponent_status}"
        )
    if snapshot is None:
        raise RuntimeError("Capacity feature snapshot was not captured")
    agent_reward = float(final[player].reward)
    opponent_reward = float(final[opponent_player].reward)
    return {
        "features": snapshot,
        "agent_reward": agent_reward,
        "opponent_reward": opponent_reward,
        "margin": agent_reward - opponent_reward,
        "result": (
            "win"
            if agent_reward > opponent_reward
            else "loss"
            if agent_reward < opponent_reward
            else "tie"
        ),
        "utility": _utility(agent_reward, opponent_reward),
    }


def _same_features(
    first: dict[str, float],
    second: dict[str, float],
) -> bool:
    return first.keys() == second.keys() and all(
        abs(first[name] - second[name]) < 1e-9 for name in first
    )


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
    parser.add_argument("--seed-count", type=int, default=2)
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
        "arms": ARM_NAMES,
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
        key = (opponent, seed, player)
        if key in completed:
            continue
        outcomes = {
            str(arm): _run_arm(
                make,
                arm=arm,
                opponent=opponent,
                seed=seed,
                player=player,
            )
            for arm in CAPACITY_ARMS
        }
        features = outcomes[str(ARM_STRAWBERRY)].pop("features")
        for arm in CAPACITY_ARMS[1:]:
            candidate = outcomes[str(arm)].pop("features")
            if not _same_features(features, candidate):
                raise RuntimeError(
                    f"Capacity arms diverged before selection: {key}"
                )
        label = max(
            CAPACITY_ARMS,
            key=lambda arm: (
                outcomes[str(arm)]["utility"],
                outcomes[str(arm)]["margin"],
                arm,
            ),
        )
        records.append(
            {
                "opponent": opponent,
                "seed": seed,
                "player": player,
                "features": features,
                "outcomes": outcomes,
                "label": label,
            }
        )
        _write_report(args.output, metadata, records, len(contexts))
        print(
            f"opponent={opponent} seed={seed} player={player} "
            f"label={ARM_NAMES[label]}"
        )

    _write_report(args.output, metadata, records, len(contexts))
    print(f"Records: {len(records)}/{len(contexts)}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
