"""Collect paired compact/expanded macro-policy outcomes."""

from __future__ import annotations

import argparse
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark import load_agent_callable
from agents.experimental_adaptive_counter_agent import ONE_LAND_ANIMAL_PLANS
from agents.experimental_premium_throughput_agent import decide as decide_premium
from policies.macro_policy import ARM_COMPACT, ARM_EXPANDED, extract_macro_features
from policies.macro_policy import ARM_COMPACT_CROP, ARM_EXPANDED_CROP, MACRO_ARMS


ROOT = Path(__file__).resolve().parents[2]
SELECTION_DAY = 9
DEFAULT_OPPONENTS = (
    "agents/experimental_center_out_agent.py",
    "agents/experimental_lifecycle_agent.py",
    "agents/experimental_scale_agent.py",
    "agents/experimental_investment_agent.py",
    "agents/experimental_zoned_expansion_agent.py",
    "starter",
)
ARM_NAMES = {
    ARM_COMPACT: "compact-animal",
    ARM_EXPANDED: "expanded-animal",
    ARM_COMPACT_CROP: "compact-crop",
    ARM_EXPANDED_CROP: "expanded-crop",
}


def _arm_decision(observation: dict[str, Any], arm: int) -> dict[str, Any]:
    if int(observation.get("day", 0)) < SELECTION_DAY:
        return decide_premium(observation)
    if arm == ARM_COMPACT:
        return decide_premium(
            observation,
            target_extra_land=1,
            animal_plans=ONE_LAND_ANIMAL_PLANS,
        )
    if arm == ARM_EXPANDED:
        return decide_premium(observation)
    if arm == ARM_COMPACT_CROP:
        return decide_premium(
            observation,
            target_extra_land=1,
            animal_plans=ONE_LAND_ANIMAL_PLANS,
            crop_worker_reserve=3,
        )
    if arm == ARM_EXPANDED_CROP:
        return decide_premium(observation, crop_worker_reserve=3)
    raise ValueError(f"Unknown macro arm: {arm}")


def _utility(agent_reward: float, opponent_reward: float) -> float:
    outcome = 1 if agent_reward > opponent_reward else -1
    if agent_reward == opponent_reward:
        outcome = 0
    margin = max(-20.0, min(20.0, (agent_reward - opponent_reward) / 1000.0))
    return 1000.0 * outcome + margin


def _run_arm(
    make: Any,
    *,
    arm: int,
    opponent: str,
    seed: int,
    player: int,
) -> dict[str, Any]:
    snapshot: dict[str, float] | None = None

    def macro_agent(observation: dict[str, Any]) -> dict[str, Any]:
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
    agents: list[Any] = [macro_agent, opponent_input]
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
            f"Incomplete macro game: {status}/{opponent_status}"
        )
    agent_reward = float(final[player].reward)
    opponent_reward = float(final[opponent_player].reward)
    if snapshot is None:
        raise RuntimeError("Macro feature snapshot was not captured")
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
    report = {
        **metadata,
        "complete": len(records) == expected,
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument("--seed-count", type=int, default=3)
    parser.add_argument("--opponent", action="append", dest="opponents")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts" / "datasets" / "macro-counterfactuals.json",
    )
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
        "seed_start": args.seed_start,
        "seed_count": args.seed_count,
        "opponents": list(opponents),
        "arms": ARM_NAMES,
    }
    records: list[dict[str, Any]] = []
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        if all(existing.get(key) == metadata[key] for key in (
            "simulator_version",
            "seed_start",
            "seed_count",
            "opponents",
            "arms",
        )):
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
            for arm in MACRO_ARMS
        }
        compact_features = outcomes[str(ARM_COMPACT)].pop("features")
        expanded_features = outcomes[str(ARM_EXPANDED)].pop("features")
        if not _same_features(compact_features, expanded_features):
            raise RuntimeError(f"Arm context diverged before selection: {key}")
        label = max(
            MACRO_ARMS,
            key=lambda arm: (
                outcomes[str(arm)]["utility"],
                outcomes[str(arm)]["margin"],
                arm,
            ),
        )
        record = {
            "opponent": opponent,
            "seed": seed,
            "player": player,
            "features": compact_features,
            "outcomes": outcomes,
            "label": label,
        }
        records.append(record)
        _write_report(args.output, metadata, records, len(contexts))
        print(
            f"opponent={opponent} seed={seed} player={player} "
            f"label={ARM_NAMES[label]} "
            f"compact={outcomes[str(ARM_COMPACT)]['margin']:.0f} "
            f"expanded={outcomes[str(ARM_EXPANDED)]['margin']:.0f}"
        )

    _write_report(args.output, metadata, records, len(contexts))
    print(f"Records: {len(records)}/{len(contexts)}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
