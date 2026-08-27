"""Train a grouped-CV KNN counterfactual macro selector."""

from __future__ import annotations

import argparse
import json
from math import sqrt
from pathlib import Path
from statistics import fmean
from typing import Any

from policies.macro_policy import FEATURE_NAMES, select_macro_arm


def _normalization(
    records: list[dict[str, Any]],
) -> tuple[dict[str, float], dict[str, float]]:
    means = {
        name: fmean(float(record["features"][name]) for record in records)
        for name in FEATURE_NAMES
    }
    scales = {}
    for name in FEATURE_NAMES:
        variance = fmean(
            (float(record["features"][name]) - means[name]) ** 2
            for record in records
        )
        scales[name] = max(0.1, sqrt(variance))
    return means, scales


def build_model(
    records: list[dict[str, Any]],
    *,
    k: int,
    distance_power: float,
) -> dict[str, Any]:
    means, scales = _normalization(records)
    return {
        "type": "knn",
        "k": min(k, len(records)),
        "distance_power": distance_power,
        "features": list(FEATURE_NAMES),
        "means": means,
        "scales": scales,
        "examples": [
            {
                "features": {
                    name: float(record["features"][name])
                    for name in FEATURE_NAMES
                },
                "outcomes": record["outcomes"],
            }
            for record in records
        ],
    }


def _evaluate(
    model: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, float | int]:
    selected = [
        select_macro_arm(model, record["features"])
        for record in records
    ]
    outcomes = [
        record["outcomes"][str(arm)]
        for record, arm in zip(records, selected)
    ]
    return {
        "games": len(records),
        "wins": sum(outcome["result"] == "win" for outcome in outcomes),
        "utility": round(
            sum(float(outcome["utility"]) for outcome in outcomes),
            4,
        ),
        "mean_margin": round(
            fmean(float(outcome["margin"]) for outcome in outcomes),
            2,
        ),
    }


def _cross_validate(
    records: list[dict[str, Any]],
    *,
    k: int,
    distance_power: float,
) -> dict[str, Any]:
    fold_results = []
    groupings = (
        ("seed", sorted({record["seed"] for record in records})),
        (
            "opponent",
            sorted({record["opponent"] for record in records}),
        ),
    )
    for field, values in groupings:
        for value in values:
            training = [record for record in records if record[field] != value]
            held_out = [record for record in records if record[field] == value]
            if not training or not held_out:
                continue
            model = build_model(
                training,
                k=k,
                distance_power=distance_power,
            )
            fold_results.append(
                {
                    "field": field,
                    "value": value,
                    **_evaluate(model, held_out),
                }
            )
    return {
        "wins": sum(int(fold["wins"]) for fold in fold_results),
        "games": sum(int(fold["games"]) for fold in fold_results),
        "utility": round(
            sum(float(fold["utility"]) for fold in fold_results),
            4,
        ),
        "folds": fold_results,
    }


def train(
    records: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidates = []
    for k in (1, 3, 5, 7, 9, 13):
        for power in (0.0, 1.0, 2.0):
            result = _cross_validate(
                records,
                k=k,
                distance_power=power,
            )
            candidates.append({"k": k, "distance_power": power, **result})
    selected = max(
        candidates,
        key=lambda candidate: (
            candidate["wins"],
            candidate["utility"],
            -candidate["k"],
            -candidate["distance_power"],
        ),
    )
    model = build_model(
        records,
        k=int(selected["k"]),
        distance_power=float(selected["distance_power"]),
    )
    return model, {"selected": selected, "candidates": candidates}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [
        record
        for path in args.datasets
        for record in json.loads(path.read_text(encoding="utf-8"))["records"]
    ]
    model, validation = train(records)
    report = {
        "datasets": [str(path) for path in args.datasets],
        "records": len(records),
        "model": model,
        "cross_validation": validation,
        "training": _evaluate(model, records),
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
