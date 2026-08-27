"""Build own-reward macro labels from captured live counterfactuals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_labels(
    dataset: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """Join day-6 features to per-arm own rewards and oracle labels."""
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
                "features": source["day6_features"],
                "shops": source["day6_shops"],
                "rewards": rewards,
                "best_arm": best_arm,
                "best_reward_delta": rewards[best_arm] - control,
            }
        )
    oracle_gain = sum(
        float(record["best_reward_delta"]) for record in records
    )
    return {
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
    args = parser.parse_args()
    report = build_labels(
        json.loads(args.dataset.read_text(encoding="utf-8")),
        json.loads(args.evaluation.read_text(encoding="utf-8")),
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