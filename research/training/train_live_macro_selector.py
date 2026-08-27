"""Train a shallow own-reward selector over safe live-loss macro arms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from policies.live_macro_features import LIVE_FEATURE_NAMES


TRAINING_FEATURES = tuple(
    feature for feature in LIVE_FEATURE_NAMES if feature != "player"
)


def _available_arms(records: list[dict[str, Any]]) -> tuple[str, ...]:
    common = set(records[0]["rewards"])
    for record in records[1:]:
        common.intersection_update(record["rewards"])
    return tuple(sorted(common, key=lambda arm: (arm != "control", arm)))


def _restrict_arms(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    arms = _available_arms(records)
    return [
        {
            **record,
            "rewards": {
                arm: record["rewards"][arm] for arm in arms
            },
        }
        for record in records
    ]


def _deduplicate_episodes(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unique: dict[int, dict[str, Any]] = {}
    for record in records:
        episode_id = int(record["episode_id"])
        existing = unique.get(episode_id)
        if existing is not None and existing != record:
            raise ValueError(
                f"Conflicting records for episode {episode_id}"
            )
        unique.setdefault(episode_id, record)
    return list(unique.values())


def _leaf(records: list[dict[str, Any]]) -> tuple[dict[str, Any], float]:
    arms = _available_arms(records)
    rewards = {
        arm: sum(float(record["rewards"][arm]) for record in records)
        for arm in arms
    }
    arm = max(
        arms,
        key=lambda candidate: (
            rewards[candidate],
            candidate == "control",
            candidate,
        ),
    )
    return {
        "arm": arm,
        "samples": len(records),
        "arm_rewards": rewards,
    }, rewards[arm]


def train_tree(
    records: list[dict[str, Any]],
    *,
    max_depth: int,
    min_leaf: int,
    depth: int = 0,
) -> tuple[dict[str, Any], float]:
    """Fit a greedy tree maximizing summed observed own reward."""
    leaf, leaf_score = _leaf(records)
    if depth >= max_depth or len(records) < 2 * min_leaf:
        return leaf, leaf_score
    best: tuple[
        float,
        str,
        float,
        list[dict[str, Any]],
        list[dict[str, Any]],
    ] | None = None
    for feature in TRAINING_FEATURES:
        values = sorted(
            {float(record["features"][feature]) for record in records}
        )
        for left_value, right_value in zip(values, values[1:]):
            threshold = (left_value + right_value) / 2.0
            left = [
                record
                for record in records
                if float(record["features"][feature]) <= threshold
            ]
            right = [
                record
                for record in records
                if float(record["features"][feature]) > threshold
            ]
            if len(left) < min_leaf or len(right) < min_leaf:
                continue
            _, left_score = _leaf(left)
            _, right_score = _leaf(right)
            candidate = (
                left_score + right_score,
                feature,
                threshold,
                left,
                right,
            )
            if best is None or candidate[:3] > best[:3]:
                best = candidate
    if best is None or best[0] <= leaf_score:
        return leaf, leaf_score
    score, feature, threshold, left_records, right_records = best
    left, _ = train_tree(
        left_records,
        max_depth=max_depth,
        min_leaf=min_leaf,
        depth=depth + 1,
    )
    right, _ = train_tree(
        right_records,
        max_depth=max_depth,
        min_leaf=min_leaf,
        depth=depth + 1,
    )
    return {
        "feature": feature,
        "threshold": threshold,
        "left": left,
        "right": right,
        "samples": len(records),
    }, score


def select_arm(model: dict[str, Any], features: dict[str, float]) -> str:
    """Evaluate one fitted live macro tree."""
    node = model
    while "arm" not in node:
        node = (
            node["left"]
            if features[str(node["feature"])] <= float(node["threshold"])
            else node["right"]
        )
    return str(node["arm"])


def leave_one_episode_out(
    records: list[dict[str, Any]],
    *,
    max_depth: int,
    min_leaf: int,
) -> dict[str, Any]:
    records = _restrict_arms(_deduplicate_episodes(records))
    arms = _available_arms(records)
    outcomes = []
    for held_out in records:
        training = [
            record
            for record in records
            if int(record["episode_id"])
            != int(held_out["episode_id"])
        ]
        model, _ = train_tree(
            training,
            max_depth=max_depth,
            min_leaf=min_leaf,
        )
        arm = select_arm(model, held_out["features"])
        reward = float(held_out["rewards"][arm])
        control = float(held_out["rewards"]["control"])
        outcomes.append(
            {
                "episode_id": held_out["episode_id"],
                "arm": arm,
                "reward_delta": reward - control,
            }
        )
    deltas = [float(outcome["reward_delta"]) for outcome in outcomes]
    return {
        "max_depth": max_depth,
        "min_leaf": min_leaf,
        "mean_reward_delta": round(sum(deltas) / len(deltas), 2),
        "total_reward_delta": sum(deltas),
        "improved_tied_worse": [
            sum(delta > 0 for delta in deltas),
            sum(delta == 0 for delta in deltas),
            sum(delta < 0 for delta in deltas),
        ],
        "minimum_reward_delta": min(deltas),
        "arm_counts": {
            arm: sum(outcome["arm"] == arm for outcome in outcomes)
            for arm in arms
        },
        "outcomes": outcomes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [
        record
        for dataset in args.datasets
        for record in json.loads(dataset.read_text(encoding="utf-8"))[
            "records"
        ]
    ]
    records = _restrict_arms(_deduplicate_episodes(records))
    configurations = [
        (depth, min_leaf)
        for depth in (0, 1, 2)
        for min_leaf in (2, 3)
    ]
    validation = [
        leave_one_episode_out(
            records,
            max_depth=depth,
            min_leaf=min_leaf,
        )
        for depth, min_leaf in configurations
    ]
    selected = max(
        validation,
        key=lambda result: (
            result["total_reward_delta"],
            result["minimum_reward_delta"],
            -result["max_depth"],
            result["min_leaf"],
        ),
    )
    model, _ = train_tree(
        records,
        max_depth=int(selected["max_depth"]),
        min_leaf=int(selected["min_leaf"]),
    )
    report = {
        "datasets": [str(dataset) for dataset in args.datasets],
        "validation": validation,
        "selected": selected,
        "model": model,
        "status": (
            "advance to separate validation"
            if selected["total_reward_delta"] > 0
            and selected["minimum_reward_delta"] >= 0
            else "reject"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "selected": selected,
        "model": model,
        "status": report["status"],
    }, indent=2))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()