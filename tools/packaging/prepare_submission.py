"""Prepare a clean single-file Kaggriculture submission with a hash manifest."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE = PROJECT_ROOT / "main.py"
OUTPUT_DIRECTORY = PROJECT_ROOT / "submissions" / "legacy" / "baseline"
OUTPUT_AGENT = OUTPUT_DIRECTORY / "main.py"
MANIFEST = OUTPUT_DIRECTORY / "manifest.json"


def main() -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, OUTPUT_AGENT)
    digest = hashlib.sha256(OUTPUT_AGENT.read_bytes()).hexdigest()
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "competition": "kaggriculture",
        "agent": "main.py",
        "sha256": digest,
        "source": "../../../main.py",
        "policy": "v9 six-wheat price-aware baseline",
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Submission agent: {OUTPUT_AGENT}")
    print(f"SHA-256: {digest}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()