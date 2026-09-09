"""Is the built Candidate G package actually submittable?

Run this after every `prepare_candidate_g_submission`. The point is that a
broken package is invisible until the ladder rejects it, and by then the
submission is spent.

    python -m tools.eval.preflight_candidate_g

Checks, in order of what would hurt most:

1. the built file imports with the repo *off* sys.path, the way Kaggle
   runs it -- a missed local import shows up here and nowhere else;
2. it exposes `agent`;
3. it makes byte-identical decisions to `rl/candidate_g.py` across a whole
   game, so the package is the agent we measured and not a variant;
4. it plays a full game to DONE in seat 0;
5. and in seat 1, since half our games are played there;
6. it never returns a malformed action.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "submissions" / "candidate-g" / "main.py"
ROUTE = "kaggle_cache/live_clones/live_106683123.json"


def load_isolated(path: Path):
    """Import the package with the repo root off sys.path.

    The interpreter's own standard library lives under `.conda` inside the
    repo, so only the root itself may be removed -- filtering every path
    containing the repo name takes the stdlib with it.
    """
    repo = str(ROOT).lower().rstrip("\\/")
    saved = sys.path[:]
    sys.path[:] = [
        p for p in sys.path
        if not (p and p.lower().rstrip("\\/") == repo)
    ]
    try:
        spec = importlib.util.spec_from_file_location("candidate_g_pkg", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved


def valid_action(action) -> bool:
    if not isinstance(action, dict):
        return False
    if not isinstance(action.get("farmer"), list):
        return False
    if not isinstance(action.get("hands"), list):
        return False
    if not isinstance(action.get("market"), list):
        return False
    every = [action["farmer"], *action["hands"], *action["market"]]
    return all(isinstance(a, list) and a and isinstance(a[0], str)
               for a in every)


def main() -> int:
    failures = 0

    def report(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        if not ok:
            failures += 1
        print(f"  {'OK  ' if ok else 'FAIL'}  {name}"
              + (f"   {detail}" if detail else ""))

    if not PACKAGE.exists():
        print(f"no package at {PACKAGE}; run the packager first")
        return 1

    print(f"preflight {PACKAGE.relative_to(ROOT)}")

    try:
        package = load_isolated(PACKAGE)
        report("imports with the repo off sys.path", True)
    except Exception as exc:                     # noqa: BLE001
        report("imports with the repo off sys.path", False, repr(exc))
        return 1

    report("exposes agent()", hasattr(package, "agent"))
    if not hasattr(package, "agent"):
        return 1

    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    import rl.candidate_g as source
    from tools.eval.measure_panel import resolve

    opponent = resolve("clone:" + ROUTE)

    mismatches = 0
    malformed = 0
    seen = 0

    def paired(observation, *rest):
        nonlocal mismatches, malformed, seen
        mine = source.agent(observation)
        theirs = package.agent(json.loads(json.dumps(observation)))
        seen += 1
        if not valid_action(theirs):
            malformed += 1
        if (json.dumps(mine, sort_keys=True)
                != json.dumps(theirs, sort_keys=True)):
            mismatches += 1
        return mine

    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": 11}, debug=False)
    env.run([paired, opponent])
    report("package matches source on every decision", mismatches == 0,
           f"{seen - mismatches}/{seen} identical")
    report("never returns a malformed action", malformed == 0,
           f"{malformed} malformed" if malformed else "")

    for seat, seed in ((0, 11), (1, 29)):
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": seed},
                   debug=False)
        agents = ([package.agent, opponent] if seat == 0
                  else [opponent, package.agent])
        env.run(agents)
        state = env.state[seat]
        report(f"plays a full game in seat {seat}",
               str(state.status) == "DONE",
               f"status {state.status}, reward {state.reward:,.0f}")

    print(f"\n{'PREFLIGHT PASSED' if not failures else f'{failures} FAILURE(S)'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
