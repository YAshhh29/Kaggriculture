"""Prepare the measured zoned expansion as one Kaggle submission file."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASE_PACKAGE = ROOT / "submission-investment" / "main.py"
ZONED_PATH = ROOT / "agents" / "experimental_zoned_agent.py"
EXPANSION_PATH = ROOT / "agents" / "experimental_zoned_expansion_agent.py"
OUTPUT = ROOT / "submission-zoned-expansion" / "main.py"
MANIFEST = ROOT / "submission-zoned-expansion" / "manifest.json"
LOCAL_MODULES = {
    "experimental_hands_agent",
    "experimental_investment_agent",
    "experimental_scale_agent",
    "experimental_zoned_agent",
    "main",
}


def _body(path: Path, *, keep_agent: bool) -> list[ast.stmt]:
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
                    and node.module.startswith(("agents.", "policies."))
                )
            )
        )
        and not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
            and not keep_agent
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
    base.body.extend(_body(ZONED_PATH, keep_agent=False))
    base.body.extend(_body(EXPANSION_PATH, keep_agent=True))
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def main() -> None:
    source = build_source()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    zoned_digest = hashlib.sha256(ZONED_PATH.read_bytes()).hexdigest()
    expansion_digest = hashlib.sha256(EXPANSION_PATH.read_bytes()).hexdigest()
    MANIFEST.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "competition": "kaggriculture",
                "agent": "main.py",
                "sha256": digest,
                "zoned_source_sha256": zoned_digest,
                "expansion_source_sha256": expansion_digest,
                "policy": (
                    "one NE quadrant, ten daily hands, sixteen wheat, "
                    "six cows, eight sheep, paired planting and watering"
                ),
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