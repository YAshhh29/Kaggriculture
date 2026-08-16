"""Fit a standardized ridge model for HOLD-versus-SELL terminal value."""

from __future__ import annotations

import argparse
import json
from math import sqrt
from pathlib import Path
from statistics import fmean
from typing import Any

from train_market_value_tree import FEATURES


def fit_ridge(
    rows: list[dict[str, Any]],
    alpha: float,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("Cannot fit ridge regression without rows")
    means = {
        feature: fmean(float(row["features"][feature]) for row in rows)
        for feature in FEATURES
    }
    scales = {}
    for feature in FEATURES:
        variance = fmean(
            (float(row["features"][feature]) - means[feature]) ** 2
            for row in rows
        )
        scales[feature] = sqrt(variance) or 1.0

    design = [
        [
            1.0,
            *[
                (float(row["features"][feature]) - means[feature])
                / scales[feature]
                for feature in FEATURES
            ],
        ]
        for row in rows
    ]
    targets = [_target(row) for row in rows]
    size = len(FEATURES) + 1
    normal = [[0.0 for _ in range(size)] for _ in range(size)]
    right = [0.0 for _ in range(size)]
    for values, target in zip(design, targets):
        for row_index in range(size):
            right[row_index] += values[row_index] * target
            for column_index in range(size):
                normal[row_index][column_index] += (
                    values[row_index] * values[column_index]
                )
    for index in range(1, size):
        normal[index][index] += alpha
    coefficients = _solve_linear_system(normal, right)
    return {
        "alpha": alpha,
        "means": means,
        "scales": scales,
        "intercept": coefficients[0],
        "coefficients": {
            feature: coefficients[index + 1]
            for index, feature in enumerate(FEATURES)
        },
    }


def predict(model: dict[str, Any], features: dict[str, Any]) -> float:
    value = float(model["intercept"])
    for feature in FEATURES:
        standardized = (
            float(features[feature]) - float(model["means"][feature])
        ) / float(model["scales"][feature])
        value += float(model["coefficients"][feature]) * standardized
    return value


def evaluate_leave_one_seed_out(
    rows: list[dict[str, Any]],
    alpha: float,
    decision_threshold: float = 0.0,
) -> dict[str, Any]:
    evaluated = []
    for seed in sorted({int(row["seed"]) for row in rows}):
        training = [row for row in rows if int(row["seed"]) != seed]
        held_out = [row for row in rows if int(row["seed"]) == seed]
        model = fit_ridge(training, alpha)
        for row in held_out:
            predicted_delta = predict(model, row["features"])
            choice = (
                "SELL"
                if predicted_delta > decision_threshold
                else "HOLD"
            )
            evaluated.append(_evaluate_row(row, choice, predicted_delta))
    return {
        "validation": "leave-one-seed-out",
        "alpha": alpha,
        "decision_threshold": decision_threshold,
        "seeds": len({int(row["seed"]) for row in rows}),
        "states": len(evaluated),
        "model": _regret_summary(evaluated, "model_regret"),
        "v9_behavior": _regret_summary(evaluated, "v9_regret"),
        "predictions": evaluated,
    }


def _evaluate_row(
    row: dict[str, Any],
    model_choice: str,
    predicted_delta: float,
) -> dict[str, Any]:
    outcomes = row["outcomes"]
    hold_money = float(outcomes["hold"]["terminal_money"])
    sell_money = float(outcomes["sell"]["terminal_money"])
    best_money = max(hold_money, sell_money)
    v9_choice = str(row["intervention"]["baseline_choice"])
    return {
        "seed": int(row["seed"]),
        "record_index": int(row["features"]["decision_observation_step"]),
        "actual_delta": _target(row),
        "predicted_delta": round(predicted_delta, 6),
        "model_choice": model_choice,
        "v9_choice": v9_choice,
        "model_regret": round(
            best_money
            - (sell_money if model_choice == "SELL" else hold_money),
            6,
        ),
        "v9_regret": round(
            best_money
            - (sell_money if v9_choice == "SELL" else hold_money),
            6,
        ),
    }


def _regret_summary(
    rows: list[dict[str, Any]], field: str
) -> dict[str, Any]:
    regrets = [float(row[field]) for row in rows]
    by_seed: dict[int, float] = {}
    for row in rows:
        seed = int(row["seed"])
        by_seed[seed] = by_seed.get(seed, 0.0) + float(row[field])
    return {
        "total_one_step_regret": round(sum(regrets), 6),
        "mean_one_step_regret": round(fmean(regrets), 6),
        "zero_regret_states": sum(regret == 0 for regret in regrets),
        "regret_by_seed": {
            str(seed): round(regret, 6)
            for seed, regret in sorted(by_seed.items())
        },
        "worst_seed_regret": round(max(by_seed.values(), default=0.0), 6),
    }


def _target(row: dict[str, Any]) -> float:
    return float(row["outcomes"]["sell_minus_hold_terminal_coins"])


def _solve_linear_system(
    matrix: list[list[float]],
    right: list[float],
) -> list[float]:
    size = len(right)
    augmented = [
        [*matrix[row], right[row]] for row in range(size)
    ]
    for column in range(size):
        pivot = max(
            range(column, size),
            key=lambda row: abs(augmented[row][column]),
        )
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("Ridge system is singular")
        augmented[column], augmented[pivot] = (
            augmented[pivot],
            augmented[column],
        )
        pivot_value = augmented[column][column]
        augmented[column] = [
            value / pivot_value for value in augmented[column]
        ]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(
                    augmented[row], augmented[column]
                )
            ]
    return [augmented[row][-1] for row in range(size)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--alpha", type=float, default=10.0)
    parser.add_argument("--decision-threshold", type=float, default=0.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    rows = [row for episode in dataset["episodes"] for row in episode["rows"]]
    evaluation = evaluate_leave_one_seed_out(
        rows,
        args.alpha,
        args.decision_threshold,
    )
    evaluation["features"] = list(FEATURES)
    evaluation["fitted_model"] = fit_ridge(rows, args.alpha)
    evaluation["decision"] = (
        "SELL when predicted sell-minus-hold value exceeds "
        f"{args.decision_threshold}"
    )
    evaluation["limitations"] = [
        "each label changes one market decision and then returns to v9",
        "alpha is selected only from development-seed validation",
        "the model is not submission-ready without full policy rollouts",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evaluation, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"States: {evaluation['states']}")
    print(f"Model: {evaluation['model']}")
    print(f"V9: {evaluation['v9_behavior']}")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()