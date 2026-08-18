"""Prepare a self-contained one-goose Kaggriculture submission."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN_PATH = ROOT / "main.py"
GOOSE_PATH = ROOT / "experimental_goose_agent.py"
OUTPUT = ROOT / "submission-goose/main.py"
MANIFEST = ROOT / "submission-goose/manifest.json"


def _without_future_import(module: ast.Module) -> list[ast.stmt]:
    return [
        node
        for node in module.body
        if not isinstance(node, ast.ImportFrom) or node.module != "__future__"
    ]


def main() -> None:
    base = ast.parse(MAIN_PATH.read_text(encoding="utf-8"))
    goose = ast.parse(GOOSE_PATH.read_text(encoding="utf-8"))
    base.body = [
        node
        for node in _without_future_import(base)
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    goose.body = [
        node
        for node in _without_future_import(goose)
        if not (
            isinstance(node, ast.ImportFrom)
            and node.module == "main"
        )
    ]
    combined = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__",
                names=[ast.alias(name="annotations")],
                level=0,
            ),
            *base.body,
            *goose.body,
        ],
        type_ignores=[],
    )
    source = ast.unparse(ast.fix_missing_locations(combined)) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    MANIFEST.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "competition": "kaggriculture",
                "agent": "main.py",
                "sha256": digest,
                "source_files": ["../main.py", "../experimental_goose_agent.py"],
                "candidate_source_sha256": hashlib.sha256(
                    GOOSE_PATH.read_bytes()
                ).hexdigest(),
                "policy": "six wheat plots plus one near-shed goose",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Submission agent: {OUTPUT}")
    print(f"SHA-256: {digest}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
