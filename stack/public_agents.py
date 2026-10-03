"""Published top-of-ladder agents, loaded for local head-to-head measurement.

Local evaluation only, never packaged and never submitted. These are other
people's published notebooks (kaggle_cache/notebooks) and they stay that way:
nothing here is copied into our agents. They are here to answer one question
honestly -- how strong is ours against the real thing.

The agent source is the notebook's ``%%writefile main.py`` cell. Any
packaging tail that would write an archive on import is cut first, and both
files were scanned for process, network and filesystem calls beforehand.
"""

from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "kaggle_cache" / "notebooks"
CUTS = ("tarfile.open(", "ARCHIVE.open(", "with archive_data")
AURAX7 = "aurax7__kaggriculture-shop-router-reactive-v7.py"
V34 = "ahmedberatozer__kaggriculture-v34-observed-market-timing.py"


def _load(name: str):
    text = (NB / name).read_text(encoding="utf-8")
    body = []
    for cell in text.split("# ---- cell ----"):
        stripped = cell.lstrip("\r\n")
        if stripped.startswith("%%writefile main.py"):
            body.append(stripped.split("\n", 1)[1])
    if not body:
        raise RuntimeError(name + ": no %%writefile main.py cell")
    lines = "\n".join(body).splitlines()
    for i, line in enumerate(lines):
        if any(cut in line for cut in CUTS):
            lines = lines[:i]
            break
    namespace: dict = {"__name__": "public_" + name.split("__")[0]}
    exec(compile("\n".join(lines), name, "exec"), namespace)
    entry = namespace.get("agent")
    if entry is None:
        raise RuntimeError(name + ": no agent() in the written module")
    return entry


_CACHE: dict = {}


def _get(name):
    if name not in _CACHE:
        _CACHE[name] = _load(name)
    return _CACHE[name]


def aurax7(observation, configuration=None):
    """aurax7 / kaggriculture-shop-router-reactive-v7."""
    return _get(AURAX7)(observation, configuration)


def v34(observation, configuration=None):
    """ahmedberatozer / kaggriculture-v34-observed-market-timing."""
    return _get(V34)(observation, configuration)
