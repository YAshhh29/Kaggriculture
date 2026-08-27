"""Train a shallow utility-maximizing macro-policy tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from policies.macro_policy import (
    FEATURE_NAMES,
    MACRO_ARMS,
    select_macro_arm,
)


ARMS = MACRO_ARMS


def _available_arms(records: list[dict[str, Any]]) -> tuple[int, ...]:
    return tuple(
        arm
        for arm in ARMS
        if all(str(arm) in record["outcomes"] for record in records)
    )


def _arm_utility(record: dict[str, Any], arm: int) -> float:
    return float(record["outcomes"][str(arm)]["utility"])


def _leaf(records: list[dict[str, Any]]) -> tuple[dict[str, Any], float]:
    available_arms = _available_arms(records)
    utilities = {
        arm: sum(_arm_utility(record, arm) for record in records)
        for arm in available_arms
    }
    wins = {
        arm: sum(
            record["outcomes"][str(arm)]["result"] == "win"
            for record in records
        )
        for arm in available_arms
    }
    arm = max(
        available_arms,
        key=lambda candidate: (
            wins[candidate],
            utilities[candidate],
            candidate,
        ),
    )
    score = wins[arm] * 1_000_000.0 + utilities[arm]
    return {
        "arm": arm,
        "samples": len(records),
        "arm_wins": {
            str(candidate): wins[candidate]
            for candidate in available_arms
        },
        "arm_utilities": {
            str(candidate): round(utilities[candidate], 4)
            for candidate in available_arms
        },
    }, score


def train_tree(
    records: list[dict[str, Any]],
    *,
    max_depth: int,
    min_leaf: int,
    depth: int = 0,
) -> tuple[dict[str, Any], float]:
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
    available_features = [
        feature
        for feature in FEATURE_NAMES
        if all(feature in record["features"] for record in records)
    ]
    for feature in available_features:
        values = sorted(
            {float(record["features"][feature]) for record in records}
        )
        thresholds = [
            (left + right) / 2.0
            for left, right in zip(values, values[1:])
        ]
        for threshold in thresholds:
            left_records = [
                record
                for record in records
                if float(record["features"][feature]) <= threshold
            ]
            right_records = [
                record
                for record in records
                if float(record["features"][feature]) > threshold
            ]
            if len(left_records) < min_leaf or len(right_records) < min_leaf:
                continue
            _, left_score = _leaf(left_records)
            _, right_score = _leaf(right_records)
            score = left_score + right_score
            candidate = (
                score,
                feature,
                threshold,
                left_records,
                right_records,
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


def evaluate_tree(
    model: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = [
        select_macro_arm(model, record["features"])
        for record in records
    ]
    return {
        "records": len(records),
        "utility": round(
            sum(
                _arm_utility(record, arm)
                for record, arm in zip(records, selected)
            ),
            4,
        ),
        "wins": sum(
            record["outcomes"][str(arm)]["result"] == "win"
            for record, arm in zip(records, selected)
        ),
        "arm_counts": {
            str(arm): selected.count(arm)
            for arm in _available_arms(records)
        },
        "label_accuracy": round(
            sum(
                int(record["label"]) == arm
                for record, arm in zip(records, selected)
            ) / len(records),
            4,
        ) if records else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--min-leaf", type=int, default=3)
    args = parser.parse_args()
    records = [
        record
        for dataset_path in args.datasets
        for record in json.loads(
            dataset_path.read_text(encoding="utf-8")
        )["records"]
    ]
    model, training_score = train_tree(
        records,
        max_depth=args.max_depth,
        min_leaf=args.min_leaf,
    )
    by_opponent = {}
    for opponent in sorted({record["opponent"] for record in records}):
        held_out = [
            record for record in records if record["opponent"] == opponent
        ]
        training = [
            record for record in records if record["opponent"] != opponent
        ]
        fold_model, _ = train_tree(
            training,
            max_depth=args.max_depth,
            min_leaf=args.min_leaf,
        )
        by_opponent[opponent] = evaluate_tree(fold_model, held_out)
    report = {
        "datasets": [str(path) for path in args.datasets],
        "features": list(FEATURE_NAMES),
        "max_depth": args.max_depth,
        "min_leaf": args.min_leaf,
        "training_score": training_score,
        "model": model,
        "training": evaluate_tree(model, records),
        "leave_one_opponent_out": by_opponent,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["training"], indent=2))
    print(f"Model: {args.output}")


if __name__ == "__main__":
    main()
