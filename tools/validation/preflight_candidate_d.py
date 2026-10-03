"""Every gate Candidate D must clear before an upload, in one command.

Written because the last upload failure (docs/research/GOAL.md section 9h) passed
every check that existed at the time: the packaging bug lived in a place
none of them looked. These gates are ordered so the cheapest run first
and the ones that have actually caught real defects run at all.

    python -m tools.validation.preflight_candidate_d

Exit status is non-zero if any gate fails, so this is safe to gate a
release on.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "submissions" / "candidate-d" / "main.py"
MANIFEST = ROOT / "submissions" / "candidate-d" / "manifest.json"


def _ok(name: str, passed: bool, detail: str = "") -> bool:
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name}" + (f" -- {detail}" if detail else ""), flush=True)
    return passed


def gate_package_is_deterministic() -> bool:
    from tools.packaging import prepare_candidate_d_submission as prep

    first = prep.build_source()
    second = prep.build_source()
    on_disk = PACKAGE.read_text(encoding="utf-8")
    return _ok(
        "package rebuilds byte-identically and matches disk",
        first == second == on_disk,
        f"sha256={hashlib.sha256(PACKAGE.read_bytes()).hexdigest()[:16]}",
    )


def gate_manifest_matches() -> bool:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    digest = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
    return _ok(
        "manifest sha256 matches the package on disk",
        manifest.get("sha256") == digest,
    )


def gate_model_hashes() -> bool:
    from tools.packaging import prepare_candidate_d_submission as prep

    try:
        model = prep.load_verified_model()
    except ValueError as exc:
        return _ok("embedded model hashes verify", False, str(exc))
    return _ok(
        "embedded model hashes verify",
        True,
        f"episode {model['source_episode_id']} / {model['source_team']}",
    )


def gate_kaggle_loader() -> bool:
    """The check section 9h's failure would have tripped."""
    from tests.test_prepare_candidate_c_submission import get_last_callable
    from tests.test_experimental_scale_agent import scale_observation

    picked = get_last_callable(
        PACKAGE.read_text(encoding="utf-8"), str(PACKAGE)
    )
    decision = picked(scale_observation())
    shaped = all(k in decision for k in ("farmer", "hands", "market"))
    return _ok(
        "Kaggle's real loader picks a working per-turn callable",
        shaped,
        getattr(picked, "__name__", "<closure>"),
    )


def gate_equivalence(seed: int = 231) -> bool:
    from tools.validation.validate_candidate_d_equivalence import validate

    try:
        validate(PACKAGE, seed)
    except SystemExit as exc:
        return _ok("source == package == simulator", False, str(exc))
    return _ok("source == package == simulator", True, "1438 decisions")


def gate_live_games(games: int = 12) -> bool:
    """Run whole games through the loader-extracted callable, both seats."""
    from benchmark import run_game
    from tests.test_prepare_candidate_c_submission import get_last_callable
    from rl.replay_agent import build_replay_agent, load_clone_actions

    picked = get_last_callable(
        PACKAGE.read_text(encoding="utf-8"), str(PACKAGE)
    )
    make = importlib.import_module("kaggle_environments").make
    clones = sorted((ROOT / "kaggle_cache" / "clones").glob("opp_*.json"))
    if not clones:
        return _ok("full games via loader path", False, "no clones cached")
    done = 0
    total = 0
    for index in range(games // 2):
        opponent = build_replay_agent(
            load_clone_actions(clones[index % len(clones)])
        )
        for seat in (0, 1):
            record = run_game(
                make, picked, opponent, 720, 994000 + index, agent_player=seat
            )
            total += 1
            if (
                record["agent_status"] == "DONE"
                and record["opponent_status"] == "DONE"
            ):
                done += 1
    return _ok(
        "full games via loader path finish DONE",
        done == total,
        f"{done}/{total}",
    )


def gate_suite() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return _ok("full test suite", result.returncode == 0)


def main() -> None:
    gates = [
        gate_package_is_deterministic,
        gate_manifest_matches,
        gate_model_hashes,
        gate_kaggle_loader,
        gate_equivalence,
        gate_live_games,
        gate_suite,
    ]
    results = [gate() for gate in gates]
    print()
    if all(results):
        print(f"ALL {len(results)} GATES PASSED")
        return
    failed = sum(1 for r in results if not r)
    raise SystemExit(f"{failed} GATE(S) FAILED")


if __name__ == "__main__":
    main()
