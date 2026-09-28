"""Pull the source of a public Kaggriculture notebook, for reading.

The competition's strong agents are published as Kaggle notebooks. This
fetches one's source so its *mechanisms* can be read and understood -- what
it measures, when it acts -- rather than copied.

    KAGGLE_API_TOKEN=... python -m tools.data.fetch_public_notebook \\
        nathanjacob/kaggriculture-pipe-7-wheat-microstructure ...

Sources land in kaggle_cache/notebooks/<user>__<slug>.py (notebook cells are
concatenated in order). Nothing is executed.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "kaggle_cache" / "notebooks"
PULL = "https://www.kaggle.com/api/v1/kernels/pull"


def source_of(payload: dict) -> str:
    """The notebook's code, cells joined in order, or the script's text."""
    blob = payload.get("blob") or {}
    text = blob.get("source") or ""
    if not text:
        return ""
    if (blob.get("kernelType") or payload.get("metadata", {})
            .get("kernelTypeNullable")) != "notebook":
        return text
    try:
        book = json.loads(text)
    except json.JSONDecodeError:
        return text
    cells = []
    for cell in book.get("cells") or []:
        body = cell.get("source")
        body = "".join(body) if isinstance(body, list) else str(body or "")
        if cell.get("cell_type") == "code":
            cells.append(body)
        elif body.strip():
            cells.append("\n".join("# " + line
                                   for line in body.splitlines()))
    return "\n\n# ---- cell ----\n".join(cells)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebooks", nargs="+",
                        help="user/slug, or a full kaggle.com/code URL")
    parser.add_argument("--pause", type=float, default=1.0)
    args = parser.parse_args()

    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment")
    OUT.mkdir(parents=True, exist_ok=True)

    for item in args.notebooks:
        ref = item.split("kaggle.com/code/")[-1].strip("/ ")
        user, _, slug = ref.partition("/")
        if not user or not slug:
            print(f"  skip {item}: expected user/slug")
            continue
        # the API took snake_case until 2026-09-27 and answers 403 to it now
        for params in ({"userName": user, "kernelSlug": slug},
                       {"user_name": user, "kernel_slug": slug}):
            response = requests.get(PULL, params=params,
                                    headers={"Authorization": f"Bearer {token}"}, timeout=120)
            if response.status_code == 200:
                break
        if response.status_code != 200:
            print(f"  {ref}: HTTP {response.status_code}")
            continue
        payload = response.json()
        text = source_of(payload)
        if not text:
            print(f"  {ref}: no source in the response")
            continue
        path = OUT / f"{user}__{slug}.py"
        path.write_text(text, encoding="utf-8")
        title = (payload.get("metadata") or {}).get("titleNullable", "")
        print(f"  {ref}: {len(text):,} chars -> "
              f"{path.relative_to(ROOT)}   ({title})")
        time.sleep(args.pause)


if __name__ == "__main__":
    main()
