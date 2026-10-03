"""Package Agent L2: Agent A's exact file + the gate edit + our layers, isolated.

Each layer's source is embedded (zlib + base64) and executed in its OWN
namespace, so no layer name can overwrite one of the parent's ~2,000 globals
(one candidate layer defined its own `projected_shed`, a name the parent's
layers call). Layers receive the parent's namespace explicitly, as they do in
local testing (stack.candidate_l.l_stack passes it as `env`).

The opponent shadow runs fresh instances of the UNMODIFIED Agent A to predict
an opponent running the same program, so A's source is embedded too,
unchanged and with its licence notices, and exec'd by a factory (locally it
reads submissions/agent-a/main.py).

Composition (innermost first), identical to stack.l2_combo.ship():
    A (gate 120) -> animals -> wheat_rt -> outfarm.lot
      -> market_front -> labour -> shadow (reorder + early) -> safety

Verification: stdlib only (the main file and every embedded layer source);
the callable Kaggle picks is the safety wrapper; the packaged file, loaded the
way Kaggle loads it, scores exactly what stack.l2_combo:ship scores on the same
seeds in both seats, with no errors and a timed slowest turn.

    python -m tools.packaging.package_l2_full --out submissions/candidate-l2/main.py
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import importlib
import re
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from stack.candidate_l import _SHOPS3, PARENT_FILE  # noqa: E402
from tools.packaging.package_public import stdlib_only  # noqa: E402

LAYERS = [  # name, file, names injected from earlier layers
    ("market_front", "stack/market_front.py", []),
    ("animals", "stack/l2_animals.py", []),
    ("wheat_rt", "stack/l2_wheat_rt.py", [("_mf_price", "market_front")]),
    ("outfarm", "stack/l2_outfarm.py", []),
    ("labour", "stack/l2_labour.py", []),
    ("shadow", "stack/l2_shadow.py", []),
    ("safety", "stack/safety.py", []),
]
# Our packages (rl, stack, candidates) are local-only: a layer's top-level
# imports of them are removed, so the packaged layer runs on the stdlib alone.
TOP_RL_IMPORT = re.compile(r"^(from (?:rl|stack|candidates)\b[.\w]* import .*|"
                           r"import (?:rl|stack|candidates)\b[.\w]*.*)$", re.M)

ENTRY = '''
# ---- Agent L2: our layers, each in its own namespace ----
import base64 as _l2_b64
import zlib as _l2_zlib

_L2_SRC = {src_table}
_L2_A_VERBATIM = {a_verbatim!r}


def _l2_source(blob):
    return _l2_zlib.decompress(_l2_b64.b64decode(blob)).decode("utf-8")


def _l2_ns(name, inject=None):
    ns = {{"__name__": "l2_" + name}}
    ns.update(inject or {{}})
    exec(compile(_l2_source(_L2_SRC[name]), "l2_" + name, "exec"), ns)
    return ns


_L2_A_CODE = compile(_l2_source(_L2_A_VERBATIM), "agent_a_verbatim", "exec")


def _l2_a_factory():
    """A fresh copy of the unmodified Agent A, for the opponent shadow."""
    env = {{}}
    exec(_L2_A_CODE, env)
    return env, [v for v in env.values() if callable(v)][-1]


_L2_ENV = globals()
_L2 = {{}}
{loads}
_l2_agent = kaggle_agent                  # Agent A's entry point (ig_agent), gate 120
_l2_agent = _L2["animals"]["an_wrap"](_l2_agent, _L2_ENV, {{}})
_l2_agent = _L2["wheat_rt"]["rt_inner"](_l2_agent, _L2_ENV)
_l2_agent = _L2["outfarm"]["lot_wrap"](_l2_agent, _L2_ENV)
_l2_agent = _L2["market_front"]["mf_wrap"](_l2_agent)
_l2_agent = _L2["labour"]["lb_wrap"](_l2_agent)
_l2_agent = _L2["shadow"]["shadow_wrap"](_l2_agent, reorder=True, early=True,
                                         factories={{"A": _l2_a_factory}})
agent_l2 = _L2["safety"]["sf_wrap"](_l2_agent, name="L2")
'''


def layer_source(path: Path) -> tuple[str, list[str]]:
    """The layer's code with its top-level rl.* imports removed, and those imports."""
    text = path.read_text(encoding="utf-8")
    removed = TOP_RL_IMPORT.findall(text)
    return TOP_RL_IMPORT.sub("pass  # (import removed by packager)", text), removed


