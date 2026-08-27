"""Prepare deadline-tapered wheat capacity for Kaggle."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging.prepare_adaptive_submission import (
    ADAPTIVE_PATH,
    LOCAL_MODULES,
    PREMIUM_PATH,
    THROUGHPUT_PATH,
    build_source as build_adaptive,
)


ROOT = Path(__file__).resolve().parents[2]
DEADLINE_PATH = ROOT / "agents" / "experimental_deadline_tapered_wheat_agent.py"
SOURCE_PATHS = (
    THROUGHPUT_PATH,
    PREMIUM_PATH,
    ADAPTIVE_PATH,
    DEADLINE_PATH,
)
OUTPUT = ROOT / "submissions" / "deadline" / "main.py"
MANIFEST = ROOT / "submissions" / "deadline" / "manifest.json"


def _source_body(path: Path) -> list[ast.stmt]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in module.body
        if not (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "__future__"
                or node.module in LOCAL_MODULES
                or (
                    node.module is not None
                    and node.module.startswith("experimental_")
                )
                or (
                    node.module is not None
                    and node.module.startswith(("agents.", "policies.", "core."))
                )
            )
        )
    ]


def build_source() -> str:
    base = ast.parse(build_adaptive())
    base.body = [
        node
        for node in base.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    base.body.extend(_source_body(DEADLINE_PATH))
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
                    f"../{path.name}" for path in SOURCE_PATHS
                ],
                "policy": (
                    "three-quadrant wheat capacity, paired planting, "
                    "mature-crop deadline priority, stable crews, and "
                    "deadline-safe workforce taper"
                ),
                "promotion_evidence": {
                    "development_vs_compact": "10-0",
                    "fresh_six_policy_league": "60-0",
                    "elite_replay_controls": "0-4",
                    "current_top_mean_coins": 50463.5,
                    "rank_two_mean_coins": 68335.0,
                },
                "kaggle": {
                    "submission_id": 55795843,
                    "uploaded_bytes": 112839,
                    "validation_episode_id": 100091628,
                    "validation_rewards": [41908, 39495],
                    "initial_score": 600.0,
                },
                "status": "submitted to Kaggle; validation complete",
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
