"""Prepare the frozen scale policy as one self-contained Kaggle submission."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    ROOT / "main.py",
    ROOT / "agents" / "experimental_goose_agent.py",
    ROOT / "agents" / "experimental_hands_agent.py",
    ROOT / "agents" / "experimental_scale_agent.py",
)
OUTPUT = ROOT / "submission-scale" / "main.py"
MANIFEST = ROOT / "submission-scale" / "manifest.json"
LOCAL_MODULES = {
    "main",
    "experimental_goose_agent",
    "experimental_hands_agent",
}
HELPER_FUNCTIONS = {
    "experimental_goose_agent.py": {"_shed_access_tiles"},
    "experimental_hands_agent.py": {"_distance", "_task_groups"},
}
SCALE_RENAMES = {
    "_hire_orders": "_scale_hire_orders",
    "_market_orders": "_scale_market_orders",
}


class _RenameScaleSymbols(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node.name = SCALE_RENAMES.get(node.name, node.name)
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = SCALE_RENAMES.get(node.id, node.id)
        return node


def _module_body(
    path: Path,
    *,
    keep_agent: bool,
) -> list[ast.stmt]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    body = []
    selected_functions = HELPER_FUNCTIONS.get(path.name)
    for node in module.body:
        if selected_functions is not None and not (
            isinstance(node, ast.FunctionDef)
            and node.name in selected_functions
        ):
            continue
        if isinstance(node, ast.ImportFrom) and (
            node.module == "__future__" or node.module in LOCAL_MODULES
            or (
                node.module is not None
                and node.module.startswith(("agents.", "policies.", "core."))
            )
        ):
            continue
        if (
            not keep_agent
            and isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        ):
            continue
        body.append(node)
    if path.name == "experimental_scale_agent.py":
        body = [
            _RenameScaleSymbols().visit(node)
            for node in body
        ]
    return body


def main() -> None:
    body: list[ast.stmt] = [
        ast.ImportFrom(
            module="__future__",
            names=[ast.alias(name="annotations")],
            level=0,
        )
    ]
    for index, path in enumerate(SOURCE_PATHS):
        body.extend(
            _module_body(
                path,
                keep_agent=index == len(SOURCE_PATHS) - 1,
            )
        )
        if index == 0:
            body.append(
                ast.Assign(
                    targets=[ast.Name(id="decide_wheat", ctx=ast.Store())],
                    value=ast.Name(id="decide", ctx=ast.Load()),
                )
            )
    combined = ast.Module(body=body, type_ignores=[])
    source = ast.unparse(ast.fix_missing_locations(combined)) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    candidate_digest = hashlib.sha256(
        SOURCE_PATHS[-1].read_bytes()
    ).hexdigest()
    MANIFEST.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "competition": "kaggriculture",
                "agent": "main.py",
                "sha256": digest,
                "candidate_source_sha256": candidate_digest,
                "source_files": [
                    f"../{path.name}"
                    if path.name == "main.py"
                    else f"../{path.name}"
                    for path in SOURCE_PATHS
                ],
                "policy": (
                    "eight daily hands, sixteen wheat, four cows, four sheep, "
                    "daily feed, CARE, staged expansion, no land"
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Submission agent: {OUTPUT}")
    print(f"SHA-256: {digest}")
    print(f"Candidate source SHA-256: {candidate_digest}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()