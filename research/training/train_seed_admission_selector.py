"""Train a grouped-CV tree for daily wheat seed admission."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from policies.seed_admission_policy import BASELINE, EXTRA, select_seed_admission


def _utility(record: dict[str, Any], arm: int) -> float:
    key = "extra" if arm == EXTRA else "baseline"
    return float(record["outcomes"][key]["utility"])


def _leaf(
    records: list[dict[str, Any]],
    *,
    minimum_extra_gain: float,
) -> tuple[dict[str, Any], float]:
    baseline = sum(_utility(record, BASELINE) for record in records)
    extra = sum(_utility(record, EXTRA) for record in records)
    mean_extra_gain = (extra - baseline) / len(records)
    arm = EXTRA if mean_extra_gain > minimum_extra_gain else BASELINE
    selected = extra if arm == EXTRA else baseline
    return {
        "arm": arm,
        "samples": len(records),
        "baseline_utility": round(baseline, 6),
        "extra_utility": round(extra, 6),
        "mean_extra_gain": round(mean_extra_gain, 6),
    }, selected


def train_tree(
    records: list[dict[str, Any]],
    *,
    features: tuple[str, ...],
    max_depth: int,
    min_leaf: int,
    minimum_extra_gain: float = 0.0,
    depth: int = 0,
) -> tuple[dict[str, Any], float]:
    leaf, leaf_score = _leaf(
        records,
        minimum_extra_gain=minimum_extra_gain,
    )
    if depth >= max_depth or len(records) < 2 * min_leaf:
        return leaf, leaf_score
    best: tuple[
        float,
        str,
        float,
        list[dict[str, Any]],
        list[dict[str, Any]],
    ] | None = None
    for feature in features:
        values = sorted(
            {float(record["features"][feature]) for record in records}
        )
        for left_value, right_value in zip(values, values[1:]):
            threshold = (left_value + right_value) / 2.0
            left = [
                record for record in records
                if float(record["features"][feature]) <= threshold
            ]
            right = [
                record for record in records
                if float(record["features"][feature]) > threshold
            ]
            if len(left) < min_leaf or len(right) < min_leaf:
                continue
            _, left_score = _leaf(
                left,
                minimum_extra_gain=minimum_extra_gain,
            )
            _, right_score = _leaf(
                right,
                minimum_extra_gain=minimum_extra_gain,
            )
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
        features=features,
        max_depth=max_depth,
        min_leaf=min_leaf,
        minimum_extra_gain=minimum_extra_gain,
        depth=depth + 1,
    )
    right, _ = train_tree(
        right_records,
        features=features,
        max_depth=max_depth,
        min_leaf=min_leaf,
        minimum_extra_gain=minimum_extra_gain,
        depth=depth + 1,
    )
    return {
        "feature": feature,
        "threshold": threshold,
        "left": left,
        "right": right,
        "samples": len(records),
    }, score


def evaluate(
    model: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = [
        select_seed_admission(model, record["features"])
        for record in records
    ]
    selected_utility = sum(
        _utility(record, arm)
        for record, arm in zip(records, selected)
    )
    baseline_utility = sum(
        _utility(record, BASELINE) for record in records
    )
    oracle_utility = sum(
        max(_utility(record, BASELINE), _utility(record, EXTRA))
        for record in records
    )
    selected_wins = sum(
        record["outcomes"]["extra" if arm == EXTRA else "baseline"][
            "result"
        ] == "win"
        for record, arm in zip(records, selected)
    )
    baseline_wins = sum(
        record["outcomes"]["baseline"]["result"] == "win"
        for record in records
    )
    return {
        "states": len(records),
        "selected_wins": selected_wins,
        "baseline_wins": baseline_wins,
        "win_gain": selected_wins - baseline_wins,
        "extra_choices": selected.count(EXTRA),
        "selected_utility": round(selected_utility, 6),
        "baseline_utility": round(baseline_utility, 6),
        "utility_gain": round(selected_utility - baseline_utility, 6),
        "oracle_gain": round(oracle_utility - baseline_utility, 6),
    }


def _cross_validate(
    records: list[dict[str, Any]],
    *,
    features: tuple[str, ...],
    max_depth: int,
    min_leaf: int,
    minimum_extra_gain: float,
) -> dict[str, Any]:
    folds = []
    groups = (
        ("seed", sorted({record["seed"] for record in records})),
        (
            "opponent",
            sorted({record["opponent"] for record in records}),
        ),
    )
    for field, values in groups:
        for value in values:
            training = [
                record for record in records if record[field] != value
            ]
            held_out = [
                record for record in records if record[field] == value
            ]
            if not training or not held_out:
                continue
            model, _ = train_tree(
                training,
                features=features,
                max_depth=max_depth,
                min_leaf=min_leaf,
                minimum_extra_gain=minimum_extra_gain,
            )
            folds.append(
                {
                    "field": field,
                    "value": value,
                    **evaluate(model, held_out),
                }
            )
    seed_gains = [
        float(fold["utility_gain"])
        for fold in folds
        if fold["field"] == "seed"
    ]
    opponent_gains = [
        float(fold["utility_gain"])
        for fold in folds
        if fold["field"] == "opponent"
    ]
    seed_win_gains = [
        int(fold["win_gain"])
        for fold in folds
        if fold["field"] == "seed"
    ]
    opponent_win_gains = [
        int(fold["win_gain"])
        for fold in folds
        if fold["field"] == "opponent"
    ]
    return {
        "selected_wins": sum(fold["selected_wins"] for fold in folds),
        "baseline_wins": sum(fold["baseline_wins"] for fold in folds),
        "win_gain": sum(fold["win_gain"] for fold in folds),
        "states": sum(fold["states"] for fold in folds),
        "utility_gain": round(
            sum(fold["utility_gain"] for fold in folds),
            6,
        ),
        "extra_choices": sum(fold["extra_choices"] for fold in folds),
        "worst_seed_gain": round(min(seed_gains, default=0.0), 6),
        "worst_opponent_gain": round(
            min(opponent_gains, default=0.0),
            6,
        ),
        "worst_seed_win_gain": min(seed_win_gains, default=0),
        "worst_opponent_win_gain": min(
            opponent_win_gains,
            default=0,
        ),
        "folds": folds,
    }


def train(
    records: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    features = tuple(sorted(records[0]["features"]))
    candidates = []
    for minimum_extra_gain in (
        0.0,
        0.25,
        0.5,
        1.0,
        2.0,
        5.0,
        10.0,
        25.0,
        50.0,
        100.0,
    ):
        for max_depth in (1, 2, 3, 4):
            for min_leaf in (5, 10, 15):
                result = _cross_validate(
                    records,
                    features=features,
                    max_depth=max_depth,
                    min_leaf=min_leaf,
                    minimum_extra_gain=minimum_extra_gain,
                )
                candidates.append(
                    {
                        "max_depth": max_depth,
                        "min_leaf": min_leaf,
                        "minimum_extra_gain": minimum_extra_gain,
                        **result,
                    }
                )
    baseline_result = _cross_validate(
        records,
        features=features,
        max_depth=0,
        min_leaf=1,
        minimum_extra_gain=1_000_000.0,
    )
    candidates.append(
        {
            "max_depth": 0,
            "min_leaf": 1,
            "minimum_extra_gain": 1_000_000.0,
            **baseline_result,
        }
    )
    robust = [
        candidate
        for candidate in candidates
        if candidate["worst_seed_win_gain"] >= 0
        and candidate["worst_opponent_win_gain"] >= 0
        and candidate["worst_seed_gain"] >= 0
        and candidate["worst_opponent_gain"] >= 0
    ]
    selected = max(
        robust,
        key=lambda candidate: (
            candidate["win_gain"],
            candidate["utility_gain"],
            candidate["worst_seed_gain"],
            candidate["worst_opponent_gain"],
            -candidate["extra_choices"],
            -candidate["max_depth"],
            candidate["min_leaf"],
        ),
    )
    model, _ = train_tree(
        records,
        features=features,
        max_depth=int(selected["max_depth"]),
        min_leaf=int(selected["min_leaf"]),
        minimum_extra_gain=float(selected["minimum_extra_gain"]),
    )
    return model, {
        "features": list(features),
        "selected": selected,
        "candidates": candidates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [
        row
        for dataset in args.datasets
        for row in json.loads(dataset.read_text(encoding="utf-8"))["rows"]
    ]
    model, validation = train(records)
    report = {
        "datasets": [str(path) for path in args.datasets],
        "records": len(records),
        "model": model,
        "cross_validation": validation,
        "training": evaluate(model, records),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(validation["selected"], indent=2))
    print(json.dumps(report["training"], indent=2))
    print(f"Model: {args.output}")


if __name__ == "__main__":
    main()
