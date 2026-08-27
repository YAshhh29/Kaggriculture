"""Prepare the opponent-aware future-labor policy for Kaggle."""

from __future__ import annotations

import ast
import hashlib
import json
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
FROZEN_SUBMISSION_ID = 55821334
FROZEN_SHA256 = "200fef67c5a8e8b001b4a54986bb853d22b80f869af7460b67ec8eda169c70e3"


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
    if not OUTPUT.is_file() or not MANIFEST.is_file():
        raise SystemExit(
            "Future-labor submission 55821334 is immutable; "
            "the frozen package and manifest must both remain present"
        )
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    submission_id = manifest.get("kaggle", {}).get("submission_id")
    if submission_id != FROZEN_SUBMISSION_ID:
        raise SystemExit(
            "Frozen future-labor manifest does not identify submission "
            "55821334"
        )
    package_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    if package_hash != FROZEN_SHA256:
        raise SystemExit(
            "Frozen future-labor package hash does not match its "
            "uploaded artifact"
        )
    raise SystemExit(
        "Future-labor submission 55821334 is immutable; "
        "build_source() remains available for tests"
    )


if __name__ == "__main__":
    main()