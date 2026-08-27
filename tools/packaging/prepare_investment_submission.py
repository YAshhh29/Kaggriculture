"""Prepare the frozen investment policy as one Kaggle submission file."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging import prepare_scale_submission


ROOT = Path(__file__).resolve().parents[2]
INVESTMENT_PATH = ROOT / "agents" / "experimental_investment_agent.py"
OUTPUT = ROOT / "submission-investment" / "main.py"
MANIFEST = ROOT / "submission-investment" / "manifest.json"
PACKAGE_RENAMES = {
    "_hire_orders": "_scale_hire_orders",
}


class _RenamePackageSymbols(ast.NodeTransformer):
    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = PACKAGE_RENAMES.get(node.id, node.id)
        return node


def _investment_body() -> list[ast.stmt]:
    module = ast.parse(INVESTMENT_PATH.read_text(encoding="utf-8"))
    body = [
        node
        for node in module.body
        if not (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "__future__"
                or node.module == "experimental_scale_agent"
                or node.module == "main"
                or (
                    node.module is not None
                    and node.module.startswith(("agents.", "policies."))
                )
            )
        )
    ]
    return [_RenamePackageSymbols().visit(node) for node in body]


def main() -> None:
    prepare_scale_submission.main()
    scale_path = prepare_scale_submission.OUTPUT
    scale_module = ast.parse(scale_path.read_text(encoding="utf-8"))
    scale_module.body = [
        node
        for node in scale_module.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    scale_module.body.extend(_investment_body())
    source = ast.unparse(ast.fix_missing_locations(scale_module)) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    candidate_digest = hashlib.sha256(
        INVESTMENT_PATH.read_bytes()
    ).hexdigest()
    MANIFEST.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "competition": "kaggriculture",
                "agent": "main.py",
                "sha256": digest,
                "candidate_source_sha256": candidate_digest,
                "policy": (
                    "pressure-aware investment: up to 10 hands, 12 wheat, "
                    "all land, 6 cows, 12 sheep, daily feed and CARE"
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