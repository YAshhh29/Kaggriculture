"""Rebuild the final submissions (N10, N11, N12) as single-file Kaggle packages.

    python -m tools.packaging.build_final N11                # -> build/N11/main.py
    python -m tools.packaging.build_final N10 --verify       # + 8 games vs the local factory

Each package is the public 2965 Master Hybrid Engine (rl/public, extracted from
its Apache-2.0 notebook) with our layers from stack/ embedded, plus the opponent
library the shadow layer simulates. The public programs are not in this repo:
extract them first (tools/data/extract_notebook_agents.py).

Rebuilt from this tree, N10 and N12 match submissions/candidate-n10 and
submissions/candidate-n12 line for line except the dated header and comments
that name the new folders. N11's own_book layer was refactored after N11 was
packaged (an option was added, off by default), so its rebuild plays the same
moves with slightly different embedded source.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PARENT = "rl/public/nb_haideptry_the_2965_master_hybrid_engine.py"
LIBRARY_18 = (
    "A", "nb_arsgorynich_herdsafe_v3", "nb_haideptry_2965", "nb_guru_master_v4",
    "nb_dmitrii_herdsafe_2700", "nb_nihilistic_robust", "nb_tschinkel_metav4_v13", "nb_ahmed_v55",
    "nb_statma_herd_safe_sale_window_submit", "nb_statma_herd_safe_sale_window_race_ca20",
    "nb_ahmedberatoz_v56_smarter_seeds_and_fertilizer",
    "nb_arsgorynich_order_book_v3_response_improvement",
    "nb_ahmedberatoz_v57_funding_order_invariant", "nb_ahmedberatoz_v54_productive_wheat_and_patient",
    "nb_haodou092_harvest_ledger", "nb_haideptry_the_2965_master_hybrid_engine",
    "nb_hosen42_v11_hc1_vs_h5_validation", "nb_haodou092_harvest_ledger_r0930",
)
COMMON = [
    "--parent", PARENT, "--no-gate", "--agree", "--early-now",
    "--rt", "flow_window=8", "flow_stat=median", "trap_guard=20", "sandwich=True",
    "--msell", "after_beaten=True", "beaten_any=True",
    "--wool-first", "--sell-first", "FERTILIZER",
    "--annex", "min_tomato_shops=3", "min_shortage=140",
    "--dlast", "pad=True", "detect=True", "implied=True",
    "--cap-counters", "--place-guard", "--shed-guard",
    "--wheat-weight", "0.25", "--wheat-adapt",
]
AGENTS = {
    "N10": ([], LIBRARY_18, "stack.l2_combo:n10"),
    "N11": (["--own-book"], LIBRARY_18, "stack.l2_combo:n11"),
    "N12": (["--own-book"], LIBRARY_18 + ("nb_haodou092_harvest_ledger_r1001",), "stack.l2_combo:n12"),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agent", choices=sorted(AGENTS))
    ap.add_argument("--out", default=None, help="output file (default build/<agent>/main.py)")
    ap.add_argument("--verify", action="store_true",
                    help="play 8 verification games: the package must match the local factory move for move")
    args = ap.parse_args()
    extra, library, factory = AGENTS[args.agent]
    missing = [name for name in library if name != "A" and not (ROOT / "rl" / "public" / f"{name}.py").exists()]
    if missing or not (ROOT / PARENT).exists():
        raise SystemExit("public programs missing from rl/public/ (extract them from their notebooks with "
                         f"tools/data/extract_notebook_agents.py): {missing or [PARENT]}")
    out = Path(args.out) if args.out else ROOT / "build" / args.agent / "main.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    from tools.packaging import package_l3
    if not args.verify:
        package_l3.verify = lambda *a, **k: None
    sys.argv = ["package_l3", *COMMON, *extra, "--name", args.agent, "--library", *library,
                "--factory", factory, "--out", str(out.resolve().relative_to(ROOT)) if out.resolve().is_relative_to(ROOT)
                else str(out)]
    package_l3.main()


if __name__ == "__main__":
    main()
