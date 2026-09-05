"""Prepare Candidate D (searched-best elite route under the A+B stack)."""

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
    ROOT / "agents" / "experimental_distilled_elite_andrey_agent.py"
)
ELITE_MODEL_PATH = (
    ROOT / "models" / "v1327-public-elite-andrey-105520725.json"
)
CANDIDATE_D_PATH = ROOT / "rl" / "candidate_d.py"
SOURCE_PATHS = (ELITE_AGENT_PATH, ELITE_MODEL_PATH, CANDIDATE_D_PATH)
OUTPUT = ROOT / "submissions" / "candidate-d" / "main.py"
MANIFEST = ROOT / "submissions" / "candidate-d" / "manifest.json"
MODEL_TYPE = "public_calendar_behavior_clone"
STRIPPED_IMPORT_PREFIXES = ("agents.", "policies.", "core.", "rl.")


def load_verified_model(path: Path = ELITE_MODEL_PATH) -> dict[str, Any]:
    model = json.loads(path.read_text(encoding="utf-8"))
    if model.get("model_type") != MODEL_TYPE:
        raise ValueError("Unexpected Candidate D model type")
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
        raise ValueError("Candidate D model must contain 720 records")
    raw = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != model.get("actions_sha256"):
        raise ValueError("Candidate D action hash mismatch")
    return model


# The bundled Candidate B package already contains a distilled calendar
# agent that defines MODEL_PAYLOAD, CALENDAR_ACTIONS and _load_actions at
# module level. Appending a second clone verbatim would silently rebind
# all three, so the bundled calendar's own decide() would start executing
# this route's tape. Candidate D never selects that route, so the effect
# is inert here -- but it is exactly the kind of quiet aliasing that
# section 9h's packaging bug was made of, so namespace them instead.
_ELITE_RENAMES = {
    "decide": "elite_andrey_decide",
    "MODEL_PAYLOAD": "ANDREY_MODEL_PAYLOAD",
    "CALENDAR_ACTIONS": "ANDREY_ACTIONS",
    "_load_actions": "_load_andrey_actions",
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
    """`decide` in rl/candidate_d.py would shadow the elite route's."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        if node.name == "decide":
            node.name = "candidate_d_decide"
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
            targets=[ast.Name(id="elite_andrey_route", ctx=ast.Store())],
            value=ast.Name(id="elite_andrey_decide", ctx=ast.Load()),
        )
    )
    module = ast.parse(CANDIDATE_D_PATH.read_text(encoding="utf-8"))
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
                    "agents/experimental_distilled_elite_andrey_agent.py",
                    "models/v1327-public-elite-andrey-105520725.json",
                    "rl/candidate_d.py",
                ],
                "policy": (
                    "Candidate A's guarded recovery and live terminal "
                    "liquidation, plus Candidate B's market-timing "
                    "residuals (land priority off), over the physical route "
                    "that won a systematic search. 191 candidate tapes -- "
                    "every side of every cached replay from a team rated "
                    "2400+, on a game that team won -- were scored on our "
                    "own final reward under this exact stack, then the "
                    "leaders were re-screened against real top-500 "
                    "opponents. Episode 105520725 (Andrey Tikhomirov, LB "
                    "2920.0, rank 4) led all three evaluations: the search, "
                    "a 60-game stratified panel (70.0%) and a 184-game full "
                    "panel (64.1%)."
                ),
                "training_data": {
                    "source_episode_id": model["source_episode_id"],
                    "source_team": model["source_team"],
                    "source_context": model.get("source_leaderboard_context"),
                    "actions_sha256": model["actions_sha256"],
                },
                "validation": {
                    "top500_panel": {
                        "games": (
                            "184 per agent "
                            "(92 distinct top-500 opponents x 2 seats)"
                        ),
                        "candidate_d_andrey": (
                            "118/184 = 64.1%, mean 91199, floor 42858"
                        ),
                        "prev_route_giulio": (
                            "108/184 = 58.7%, mean 86859, floor 47689"
                        ),
                        "candidate_c1": (
                            "103/184 = 56.0%, mean 85811, floor 35703"
                        ),
                        "significance": (
                            "paired McNemar: Andrey vs Giulio p=0.19, "
                            "Andrey vs C1 p=0.079 -- NOT significant at "
                            "p<0.05; selection rests on leading three "
                            "independent evaluations, not one test"
                        ),
                    },
                    "stratified_panel": (
                        "60 games: Andrey 70.0%, Giulio 61.7%, C1 48.3%; "
                        "Andrey vs C1 p=0.0124"
                    ),
                    "search": "191 tapes scored on own final reward",
                    "caveat": (
                        "rl/GOAL.md section 9m: win rate against frozen "
                        "tapes overstates live strength by roughly forty "
                        "points. Own-reward improvement (+12% mean, +8% "
                        "floor over C1) is the transferable part of this "
                        "result; the win-rate figures are not a live "
                        "forecast."
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
