"""Prepare the public-calendar behavior clone for Kaggle."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AGENT_PATH = ROOT / "agents" / "experimental_distilled_calendar_agent.py"
MODEL_PATH = ROOT / "models" / "v1327-public-calendar-99058164.json"
EVIDENCE_PATH = (
    ROOT
    / "research"
    / "evaluation"
    / "distilled_calendar_validation_2026-08-31.json"
)
SOURCE_PATHS = (AGENT_PATH, MODEL_PATH)
OUTPUT = ROOT / "submissions" / "distilled-calendar" / "main.py"
MANIFEST = ROOT / "submissions" / "distilled-calendar" / "manifest.json"
MODEL_TYPE = "public_calendar_behavior_clone"
SIMULATOR_VERSION = "1.32.7"
FROZEN_SUBMISSION_ID = 55910432
FROZEN_SHA256 = (
    "43d24a73c346c7687e574de69b8ffaf0ef959b34649e4e333a70f3f6c44b0976"
)
FROZEN_BYTES = 19561


def load_verified_model(path: Path = MODEL_PATH) -> dict[str, Any]:
    model = json.loads(path.read_text(encoding="utf-8"))
    if model.get("model_type") != MODEL_TYPE:
        raise ValueError("Unexpected public-calendar model type")
    if model.get("simulator_version") != SIMULATOR_VERSION:
        raise ValueError("Unexpected public-calendar simulator version")
    payload = str(model.get("actions_zlib_b64", ""))
    try:
        compressed = base64.b64decode(payload, validate=True)
        actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, zlib.error) as error:
        raise ValueError("Invalid public-calendar action payload") from error
    records = int(model.get("records", -1))
    if (
        not isinstance(actions, list)
        or records != 720
        or len(actions) != records
    ):
        raise ValueError("Public-calendar model must contain 720 records")
    raw = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != model.get("actions_sha256"):
        raise ValueError("Public-calendar action hash mismatch")
    return model


def load_verified_evidence(
    package_hash: str,
    model: dict[str, Any],
) -> dict[str, Any]:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    source = evidence.get("training_data", {})
    if evidence.get("simulator_version") != SIMULATOR_VERSION:
        raise ValueError("Validation evidence simulator version mismatch")
    if evidence.get("package", {}).get("sha256") != package_hash:
        raise ValueError("Validation evidence package hash mismatch")
    if source.get("replay_sha256") != model.get("replay_sha256"):
        raise ValueError("Validation evidence replay hash mismatch")
    if source.get("actions_sha256") != model.get("actions_sha256"):
        raise ValueError("Validation evidence action hash mismatch")
    return evidence


class _EmbedModelPayload(ast.NodeTransformer):
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        if (
            isinstance(node.target, ast.Name)
            and node.target.id == "MODEL_PAYLOAD"
        ):
            node.value = ast.Constant(value=self._payload)
        return self.generic_visit(node)


def build_source() -> str:
    model = load_verified_model()
    module = ast.parse(AGENT_PATH.read_text(encoding="utf-8"))
    module.body = [
        node
        for node in module.body
        if not (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
        )
        and not (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "MODEL_PATH"
                for target in node.targets
            )
        )
    ]
    module = _EmbedModelPayload(str(model["actions_zlib_b64"])).visit(module)
    return ast.unparse(ast.fix_missing_locations(module)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    for path in SOURCE_PATHS:
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _refuse_submitted_overwrite() -> None:
    if not OUTPUT.is_file() or not MANIFEST.is_file():
        raise SystemExit(
            f"Distilled-calendar submission {FROZEN_SUBMISSION_ID} is "
            "immutable; the package and manifest must both remain present"
        )
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    submission_id = manifest.get("kaggle", {}).get("submission_id")
    if submission_id != FROZEN_SUBMISSION_ID:
        raise SystemExit(
            "Frozen distilled-calendar manifest does not identify "
            f"submission {FROZEN_SUBMISSION_ID}"
        )
    package_bytes = OUTPUT.read_bytes()
    if len(package_bytes) != FROZEN_BYTES:
        raise SystemExit(
            "Submitted distilled-calendar package length does not match "
            "the uploaded artifact"
        )
    if hashlib.sha256(package_bytes).hexdigest() != FROZEN_SHA256:
        raise SystemExit(
            "Submitted distilled-calendar package hash does not match "
            "the uploaded artifact"
        )
    raise SystemExit(
        f"Distilled-calendar submission {FROZEN_SUBMISSION_ID} is immutable"
    )


def main() -> None:
    _refuse_submitted_overwrite()
    source = build_source()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")
    package_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    model = load_verified_model()
    load_verified_evidence(package_hash, model)
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
                    "behavior clone of a public elite action calendar, "
                    "preserving simulator-native no-op and atomic planting "
                    "semantics"
                ),
                "training_data": {
                    "source_episode_id": model["source_episode_id"],
                    "source_team": model["source_team"],
                    "replay_sha256": model["replay_sha256"],
                    "actions_sha256": model["actions_sha256"],
                    "records": model["records"],
                    "license": "Apache-2.0",
                    "license_basis": (
                        "Kaggriculture Rules 1.7 Data Access and Use, "
                        "2.4 Competition Data, and 2.11 Environments & "
                        "Public Availability"
                    ),
                    "distribution_constraint": (
                        "private participant repository; do not publish "
                        "Competition Data to non-participants"
                    ),
                },
                "validation": {
                    "evidence_path": str(EVIDENCE_PATH.relative_to(ROOT)),
                    "evidence_sha256": hashlib.sha256(
                        EVIDENCE_PATH.read_bytes()
                    ).hexdigest(),
                    "source_replay_decisions": "719/719 exact",
                    "package_equivalence": {
                        "seed": 230,
                        "decisions": 1438,
                        "mismatches": 0,
                    },
                    "broad_gate": {
                        "runtime": "standalone package",
                        "seeds": "225-229",
                        "games": 80,
                        "candidate": "72-8",
                        "control": "55-25",
                        "candidate_mean_margin": 48431.57,
                        "control_mean_margin": -4401.48,
                        "errors": 0,
                        "mean_plant_cycles": 160.86,
                        "control_mean_plant_cycles": 77.46,
                    },
                    "hard_holdout": {
                        "runtime": "action-equivalent source",
                        "seeds": "230-234",
                        "games": 60,
                        "candidate": "41-15-4",
                        "control": "10-50-0",
                        "candidate_mean_margin": 24347.3,
                        "control_mean_margin": -31668.1,
                        "errors": 0,
                        "mean_plant_cycles": 154.3,
                        "control_mean_plant_cycles": 77.73,
                    },
                    "limitation": (
                        "open-loop calendar; not a guaranteed leaderboard "
                        "rating or a state-adaptive policy"
                    ),
                },
                "kaggle": {
                    "submission_id": FROZEN_SUBMISSION_ID,
                    "submitted_at": "2026-08-31T07:38:03.267Z",
                    "uploaded_bytes": FROZEN_BYTES,
                    "validation_episode_id": 103922332,
                    "validation_rewards": [47243, 44975],
                    "initial_score": 600.0,
                    "public_leaderboard_selected": False,
                    "incumbent_submission_id": 55887535,
                    "incumbent_score_snapshot": 655.2,
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
