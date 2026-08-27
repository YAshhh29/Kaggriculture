"""Prepare the learned service policy as one Kaggle-loadable file."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from prepare_adaptive_submission import LOCAL_MODULES
from prepare_deadline_submission import (
    SOURCE_PATHS as DEADLINE_SOURCE_PATHS,
    build_source as build_deadline,
)


ROOT = Path(__file__).resolve().parent
MACRO_PATH = ROOT / "policies" / "macro_policy.py"
SERVICE_PATH = ROOT / "policies" / "service_policy.py"
RUNTIME_PATH = ROOT / "agents" / "experimental_learned_service_agent.py"
MODEL_PATH = ROOT / "models" / "v1327-service-bandit-depth2.json"
SOURCE_PATHS = (
    *DEADLINE_SOURCE_PATHS,
    MACRO_PATH,
    SERVICE_PATH,
    RUNTIME_PATH,
    MODEL_PATH,
)
OUTPUT = ROOT / "submission-learned-service" / "main.py"
MANIFEST = ROOT / "submission-learned-service" / "manifest.json"
LEARNED_MODULES = {
    *LOCAL_MODULES,
    "learned_service_model",
    "macro_policy",
    "service_policy",
}


def _source_body(path: Path) -> list[ast.stmt]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in module.body
        if not (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "__future__"
                or node.module in LEARNED_MODULES
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
    base = ast.parse(build_deadline())
    base.body = [
        node
        for node in base.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    base.body.extend(_source_body(MACRO_PATH))
    base.body.extend(_source_body(SERVICE_PATH))
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))["model"]
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="SERVICE_MODEL", ctx=ast.Store())],
            value=ast.parse(repr(model), mode="eval").body,
        )
    )
    base.body.extend(_source_body(RUNTIME_PATH))
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
                    "deadline-safe three-quadrant capacity with a frozen "
                    "day-1 contextual selector over baseline and zero-travel "
                    "colocated FEED+CARE service"
                ),
                "promotion_evidence": {
                    "training_contexts": 80,
                    "validation_contexts": 40,
                    "validation": "37-3 learned vs 35-5 baseline",
                    "direct_spent_seed_league": "37-3",
                    "fresh_six_policy_league": "23-1",
                    "fresh_vs_deadline": "3-1",
                    "elite_replay_controls": "0-4 with exact deadline fallback",
                },
                "kaggle": {
                    "submission_id": 55803952,
                    "uploaded_bytes": 133479,
                    "validation_episode_id": 100394606,
                    "validation_rewards": [60004, 57984],
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
