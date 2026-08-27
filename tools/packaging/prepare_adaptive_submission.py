"""Prepare the adaptive counterpolicy as one Kaggle-loadable file."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging.prepare_center_out_submission import build_source as build_center_out


ROOT = Path(__file__).resolve().parents[2]
THROUGHPUT_PATH = ROOT / "agents" / "experimental_throughput_agent.py"
PREMIUM_PATH = ROOT / "agents" / "experimental_premium_throughput_agent.py"
ADAPTIVE_PATH = ROOT / "agents" / "experimental_adaptive_counter_agent.py"
SOURCE_PATHS = (THROUGHPUT_PATH, PREMIUM_PATH, ADAPTIVE_PATH)
OUTPUT = ROOT / "submissions" / "legacy" / "adaptive" / "main.py"
MANIFEST = ROOT / "submissions" / "legacy" / "adaptive" / "manifest.json"
LOCAL_MODULES = {
    "experimental_center_out_agent",
    "experimental_hands_agent",
    "experimental_lifecycle_agent",
    "experimental_premium_throughput_agent",
    "experimental_scale_agent",
    "experimental_throughput_agent",
    "experimental_zoned_agent",
}


def _source_body(path: Path, *, keep_agent: bool) -> list[ast.stmt]:
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
        and not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
            and not keep_agent
        )
    ]


def build_source() -> str:
    base = ast.parse(build_center_out())
    base.body = [
        node
        for node in base.body
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name == "agent"
        )
    ]
    base.body.extend(_source_body(THROUGHPUT_PATH, keep_agent=False))
    base.body.extend(_source_body(PREMIUM_PATH, keep_agent=False))
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="decide_premium", ctx=ast.Store())],
            value=ast.Name(id="decide", ctx=ast.Load()),
        )
    )
    base.body.extend(_source_body(ADAPTIVE_PATH, keep_agent=True))
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    for path in SOURCE_PATHS:
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


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
                "combined_source_sha256": combined_source_hash(),
                "source_files": [
                    f"../../../agents/{path.name}" for path in SOURCE_PATHS
                ],
                "policy": (
                    "opponent-aware one/two-land selection, paired crop "
                    "admission, stable quadrant crews, affordability-filtered "
                    "orders, protected animal service, exact crop cleanup"
                ),
                "status": "exploratory submission approved by user",
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
