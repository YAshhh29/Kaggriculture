"""Evaluate learned daily seed admission on paired holdouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from policies.seed_admission_policy import BASELINE, EXTRA, select_seed_admission


def _utility(record: dict[str, Any], arm: int) -> float:
    key = "extra" if arm == EXTRA else "baseline"
    return float(record["outcomes"][key]["utility"])


def _summary(
    model: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = [
        select_seed_admission(model, record["features"])
        for record in records
    ]
    learned = sum(
        _utility(record, arm)
        for record, arm in zip(records, selected)
    )
    baseline = sum(_utility(record, BASELINE) for record in records)
    extra = sum(_utility(record, EXTRA) for record in records)
    oracle = sum(
        max(_utility(record, BASELINE), _utility(record, EXTRA))
        for record in records
    )
    return {
        "states": len(records),
        "extra_choices": selected.count(EXTRA),
        "learned_utility": round(learned, 6),
        "baseline_utility": round(baseline, 6),
        "always_extra_utility": round(extra, 6),
        "learned_gain": round(learned - baseline, 6),
        "always_extra_gain": round(extra - baseline, 6),
        "oracle_gain": round(oracle - baseline, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("datasets", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = json.loads(args.model.read_text(encoding="utf-8"))["model"]
    records = [
        row
        for dataset in args.datasets
        for row in json.loads(dataset.read_text(encoding="utf-8"))["rows"]
    ]
    report = {
        "model": str(args.model),
        "datasets": [str(path) for path in args.datasets],
        "overall": _summary(model, records),
        "by_opponent": {
            opponent: _summary(
                model,
                [
                    record for record in records
                    if record["opponent"] == opponent
                ],
            )
            for opponent in sorted(
                {record["opponent"] for record in records}
            )
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
