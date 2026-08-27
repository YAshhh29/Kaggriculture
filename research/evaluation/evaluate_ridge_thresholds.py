"""Evaluate confidence thresholds for a fixed ridge market model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.training.train_market_ridge import evaluate_leave_one_seed_out


THRESHOLDS = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--alpha", type=float, default=100.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    rows = [row for episode in dataset["episodes"] for row in episode["rows"]]
    configurations = []
    for threshold in THRESHOLDS:
        evaluation = evaluate_leave_one_seed_out(rows, args.alpha, threshold)
        choices = {
            "HOLD": sum(
                row["model_choice"] == "HOLD"
                for row in evaluation["predictions"]
            ),
            "SELL": sum(
                row["model_choice"] == "SELL"
                for row in evaluation["predictions"]
            ),
        }
        configurations.append(
            {
                "threshold": threshold,
                "model": evaluation["model"],
                "v9_behavior": evaluation["v9_behavior"],
                "predicted_choices": choices,
            }
        )

    selected = min(
        configurations,
        key=lambda item: (
            item["model"]["total_one_step_regret"],
            item["model"]["worst_seed_regret"],
            item["threshold"],
        ),
    )
    report = {
        "dataset": str(args.dataset),
        "alpha": args.alpha,
        "validation": "leave-one-seed-out",
        "selection": "minimum total regret, then worst-seed regret",
        "selected": selected,
        "configurations": configurations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Selected: {selected}")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
