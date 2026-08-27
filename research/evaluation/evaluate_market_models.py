"""Evaluate compact market value models with seed-grouped validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.training.train_market_ridge import evaluate_leave_one_seed_out as evaluate_ridge
from research.training.train_market_value_tree import (
    evaluate_leave_one_seed_out as evaluate_tree,
)


TREE_CONFIGURATIONS = [
    (depth, min_leaf)
    for depth in (0, 1, 2, 3)
    for min_leaf in (2, 4, 6, 8, 10)
]
RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0, 1000.0)


def evaluate_grid(rows: list[dict[str, Any]]) -> dict[str, Any]:
    configurations = []
    for depth, min_leaf in TREE_CONFIGURATIONS:
        result = evaluate_tree(
            rows,
            max_depth=depth,
            min_leaf=min_leaf,
        )
        configurations.append(
            _configuration(
                "tree",
                {"max_depth": depth, "min_leaf": min_leaf},
                result,
            )
        )
    for alpha in RIDGE_ALPHAS:
        result = evaluate_ridge(rows, alpha)
        configurations.append(
            _configuration("ridge", {"alpha": alpha}, result)
        )

    v9 = configurations[0]["v9_behavior"]
    qualifying = [
        configuration
        for configuration in configurations
        if (
            configuration["model"]["total_one_step_regret"]
            < v9["total_one_step_regret"]
            and configuration["model"]["worst_seed_regret"]
            < v9["worst_seed_regret"]
            and configuration["predicted_choices"]["HOLD"] > 0
            and configuration["predicted_choices"]["SELL"] > 0
        )
    ]
    selected = min(
        qualifying,
        key=lambda configuration: (
            configuration["model"]["total_one_step_regret"],
            configuration["model"]["worst_seed_regret"],
            configuration["family"],
            json.dumps(configuration["parameters"], sort_keys=True),
        ),
        default=None,
    )
    return {
        "validation": "leave-one-seed-out",
        "selection_gate": (
            "model must beat v9 on both total one-step regret and "
            "worst-seed regret and predict both HOLD and SELL"
        ),
        "states": len(rows),
        "seeds": len({int(row["seed"]) for row in rows}),
        "v9_behavior": v9,
        "qualifying_configurations": len(qualifying),
        "selected_configuration": selected,
        "configurations": configurations,
    }


def _configuration(
    family: str,
    parameters: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "family": family,
        "parameters": parameters,
        "model": result["model"],
        "v9_behavior": result["v9_behavior"],
        "predicted_choices": {
            "HOLD": sum(
                prediction["model_choice"] == "HOLD"
                for prediction in result["predictions"]
            ),
            "SELL": sum(
                prediction["model_choice"] == "SELL"
                for prediction in result["predictions"]
            ),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    rows = [row for episode in dataset["episodes"] for row in episode["rows"]]
    evaluation = evaluate_grid(rows)
    evaluation["dataset"] = str(args.dataset)
    evaluation["limitations"] = [
        "all configurations are selected only on development seeds",
        "one-step counterfactual regrets are not additive full-policy returns",
        "fresh holdout seeds remain untouched until a full policy candidate exists",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evaluation, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"States: {evaluation['states']}")
    print(f"V9: {evaluation['v9_behavior']}")
    print(
        "Qualifying configurations: "
        f"{evaluation['qualifying_configurations']}"
    )
    print(f"Selected: {evaluation['selected_configuration']}")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()