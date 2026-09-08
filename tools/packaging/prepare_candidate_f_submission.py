"""Prepare Candidate F (live-ladder elite route under the A+B stack)."""

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
    ROOT / "agents" / "experimental_distilled_elite_mhuang_agent.py"
)
ELITE_MODEL_PATH = (
    ROOT / "models" / "v1327-live-elite-mhuang-106610780.json"
)
CANDIDATE_F_PATH = ROOT / "rl" / "candidate_f.py"
SOURCE_PATHS = (ELITE_AGENT_PATH, ELITE_MODEL_PATH, CANDIDATE_F_PATH)
OUTPUT = ROOT / "submissions" / "candidate-f" / "main.py"
MANIFEST = ROOT / "submissions" / "candidate-f" / "manifest.json"
MODEL_TYPE = "public_calendar_behavior_clone"
STRIPPED_IMPORT_PREFIXES = ("agents.", "policies.", "core.", "rl.")


def load_verified_model(path: Path = ELITE_MODEL_PATH) -> dict[str, Any]:
    model = json.loads(path.read_text(encoding="utf-8"))
    if model.get("model_type") != MODEL_TYPE:
        raise ValueError("Unexpected Candidate F model type")
    compressed = base64.b64decode(
        str(model.get("actions_zlib_b64", "")), validate=True
    )
    actions = json.loads(zlib.decompress(compressed).decode("utf-8"))
    records = int(model.get("records", -1))
    if (
        not isinstance(actions, list)
        or records != 720
        or len(actions) != records
    ):
        raise ValueError("Candidate F model must contain 720 records")
    raw = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != model.get("actions_sha256"):
        raise ValueError("Candidate F action hash mismatch")
    return model


# The bundled Candidate B package already contains a distilled calendar
# agent that defines MODEL_PAYLOAD, CALENDAR_ACTIONS and _load_actions at
# module level. Appending a second clone verbatim would silently rebind
# all three, so the bundled calendar's own decide() would start executing
# this route's tape. Candidate F never selects that route, so the effect
# is inert here -- but it is exactly the kind of quiet aliasing that
# section 9h's packaging bug was made of, so namespace them instead.
_ELITE_RENAMES = {
    "decide": "elite_mhuang_decide",
    "MODEL_PAYLOAD": "MHUANG_MODEL_PAYLOAD",
    "CALENDAR_ACTIONS": "MHUANG_ACTIONS",
    "_load_actions": "_load_mhuang_actions",
}


class _RenameEliteSymbols(ast.NodeTransformer):
    """Namespace every module-level name this clone would otherwise share."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        if node.name == "agent":
            return None
        node.name = _ELITE_RENAMES.get(node.name, node.name)
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = _ELITE_RENAMES.get(node.id, node.id)
        return node


class _RenameCandidateDSymbols(ast.NodeTransformer):
    """`decide` in rl/candidate_f.py would shadow the elite route's."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        if node.name == "decide":
            node.name = "candidate_f_decide"
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
    model = load_verified_model()
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
    """Drop the embedded Candidate B bundle's own `agent` export.

    Kaggle's loader takes the last callable *value* in the exec namespace by
    insertion order, not a name lookup, and reassigning an existing key does
    not move it. A stray earlier `agent = ...` therefore pins the name near
    the top of the file and the loader picks the wrong callable -- the bug
    that broke Candidate C's first upload (rl/GOAL.md section 9h). Filter
    both the FunctionDef and the Assign spelling.
    """
    return [
        node
        for node in body
        if not (isinstance(node, ast.FunctionDef) and node.name == "agent")
        and not (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "agent"
                for target in node.targets
            )
        )
    ]


def build_source() -> str:
    base = ast.parse(build_candidate_b_full())
    base.body = _drop_top_level_agent(base.body)
    base.body.extend(_elite_agent_body())
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="elite_mhuang_route", ctx=ast.Store())],
            value=ast.Name(id="elite_mhuang_decide", ctx=ast.Load()),
        )
    )
    module = ast.parse(CANDIDATE_F_PATH.read_text(encoding="utf-8"))
    body: list[ast.stmt] = []
    for node in _strip_imports(module):
        body.append(_RenameCandidateDSymbols().visit(node))
    base.body.extend(body)
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
    model = load_verified_model()
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
                    "agents/experimental_distilled_elite_mhuang_agent.py",
                    "models/v1327-live-elite-mhuang-106610780.json",
                    "rl/candidate_f.py",
                ],
                "policy": (
                    "Candidate A's guarded recovery and live terminal "
                    "liquidation, plus Candidate B's market-timing "
                    "residuals (land priority off), over a route captured "
                    "from the CURRENT ladder rather than the 2026-09-04 "
                    "cache. Every route this project could previously "
                    "choose from came from that cache and was screened "
                    "against opponents drawn from it; profiling the live "
                    "corpus showed fourteen of the twenty-four teams we "
                    "are drawn against run one public notebook unmodified "
                    "(5 carrot seeds, 198 wheat, no geese), and the "
                    "previous route shared that fingerprint. All eight "
                    "captured games of this submission were screened "
                    "separately, because tape quality belongs to the game "
                    "rather than the player."
                ),
                "training_data": {
                    "source_episode_id": model["source_episode_id"],
                    "source_team": model["source_team"],
                    "source_team_rating": model.get("source_team_rating"),
                    "source_context": model.get("source_leaderboard_context"),
                    "actions_sha256": model["actions_sha256"],
                },
                "validation": {
                    "selection": (
                        "8 live ladder tapes screened 18 candidates; the "
                        "64 tapes those 8 were drawn from were held out "
                        "until the winner was fixed"
                    ),
                    "ladder_holdout": {
                        "games": (
                            "64 per agent "
                            "(32 held-out live opponents x 2 seats)"
                        ),
                        "candidate_f_mhuang": (
                            "59/64 = 92.2%, mean 78554, median margin "
                            "+18030"
                        ),
                        "prev_route_rb25det": (
                            "24/64 = 37.5%, mean 67514, median margin -3786"
                        ),
                        "candidate_d_andrey": (
                            "26/64 = 40.6%, mean 64501, median margin -1085"
                        ),
                    },
                    "elite_panel": {
                        "games": (
                            "48 per agent (24 tapes from the nine teams "
                            "rated 2765-2882 x 2 seats)"
                        ),
                        "candidate_f_mhuang": (
                            "34/48 = 70.8%, mean 86979, median margin "
                            "+12984"
                        ),
                        "candidate_d_andrey": (
                            "20/48 = 41.7%, mean 74708, median margin -7639"
                        ),
                    },
                    "caveat": (
                        "rl/GOAL.md section 9m: win rate against frozen "
                        "tapes overstates live strength, because a "
                        "recording cannot react to us. The panels above "
                        "are built from current ladder play rather than "
                        "the stale cache that produced section 10.8's "
                        "85-92% figures against a real 45.2%, but they are "
                        "still tapes and are not a live forecast."
                    ),
                },
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
