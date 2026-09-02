"""Prepare Candidate A calendar recovery for Kaggle."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging.prepare_distilled_calendar_submission import (
    MODEL_PATH,
    build_source as build_distilled_calendar,
    combined_source_hash as distilled_source_hash,
    load_verified_model,
)


ROOT = Path(__file__).resolve().parents[2]
ROUTING_PATH = ROOT / "core" / "routing.py"
MACRO_FEATURES_PATH = ROOT / "policies" / "macro_policy.py"
LIVE_FEATURES_PATH = ROOT / "policies" / "live_macro_features.py"
ACTION_SPACE_PATH = ROOT / "rl" / "action_space.py"
FEATURES_PATH = ROOT / "rl" / "features.py"
POLICY_PATH = ROOT / "rl" / "policy.py"
RUNTIME_PATH = ROOT / "rl" / "runtime.py"
CANDIDATE_PATH = ROOT / "rl" / "candidate_a.py"
RECOVERY_PATH = ROOT / "agents" / "experimental_calendar_recovery_agent.py"
SOURCE_PATHS = (
    MODEL_PATH,
    ROUTING_PATH,
    MACRO_FEATURES_PATH,
    LIVE_FEATURES_PATH,
    ACTION_SPACE_PATH,
    FEATURES_PATH,
    POLICY_PATH,
    RUNTIME_PATH,
    CANDIDATE_PATH,
    RECOVERY_PATH,
)
OUTPUT = ROOT / "submissions" / "calendar-recovery" / "main.py"
MANIFEST = ROOT / "submissions" / "calendar-recovery" / "manifest.json"
STRIPPED_IMPORT_PREFIXES = ("agents.", "policies.", "core.", "rl.")


class _RenameCalendarSymbols(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        if node.name == "decide":
            node.name = "calendar_decide"
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


def _source_body(path: Path, *, keep_agent: bool = False) -> list[ast.stmt]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in _strip_imports(module)
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
            and not keep_agent
        )
    ]


def build_source() -> str:
    base = ast.parse(build_distilled_calendar())
    renamed_body: list[ast.stmt] = []
    for node in base.body:
        transformed = _RenameCalendarSymbols().visit(node)
        if transformed is not None:
            renamed_body.append(transformed)
    base.body = renamed_body
    base.body.extend(_source_body(ROUTING_PATH))
    base.body.extend(_source_body(MACRO_FEATURES_PATH))
    base.body.extend(_source_body(LIVE_FEATURES_PATH))
    base.body.extend(_source_body(ACTION_SPACE_PATH))
    base.body.extend(_source_body(FEATURES_PATH))
    base.body.extend(_source_body(POLICY_PATH))
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="calendar", ctx=ast.Store())],
            value=ast.Name(id="calendar_decide", ctx=ast.Load()),
        )
    )
    base.body.extend(_source_body(RUNTIME_PATH))
    base.body.extend(_source_body(CANDIDATE_PATH))
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="_DECIDE", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="build_candidate_a_agent", ctx=ast.Load()),
                args=[],
                keywords=[
                    ast.keyword(
                        arg="baseline",
                        value=ast.Name(id="calendar", ctx=ast.Load()),
                    )
                ],
            ),
        )
    )
    base.body.extend(
        [
            node
            for node in _source_body(RECOVERY_PATH, keep_agent=True)
            if not (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "_DECIDE"
                    for target in node.targets
                )
            )
        ]
    )
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    digest.update(distilled_source_hash().encode("utf-8"))
    digest.update(b"\0")
    for path in SOURCE_PATHS:
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    model = load_verified_model()
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
                "parent_submission": {
                    "submission_id": 55910432,
                    "sha256": (
                        "43d24a73c346c7687e574de69b8ffaf0ef959b34649e4e333a70f3f6c44b0976"
                    ),
                },
                "source_files": [
                    "submissions/distilled-calendar/main.py (parent)",
                    *[str(path.relative_to(ROOT)) for path in SOURCE_PATHS],
                ],
                "policy": (
                    "Crop Dusta public calendar plus guarded weed/setup "
                    "recovery, live terminal liquidation, and stranded "
                    "harvest commitments"
                ),
                "training_data": {
                    "parent_source_episode_id": model["source_episode_id"],
                    "parent_source_team": model["source_team"],
                    "parent_actions_sha256": model["actions_sha256"],
                },
                "validation": {
                    "captured_live_gate": {
                        "record": "21-12",
                        "parent_wins_preserved": "20/20",
                        "loss_conversions": 1,
                        "own_reward_regressions": 0,
                        "reports": [
                            "artifacts/benchmarks/v1327-candidate-a-terminal-live-losses-13.json",
                            "artifacts/benchmarks/v1327-candidate-a-terminal-live-wins-20.json",
                        ],
                    },
                    "fresh_family_gate": {
                        "seeds": "240-249",
                        "games": 120,
                        "control": "93-23",
                        "candidate": "103-17",
                        "errors": 0,
                        "mean_margin_delta": 696.89,
                        "decision": "PROMOTE",
                        "report": (
                            "artifacts/benchmarks/"
                            "v1327-candidate-a-terminal-fresh-gate-240-249.json"
                        ),
                    },
                    "package_equivalence": {
                        "seed": 230,
                        "decisions": 1438,
                        "mismatches": 0,
                    },
                },
                "status": "candidate A package built; upload only after gates",
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
