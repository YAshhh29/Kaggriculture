"""Prepare Candidate C (elite-pasture route, guarded, market-timing on top)."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.packaging.prepare_candidate_b_submission import (
    build_source as build_candidate_b_full,
    combined_source_hash as candidate_b_source_hash,
)
from tools.packaging.prepare_distilled_calendar_submission import (
    _EmbedModelPayload,
)


ROOT = Path(__file__).resolve().parents[2]
ELITE_AGENT_PATH = (
    ROOT / "agents" / "experimental_distilled_elite_pasture_agent.py"
)
ELITE_MODEL_PATH = (
    ROOT / "models" / "v1327-public-elite-fogflower-105144807.json"
)
CANDIDATE_C_PATH = ROOT / "rl" / "candidate_c.py"
SOURCE_PATHS = (ELITE_AGENT_PATH, ELITE_MODEL_PATH, CANDIDATE_C_PATH)
OUTPUT = ROOT / "submissions" / "candidate-c" / "main.py"
MANIFEST = ROOT / "submissions" / "candidate-c" / "manifest.json"
MODEL_TYPE = "public_calendar_behavior_clone"
STRIPPED_IMPORT_PREFIXES = ("agents.", "policies.", "core.", "rl.")


def load_verified_elite_model(path: Path = ELITE_MODEL_PATH) -> dict[str, Any]:
    model = json.loads(path.read_text(encoding="utf-8"))
    if model.get("model_type") != MODEL_TYPE:
        raise ValueError("Unexpected elite-pasture model type")
    payload = str(model.get("actions_zlib_b64", ""))
    compressed = base64.b64decode(payload, validate=True)
    actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    records = int(model.get("records", -1))
    if (
        not isinstance(actions, list)
        or records != 720
        or len(actions) != records
    ):
        raise ValueError("Elite-pasture model must contain 720 records")
    raw = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != model.get("actions_sha256"):
        raise ValueError("Elite-pasture action hash mismatch")
    return model


class _RenameEliteSymbols(ast.NodeTransformer):
    """Avoid colliding with the calendar route's own decide/agent names."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        if node.name == "decide":
            node.name = "elite_pasture_decide"
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


def _elite_agent_body() -> list[ast.stmt]:
    model = load_verified_elite_model()
    module = ast.parse(ELITE_AGENT_PATH.read_text(encoding="utf-8"))
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
        transformed = _RenameEliteSymbols().visit(node)
        if transformed is not None:
            renamed.append(transformed)
    return renamed


def _drop_top_level_agent(body: list[ast.stmt]) -> list[ast.stmt]:
    return [
        node
        for node in body
        if not (isinstance(node, ast.FunctionDef) and node.name == "agent")
    ]


def build_source() -> str:
    base = ast.parse(build_candidate_b_full())
    base.body = _drop_top_level_agent(base.body)
    base.body.extend(_elite_agent_body())
    candidate_c_module = ast.parse(
        CANDIDATE_C_PATH.read_text(encoding="utf-8")
    )
    elite_import = "agents.experimental_distilled_elite_pasture_agent"
    candidate_c_body = [
        node
        for node in _strip_imports(candidate_c_module)
        if not (
            isinstance(node, ast.ImportFrom)
            and node.module == elite_import
        )
    ]
    # rl/candidate_c.py imports elite_pasture_route and calendar_route;
    # supply both from the bundled definitions instead of module imports.
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="elite_pasture_route", ctx=ast.Store())],
            value=ast.Name(id="elite_pasture_decide", ctx=ast.Load()),
        )
    )
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="calendar_route", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="build_candidate_b_agent", ctx=ast.Load()),
                args=[],
                keywords=[],
            ),
        )
    )
    base.body.extend(candidate_c_body)
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    digest.update(candidate_b_source_hash().encode("utf-8"))
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
    model = load_verified_elite_model()
    MANIFEST.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "competition": "kaggriculture",
                "agent": "main.py",
                "sha256": package_hash,
                "combined_source_sha256": combined_source_hash(),
                "parent_submission": {
                    "note": "built on the Candidate B package",
                    "source_files": [
                        "submissions/candidate-b/main.py (parent)"
                    ],
                },
                "source_files": [
                    "submissions/candidate-b/main.py (parent)",
                    "agents/experimental_distilled_elite_pasture_agent.py",
                    "models/v1327-public-elite-fogflower-105144807.json",
                    "rl/candidate_c.py",
                ],
                "policy": (
                    "Public-state route portfolio (currently a placeholder "
                    "selector that always picks the better-measured route): "
                    "the default route clones a real elite player (\"fog "
                    "flower\", public leaderboard score 2882.6, pulled via "
                    "the Kaggle API from episode 105144807 where they beat "
                    "the leaderboard's #2 team), wrapped in Candidate A's "
                    "guarded recovery/terminal liquidation and Candidate "
                    "B's market-timing residuals. Candidate B itself is "
                    "kept as a second, documented route, not currently "
                    "selectable by any live signal."
                ),
                "training_data": {
                    "elite_route_source_episode_id": model["source_episode_id"],
                    "elite_route_source_team": model["source_team"],
                    "elite_route_source_context": model.get(
                        "source_leaderboard_context"
                    ),
                    "elite_route_actions_sha256": model["actions_sha256"],
                },
                "validation": {
                    "local_fresh_seed_gates": {
                        "elite_route_vs_candidate_b": "20-0",
                        "elite_route_vs_candidate_a": "8-0",
                        "elite_route_stacked_vs_candidate_b": "8-0",
                        "note": (
                            "All fresh seeds (600-602, 700-703, 750-753, "
                            "800-803), both seats, neither this route nor "
                            "Candidate A/B was recorded on any of them. "
                            "Four prior candidates (center_out_agent, the "
                            "best homegrown lineage, and two clones sourced "
                            "from this project's own Kaggle match history) "
                            "were rejected the same way before this one "
                            "was tried -- see rl/GOAL.md section 9c."
                        ),
                    },
                    "not_yet_run": (
                        "captured-live gate; large-scale fresh family gate "
                        "(GOAL.md section 9's full 1000-game/panel "
                        "requirement); package/source/simulator equivalence"
                    ),
                },
                "status": (
                    "strong initial local validation; upload only after "
                    "you decide the remaining gates in rl/GOAL.md section 9 "
                    "are not required first"
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
