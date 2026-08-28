"""Build own-reward macro labels from captured live counterfactuals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_labels(
    dataset: dict[str, Any],
    evaluation: dict[str, Any],
    *,
    context: str = "day6_hour0",
    selected_arms: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Join one decision context to per-arm own rewards and oracle labels."""
    available_arms = set(evaluation.get("results", {}))
    if "control" not in available_arms:
        raise ValueError("Evaluation does not contain control outcomes")
    missing_arms = set(selected_arms or ()) - available_arms
    if missing_arms:
        missing = ", ".join(sorted(missing_arms))
        raise ValueError(
            f"Evaluation does not contain requested arms: {missing}"
        )
    features_by_episode = {
        int(record["episode_id"]): record
        for record in dataset["records"]
    }
    outcomes_by_arm = {
        arm: {
            int(outcome["episode_id"]): float(outcome["reward"])
            for outcome in result["outcomes"]
        }
        for arm, result in evaluation["results"].items()
        if selected_arms is None or arm in selected_arms or arm == "control"
    }
    arms = tuple(outcomes_by_arm)
    records = []
    for episode_id, source in sorted(features_by_episode.items()):
        rewards = {
            arm: outcomes_by_arm[arm][episode_id]
            for arm in arms
        }
        control = rewards["control"]
        best_arm = max(
            arms,
            key=lambda arm: (
                rewards[arm],
                arm == "control",
                arm,
            ),
        )
        records.append(
            {
                "episode_id": episode_id,
                "features": (
                    source["decision_contexts"][context]["features"]
                    if "decision_contexts" in source
                    else source["day6_features"]
                ),
                "shops": (
                    source["decision_contexts"][context]["shops"]
                    if "decision_contexts" in source
                    else source["day6_shops"]
                ),
                "rewards": rewards,
                "best_arm": best_arm,
                "best_reward_delta": rewards[best_arm] - control,
            }
        )
    oracle_gain = sum(
        float(record["best_reward_delta"]) for record in records
    )
    return {
        "context": context,
        "arms": list(arms),
        "records": records,
        "oracle": {
            "games": len(records),
            "total_reward_gain": oracle_gain,
            "mean_reward_gain": (
                round(oracle_gain / len(records), 2) if records else None
            ),
            "arm_counts": {
                arm: sum(record["best_arm"] == arm for record in records)
                for arm in arms
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("evaluation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--context", default="day6_hour0")
    parser.add_argument("--arm", action="append")
    args = parser.parse_args()
    report = build_labels(
        json.loads(args.dataset.read_text(encoding="utf-8")),
        json.loads(args.evaluation.read_text(encoding="utf-8")),
        context=args.context,
        selected_arms=tuple(args.arm) if args.arm else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["oracle"], indent=2))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
