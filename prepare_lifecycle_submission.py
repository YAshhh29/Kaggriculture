"""Prepare the selected lifecycle policy as one Kaggle submission file."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASE_PACKAGE = ROOT / "submission-zoned-expansion" / "main.py"
CORE_PATH = ROOT / "agents" / "experimental_lifecycle_agent.py"
WRAPPER_PATH = ROOT / "agents" / "experimental_lifecycle_compact_agent.py"
OUTPUT = ROOT / "submission-lifecycle" / "main.py"
MANIFEST = ROOT / "submission-lifecycle" / "manifest.json"
LOCAL_MODULES = {
    "experimental_hands_agent",
    "experimental_investment_agent",
    "experimental_lifecycle_agent",
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
    base.body.extend(_body(CORE_PATH, keep_agent=False))
    base.body.extend(_body(WRAPPER_PATH, keep_agent=True))
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    for path in (CORE_PATH, WRAPPER_PATH):
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    source = build_source()
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
                "combined_source_sha256": combined_source_hash(),
                "policy": (
                    "ten hands, six animal specialists, two fixed crop "
                    "pairs, one floater, demand-aware wheat admission, "
                    "nearby-only assistance, lifecycle deadlines, "
                    "two-hand final-day animal liquidation"
                ),
                "status": "research package; not submitted",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Submission agent: {OUTPUT}")
    print(f"SHA-256: {digest}")
    print(f"Combined source SHA-256: {combined_source_hash()}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()