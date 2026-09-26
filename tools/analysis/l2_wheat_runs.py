"""Replay the 2600-2700 teams' real games and play our agent in their seat.

For every faithful band game of Agent A against a 2600-2700 recording
(rl/data/band_panel/band_2600_2900.json: agent A, score < 2700, replayed
team >= 0.9 x recorded), the team's own real ladder game is taken from
kaggle_cache/corpus_v2 and played twice with the exact engine:

  team : the team's recorded moves vs its recorded opponent (reproduces the
         real game; the final score is checked against the record)
  <agent> : our agent in the team's seat vs the same recorded opponent

Each run is traced event by event (tools/analysis/l2_wheat_trace.py) and a
compact log of the watched seat is saved to
rl/data/l2/wheat/traces/<episode>_<side>.json.gz for l2_wheat_report.py.

    python -m tools.analysis.l2_wheat_runs --agent A --workers 2
    python -m tools.analysis.l2_wheat_runs --agent A --episodes 113409408 --workers 1
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
import time
import zlib
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CORPUS = ROOT / "kaggle_cache" / "corpus_v2"
OUT = ROOT / "rl" / "data" / "l2" / "wheat" / "traces"
BAND = ROOT / "rl" / "data" / "band_panel" / "band_2600_2900.json"
MOVES = ("NORTH", "SOUTH", "EAST", "WEST")


def unpack(blob: str):
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def faithful_games(agent: str = "A", high: float = 2700, fidelity: float = 0.9) -> list[dict]:
    rows = json.loads(BAND.read_text(encoding="utf-8"))
    return [r for r in rows if r.get("agent") == agent and "ours" in r
            and r["score"] < high and r["theirs"] >= fidelity * r["recorded"]]


def compact(log: dict, seat: int) -> dict:
    """Watched-seat events, both seats' market, in small JSON-able lists."""
    ev = {k: [] for k in ("plant", "water", "fert", "harvest", "collect", "pickup",
                          "shed_in", "feed", "care", "dig")}
    ops = [[] for _ in range(720)]
    for (t, s, idx, op, arg, x, y, before, after, ib, ia) in log["units"]:
        if s != seat or t < 0:
            continue
        ops[t].append([idx, op if not arg else f"{op}:{arg[0]}", x, y])
        bplant = isinstance(before, tuple) and before[0] == "PLANT"
        day = t // 24
        if op == "PLANT":
            if isinstance(after, tuple) and after[0] == "PLANT" and before is None:
                ev["plant"].append([t, idx, after[1], x, y])
        elif op == "WATER":
            if bplant and not before[5]:
                ev["water"].append([t, idx, before[1], x, y, day - before[2], before[3],
                                    after[3] if isinstance(after, tuple) else None,
                                    int(before[4] >= day)])
        elif op == "FERTILIZE":
            ok = ib.get("FERTILIZER", 0) > ia.get("FERTILIZER", 0)
            target = (before[1] if bplant else (before[0] if isinstance(before, tuple)
                                                 else before))
            age = day - before[2] if bplant else None
            ev["fert"].append([t, idx, x, y, target, age, int(ok),
                               before[4] if bplant else None, ib.get("FERTILIZER", 0),
                               before[3] if bplant else None])
        elif op == "HARVEST":
            got = {k: ia.get(k, 0) - ib.get(k, 0) for k in set(ia) | set(ib)}
            got = {k: v for k, v in got.items() if v > 0}
            if got:
                item, n = next(iter(got.items()))
                ev["harvest"].append([t, idx, item, x, y,
                                      day - before[2] if bplant else None, n,
                                      before[4] if bplant else None,
                                      before[2] if bplant else None])
        elif op == "COLLECT_FERTILIZER":
            ok = ia.get("FERTILIZER", 0) > ib.get("FERTILIZER", 0)
            ev["collect"].append([t, idx, x, y, before[1] if isinstance(before, tuple)
                                  and before[0] == "ANIMAL" else None, int(ok)])
        elif op == "PICKUP":
            got = {k: ia.get(k, 0) - ib.get(k, 0) for k in set(ia) | set(ib)}
            got = {k: v for k, v in got.items() if v > 0}
            for k, v in got.items():
                ev["pickup"].append([t, idx, k, v])
        elif op in ("DROP", "PLACE"):
            lost = {k: ib.get(k, 0) - ia.get(k, 0) for k in set(ia) | set(ib)}
            lost = {k: v for k, v in lost.items() if v > 0}
            if lost and not (op == "PLACE" and isinstance(after, tuple) and after[0] == "ANIMAL"
                             and not (isinstance(before, tuple) and before[0] == "ANIMAL")):
                ev["shed_in"].append([t, idx, lost])
        elif op == "FEED":
            ok = ib.get("WHEAT", 0) > ia.get("WHEAT", 0)
            ev["feed"].append([t, idx, x, y, before[1] if isinstance(before, tuple)
                               and before[0] == "ANIMAL" else None, int(ok)])
        elif op == "CARE":
            ev["care"].append([t, idx, x, y])
        elif op == "DIG":
            ev["dig"].append([t, idx, x, y, list(before) if isinstance(before, tuple) else before])
    market = {}
    for (t, s, op, item, price) in log["market"]:
        key = f"{t}|{s}|{op}|{item}"
        cell = market.setdefault(key, [0, 0.0])
        cell[0] += 1
        cell[1] += price
    return {"events": ev, "ops": ops,
            "market": [[*k.split("|"), v[0], v[1]] for k, v in market.items()],
            "hires": [list(h) for h in log["hires"]],
            "daily": [list(d) for d in log["daily"]],
            "rewards": log["rewards"], "statuses": log["statuses"],
            "actions": log["actions"][seat]}


