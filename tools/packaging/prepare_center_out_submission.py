"""Prepare the center-out challenger as one Kaggle-loadable review file."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_PACKAGE = ROOT / "submissions" / "legacy" / "lifecycle" / "main.py"
SOURCE_PATH = ROOT / "agents" / "experimental_center_out_agent.py"
OUTPUT = ROOT / "submissions" / "legacy" / "center-out" / "main.py"
MANIFEST = ROOT / "submissions" / "legacy" / "center-out" / "manifest.json"
LOCAL_MODULES = {
    "experimental_hands_agent",
    "experimental_investment_agent",
    "experimental_lifecycle_agent",
    "experimental_scale_agent",
    "experimental_zoned_agent",
}


def _source_body(path: Path) -> list[ast.stmt]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in module.body
        if not (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "__future__"
                or node.module in LOCAL_MODULES
                or (
                    node.module is not None
                    and node.module.startswith(("agents.", "policies.", "core."))
                )
            )
        )
    ]


def build_source() -> str:
    base = ast.parse(BASE_PACKAGE.read_text(encoding="utf-8"))
    base.body = [
        node
        for node in base.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    base.body.extend(_source_body(SOURCE_PATH))
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def source_hash() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def main() -> None:
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
                "source_sha256": source_hash(),
                "policy": (
                    "NW-NE-SW center-out layout, balanced cow/sheep cores, "
                    "six managed crop blocks per quadrant, four heavily "
                    "fertilized strawberries, two melon positions"
                ),
                "status": (
                    "research review package; not submitted; starter-safe "
                    "but rejected for submission after 0-10 lifecycle direct gate"
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Submission agent: {OUTPUT}")
    print(f"SHA-256: {package_hash}")
    print(f"Source SHA-256: {source_hash()}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()