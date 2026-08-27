"""Prepare the demand-aware expansion-animal policy for Kaggle."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging.prepare_learned_service_submission import (
    SOURCE_PATHS as LEARNED_SOURCE_PATHS,
    build_source as build_learned_service,
)


ROOT = Path(__file__).resolve().parents[2]
ECONOMICS_PATH = ROOT / "core" / "economics.py"
DEMAND_POLICY_PATH = ROOT / "policies" / "demand_policy.py"
DEMAND_AWARE_PATH = ROOT / "agents" / "experimental_demand_aware_agent.py"
DEMAND_ANIMAL_PATH = ROOT / "agents" / "experimental_demand_animal_agent.py"
SOURCE_PATHS = (
    *LEARNED_SOURCE_PATHS,
    ECONOMICS_PATH,
    DEMAND_POLICY_PATH,
    DEMAND_AWARE_PATH,
    DEMAND_ANIMAL_PATH,
)
OUTPUT = ROOT / "submissions" / "demand-animal" / "main.py"
MANIFEST = ROOT / "submissions" / "demand-animal" / "manifest.json"


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
    base = ast.parse(build_learned_service())
    base.body = [
        node
        for node in base.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    base.body.extend(_source_body(ECONOMICS_PATH))
    base.body.extend(_source_body(DEMAND_POLICY_PATH))
    base.body.extend(_source_body(DEMAND_AWARE_PATH))
    base.body.extend(_source_body(DEMAND_ANIMAL_PATH))
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
                    "learned safe service plus day-6 shop-demand selection "
                    "for two expansion-animal slots; wheat crop rotation"
                ),
                "promotion_evidence": {
                    "development_vs_submitted": "13-7",
                    "validation_vs_submitted": "7-3",
                    "spent_five-policy_league": "47-3",
                    "fresh_six-policy_league": "23-1 on seeds 186-187",
                    "elite_replay_controls": "0-4 with exact baseline fallback",
                    "learned_three_arm_tree": (
                        "rejected: 35-5 ties fixed cows and trails margin"
                    ),
                    "overnight_shadow_gate": (
                        "92-8 across 100 unseen games versus 89-11 for "
                        "the submitted control; no opponent regression"
                    ),
                },
                "kaggle": {
                    "submission_id": 55817911,
                    "submitted_at": "2026-08-27T12:15:52.800Z",
                    "validation_episode_id": 100869093,
                    "validation_rewards": [58100, 59301],
                    "initial_score": 600.0,
                    "status": "COMPLETE",
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
