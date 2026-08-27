"""Prepare the opponent-aware future-labor policy for Kaggle."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging.prepare_demand_animal_submission import (
    SOURCE_PATHS as DEMAND_SOURCE_PATHS,
    build_source as build_demand_animal,
)


ROOT = Path(__file__).resolve().parents[2]
FUTURE_LABOR_PATH = ROOT / "agents" / "experimental_future_labor_agent.py"
SOURCE_PATHS = (*DEMAND_SOURCE_PATHS, FUTURE_LABOR_PATH)
OUTPUT = ROOT / "submissions" / "future-labor" / "main.py"
MANIFEST = ROOT / "submissions" / "future-labor" / "manifest.json"


def _source_body(path: Path) -> list[ast.stmt]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in module.body
        if not (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "__future__"
                or (
                    node.module is not None
                    and node.module.startswith(
                        ("agents.", "policies.", "core.")
                    )
                )
            )
        )
    ]


def build_source() -> str:
    base = ast.parse(build_demand_animal())
    base.body = [
        node
        for node in base.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    base.body.extend(_source_body(FUTURE_LABOR_PATH))
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    for path in SOURCE_PATHS:
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    source = build_source()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")
    package_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    MANIFEST.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "competition": "kaggriculture",
                "agent": "main.py",
                "sha256": package_hash,
                "combined_source_sha256": combined_source_hash(),
                "source_files": [
                    str(path.relative_to(ROOT)) for path in SOURCE_PATHS
                ],
                "policy": (
                    "demand-animal safety plus a day-6 opponent-aware "
                    "decision to reinvest cheaper cow/goose herd capital "
                    "in one peak-production hand"
                ),
                "promotion_evidence": {
                    "direct_development": (
                        "6-0 versus exact demand-animal package on "
                        "seeds 206-208"
                    ),
                    "first_broad_holdout": (
                        "12-4 versus control 10-6 on seed 212"
                    ),
                    "second_broad_holdout": (
                        "10-6 versus control 9-7 on seed 213"
                    ),
                    "combined_broad_holdout": (
                        "22-10 versus control 19-13; zero errors and "
                        "no opponent-level win regression"
                    ),
                    "elite_replay_controls": (
                        "0-8 combined; top-throughput gap remains"
                    ),
                },
                "status": "packaged; not submitted",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Submission agent: {OUTPUT}")
    print(f"SHA-256: {package_hash}")
    print(f"Combined source SHA-256: {combined_source_hash()}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()