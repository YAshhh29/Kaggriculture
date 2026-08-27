"""Fit and evaluate a shallow tree for one-step wheat market choices."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import fmean
from typing import Any


FEATURES = (
    "day",
    "hour",
    "money",
    "wheat_seeds",
    "shed_wheat",
    "carried_wheat",
    "planted_wheat",
    "wheat_market_price",
    "wheat_market_inventory",
)


def fit_tree(
    rows: list[dict[str, Any]],
    max_depth: int = 2,
    min_leaf: int = 2,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("Cannot fit a tree without rows")
    return _fit_node(rows, max_depth, min_leaf, depth=0)


def predict(tree: dict[str, Any], features: dict[str, Any]) -> float:
    node = tree
    while "feature" in node:
        node = (
            node["left"]
            if float(features[node["feature"]]) <= node["threshold"]
            else node["right"]
        )
    return float(node["value"])


def evaluate_leave_one_seed_out(
    rows: list[dict[str, Any]],
    max_depth: int = 2,
    min_leaf: int = 2,
) -> dict[str, Any]:
    predictions = []
    for seed in sorted({int(row["seed"]) for row in rows}):
        training = [row for row in rows if int(row["seed"]) != seed]
        held_out = [row for row in rows if int(row["seed"]) == seed]
        tree = fit_tree(training, max_depth=max_depth, min_leaf=min_leaf)
        for row in held_out:
            predicted_delta = predict(tree, row["features"])
            predicted_choice = "SELL" if predicted_delta > 0 else "HOLD"
            predictions.append(
                _evaluated_row(row, predicted_choice, predicted_delta)
            )

    return {
        "validation": "leave-one-seed-out",
        "seeds": len({int(row["seed"]) for row in rows}),
        "states": len(predictions),
        "model": _strategy_summary(predictions, "model"),
        "v9_behavior": _strategy_summary(predictions, "v9"),
        "always_hold": _strategy_summary(predictions, "always_hold"),
        "always_sell": _strategy_summary(predictions, "always_sell"),
        "predictions": predictions,
    }


def _fit_node(
    rows: list[dict[str, Any]],
    max_depth: int,
    min_leaf: int,
    depth: int,
) -> dict[str, Any]:
    values = [_target(row) for row in rows]
    value = round(fmean(values), 6)
    leaf = {"value": value, "samples": len(rows)}
    if depth >= max_depth or len(rows) < min_leaf * 2:
        return leaf

    parent_error = _squared_error(values)
    best: tuple[float, str, float, list[Any], list[Any]] | None = None
    for feature in FEATURES:
        unique = sorted({float(row["features"][feature]) for row in rows})
        thresholds = [
            (left + right) / 2
            for left, right in zip(unique, unique[1:])
        ]
        for threshold in thresholds:
            left_rows = [
                row
                for row in rows
                if float(row["features"][feature]) <= threshold
            ]
            right_rows = [row for row in rows if row not in left_rows]
            if len(left_rows) < min_leaf or len(right_rows) < min_leaf:
                continue
            error = _squared_error([_target(row) for row in left_rows])
            error += _squared_error([_target(row) for row in right_rows])
            candidate = (error, feature, threshold, left_rows, right_rows)
            if best is None or candidate[:3] < best[:3]:
                best = candidate

    if best is None or best[0] >= parent_error:
        return leaf
    _, feature, threshold, left_rows, right_rows = best
    return {
        "feature": feature,
        "threshold": threshold,
        "samples": len(rows),
        "value": value,
        "left": _fit_node(
            left_rows,
            max_depth,
            min_leaf,
            depth + 1,
        ),
        "right": _fit_node(
            right_rows,
            max_depth,
            min_leaf,
            depth + 1,
        ),
    }


def _target(row: dict[str, Any]) -> float:
    return float(row["outcomes"]["sell_minus_hold_terminal_coins"])


def _squared_error(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = fmean(values)
    return sum((value - mean) ** 2 for value in values)


def _evaluated_row(
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
        "hold_regret": round(best_money - hold_money, 6),
        "sell_regret": round(best_money - sell_money, 6),
    }


def _strategy_summary(
    rows: list[dict[str, Any]], strategy: str
) -> dict[str, Any]:
    field = {
        "model": "model_regret",
        "v9": "v9_regret",
        "always_hold": "hold_regret",
        "always_sell": "sell_regret",
    }[strategy]
    regrets = [float(row[field]) for row in rows]
    regret_by_seed: dict[int, float] = {}
    for row in rows:
        seed = int(row["seed"])
        regret_by_seed[seed] = regret_by_seed.get(seed, 0.0) + float(
            row[field]
        )
    return {
        "total_one_step_regret": round(sum(regrets), 6),
        "mean_one_step_regret": round(fmean(regrets), 6),
        "zero_regret_states": sum(regret == 0 for regret in regrets),
        "regret_by_seed": {
            str(seed): round(regret, 6)
            for seed, regret in sorted(regret_by_seed.items())
        },
        "worst_seed_regret": round(
            max(regret_by_seed.values(), default=0.0),
            6,
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--min-leaf", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    rows = [row for episode in dataset["episodes"] for row in episode["rows"]]
    evaluation = evaluate_leave_one_seed_out(
        rows,
        max_depth=args.max_depth,
        min_leaf=args.min_leaf,
    )
    evaluation["model_configuration"] = {
        "type": "regression_tree",
        "features": list(FEATURES),
        "max_depth": args.max_depth,
        "min_leaf": args.min_leaf,
        "decision": "SELL when predicted sell-minus-hold value is positive",
    }
    evaluation["fitted_tree"] = fit_tree(
        rows,
        max_depth=args.max_depth,
        min_leaf=args.min_leaf,
    )
    evaluation["limitations"] = [
        "each label changes one market decision and then returns to v9",
        "one-step regrets are not additive policy returns",
        "the tree is not submission-ready without full policy rollouts",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evaluation, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"States: {evaluation['states']}")
    print(f"Model: {evaluation['model']}")
    print(f"V9: {evaluation['v9_behavior']}")
    print(f"Tree: {evaluation['fitted_tree']}")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()