def non_stdlib(text: str) -> list[str]:
    """Imports that are not standard library, ignoring imports of our own packages
    (rl, stack, candidates) inside functions (only reached by local test
    factories, never by the shipped composition)."""
    bad = []
    tree = ast.parse(text)
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            mods = [node.module]
        for m in mods:
            top = m.split(".")[0]
            if top == "__future__" or top in sys.stdlib_module_names or top in ("rl", "stack", "candidates"):
                continue
            bad.append(m)
    return bad


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
    parent = src.replace(_SHOPS3, relaxed)
    table, loads = {}, []
    for name, rel, inject in LAYERS:
        code, removed = layer_source(ROOT / rel)
        bad = non_stdlib(code)
        assert not bad, f"{rel}: non-stdlib imports {bad}"
        compile(code, rel, "exec")
        table[name] = base64.b64encode(zlib.compress(code.encode("utf-8"), 9)).decode()
        inj = "{" + ", ".join(f'"{n}": _L2["{src_name}"]["{n}"]' for n, src_name in inject) + "}"
        loads.append(f'_L2["{name}"] = _l2_ns("{name}", {inj})')
        if removed:
            print(f"  {rel}: removed top-level imports {removed}")
    a_verbatim = base64.b64encode(zlib.compress(src.encode("utf-8"), 9)).decode()
    src_table = "{\n" + "".join(f'    "{k}": "{v}",\n' for k, v in table.items()) + "}"
    header = (f"# Agent L2 (Kaggriculture), Yash Jain, {time.strftime('%Y-%m-%d')}.\n"
              "# Base: tetsutani's public build (Apache-2.0), unchanged below with its\n"
              "# licence notices, except one condition in _v219_qualifies (marked\n"
              "# \"Agent L\"). Our layers are embedded at the end of the file, each run\n"
              "# in its own namespace; the base is also embedded, unchanged, for the\n"
              "# opponent shadow.\n")
    return header + parent + ENTRY.format(src_table=src_table, a_verbatim=a_verbatim,
                                          loads="\n".join(loads))


def verify(path: Path, factory: str, seeds: list[int], opponent: str) -> None:
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable

    from tools.arena.arena import CONFIG, load

    text = path.read_text(encoding="utf-8")
    bad = stdlib_only(text)
    assert not bad, f"non-stdlib imports: {bad}"
    entry = get_last_callable(text, path=str(path))
    print(f"  imports: stdlib only; entry Kaggle picks: {entry.__name__}")
    assert entry.__name__ == "safe_agent", entry.__name__
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
                tel = getattr(ours, "telemetry", {}) or {}
                scores.append(([float(final[i]["reward"] or 0) for i in (0, 1)],
                               max(times), sum(times) / 1000, tel))
            (pr, pmax, ptot, ptel), (fr, _, _, _) = scores
            print(f"  seed {seed} seat {seat}: package {pr[seat]:,.0f} vs {opponent} "
                  f"{pr[1 - seat]:,.0f} | factory {fr[seat]:,.0f} | "
                  f"{'identical' if pr == fr else 'DIFFERENT'} | slowest turn {pmax:.0f} ms, "
                  f"total {ptot:.1f} s | guard errors {ptel.get('errors')}, repaired {ptel.get('repaired')}")
            assert pr == fr, "packaged file does not play like the tested factory"
            assert not ptel.get("errors"), "the safety guard caught an exception"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="submissions/candidate-l2/main.py")
    ap.add_argument("--factory", default="stack.l2_combo:ship")
    ap.add_argument("--deficit", type=int, default=120)
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 105, 134])
    ap.add_argument("--opponent", default="A")
    args = ap.parse_args()
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(args.deficit), encoding="utf-8")
    data = out.read_bytes()
    print(f"wrote {out} ({len(data):,} bytes, sha256 {hashlib.sha256(data).hexdigest()[:12]})")
    verify(out, args.factory, args.seeds, args.opponent)
    print("verified")


if __name__ == "__main__":
    main()
