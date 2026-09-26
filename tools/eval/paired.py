"""Paired test of an L2 candidate against Agent L (or any arena agents).

The candidate is built in each game's own process from a factory,
"module:function" returning an agent (e.g. rl.l2_endgame:build). Every seed is
played in both seats. L against itself is all draws, so against L any change
in the result is the candidate's own effect.

    python -m tools.eval.paired rl.l2_endgame:build --label endgame-v1
    python -m tools.eval.paired rl.l2_endgame:build --label endgame-v1 \
        --opponents nb_haideptry_shepherds nb_haideptry_2965 live_H2 --seeds 11 29 53 97
    python -m tools.eval.paired rl.l2_endgame:build --label endgame-v1 --store

--store also writes each game to arena/games (id "<label>__vs__<opp>__s<seed>")
so it can be rendered: python -m tools.arena.arena render <game_id>
"""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "rl" / "data" / "l2" / "paired"


def _factory(spec: str):
    module, func = spec.rsplit(":", 1)
    return getattr(importlib.import_module(module), func)()


def _telemetry(agent) -> dict:
    """Collect .telemetry from the agent and from agents it wraps."""
    out, seen, todo = {}, set(), [agent]
    while todo:
        f = todo.pop()
        if id(f) in seen or not callable(f):
            continue
        seen.add(id(f))
        tel = getattr(f, "telemetry", None)
        if isinstance(tel, dict):
            for k, v in tel.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.setdefault(k, v)
        for cell in getattr(f, "__closure__", None) or ():
            try:
                todo.append(cell.cell_contents)
            except ValueError:
                pass
    return out


def play(job):
    spec, label, opponent, seed, seat, store = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    from tools.arena.arena import CONFIG, GAMES, _pack, load

    started = time.time()
    try:
        ours = _factory(spec)
        theirs = load(opponent)
        errors = [0]

        def guarded(obs, cfg=None):
            try:
                return ours(obs, cfg)
            except Exception:
                errors[0] += 1
                raise

        agents = [guarded, theirs] if seat == 0 else [theirs, guarded]
        env = make("kaggriculture", configuration={**CONFIG, "seed": seed},
                   debug=False)
        env.run(agents)
    except Exception as error:
        return {"opponent": opponent, "seed": seed, "seat": seat,
                "error": f"{type(error).__name__}: {error}"}
    final = env.steps[-1]
    rewards = [float(final[i].get("reward") or 0) for i in (0, 1)]
    statuses = [str(final[i].get("status")) for i in (0, 1)]
    row = {"opponent": opponent, "seed": seed, "seat": seat,
           "ours": rewards[seat], "theirs": rewards[1 - seat],
           "margin": rewards[seat] - rewards[1 - seat],
           "won": rewards[seat] > rewards[1 - seat],
           "status": statuses[seat], "errors": errors[0],
           "seconds": round(time.time() - started, 1),
           "telemetry": _telemetry(ours)}
    if store:
        names = [label, opponent] if seat == 0 else [opponent, label]
        game_id = f"{names[0]}__vs__{names[1]}__s{seed}"
        tapes = [_pack([env.steps[s][i].get("action") for s in range(len(env.steps))])
                 for i in (0, 1)]
        GAMES.mkdir(parents=True, exist_ok=True)
        (GAMES / f"{game_id}.json").write_text(json.dumps({
            "game_id": game_id, "agents": names, "specs": [spec, opponent],
            "seed": seed, "rewards": rewards, "statuses": statuses,
            "winner": names[0] if rewards[0] > rewards[1] else
            names[1] if rewards[1] > rewards[0] else None,
            "turn_errors": [errors[0] if seat == 0 else 0, errors[0] if seat == 1 else 0],
            "played_unix": int(time.time()), "seconds": row["seconds"],
            "tapes": tapes}), encoding="utf-8")
        row["game_id"] = game_id
    return row


def report(rows: list[dict], label: str) -> str:
    lines = []
    for opp in sorted({r["opponent"] for r in rows}):
        g = [r for r in rows if r["opponent"] == opp and "margin" in r]
        bad = [r for r in rows if r["opponent"] == opp and "margin" not in r]
        if not g:
            lines.append(f"  vs {opp}: all {len(bad)} games crashed: {bad[0]['error']}")
            continue
        wins = sum(r["won"] for r in g)
        ties = sum(r["margin"] == 0 for r in g)
        lines.append(
            f"  {label} vs {opp:24s} {wins:3d}/{len(g):<3d} won ({ties} tied)  "
            f"mean {statistics.mean(r['margin'] for r in g):+8,.0f}  "
            f"median {statistics.median(r['margin'] for r in g):+8,.0f}  "
            f"worst {min(r['margin'] for r in g):+8,.0f}  "
            f"errors {sum(r['errors'] for r in g)}  crashes {len(bad)}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("factory", help="module:function returning the candidate agent")
    ap.add_argument("--label", required=True)
    ap.add_argument("--opponents", nargs="+", default=["L"])
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(100, 120)))
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--store", action="store_true")
    args = ap.parse_args()

    jobs = [(args.factory, args.label, opp, s, seat, args.store)
            for opp in args.opponents for s in args.seeds for seat in (0, 1)]
    print(f"{len(jobs)} games: {args.label} vs {', '.join(args.opponents)} on "
          f"{len(args.seeds)} seeds x 2 seats, {args.workers} workers", flush=True)
    with Pool(args.workers, maxtasksperchild=1) as pool:
        rows = list(pool.imap_unordered(play, jobs))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{args.label}.json"
    path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"saved {path.relative_to(ROOT)}")
    print(report(rows, args.label))
    tel = [r.get("telemetry") or {} for r in rows if "margin" in r]
    keys = sorted({k for t in tel for k in t})
    if keys:
        print("  telemetry (mean per game): " + ", ".join(
            f"{k} {statistics.mean(t.get(k, 0) for t in tel):.1f}" for k in keys[:16]))


if __name__ == "__main__":
    main()
