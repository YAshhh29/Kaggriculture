"""Every packaged submission, loadable by name, for honest comparison.

These are the files that were actually sent to the ladder -- not the source
modules they were built from. That distinction matters here: a submission is
loaded by `get_last_callable`, which takes the final callable in the file
rather than the one named `agent`, and this project has already put a dead
agent on the ladder because the source module was measured and the packaged
file was not.

    python -m tools.eval.broad_panel candidates.submitted:g --tapes 30
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBS = ROOT / "submissions"

# Ladder order, oldest first. The name on the left is what the project has
# called each agent in its own notes.
PACKAGES = {
    "a": "candidate-a",
    "b": "candidate-b",
    "c": "candidate-c",
    "c2": "candidate-c2",
    "d": "candidate-d",
    "e": "candidate-e",
    "f": "candidate-f",
    "g": "candidate-g",
    "h": "candidate-h",
    "hd": "candidate-hd",
    "h2": "candidate-h2",
    "i": "candidate-i",
    "j": "candidate-j",
}


def _load(folder: str):
    path = SUBS / folder / "main.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("submitted_" + folder, path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return getattr(module, "agent", None)


for _name, _folder in PACKAGES.items():
    globals()[_name] = _load(_folder)
