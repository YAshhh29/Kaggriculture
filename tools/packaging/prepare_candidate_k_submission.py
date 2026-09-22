"""Package Candidate K into a single standalone ``main.py``.

K runs H2's whole recorded route for the opening and hands the farm to J's
reactive engine at day 12. That makes it a harder packaging problem than
either agent alone: a Kaggle submission is one file, and this one file has
to hold two complete, independently-authored agents without either
clobbering the other.

Flat inlining -- the approach J's own packager uses -- is not safe here.
H2 defines 83 top-level functions and three classes (``_View``,
``Chassis``, ``FarmView``); J defines dozens of its own. Concatenated into
one namespace, an unknown number of those names collide and one agent
silently rewrites the other's helpers.

The first version of this packager solved that by embedding each agent as
a base64 blob and running it through ``exec(compile(...))`` at import
time, each into its own throwaway namespace. That was verified correct --
matched the source action by action, 719 of 719 steps -- but both this
and J's own conventionally-inlined submission failed Kaggle's validation
episode for a reason eight separate local hypotheses could not reproduce.
The blob-and-exec approach is the one structural thing neither this
project's other packaged files nor any of the seven public notebooks read
for this project do at runtime -- every one of them decodes and verifies
a blob like that at BUILD time, inside their own notebook, and ships the
plain, already-decoded source. So it is gone here too, whether or not it
was the actual cause, replaced by ``namespace_merge.py``: an AST-level
rename of every top-level name H2 and J each define, behind a unique
prefix, then a single flat, ordinary, linearly-compiled file -- the same
shape as everything proven to work. The rename is verified the same way
the blob was: matched against the un-renamed source, 719 of 719 steps.

One thing the rename had to solve that the blob never needed to: H2's own
file layers many versions of ``agent`` by *popping the current one out of
its own namespace by string name* and rebinding a new one over it --
``agent = globals().pop("agent")``, sixteen times through the file. A
plain identifier rename cannot see a string constant, so the sixteen
``globals().pop("agent")`` calls needed rewriting to match, or the
renamed file would have failed with exactly the ``KeyError: 'agent'`` the
first version of this fix did before that was found and handled.

H2's file opens with an attribution block -- Apache-2.0, several named
contributors -- for the public code its opening is built on. Embedding it
byte-for-byte, licence notices included, is not optional; it is the
condition the licence is used under, and it is why this script reads the
file rather than writing a fresh copy of it. The rename changes bound
identifiers only -- comments, strings and the licence text are untouched.

Two properties are checked here rather than assumed, same as J's
packager:

**``agent`` must be the last callable defined in the file**, because
``kaggle_environments`` loads a submission with ``get_last_callable``,
which takes the final callable in the module rather than the one named
``agent``.

**The packaged file must make the same decisions as the source.** A full
game is played with the source agent, every observation it sees is
recorded, and the packaged file is fed the same sequence and compared
action by action -- across the splice, so both the H2 phase and the J
phase are exercised in one run.

    python -m tools.packaging.prepare_candidate_k_submission
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "submissions" / "candidate-k" / "main.py"
H2_SOURCE = ROOT / "submissions" / "candidate-h2" / "main.py"

sys.path.insert(0, str(ROOT))
from tools.packaging.prepare_candidate_j_submission import (  # noqa: E402
    build as build_j, strip_module,
)
from tools.packaging.namespace_merge import merge, merge_file  # noqa: E402

# In dependency order, same two modules J's own packager inlines for
# itself -- K needs the identical pair, plus crew_extra, plus K's own body.
K_PARTS = (
    ROOT / "rl" / "economics.py",
    ROOT / "rl" / "market.py",
    ROOT / "rl" / "crew_extra.py",
)

# The loader block being replaced with an isolated-namespace exec of the
# embedded blob. Matched exactly, once, so a change to candidate_k.py that
# moves this block fails the build loudly instead of packaging stale code.
K_HEADER = """import importlib.util
import json
import os
from pathlib import Path
from typing import Any


_PATH = (Path(__file__).resolve().parents[1] / "submissions"
         / "candidate-h2" / "main.py")
_spec = importlib.util.spec_from_file_location("candidate_k_h2_core", _PATH)
_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)"""


def strip_k_body() -> str:
    """K's own module body, with its own loader block cut out."""
    path = ROOT / "rl" / "candidate_k.py"
    text = strip_module(path)  # drops K's module docstring, as for J's parts
    if K_HEADER not in text:
        raise SystemExit(
            "candidate_k.py's loader block has moved or changed; update "
            "K_HEADER in this script to match before packaging.")
    return text.replace(
        K_HEADER, "import json\nimport os\nfrom typing import Any", 1)


