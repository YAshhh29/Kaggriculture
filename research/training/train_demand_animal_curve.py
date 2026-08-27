"""Train demand-animal trees and emit a held-out learning curve."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from policies.demand_animal_policy import DEMAND_ANIMAL_FEATURE_NAMES
from research.evaluation.evaluate_demand_animal_selector import evaluate
from research.training.train_macro_selector import train_tree


def learning_curve(
    training: list[dict[str, Any]],
    validation: list[dict[str, Any]],
    sizes: tuple[int, ...],
    *,
    max_depth: int,
    min_leaf: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    points = []
    final_model: dict[str, Any] = {"arm": 0}
    for requested_size in sizes:
        size = min(requested_size, len(training))
        subset = training[:size]
        model, _ = train_tree(
            subset,
            max_depth=max_depth,
            min_leaf=min(min_leaf, max(1, size // 4)),
            feature_names=DEMAND_ANIMAL_FEATURE_NAMES,
        )
        result = evaluate(model, validation)
        points.append(
            {
                "training_contexts": size,
                **result,
            }
        )
        if size == len(training):
            final_model = model
    return points, final_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("training", type=Path)
    parser.add_argument("validation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-output", type=Path, required=True)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--min-leaf", type=int, default=6)
    args = parser.parse_args()
    training = json.loads(args.training.read_text(encoding="utf-8"))[
        "records"
    ]
    validation = json.loads(args.validation.read_text(encoding="utf-8"))[
        "records"
    ]
    sizes = tuple(
        sorted(
            {
                min(size, len(training))
                for size in (8, 16, 32, 48, 64, len(training))
            }
        )
    )
    points, model = learning_curve(
        training,
        validation,
        sizes,
        max_depth=args.max_depth,
        min_leaf=args.min_leaf,
    )
    report = {
        "training_dataset": str(args.training),
        "validation_dataset": str(args.validation),
        "max_depth": args.max_depth,
        "min_leaf": args.min_leaf,
        "points": points,
        "model": model,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.model_output.write_text(
        json.dumps({"model": model}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(points, indent=2))
    print(f"Curve: {args.output}")
    print(f"Model: {args.model_output}")


if __name__ == "__main__":
    main()
