"""Prepare Candidate C2 (the Candidate C stack over a second distilled elite route)."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.packaging.prepare_candidate_c_submission import (
    build_source as build_candidate_c_full,
    combined_source_hash as candidate_c_source_hash,
)
from tools.packaging.prepare_distilled_calendar_submission import (
    _EmbedModelPayload,
)


ROOT = Path(__file__).resolve().parents[2]
GIULIO_AGENT_PATH = (
    ROOT / "agents" / "experimental_distilled_elite_giulio_agent.py"
)
GIULIO_MODEL_PATH = (
    ROOT / "models" / "v1327-public-elite-giulio-105144807.json"
)
CANDIDATE_C2_PATH = ROOT / "candidates" / "candidate_c2.py"
SOURCE_PATHS = (GIULIO_AGENT_PATH, GIULIO_MODEL_PATH, CANDIDATE_C2_PATH)
OUTPUT = ROOT / "submissions" / "candidate-c2" / "main.py"
MANIFEST = ROOT / "submissions" / "candidate-c2" / "manifest.json"
MODEL_TYPE = "public_calendar_behavior_clone"
STRIPPED_IMPORT_PREFIXES = ("agents.", "policies.", "core.", "rl.", "stack.", "candidates.")


def load_verified_giulio_model(
    path: Path = GIULIO_MODEL_PATH,
) -> dict[str, Any]:
    model = json.loads(path.read_text(encoding="utf-8"))
    if model.get("model_type") != MODEL_TYPE:
        raise ValueError("Unexpected giulio model type")
    payload = str(model.get("actions_zlib_b64", ""))
    compressed = base64.b64decode(payload, validate=True)
    actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    records = int(model.get("records", -1))
    if (
        not isinstance(actions, list)
        or records != 720
        or len(actions) != records
    ):
        raise ValueError("Giulio model must contain 720 records")
    raw = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != model.get("actions_sha256"):
        raise ValueError("Giulio action hash mismatch")
    return model


class _RenameGiulioSymbols(ast.NodeTransformer):
    """Avoid colliding with the other routes' decide/agent names."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        if node.name == "decide":
            node.name = "elite_giulio_decide"
        elif node.name == "agent":
            return None
        return self.generic_visit(node)


def _strip_imports(module: ast.Module) -> list[ast.stmt]:
    return [
        node
        for node in module.body
        if not (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "__future__"
                or (
                    node.module is not None
                    and node.module.startswith(STRIPPED_IMPORT_PREFIXES)
                )
            )
        )
    ]


def _giulio_agent_body() -> list[ast.stmt]:
    model = load_verified_giulio_model()
    module = ast.parse(GIULIO_AGENT_PATH.read_text(encoding="utf-8"))
    module.body = [
        node
        for node in _strip_imports(module)
        if not (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "MODEL_PATH"
                for target in node.targets
            )
        )
    ]
    module = _EmbedModelPayload(str(model["actions_zlib_b64"])).visit(module)
    renamed: list[ast.stmt] = []
    for node in module.body:
        transformed = _RenameGiulioSymbols().visit(node)
        if transformed is not None:
            renamed.append(transformed)
    return renamed


def _drop_trailing_agent_assign(body: list[ast.stmt]) -> list[ast.stmt]:
    """Drop Candidate C's own final `agent = ...`; C2 defines the last one."""
    return [
        node
        for node in body
        if not (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "agent"
                for target in node.targets
            )
        )
    ]


def build_source() -> str:
    base = ast.parse(build_candidate_c_full())
    base.body = _drop_trailing_agent_assign(base.body)
    base.body.extend(_giulio_agent_body())
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="giulio_route", ctx=ast.Store())],
            value=ast.Name(id="elite_giulio_decide", ctx=ast.Load()),
        )
    )
    base.body.extend(
        _strip_imports(
            ast.parse(CANDIDATE_C2_PATH.read_text(encoding="utf-8"))
        )
    )
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    digest.update(candidate_c_source_hash().encode("utf-8"))
    digest.update(b"\0")
    for path in SOURCE_PATHS:
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    source = build_source()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")
    package_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    model = load_verified_giulio_model()
    MANIFEST.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "competition": "kaggriculture",
                "agent": "main.py",
                "sha256": package_hash,
                "combined_source_sha256": combined_source_hash(),
                "parent_submission": {
                    "note": "built on the Candidate C package",
                    "source_files": [
                        "submissions/candidate-c/main.py (parent)"
                    ],
                },
                "source_files": [
                    "submissions/candidate-c/main.py (parent)",
                    "agents/experimental_distilled_elite_giulio_agent.py",
                    "models/v1327-public-elite-giulio-105144807.json",
                    "candidates/candidate_c2.py",
                ],
                "policy": (
                    "Candidate C's stack (Candidate A guards + Candidate B "
                    "market-timing residuals, land priority off by default) "
                    "over a second elite baseline: a behavior clone of "
                    "\"Giulio Ravasio\", public leaderboard rank #2 (2965.4) "
                    "at capture. Shipped as a comparison arm against "
                    "Candidate C's \"fog flower\" (2882.6) clone so a live "
                    "upload can tell which elite programme actually "
                    "transfers; the two disagree in most head-to-head games, "
                    "unlike two variants differing only by a residual flag."
                ),
                "training_data": {
                    "source_episode_id": model["source_episode_id"],
                    "source_team": model["source_team"],
                    "source_context": model.get("source_leaderboard_context"),
                    "actions_sha256": model["actions_sha256"],
                },
                "validation": {
                    "head_to_head": {
                        "vs_candidate_b": "8-0",
                        "vs_candidate_c1_fog_flower": "2-6",
                        "seeds": "970-973",
                        "seats": "both",
                        "note": (
                            "Fresh seeds neither baseline was recorded on. "
                            "C2 is clearly stronger than Candidate B and "
                            "clearly weaker than Candidate C1 locally; it is "
                            "shipped as a comparison arm, not as a claimed "
                            "improvement over C1."
                        ),
                    },
                    "not_yet_run": (
                        "broad 56-opponent panel (Candidate C1 scored "
                        "218-6 there); captured-live gate; section 9's "
                        "1000-game bar"
                    ),
                },
                "status": (
                    "comparison arm; upload alongside Candidate C to learn "
                    "which elite baseline transfers to live play"
                ),
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