def build() -> str:
    h2_renamed, h2_entry = merge_file(H2_SOURCE, "_H2_")
    j_renamed, j_entry = merge(build_j(), "_J_")
    assert h2_entry == "_H2_agent" and j_entry == "_J_agent", (
        f"unexpected renamed entry points: h2={h2_entry!r} j={j_entry!r}")

    # Both agents are now uniquely prefixed; flat concatenation cannot
    # collide with either. A last check anyway, since a silent collision
    # would not raise -- it would just make one agent quietly answer to
    # the other's name.
    h2_top = {n.name if hasattr(n, "name") else None
             for n in __import__("ast").parse(h2_renamed).body
             if hasattr(n, "name")}
    j_top = {n.name if hasattr(n, "name") else None
            for n in __import__("ast").parse(j_renamed).body
            if hasattr(n, "name")}
    clash = (h2_top & j_top) - {None}
    if clash:
        raise SystemExit(f"H2 and J still share top-level names after "
                         f"renaming: {sorted(clash)}")

    header = [
        '"""Candidate K -- one file, assembled by',
        '   tools/packaging/prepare_candidate_k_submission.py',
        "",
        "   Do not edit this file. Edit rl/candidate_k.py and repackage.",
        "   `agent` must remain the last callable defined here.",
        "",
        "   H2's whole file is merged in below with every one of its",
        "   top-level names prefixed _H2_ -- byte-identical behaviour to",
        "   the original, verified action by action, not just renamed by",
        "   assumption. Its licence notices are reproduced verbatim; only",
        "   bound identifiers were ever touched.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
    ]
    chunks = ["\n".join(header)]
    chunks.append("# --- H2's opening, renamed, not reloaded "
                  + "-" * 20 + "\n")
    chunks.append(h2_renamed)
    for part in K_PARTS:
        chunks.append(f"\n# --- {part.relative_to(ROOT).as_posix()} "
                      + "-" * max(0, 60 - len(part.name)) + "\n")
        chunks.append(strip_module(part))
    chunks.append("\n# --- J's reactive engine, renamed, not reloaded "
                  + "-" * 12 + "\n")
    chunks.append(j_renamed)
    chunks.append("\n# --- rl/candidate_k.py " + "-" * 40 + "\n")
    body = strip_k_body()
    body = body.replace("_core.agent(", "_H2_agent(")
    body = body.replace("_reactive.agent(", "_J_agent(")
    chunks.append(body)
    return "\n".join(chunks) + "\n"


def load_packaged(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_k_packaged", path)
    module = importlib.util.module_from_spec(spec)
    saved = list(sys.path)
    sys.path[:] = [p for p in sys.path
                   if Path(p or ".").resolve() != ROOT.resolve()]
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = saved
    return module


def last_callable_name(path: Path) -> str:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = [node.name for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not names:
        raise SystemExit("packaged file defines no functions at all")
    return names[-1]


def verify(path: Path) -> dict:
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable

    name = last_callable_name(path)
    if name != "agent":
        raise SystemExit(
            f"the last callable in the packaged file is {name!r}, not "
            "'agent'. Kaggle would run that instead.")

    sys.path.insert(0, str(ROOT))
    import rl.candidate_k as source  # noqa: E402

    seen: list[tuple[dict, Any]] = []

    def recorder(observation, configuration=None):
        action = source.agent(observation, configuration)
        seen.append((copy.deepcopy(dict(observation)),
                     copy.deepcopy(action)))
        return action

    # A seed long enough to run well past the day-12 splice, so both the
    # H2 phase and the J phase are exercised by the comparison.
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": 4242,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run([recorder, "random"])
    source_score = float(env.steps[-1][0].get("reward") or 0.0)

    packaged = load_packaged(path)
    if not callable(getattr(packaged, "agent", None)):
        raise SystemExit("packaged main.py does not expose agent()")
    mismatches = []
    for observation, expected in seen:
        got = packaged.agent(observation, None)
        if got != expected:
            mismatches.append({"step": observation.get("step"),
                               "expected": expected, "got": got})
            if len(mismatches) >= 3:
                break
    if mismatches:
        raise SystemExit("packaged agent diverges from the source:\n"
                         + json.dumps(mismatches, indent=1)[:2000])

    played = get_last_callable(path.read_text(encoding="utf-8"))
    env2 = make("kaggriculture",
                configuration={"episodeSteps": 720, "seed": 909,
                               "runTimeout": 36000, "actTimeout": 60},
                debug=False)
    env2.run([played, "random"])
    final = env2.steps[-1]
    score = float(final[0].get("reward") or 0.0)
    status = str(final[0].get("status"))
    if status != "DONE":
        raise SystemExit(f"packaged file did not finish cleanly: {status}")
    if score < 30_000:
        raise SystemExit(f"packaged file scored {score:,.0f} against random, "
                         "far too low to be the real agent")
    return {"last_callable": name, "source_score": source_score,
            "packaged_score": score, "steps_compared": len(seen),
            "bytes": path.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(), encoding="utf-8")
    print(f"wrote {args.out.relative_to(ROOT).as_posix()}")
    report = verify(args.out)
    print("\nverified:")
    for key, value in report.items():
        if isinstance(value, float):
            print(f"  {key:16s} {value:,.0f}")
        else:
            print(f"  {key:16s} {value}")
    print("\n  agent() is the last callable, the packaged file makes the same")
    print("  decisions as the source across the H2-to-J splice, and it plays")
    print("  a clean game when loaded by path the way Kaggle loads it.")


if __name__ == "__main__":
    main()
