"""Prepare Candidate B (Candidate A + sequential-affordability residual)."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.packaging.prepare_calendar_recovery_submission import (
    SUBMISSION_DIR as CANDIDATE_A_SUBMISSION_DIR,
    build_source as build_calendar_recovery,
    combined_source_hash as calendar_recovery_source_hash,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_B_PATH = ROOT / "rl" / "candidate_b.py"
SOURCE_PATHS = (CANDIDATE_B_PATH,)
OUTPUT = ROOT / "submissions" / "candidate-b" / "main.py"
MANIFEST = ROOT / "submissions" / "candidate-b" / "manifest.json"
STRIPPED_IMPORT_PREFIXES = ("agents.", "policies.", "core.", "rl.")


def _drop_top_level_agent(body: list[ast.stmt]) -> list[ast.stmt]:
    """Drop Candidate A's own top-level `agent` export.

    Candidate B defines the final one. This must not recurse into nested
    function bodies -- `rl/runtime.py`'s `build_residual_agent` returns its
    own inner closure named `agent`, which is not the export being dropped.
    """
    return [
        node
        for node in body
        if not (isinstance(node, ast.FunctionDef) and node.name == "agent")
    ]


def _strip_imports(module: ast.Module) -> list[ast.stmt]:
    return [
        node
        for node in module.body
        if not (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "__future__"
                or (
                    node.module is not None
                    and node.module.startswith(STRIPPED_IMPORT_PREFIXES)
                )
            )
        )
    ]


def _source_body(path: Path) -> list[ast.stmt]:
    return _strip_imports(ast.parse(path.read_text(encoding="utf-8")))


def build_source() -> str:
    base = ast.parse(build_calendar_recovery())
    base.body = _drop_top_level_agent(base.body)
    base.body.append(
        ast.Assign(
            targets=[ast.Name(id="candidate_a", ctx=ast.Store())],
            value=ast.Name(id="decide", ctx=ast.Load()),
        )
    )
    base.body.extend(_source_body(CANDIDATE_B_PATH))
    return ast.unparse(ast.fix_missing_locations(base)) + "\n"


def combined_source_hash() -> str:
    digest = hashlib.sha256()
    digest.update(calendar_recovery_source_hash().encode("utf-8"))
    digest.update(b"\0")
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
                "parent_submission": {
                    "note": (
                        "built on the Candidate A package, live on Kaggle"
                    ),
                    "source_files": [
                        f"submissions/{CANDIDATE_A_SUBMISSION_DIR}/main.py"
                        " (parent)",
                    ],
                },
                "source_files": [
                    f"submissions/{CANDIDATE_A_SUBMISSION_DIR}/main.py"
                    " (parent)",
                    "rl/candidate_b.py",
                ],
                "policy": (
                    "Candidate A (guarded calendar recovery, live terminal "
                    "liquidation, stranded harvest commitments) plus a "
                    "sequential-affordability market residual: moves SELL "
                    "orders ahead of HIRE/BUY_PRODUCT purchases in the same "
                    "turn's batch that they can fund, applied only when a "
                    "local single-player market replay proves no order's "
                    "fulfilled quantity ever decreases. BUY_ANIMAL, "
                    "BUY_SEED, and BUY_LAND are walled off as rescue "
                    "targets: real testing showed rescuing them can desync "
                    "the fixed calendar's unmanaged assumptions or lose "
                    "value to live opponent market-timing interaction that "
                    "the local safety simulation cannot see, pending "
                    "separate per-type validation."
                ),
                "validation": {
                    "captured_live_gate": {
                        "record": "22-11",
                        "parent_a_record": "21-12",
                        "parent_wins_preserved": "21/21",
                        "loss_conversions": 1,
                        "own_reward_regressions_to_worse_result": 0,
                        "notes": (
                            "33 captured live episodes (13 losses + 20 "
                            "wins from the distilled-calendar parent); "
                            "compared against Candidate A (calendar_recovery"
                            " arm) on the identical replays."
                        ),
                        "reports": [
                            "artifacts/benchmarks/"
                            "v1327-candidate-b-v2-seqaffordability-"
                            "live-losses-13.json",
                            "artifacts/benchmarks/"
                            "v1327-candidate-b-v2-seqaffordability-"
                            "live-wins-20.json",
                        ],
                    },
                    "fresh_family_gate": {
                        "seeds": "300-309",
                        "games": 120,
                        "control_a": "107-13",
                        "candidate_ab_no_land_priority": "108-12",
                        "errors": 0,
                        "per_family_win_regression": 0,
                        "mean_margin_delta_vs_control_a": 2335.23,
                        "land_priority": "disabled by default",
                        "land_priority_evidence": (
                            "This gate compares Candidate A against A+B; it "
                            "does not isolate the land-priority rule. Section "
                            "8's original A+B gate scored the same 108-12 on "
                            "these seeds and families WITH the rule enabled, "
                            "so the rule is a null result here, and the "
                            "margin delta above is the A-to-B delta, not a "
                            "land-priority effect. Instrumented measurement "
                            "over 8 complete games (5752 decisions) found it "
                            "reorders 3 times and the sell pass 8 times. It "
                            "is off by default on risk grounds -- it is the "
                            "one residual never justified by the "
                            "fulfilled-count invariant -- not because "
                            "disabling it was measured to fix anything."
                        ),
                        "families": [
                            "distilled-calendar",
                            "current_rank2_replay_agent",
                            "gated-late-strawberry",
                            "experimental_scale_agent",
                            "experimental_lifecycle_agent",
                            "learned-service",
                        ],
                        "report": (
                            "artifacts/benchmarks/"
                            "v1327-candidate-b-no-land-ablation-300-309.json"
                        ),
                    },
                },
                "status": "candidate B package built; upload only after gates",
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
