"""Evaluate a learned capacity selector against every fixed template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from policies.capacity_policy import ARM_NAMES, CAPACITY_ARMS
from policies.macro_policy import select_macro_arm


Selector = Callable[[dict[str, Any]], int]


def _summarize(
    records: list[dict[str, Any]],
    selector: Selector,
) -> dict[str, Any]:
    selected = [selector(record) for record in records]
    outcomes = [
        record["outcomes"][str(arm)]
        for record, arm in zip(records, selected)
    ]
    return {
        "games": len(records),
        "wins": sum(outcome["result"] == "win" for outcome in outcomes),
        "losses": sum(outcome["result"] == "loss" for outcome in outcomes),
        "ties": sum(outcome["result"] == "tie" for outcome in outcomes),
        "utility": round(
            sum(float(outcome["utility"]) for outcome in outcomes),
            4,
        ),
        "mean_margin": round(
            sum(float(outcome["margin"]) for outcome in outcomes)
            / len(outcomes),
            2,
        ) if outcomes else None,
        "arm_counts": {
            ARM_NAMES[arm]: selected.count(arm)
            for arm in CAPACITY_ARMS
        },
    }


def evaluate(
    model: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    selectors: dict[str, Selector] = {
        "learned": lambda record: select_macro_arm(
            model,
            record["features"],
        ),
        "oracle": lambda record: int(record["label"]),
    }
    selectors.update(
        {
            ARM_NAMES[arm]: lambda record, fixed=arm: fixed
            for arm in CAPACITY_ARMS
        }
    )
    return {
        name: _summarize(records, selector)
        for name, selector in selectors.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("datasets", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model_report = json.loads(args.model.read_text(encoding="utf-8"))
    records = [
        record
        for dataset in args.datasets
        for record in json.loads(
            dataset.read_text(encoding="utf-8")
        )["records"]
    ]
    opponents = sorted({record["opponent"] for record in records})
    report = {
        "model": str(args.model),
        "datasets": [str(path) for path in args.datasets],
        "overall": evaluate(model_report["model"], records),
        "by_opponent": {
            opponent: evaluate(
                model_report["model"],
                [
                    record for record in records
                    if record["opponent"] == opponent
                ],
            )
            for opponent in opponents
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["overall"], indent=2))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
