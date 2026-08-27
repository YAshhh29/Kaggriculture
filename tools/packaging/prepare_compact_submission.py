"""Prepare the compact macro policy as one Kaggle-loadable file."""

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
COMPACT_PATH = ROOT / "agents" / "experimental_compact_macro_agent.py"
SOURCE_PATHS = (
    THROUGHPUT_PATH,
    PREMIUM_PATH,
    ADAPTIVE_PATH,
    COMPACT_PATH,
)
OUTPUT = ROOT / "submission-compact" / "main.py"
MANIFEST = ROOT / "submission-compact" / "manifest.json"


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
                    and node.module.startswith(("agents.", "policies."))
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
    base.body.extend(_source_body(COMPACT_PATH))
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
                    "shared safe opening through day 8, fixed one-extra-land "
                    "animal macro from day 9, paired crop admission, stable "
                    "quadrant crews, affordability-filtered orders, protected "
                    "animal service, exact crop cleanup"
                ),
                "promotion_evidence": {
                    "versus_submitted_adaptive": "20-0",
                    "fresh_incumbent_suite": "44-6",
                    "top_replay_controls": "0-4",
                },
                "kaggle": {
                    "submission_id": 55778351,
                    "validation_episode_id": 99509927,
                    "validation_rewards": [70494, 71744],
                    "initial_score": 600.0,
                    "public_snapshot": {
                        "games": 3,
                        "wins": 1,
                        "losses": 2,
                        "score": 542.3,
                        "episode_ids": [99514128, 99516420, 99518695],
                    },
                    "failed_predecessor_id": 55778248,
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
