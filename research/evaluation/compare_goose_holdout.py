"""Create the goose fresh-holdout paired comparison artifact."""

from __future__ import annotations

import json
from pathlib import Path

from research.evaluation.compare_benchmarks import compare_reports


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "artifacts/benchmarks/v1327-goose-cutoff21-holdout-seeds50-59.json"
CONTROL = ROOT / "artifacts/benchmarks/v1327-v9-goose-holdout-seeds50-59.json"
OUTPUT = ROOT / "artifacts/benchmarks/v1327-goose-cutoff21-vs-v9-holdout-paired.json"


def main() -> None:
    comparison = compare_reports(
        json.loads(CANDIDATE.read_text(encoding="utf-8")),
        json.loads(CONTROL.read_text(encoding="utf-8")),
    )
    comparison["candidate_report"] = str(CANDIDATE.relative_to(ROOT))
    comparison["control_report"] = str(CONTROL.relative_to(ROOT))
    OUTPUT.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    print(comparison["summary"]["all_seeds"])
    print(comparison["checks"])


if __name__ == "__main__":
    main()
