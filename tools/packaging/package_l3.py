"""Package Agent L3: L2 with the opponent shadow modelling the whole public library.

L2's shadow predicts an opponent that is an exact copy of Agent A. Many ladder
opponents are exact copies of other public programs we hold (the shadow's
sync logs on our live games show whole-game syncs with arsgorynich_herdsafe_v3,
guru_master_v4, haideptry_2965, nihilistic_robust, tschinkel_metav4_v13 and
ahmed_v55 as well as A). L3 embeds all eight programs; the shadow runs each
until it mismatches the opponent once, and acts only while one is in sync.

Each library program is embedded exactly as the local test loads it (A: the
verbatim submissions/agent-a/main.py; the others: their rl/public/<name>.py
wrappers, which carry the author's main.py byte for byte), compiled and
instantiated once when the file loads, so turn 0 does not pay for eight
compilations (Kaggle allows 1 s per turn plus a 60 s reserve).

Verification: as for L2 (stdlib only, the safety wrapper is the entry, the
packaged file plays exactly like rl.l2_combo:ship_lib), against A and against
a library opponent so the shadow's sync path is exercised.

    python -m tools.packaging.package_l3 --out submissions/candidate-l3/main.py
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rl.candidate_l import _SHOPS3, PARENT_FILE  # noqa: E402
from rl.l2_shadow import SH_LIBRARY  # noqa: E402
from tools.packaging.package_l2_full import (LAYERS, layer_source,  # noqa: E402
                                             non_stdlib, verify)

ENTRY = '''
# ---- Agent L3: our layers, each in its own namespace ----
import base64 as _l2_b64
import zlib as _l2_zlib

_L2_SRC = {src_table}
_L3_LIBRARY = {library}
_L3_SOURCES = {lib_table}


def _l2_source(blob):
    return _l2_zlib.decompress(_l2_b64.b64decode(blob)).decode("utf-8")


def _l2_ns(name, inject=None):
    ns = {{"__name__": "l2_" + name}}
    ns.update(inject or {{}})
    exec(compile(_l2_source(_L2_SRC[name]), "l2_" + name, "exec"), ns)
    return ns


# Compile every library program once, at load time.
_L3_CODE = {{name: compile(_l2_source(blob), "library_" + name, "exec")
            for name, blob in _L3_SOURCES.items()}}


def _l3_make(name):
    """A fresh (namespace, entry) for a library program -- exactly what the
    local shadow's factory returns for it."""
    if name == "A":
        env = {{}}
        exec(_L3_CODE[name], env)
        return env, [v for v in env.values() if callable(v)][-1]
    env = {{"__name__": "shadow_" + name, "__file__": "rl/public/" + name + ".py"}}
    exec(_L3_CODE[name], env)
    if "NAMESPACE" in env and "KAGGLE_ENTRY" in env:
        return env["NAMESPACE"], env["KAGGLE_ENTRY"]
    return env["agent"].__globals__, env["agent"]


# One pristine instance of each program, built at load time and handed to
# the shadow on turn 0; later requests (a new game in the same process) build
# fresh ones.
_L3_POOL = {{name: [_l3_make(name)] for name in _L3_LIBRARY}}


def _l3_factory(name):
    def make():
        pool = _L3_POOL.get(name)
        return pool.pop() if pool else _l3_make(name)
    return make


_L3_FACTORIES = {{name: _l3_factory(name) for name in _L3_LIBRARY}}
_L2_ENV = globals()
_L2 = {{}}
{loads}
_l2_agent = kaggle_agent                  # Agent A's entry point (ig_agent), gate 120
_l2_agent = _L2["animals"]["an_wrap"](_l2_agent, _L2_ENV, {{}})
_l2_agent = _L2["wheat_rt"]["rt_inner"](_l2_agent, _L2_ENV)
_l2_agent = _L2["outfarm"]["lot_wrap"](_l2_agent, _L2_ENV)
_l2_agent = _L2["market_front"]["mf_wrap"](_l2_agent)
_l2_agent = _L2["labour"]["lb_wrap"](_l2_agent)
_l2_agent = _L2["shadow"]["shadow_wrap"](_l2_agent, programs=_L3_LIBRARY,
                                         reorder=True, early=True,
                                         factories=_L3_FACTORIES)
agent_l3 = _L2["safety"]["sf_wrap"](_l2_agent, name="L3")
'''


def _blob(text: str) -> str:
    return base64.b64encode(zlib.compress(text.encode("utf-8"), 9)).decode()


def build(deficit: int, library=SH_LIBRARY, name="L3") -> str:
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
        code, _ = layer_source(ROOT / rel)
        assert not non_stdlib(code), rel
        table[name] = _blob(code)
        inj = "{" + ", ".join(f'"{n}": _L2["{s}"]["{n}"]' for n, s in inject) + "}"
        loads.append(f'_L2["{name}"] = _l2_ns("{name}", {inj})')
    lib = {}
    for lib_name in library:
        path = PARENT_FILE if lib_name == "A" else ROOT / "rl" / "public" / f"{lib_name}.py"
        text = path.read_text(encoding="utf-8")
        bad = non_stdlib(text)
        assert not bad, f"{lib_name}: non-stdlib imports {bad}"
        lib[lib_name] = _blob(text)
        print(f"  library {lib_name}: {len(text):,} bytes of source")
    src_table = "{\n" + "".join(f'    "{k}": "{v}",\n' for k, v in table.items()) + "}"
    lib_table = "{\n" + "".join(f'    "{k}": "{v}",\n' for k, v in lib.items()) + "}"
    header = (f"# Agent L3 (Kaggriculture), Yash Jain, {time.strftime('%Y-%m-%d')}.\n"
              "# Base: tetsutani's public build (Apache-2.0), verbatim below with its\n"
              "# licence notices, except one condition in _v219_qualifies (marked\n"
              "# \"Agent L\"). Our layers are embedded at the end, each run in its own\n"
              "# namespace. The opponent shadow's library -- verbatim copies of public\n"
              "# Apache-2.0 programs, notices retained inside each -- is embedded too.\n")
    return header + parent + ENTRY.format(src_table=src_table, library=tuple(library),
                                          lib_table=lib_table, loads="\n".join(loads))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="submissions/candidate-l3/main.py")
    ap.add_argument("--factory", default="rl.l2_combo:ship_lib")
    ap.add_argument("--deficit", type=int, default=120)
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 105])
    ap.add_argument("--opponents", nargs="+", default=["A", "nb_ahmed_v55"])
    ap.add_argument("--library", nargs="+", default=list(SH_LIBRARY),
                    help="programs the shadow models (A = the verbatim base)")
    args = ap.parse_args()
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    out.write_text(build(args.deficit, tuple(args.library)), encoding="utf-8")
    data = out.read_bytes()
    print(f"wrote {out} ({len(data):,} bytes, sha256 {hashlib.sha256(data).hexdigest()[:12]}) "
          f"in {time.perf_counter() - t0:.1f} s")
    from kaggle_environments.agent import get_last_callable
    t0 = time.perf_counter()
    get_last_callable(out.read_text(encoding="utf-8"), path=str(out))
    print(f"  load time (as Kaggle loads it): {time.perf_counter() - t0:.1f} s")
    for opp in args.opponents:
        verify(out, args.factory, args.seeds, opp)
    print("verified")


if __name__ == "__main__":
    main()