def run(job) -> dict:
    episode, side, spec = job
    sys.path.insert(0, str(ROOT))
    from rl.replay_agent import build_replay_agent
    from tools.analysis.l2_wheat_trace import trace

    rec = json.loads((CORPUS / f"ep{episode}.json").read_text(encoding="utf-8"))
    seat = int(rec["seat"])
    team = unpack(rec["actions_zlib_b64"])
    opp = unpack(rec["opponent_actions_zlib_b64"])
    agents = [None, None]
    agents[1 - seat] = build_replay_agent(tuple(opp))
    if side == "team":
        agents[seat] = build_replay_agent(tuple(team))
    else:
        if ":" in spec and not spec.startswith("file:"):
            import importlib
            module, func = spec.rsplit(":", 1)
            obj = getattr(importlib.import_module(module), func)
            # a factory "module:function" (rl.l2_*:build) or an agent attribute
            agents[seat] = obj() if getattr(obj, "__name__", "") == "build" else obj
        else:
            from tools.arena.arena import load
            agents[seat] = load(spec)
    started = time.time()
    try:
        log = trace(int(rec["seed"]), agents)
    except Exception as error:
        return {"episode": episode, "side": side, "error": f"{type(error).__name__}: {error}"}
    out = compact(log, seat)
    out.update(episode=episode, side=side, spec=spec, seat=seat, seed=int(rec["seed"]),
               team=rec["source_team"], team_score=rec["team_score"],
               recorded=rec.get("rewards"), seconds=round(time.time() - started, 1))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{episode}_{side}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    return {"episode": episode, "side": side, "rewards": log["rewards"],
            "seconds": out["seconds"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", default="A", help="arena name or module:attr / module:build")
    ap.add_argument("--side", default=None, help="label for the agent's runs (default: agent)")
    ap.add_argument("--episodes", nargs="*", type=int, default=None)
    ap.add_argument("--skip-team", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    side = args.side or args.agent.replace(":", "_").replace(".", "_")
    games = faithful_games()
    episodes = args.episodes or [int(r["episode"]) for r in games]
    jobs = []
    for ep in episodes:
        if not args.skip_team and not (OUT / f"{ep}_team.json.gz").exists():
            jobs.append((ep, "team", None))
        if not (OUT / f"{ep}_{side}.json.gz").exists():
            jobs.append((ep, side, args.agent))
    print(f"{len(jobs)} runs over {len(episodes)} games, {args.workers} workers", flush=True)
    with Pool(args.workers, maxtasksperchild=1) as pool:
        for i, row in enumerate(pool.imap_unordered(run, jobs), 1):
            print(f"  {i}/{len(jobs)} {row}", flush=True)


if __name__ == "__main__":
    main()
