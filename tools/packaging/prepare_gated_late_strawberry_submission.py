"""Prepare the gated late-strawberry policy for Kaggle."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging.prepare_tiered_fertilizer_submission import (
    SOURCE_PATHS as TIERED_SOURCE_PATHS,
    build_source as build_tiered,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = (
    ROOT / "agents" / "experimental_tiered_late_strawberry_agent.py"
)
SOURCE_PATHS = (*TIERED_SOURCE_PATHS, CANDIDATE_PATH)
OUTPUT = ROOT / "submissions" / "gated-late-strawberry" / "main.py"
MANIFEST = ROOT / "submissions" / "gated-late-strawberry" / "manifest.json"
CANDIDATE_RENAMES = {
    "SELECTION_DAY": "LATE_STRAWBERRY_SELECTION_DAY",
}


class _RenameCandidateSymbols(ast.NodeTransformer):
    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = CANDIDATE_RENAMES.get(node.id, node.id)
        return node


def _candidate_body() -> list[ast.stmt]:
    module = ast.parse(CANDIDATE_PATH.read_text(encoding="utf-8"))
    body = [
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
    return [_RenameCandidateSymbols().visit(node) for node in body]


def build_source() -> str:
    """Append the gated late cohort to the standalone tiered policy."""
    base = ast.parse(build_tiered())
    base.body = [
        node
        for node in base.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="decide_tiered", ctx=ast.Store())],
            value=ast.Name(id="decide", ctx=ast.Load()),
        )
    )
    base.body.extend(_candidate_body())
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    for path in SOURCE_PATHS:
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _refuse_submitted_overwrite() -> None:
    if not OUTPUT.is_file() or not MANIFEST.is_file():
        return
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    submission_id = manifest.get("kaggle", {}).get("submission_id")
    if submission_id is None:
        return
    expected_hash = str(manifest.get("sha256", ""))
    actual_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise SystemExit(
            "Submitted gated-late-strawberry package hash does not match "
            "its manifest"
        )
    raise SystemExit(
        f"Gated late-strawberry submission {submission_id} is immutable"
    )


def main() -> None:
    _refuse_submitted_overwrite()
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
                    "tiered four-application fertilizer plus eight late "
                    "strawberry replacements when day-6 strawberry price "
                    "is at least 1.30 and day-9 demand selects strawberry"
                ),
                "validation": {
                    "live_contexts": 27,
                    "live_control": "15-12",
                    "live_candidate": "17-10",
                    "live_own_reward": "2 improved, 25 tied, 0 worse",
                    "fresh_seed_222": (
                        "11-5 candidate and control; +340.31 mean-margin delta"
                    ),
                    "fresh_seed_223": (
                        "11-5 candidate and control; +246.88 mean-margin delta"
                    ),
                    "formal_local_promotion": (
                        "REJECT: broad wins tied despite no regression"
                    ),
                },
                "kaggle": {
                    "submission_id": None,
                    "status": "NOT_SUBMITTED",
                },
                "status": "validated live-measurement candidate",
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
