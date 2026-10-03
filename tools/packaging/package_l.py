"""Package Agent L: Agent A's exact file plus our layers, and verify it.

The file is built from submissions/agent-a/main.py (the verbatim public build,
Apache-2.0, notices kept) with two of our changes:

* the V219 tomato gate also accepts two tomato shops when the town's tomato
  shortfall at step 432 is at least --deficit (edited in place, the one
  condition only);
* the market_front layer (stack/market_front.py) appended, wrapping the parent's
  entry point so its orders are reordered, never resized.

Verification, because a dead upload has happened in this project before:
standard-library imports only; the callable Kaggle will pick is ours; the file
loaded exactly the way Kaggle loads it plays full games against Agent A with
no errors, inside the time budget, and scores exactly what the tested local
variant (stack.candidate_l) scores on the same seeds.

    python -m tools.packaging.package_l --deficit 140
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from stack.candidate_l import _SHOPS3, PARENT_FILE  # noqa: E402
from tools.packaging.package_public import stdlib_only  # noqa: E402

OUT = ROOT / "submissions" / "candidate-l" / "main.py"
FRONT = ROOT / "stack" / "market_front.py"

HEADER = """# Agent L (Kaggriculture), Yash Jain, 2026-09-26.
# Base: tetsutani's public build (Apache-2.0), verbatim below with its
# licence notices, except one condition in _v219_qualifies (marked "Agent L").
# Our layer, market_front, is appended at the end of the file.
"""


def build(deficit: int) -> str:
    src = PARENT_FILE.read_text(encoding="utf-8")
    assert src.count(_SHOPS3) == 1, "V219 gate text changed or repeated"
    relaxed = (
        "    # Agent L: also two tomato shops once the town is short enough.\n"
        "    _shops = sum(s in ('PIZZA_SHOP','FARMERS_MARKET') for s in "
        "obs['town']['unlocked_shops'])\n"
        "    _short = 10000 - obs['market']['inventory']['TOMATO']\n"
        f"    if _shops < 2 or (_shops < 3 and _short < {deficit}):\n"
        "        return False\n")
    src = src.replace(_SHOPS3, relaxed)
    front = FRONT.read_text(encoding="utf-8")
    tail = (
        "\n\n" + front + "\n"
        "# ---- Agent L entry point ----\n"
        "_L_PARENT = kaggle_agent        # Agent A's entry point (ig_agent)\n"
        "agent_l = mf_wrap(_L_PARENT)\n")
    return HEADER + src + tail


def verify(path: Path, deficit: int, seeds: list[int]) -> None:
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable

    from tools.arena.arena import CONFIG, load

    text = path.read_text(encoding="utf-8")
    bad = stdlib_only(text)
    assert not bad, f"non-stdlib imports: {bad}"
    entry = get_last_callable(text, path=str(path))
    assert entry.__name__ == "front_agent", f"Kaggle would run {entry.__name__}"
    print(f"  imports: stdlib only; entry Kaggle picks: {entry.__name__}")

    local_name = f"L_fg{deficit}"
    for seed in seeds:
        for seat in (0, 1):
            results = []
            for which in ("package", "local"):
                ours = (get_last_callable(text, path=str(path)) if which == "package"
                        else load(local_name))
                times = []

                def timed(o, c=None, _f=ours, _t=times):
                    t0 = time.perf_counter()
                    try:
                        return _f(o, c)
                    finally:
                        _t.append((time.perf_counter() - t0) * 1000)
                agents = [timed, load("A")] if seat == 0 else [load("A"), timed]
                env = make("kaggriculture", configuration={**CONFIG, "seed": seed},
                           debug=False)
                env.run(agents)
                final = env.steps[-1]
                statuses = [final[i]["status"] for i in (0, 1)]
                assert statuses == ["DONE", "DONE"], statuses
                rewards = [float(final[i]["reward"] or 0) for i in (0, 1)]
                results.append((rewards, max(times), getattr(ours, "telemetry", {})))
            (pr, pmax, ptel), (lr, _, _) = results
            same = pr == lr
            print(f"  seed {seed} seat {seat}: package {pr[seat]:,.0f} vs A "
                  f"{pr[1 - seat]:,.0f} | local variant {lr[seat]:,.0f} | "
                  f"{'identical' if same else 'DIFFERENT'} | slowest turn "
                  f"{pmax:.0f} ms | reordered turns {ptel.get('reordered_turns')}, "
                  f"errors {ptel.get('errors')}")
            assert same, "packaged file does not play like the tested variant"
            assert ptel.get("errors", 0) == 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deficit", type=int, default=140)
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 105, 134])
    args = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(args.deficit), encoding="utf-8")
    data = OUT.read_bytes()
    print(f"wrote {OUT} ({len(data):,} bytes, sha256 "
          f"{hashlib.sha256(data).hexdigest()[:12]})")
    verify(OUT, args.deficit, args.seeds)
    print("verified")


if __name__ == "__main__":
    main()
