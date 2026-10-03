"""Which live opponents run a program we have: shadow sync on real ladder games.

For each of our live ladder games (rl/data/our_live_tapes), the game is
replayed exactly from both tapes. Before every step, each candidate program
(a fresh instance: Agent A as Kaggle loads it, Agent L, or an extracted public
agent) is handed the opponent's EXACT observation (their seat, their private
shed/seeds/inventories) and its action is compared with what the opponent
really did (the action stored at t+1). An opponent running exactly the same
program as a candidate is matched on all 719 turns; a modified version
matches until it diverges.

This is the upper bound for an in-game shadow: in a real game the private
state has to be reconstructed (stack/l2_shadow.py does that; see --tracked).

    python -m tools.analysis.l2_shadow_sync --submission 56571049 --workers 2
    python -m tools.analysis.l2_shadow_sync --submission 56582917 --candidates A L
    python -m tools.analysis.l2_shadow_sync --episodes 113802345 --candidates A nb_all

Writes rl/data/l2/shadow/sync_<label>.json.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_shadow_replay import (OUT, PUBLIC, TAPES, Replay,  # noqa: E402
                                             fresh_program, live_paths,
                                             load_game, norm)

DROP_AFTER = 24     # stop feeding a candidate after this many mismatching turns


def sync_one(job) -> dict:
    path, candidates, tracked = job
    sys.path.insert(0, str(ROOT))
    g = load_game(path)
    side = g["our_side"]
    opp = 1 - side
    cfg = g["config"]
    progs, stats = {}, {}
    for name in candidates:
        try:
            progs[name] = fresh_program(name)
        except Exception as error:  # a program that fails to load is reported
            stats[name] = {"error": f"load: {type(error).__name__}: {error}"}
            continue
        stats[name] = {"turns": 0, "full": 0, "units": 0, "market": 0,
                       "market_set": 0, "first_miss": None, "misses": [],
                       "ms": 0.0, "dropped_at": None, "raised": 0}
    tracker = None
    if tracked:
        from stack.l2_shadow import OpponentShadow
        tracker = OpponentShadow(program="A", seat=side)
    rp = Replay(g["seed"])
    started = time.time()
    track_rows = []
    for t in range(719):
        obs = rp.observation(opp)
        real = norm(g["tapes"][opp][t + 1])
        for name, prog in list(progs.items()):
            st = stats[name]
            a = time.perf_counter()
            try:
                pred = norm(prog(obs, cfg))
            except Exception:
                st["raised"] += 1
                pred = None
            st["ms"] += (time.perf_counter() - a) * 1000.0
            st["turns"] += 1
            if pred is None:
                ok = units = market = mset = False
            else:
                units = pred["farmer"] == real["farmer"] and pred["hands"] == real["hands"]
                market = pred["market"] == real["market"]
                mset = sorted(map(json.dumps, pred["market"])) == sorted(map(json.dumps, real["market"]))
                ok = units and market
            st["full"] += ok
            st["units"] += units
            st["market"] += market
            st["market_set"] += mset
            if not ok:
                if st["first_miss"] is None:
                    st["first_miss"] = t
                if len(st["misses"]) < 40:
                    st["misses"].append(t)
                if st["turns"] - st["full"] >= DROP_AFTER:
                    st["dropped_at"] = t
                    del progs[name]
        if tracker is not None:
            own = rp.observation(side)
            info = tracker.observe(own, cfg)
            track_rows.append(info)
            tracker.record_own_action(g["tapes"][side][t + 1])
        rp.step(g["tapes"][0][t + 1], g["tapes"][1][t + 1])
    for st in stats.values():
        if "turns" in st:
            st["ms_per_turn"] = round(st["ms"] / max(1, st["turns"]), 2)
    out = {"episode_id": g["id"], "submission": g.get("submission"),
           "opponent": g.get("opponent"), "opponent_rating": g.get("opponent_rating"),
           "live": g["rewards"], "our_side": side, "won": g.get("won"),
           "replayed": rp.rewards(), "seconds": round(time.time() - started, 1),
           "candidates": stats}
    if tracker is not None:
        out["tracked"] = tracker.summary()
    return out


def report(rows: list[dict]) -> None:
    names = sorted({n for r in rows for n in r["candidates"]})
    print(f"{len(rows)} games")
    for name in names:
        full = [r for r in rows if r["candidates"].get(name, {}).get("full") == 719]
        firsts = [r["candidates"][name].get("first_miss") for r in rows
                  if "turns" in r["candidates"].get(name, {})]
        late = [f for f in firsts if f is not None and f >= 216]
        print(f"  {name:28s} exact copy in {len(full):3d} games; "
              f"first miss on/after day 9 in {len(late)} more")
    print("\n  per game (opponent, rating, live result, best candidate, "
          "matched turns before first miss):")
    for r in sorted(rows, key=lambda r: str(r["episode_id"])):
        best = max(((n, s) for n, s in r["candidates"].items() if "turns" in s),
                   key=lambda kv: (kv[1]["first_miss"] if kv[1]["first_miss"] is not None
                                   else 999, kv[1]["full"]), default=(None, {}))
        name, s = best
        fm = s.get("first_miss")
        live = r["live"]
        side = r["our_side"]
        res = ("WIN" if live[side] > live[1 - side] else
               "TIE" if live[side] == live[1 - side] else "LOSS")
        print(f"   ep{r['episode_id']} {str(r['opponent'])[:18]:18s} "
              f"{(r['opponent_rating'] or 0):7.1f} {res:4s} "
              f"{live[side] - live[1 - side]:+8.0f}  {name}: "
              f"{'ALL 719' if fm is None else f'first miss t={fm}'} "
              f"(full {s.get('full')}, market {s.get('market')}, units {s.get('units')})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--submission", type=int, default=None)
    ap.add_argument("--episodes", type=int, nargs="*", default=None)
    ap.add_argument("--candidates", nargs="+", default=["A"])
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--label", default=None)
    ap.add_argument("--tracked", action="store_true",
                    help="also run stack.l2_shadow's in-game tracker (reconstructed private)")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    cands = []
    for c in args.candidates:
        cands += PUBLIC if c == "nb_all" else [c]
    if args.episodes:
        paths = [TAPES / f"ep{e}.json" for e in args.episodes]
    else:
        paths = live_paths(args.submission)
    if args.limit:
        paths = paths[: args.limit]
    label = args.label or f"{args.submission or 'eps'}_{'-'.join(args.candidates)}"
    print(f"{len(paths)} games x {len(cands)} candidates, {args.workers} workers", flush=True)
    jobs = [(str(p), cands, args.tracked) for p in paths]
    rows = []
    with Pool(args.workers, maxtasksperchild=1) as pool:
        for row in pool.imap_unordered(sync_one, jobs):
            rows.append(row)
            best = {n: (s.get("first_miss"), s.get("full")) for n, s in row["candidates"].items()}
            print(f"  ep{row['episode_id']} {str(row['opponent'])[:16]:16s} {best} "
                  f"{row['seconds']}s", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"sync_{label}.json"
    path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"saved {path.relative_to(ROOT)}")
    report(rows)


if __name__ == "__main__":
    main()
