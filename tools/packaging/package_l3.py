"""Package Agent L3: L2 with the opponent shadow modelling the whole public library.

L2's shadow predicts an opponent running exactly the same program as Agent A.
Many ladder opponents run other public programs we hold, unchanged (the shadow's
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
packaged file plays exactly like stack.l2_combo:ship_lib), against A and against
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

from stack.candidate_l import _SHOPS3, PARENT_FILE  # noqa: E402
from stack.l2_combo import WOOL_FIRST  # noqa: E402
from stack.l2_shadow import SH_LIBRARY  # noqa: E402
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
_l2_agent = {parent_entry}                  # the parent's entry point (Kaggle's last callable)
{book_rec_line}_l2_agent = _L2["animals"]["an_wrap"](_l2_agent, _L2_ENV, {{}})
_l2_agent = _L2["wheat_rt"]["rt_inner"](_l2_agent, _L2_ENV{rt})
{lot_line}_l2_agent = _L2["market_front"]["mf_wrap"](_l2_agent{mf_args})
_l2_agent = _L2["labour"]["lb_wrap"](_l2_agent)
_l2_agent = _L2["shadow"]["shadow_wrap"](_l2_agent, programs=_L3_LIBRARY,
                                         reorder=True, early=True,
                                         factories=_L3_FACTORIES{agree})
{msell_line}{annex_line}{dlast_line}{place_line}{shed_line}{book_line}agent_l3 = _L2["safety"]["sf_wrap"](_l2_agent, name="{agent_name}")
'''


def _blob(text: str) -> str:
    return base64.b64encode(zlib.compress(text.encode("utf-8"), 9)).decode()


def parent_source(path: Path) -> str:
    """The parent's main.py: an extracted public program's text between its
    BEGIN/END markers, or a plain main.py as is."""
    text = path.read_text(encoding="utf-8")
    begin, end = "# ---- BEGIN main.py ----\n", "# ---- END main.py ----"
    if begin in text and end in text:
        return text.split(begin, 1)[1].split(end, 1)[0]
    return text


def entry_name(text: str) -> str:
    env: dict = {}
    exec(compile(text, "parent", "exec"), env)
    return [k for k, v in env.items() if callable(v)][-1]


def build(deficit: int, library=SH_LIBRARY, name="L3", lot=True, agree=False,
          rt=None, msell=None, early_now=False, parent_path=None, gate=True, annex=None,
          parent_patches=(), sell_first=(), dlast=None, cap_counters=False, place_guard=False,
          wheat_weight=1.0, wheat_adapt=False, shed_guard=False, own_book=False) -> str:
    """rt: keyword settings for the round trip (e.g. flow_window=8, flow_stat="median");
    annex: settings for the tomato annex (N3ta), None to leave it out."""
    src = parent_source(Path(parent_path)) if parent_path else PARENT_FILE.read_text(encoding="utf-8")
    parent_entry = entry_name(src)
    assert not gate or src.count(_SHOPS3) == 1, "V219 gate text changed or repeated"
    relaxed = (
        "    # Agent L: also two tomato shops once the town is short enough.\n"
        "    _shops = sum(s in ('PIZZA_SHOP','FARMERS_MARKET') for s in "
        "obs['town']['unlocked_shops'])\n"
        "    _short = 10000 - obs['market']['inventory']['TOMATO']\n"
        f"    if _shops < 2 or (_shops < 3 and _short < {deficit}):\n"
        "        return False\n")
    parent = src.replace(_SHOPS3, relaxed) if gate else src
    for old, new in parent_patches:     # exact text patches of the parent (N3: wool-first crew)
        assert parent.count(old) == 1, f"parent patch target not unique: {old[:60]!r}"
        parent = parent.replace(old, new)
    table, loads = {}, []
    layers = list(LAYERS)
    if msell is not None:     # Agent M: the in-game opponent-clock seller, outside the shadow
        layers.insert(layers.index(next(x for x in layers if x[0] == "safety")),
                      ("m_sell", "stack/m_sell.py", []))
    if own_book:              # N11: the parent's rival-sale trackers see what we really sold
        layers.insert(layers.index(next(x for x in layers if x[0] == "safety")),
                      ("own_book", "stack/own_book.py", []))
    if shed_guard:            # N10: sell/cut purchases so the day-end drop destroys nothing
        layers.insert(layers.index(next(x for x in layers if x[0] == "safety")),
                      ("shed_guard", "stack/shed_guard.py", []))
    if place_guard:           # N7: build the missing pasture/coop under an animal being placed
        layers.insert(layers.index(next(x for x in layers if x[0] == "safety")),
                      ("place_guard", "stack/place_guard.py", []))
    if dlast is not None:     # N4: rider-aware draw-step purchase order, outermost
        layers.insert(layers.index(next(x for x in layers if x[0] == "safety")),
                      ("draw_last", "stack/draw_last.py", []))
    if annex is not None:     # N3ta: the tomato annex, outermost inside the safety guard
        layers.insert(layers.index(next(x for x in layers if x[0] == "safety")),
                      ("tomato_annex", "stack/tomato_annex.py", []))
    for layer, rel, inject in layers:
        if layer == "outfarm" and not lot:
            continue
        code, _ = layer_source(ROOT / rel)
        assert not non_stdlib(code), rel
        table[layer] = _blob(code)
        inj = "{" + ", ".join(f'"{n}": _L2["{s}"]["{n}"]' for n, s in inject) + "}"
        loads.append(f'_L2["{layer}"] = _l2_ns("{layer}", {inj})')
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
    if parent_path:
        base = (f"# Base: {Path(parent_path).stem} (a public Kaggle notebook built from\n"
                "# Apache-2.0 code), its main.py unchanged below, with its licence notices.\n")
    else:
        base = ("# Base: tetsutani's public build (Apache-2.0), unchanged below with its\n"
                "# licence notices, except one condition in _v219_qualifies (marked\n"
                "# \"Agent L\").\n")
    header = (f"# Agent {name} (Kaggriculture), Yash Jain, {time.strftime('%Y-%m-%d')}.\n"
              + base +
              "# Our layers are embedded at the end, each run in its own namespace. The\n"
              "# opponent shadow's library -- public Apache-2.0 programs, unchanged,\n"
              "# with the notices of each retained -- is embedded too.\n")
    lot_line = ('_l2_agent = _L2["outfarm"]["lot_wrap"](_l2_agent, _L2_ENV)\n'
                if lot else '')
    return header + parent + ENTRY.format(src_table=src_table, library=tuple(library),
                                          lot_line=lot_line, agent_name=name, parent_entry=parent_entry,
                                          agree=(', early_when_agree=True' if agree else '')
                                                + (', early_now=True' if early_now else ''),
                                          rt="".join(f", {k}={v!r}" for k, v in (rt or {}).items()),
                                          msell_line=("" if msell is None else
                                                      '_l2_agent = _L2["m_sell"]["m_sell_wrap"](_l2_agent'
                                                      + "".join(f", {k}={v!r}" for k, v in msell.items())
                                                      + ")" + chr(10)),
                                          annex_line=("" if annex is None else
                                                      '_l2_agent = _L2["tomato_annex"]["ta_wrap"](_l2_agent'
                                                      + "".join(f", {k}={v!r}" for k, v in annex.items())
                                                      + ")" + chr(10)),
                                          place_line=('_l2_agent = _L2["place_guard"]["pg_wrap"](_l2_agent)' + chr(10)
                                                      if place_guard else ""),
                                          shed_line=('_l2_agent = _L2["shed_guard"]["sg_wrap"](_l2_agent)' + chr(10)
                                                     if shed_guard else ""),
                                          book_rec_line=('_l2_agent = _OB_REC = _L2["own_book"]["ob_record"](_l2_agent)' + chr(10)
                                                         if own_book else ""),
                                          book_line=('_l2_agent = _L2["own_book"]["ob_wrap"](_l2_agent, _L2_ENV, _OB_REC)' + chr(10)
                                                     if own_book else ""),
                                          dlast_line=("" if dlast is None else
                                                      '_l2_agent = _L2["draw_last"]["dl_wrap"](_l2_agent'
                                                      + "".join(f", {k}={v!r}" for k, v in dlast.items())
                                                      + ")" + chr(10)),
                                          mf_args=(f", sell_first={tuple(sell_first)!r}" if sell_first else "")
                                                  + (", cap_counters=True" if cap_counters else "")
                                                  + (f", wheat_weight={float(wheat_weight)!r}" if wheat_weight != 1.0 else "")
                                                  + (", wheat_adapt=True" if wheat_adapt else ""),
                                          lib_table=lib_table, loads="\n".join(loads))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="submissions/candidate-l3/main.py")
    ap.add_argument("--factory", default="stack.l2_combo:ship_lib")
    ap.add_argument("--deficit", type=int, default=120)
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 105])
    ap.add_argument("--opponents", nargs="+", default=["A", "nb_ahmed_v55"])
    ap.add_argument("--no-lot", action="store_true", help="omit the lot layer (L4)")
    ap.add_argument("--agree", action="store_true",
                    help="early sales also while several in-sync programs agree (L4b)")
    ap.add_argument("--name", default="L3")
    ap.add_argument("--parent", default=None,
                    help="parent program (rl/public/nb_*.py or a main.py); default Agent A")
    ap.add_argument("--no-gate", action="store_true",
                    help="keep the parent's own tomato gate (N)")
    ap.add_argument("--early-now", action="store_true",
                    help="the shadow also races the opponent's current-turn sale (M2)")
    ap.add_argument("--msell", nargs="*", default=None, metavar="KEY=VALUE",
                    help="add Agent M's seller, e.g. --msell value_check=True (M2)")
    ap.add_argument("--rt", nargs="*", default=[], metavar="KEY=VALUE",
                    help="round-trip settings, e.g. flow_window=8 flow_stat=median (L4e)")
    ap.add_argument("--dlast", nargs="*", default=None, metavar="KEY=VALUE",
                    help="add the rider-aware draw_last layer, e.g. --dlast pad=True detect=True (N4)")
    ap.add_argument("--place-guard", action="store_true",
                    help="build the missing structure under an animal being placed (N7)")
    ap.add_argument("--cap-counters", action="store_true",
                    help="market_front caps a same-step sell/rebuy pair at the stock (N6)")
    ap.add_argument("--wheat-weight", type=float, default=1.0,
                    help="market_front scales wheat orders' damage weight (N8: goods sales ahead of the trip)")
    ap.add_argument("--shed-guard", action="store_true",
                    help="never let the day-end drop overflow the shed (N10)")
    ap.add_argument("--own-book", action="store_true",
                    help="N11: correct the parent's records of our own sales after our layers (stack/own_book.py)")
    ap.add_argument("--wheat-adapt", action="store_true",
                    help="market_front restores full wheat weight once the rival round-trips wheat (N8)")
    ap.add_argument("--terminal-step", type=int, default=648,
                    help="step at which the 2965 parent switches to its terminal route (N10: 624)")
    ap.add_argument("--wool-first", action="store_true",
                    help="patch the parent's V233 crew to deliver wool first (stack.l2_combo.WOOL_FIRST)")
    ap.add_argument("--sell-first", nargs="*", default=[],
                    help="market_front keeps these items' SELL ahead of their BUY (N3: FERTILIZER)")
    ap.add_argument("--annex", nargs="*", default=None, metavar="KEY=VALUE",
                    help="add the tomato annex, e.g. --annex rows=7,8 (N3ta)")
    ap.add_argument("--library", nargs="+", default=list(SH_LIBRARY),
                    help="programs the shadow models (A = the verbatim base)")
    args = ap.parse_args()
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    rt = {}
    for item in args.rt:
        key, _, raw = item.partition("=")
        rt[key] = {"True": True, "False": False}.get(raw, int(raw) if raw.lstrip("-").isdigit() else raw)
    msell = None
    if args.msell is not None:
        msell = {}
        for item in args.msell:
            key, _, raw = item.partition("=")
            msell[key] = {"True": True, "False": False}.get(raw, int(raw) if raw.lstrip("-").isdigit() else raw)
    annex = None
    if args.annex is not None:
        annex = {}
        for item in args.annex:
            key, _, raw = item.partition("=")
            annex[key] = (tuple(int(v) for v in raw.split(",")) if key in ("rows", "fert_days", "harvest_days")
                          else int(raw) if raw.lstrip("-").isdigit() else raw)
    out.write_text(build(args.deficit, tuple(args.library), args.name, lot=not args.no_lot,
                         agree=args.agree, rt=rt, msell=msell, early_now=args.early_now,
                         parent_path=args.parent, gate=not args.no_gate, annex=annex,
                         parent_patches=(tuple(WOOL_FIRST if args.wool_first else ())
                                         + ((("if step>=648 and not state.get('day27'):",
                                              f"if step>={args.terminal_step} and not state.get('day27'):"),)
                                            if args.terminal_step != 648 else ())),
                         sell_first=tuple(args.sell_first), cap_counters=args.cap_counters,
                         place_guard=args.place_guard, wheat_weight=args.wheat_weight,
                         wheat_adapt=args.wheat_adapt, shed_guard=args.shed_guard, own_book=args.own_book,
                         dlast=(None if args.dlast is None else
                                {k: {"True": True, "False": False}.get(v, int(v) if v.isdigit() else v)
                                 for k, _, v in (x.partition("=") for x in args.dlast)})),
                   encoding="utf-8")
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
