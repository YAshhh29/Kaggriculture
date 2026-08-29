"""Prepare the tiered value-fertilizer policy for Kaggle."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging.prepare_future_labor_submission import (
    SOURCE_PATHS as FUTURE_SOURCE_PATHS,
    build_source as build_future_labor,
)


ROOT = Path(__file__).resolve().parents[2]
ROUTING_PATH = ROOT / "core" / "routing.py"
LIVE_FEATURES_PATH = ROOT / "policies" / "live_macro_features.py"
FERTILIZER_POLICY_PATH = ROOT / "policies" / "fertilizer_policy.py"
GUARDED_SERVICE_PATH = (
    ROOT / "agents" / "experimental_guarded_colocated_crop_service_agent.py"
)
LATE_VALUE_PATH = (
    ROOT / "agents" / "experimental_late_value_fertilizer_agent.py"
)
IDLE_VALUE_PATH = (
    ROOT / "agents" / "experimental_idle_value_fertilizer_agent.py"
)
TIERED_VALUE_PATH = (
    ROOT / "agents" / "experimental_tiered_value_fertilizer_agent.py"
)
SOURCE_PATHS = (
    *FUTURE_SOURCE_PATHS,
    ROUTING_PATH,
    LIVE_FEATURES_PATH,
    FERTILIZER_POLICY_PATH,
    GUARDED_SERVICE_PATH,
    LATE_VALUE_PATH,
    IDLE_VALUE_PATH,
    TIERED_VALUE_PATH,
)
OUTPUT = ROOT / "submissions" / "tiered-fertilizer" / "main.py"
MANIFEST = ROOT / "submissions" / "tiered-fertilizer" / "manifest.json"
FROZEN_SUBMISSION_ID = 55858409
FROZEN_SHA256 = (
    "bc0ab6cbc74cfc6f1f5e8ba02c42292b6cda718dc805b611d343e41587ac71e9"
)
MODULE_RENAMES = {
    GUARDED_SERVICE_PATH: {
        "SELECTION_DAY": "CROP_SERVICE_SELECTION_DAY",
    },
    TIERED_VALUE_PATH: {
        "SELECTION_DAY": "TIERED_SELECTION_DAY",
        "SELECTION_HOUR": "TIERED_SELECTION_HOUR",
    },
}


class _RenameModuleSymbols(ast.NodeTransformer):
    def __init__(self, renames: dict[str, str]) -> None:
        self._renames = renames

    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = self._renames.get(node.id, node.id)
        return node


def _source_body(
    path: Path,
    *,
    include_agent: bool = False,
    excluded_functions: frozenset[str] = frozenset(),
) -> list[ast.stmt]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    body = [
        node
        for node in module.body
        if not (
            (
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
            or (
                isinstance(node, ast.FunctionDef)
                and node.name == "agent"
                and not include_agent
            )
            or (
                isinstance(node, ast.FunctionDef)
                and node.name in excluded_functions
            )
        )
    ]
    renames = MODULE_RENAMES.get(path, {})
    return [_RenameModuleSymbols(renames).visit(node) for node in body]


def build_source() -> str:
    """Flatten the validated dependency chain into one Python module."""
    base = ast.parse(build_future_labor())
    base.body = [
        node
        for node in base.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    base.body.extend(_source_body(ROUTING_PATH))
    base.body.extend(_source_body(LIVE_FEATURES_PATH))
    base.body.extend(_source_body(FERTILIZER_POLICY_PATH))
    base.body.extend(
        _source_body(
            GUARDED_SERVICE_PATH,
            excluded_functions=frozenset({"decide"}),
        )
    )
    base.body.extend(
        _source_body(
            LATE_VALUE_PATH,
            excluded_functions=frozenset({"decide"}),
        )
    )
    base.body.extend(_source_body(IDLE_VALUE_PATH))
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="decide_idle", ctx=ast.Store())],
            value=ast.Name(id="decide", ctx=ast.Load()),
        )
    )
    base.body.extend(_source_body(TIERED_VALUE_PATH, include_agent=True))
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    for path in SOURCE_PATHS:
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _refuse_submitted_overwrite() -> None:
    if not OUTPUT.is_file() or not MANIFEST.is_file():
        raise SystemExit(
            f"Tiered-fertilizer submission {FROZEN_SUBMISSION_ID} is "
            "immutable; the package and manifest must both remain present"
        )
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    submission_id = manifest.get("kaggle", {}).get("submission_id")
    if submission_id != FROZEN_SUBMISSION_ID:
        raise SystemExit(
            "Frozen tiered-fertilizer manifest does not identify "
            f"submission {FROZEN_SUBMISSION_ID}"
        )
    actual_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    if actual_hash != FROZEN_SHA256:
        raise SystemExit(
            "Submitted tiered-fertilizer package hash does not match its "
            "uploaded artifact"
        )
    raise SystemExit(
        f"Tiered-fertilizer submission {FROZEN_SUBMISSION_ID} is immutable"
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
                    "future-labor safety plus four value-ranked strawberry "
                    "fertilizer applications; day-12 price selects "
                    "colocated-only or two-step idle-carrier staging"
                ),
                "validation": {
                    "captured_ladder_contexts": 33,
                    "own_reward": "30 improved, 3 tied, 0 worse",
                    "mean_own_reward_delta": 1220.21,
                    "captured_losses_converted": 2,
                    "captured_wins_preserved": 17,
                    "spent_broad_gate": (
                        "31-17 candidate and control on seeds 219-221; "
                        "+768.02 candidate mean-margin delta"
                    ),
                },
                "kaggle": {
                    "submission_id": FROZEN_SUBMISSION_ID,
                    "submitted_at": "2026-08-29T03:18:16.050Z",
                    "uploaded_bytes": 177080,
                    "validation_episode_id": 102172512,
                    "validation_rewards": [49447, 49745],
                    "initial_score": 600.0,
                    "public_leaderboard_selected": False,
                    "incumbent_submission_id": 55821334,
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
