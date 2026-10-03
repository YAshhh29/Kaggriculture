"""Package an Agent L2 variant: Agent A's exact file + the gate edit + our layers.

Each layer file must be standard-library only and carry its code between
"# ---- BEGIN <name>" and "# ---- END <name>" markers (as stack/market_front.py
does). The entry point is a composition expression over the parent's entry
(`_L_PARENT`, which is A's `kaggle_agent`) and the parent namespace
(`globals()`), e.g.

    mf_wrap(ew_wrap(_L_PARENT))

Verification is the same as for L: stdlib only, the callable Kaggle picks is
ours, and the packaged file, loaded exactly as Kaggle loads it, scores exactly
what the tested factory scores on the same seeds (both seats), with no errors.

    python -m tools.packaging.package_l2 --out submissions/candidate-l2/main.py \
        --layers stack/market_front.py stack/l2_endgame.py \
        --entry "mf_wrap(ew_wrap(_L_PARENT))" --factory stack.l2_endgame:build
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from stack.candidate_l import _SHOPS3, PARENT_FILE  # noqa: E402
from tools.packaging.package_public import stdlib_only  # noqa: E402

BEGIN = re.compile(r"^# ---- BEGIN .*$", re.M)
END = re.compile(r"^# ---- END .*$", re.M)


def layer_code(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    b, e = BEGIN.search(text), None
    if not b:
        raise SystemExit(f"{path}: no '# ---- BEGIN' marker")
    for m in END.finditer(text):
        if m.start() > b.end():
            e = m
    if not e:
        raise SystemExit(f"{path}: no '# ---- END' marker")
    return text[b.start():e.end()]


def build(deficit: int, layers: list[str], entry: str, name: str) -> str:
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
    header = (f"# {name} (Kaggriculture), Yash Jain, {time.strftime('%Y-%m-%d')}.\n"
              "# Base: tetsutani's public build (Apache-2.0), verbatim below with its\n"
              "# licence notices, except one condition in _v219_qualifies (marked\n"
              "# \"Agent L\"). Our layers are appended at the end of the file.\n")
    tail = "\n\n" + "\n\n".join(layer_code(ROOT / p) for p in layers)
    tail += ("\n\n# ---- entry point ----\n"
             "_L_PARENT = kaggle_agent        # Agent A's entry point (ig_agent)\n"
             f"agent_l2 = {entry}\n")
    return header + src + tail


def verify(path: Path, factory: str, seeds: list[int], opponent: str) -> None:
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable

    from tools.arena.arena import CONFIG, load

    text = path.read_text(encoding="utf-8")
    bad = stdlib_only(text)
    assert not bad, f"non-stdlib imports: {bad}"
    entry = get_last_callable(text, path=str(path))
    print(f"  imports: stdlib only; entry Kaggle picks: {entry.__name__}")
    module, func = factory.rsplit(":", 1)
    for seed in seeds:
        for seat in (0, 1):
            scores = []
            for which in ("package", "factory"):
                ours = (get_last_callable(text, path=str(path)) if which == "package"
                        else getattr(importlib.import_module(module), func)())
                times = []

                def timed(o, c=None, _f=ours, _t=times):
                    t0 = time.perf_counter()
                    try:
                        return _f(o, c)
                    finally:
                        _t.append((time.perf_counter() - t0) * 1000)
                agents = [timed, load(opponent)] if seat == 0 else [load(opponent), timed]
                env = make("kaggriculture", configuration={**CONFIG, "seed": seed},
                           debug=False)
                env.run(agents)
                final = env.steps[-1]
                assert [final[i]["status"] for i in (0, 1)] == ["DONE", "DONE"]
                scores.append(([float(final[i]["reward"] or 0) for i in (0, 1)], max(times)))
            (pr, pmax), (fr, _) = scores
            print(f"  seed {seed} seat {seat}: package {pr[seat]:,.0f} vs {opponent} "
                  f"{pr[1 - seat]:,.0f} | factory {fr[seat]:,.0f} | "
                  f"{'identical' if pr == fr else 'DIFFERENT'} | slowest turn {pmax:.0f} ms")
            assert pr == fr, "packaged file does not play like the tested factory"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--layers", nargs="+", required=True)
    ap.add_argument("--entry", required=True)
    ap.add_argument("--factory", required=True)
    ap.add_argument("--name", default="Agent L2")
    ap.add_argument("--deficit", type=int, default=120)
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 105, 134])
    ap.add_argument("--opponent", default="L")
    args = ap.parse_args()
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(args.deficit, args.layers, args.entry, args.name), encoding="utf-8")
    data = out.read_bytes()
    print(f"wrote {out} ({len(data):,} bytes, sha256 {hashlib.sha256(data).hexdigest()[:12]})")
    verify(out, args.factory, args.seeds, args.opponent)
    print("verified")


if __name__ == "__main__":
    main()
