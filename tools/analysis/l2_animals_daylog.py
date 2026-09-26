"""Per-animal, per-day log of real games, for judging each FEED and CARE.

Replays both recorded tapes on the seed (exact) and records for the chosen
seat, for every animal and every end-of-day refresh:

    fed, cared, production day, bank before, bonus paid, units credited,
    units lost at the cap, fertilizer available before (i.e. left
    uncollected), escaped,

and for every FEED / CARE / HARVEST / COLLECT_FERTILIZER issued on an animal
tile: step, hour, unit, applied or not, and the tile and the unit's state at
that moment (yield on the tile, fertilizer available, fed / cared flags,
wheat carried) plus the market price of the product. From that each CARE
and FEED can be judged afterwards:

* a CARE banks only if the animal is fed that day; the bank pays only on a
  later fed production day that the season still reaches (last refresh is
  the end of day 28), and only up to the holding cap;
* a FEED matters only if it lets a CARE bank, lets a bank pay out, or keeps
  the animal from escaping (the previous or the next day unfed).

    python -m tools.analysis.l2_animals_daylog --group L --workers 1

Output: rl/data/l2/animals/daylog/<group>/ep<id>.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_animals_trace import CONFIG, PRODUCT, _jobs, _unpack  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "animals" / "daylog"
OPS = ("FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER")


def daylog(seed: int, tapes: list, seat: int) -> dict:
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine

    now = {"step": 0, "farms": [], "prices": {}}
    days: dict = {}      # animal key -> list of day rows
    acts: list = []

    def seat_of(farm) -> int:
        for i, f in enumerate(now["farms"]):
            if f is farm:
                return i
        now["farms"].append(farm)
        return len(now["farms"]) - 1

    orig_apply = engine._apply_unit_action
    orig_refresh = engine._daily_refresh_animals

    def apply(farm, private, idx, action, board_size, day, tpd, cap=100):
        p = seat_of(farm)
        op = action[0] if isinstance(action, list) and action else None
        pos = engine._farmer_position(farm, idx)
        if p != seat or op not in OPS or pos is None:
            return orig_apply(farm, private, idx, action, board_size, day, tpd, cap)
        x, y = pos
        tile = farm["tiles"][y][x]
        pre = dict(tile) if isinstance(tile, dict) else None
        inv = engine._farmer_inventory(private, idx)
        wheat = int(inv.get("WHEAT", 0))
        orig_apply(farm, private, idx, action, board_size, day, tpd, cap)
        if not (pre and pre.get("animal")):
            if op != "HARVEST":
                acts.append([now["step"], idx, op, None, None, 0])
            return None
        post = farm["tiles"][y][x]
        ok = {"FEED": (not pre["fed_today"]) and post.get("fed_today"),
              "CARE": (not pre["cared_today"]) and post.get("cared_today"),
              "HARVEST": pre.get("yield_units", 0) > 0,
              "COLLECT_FERTILIZER": bool(pre.get("fertilizer_available"))}[op]
        key = f"{x},{y},{pre['placed_day']},{pre['animal']}"
        acts.append([now["step"], idx, op, key, bool(ok), 1,
                     int(pre.get("yield_units", 0)), bool(pre.get("fertilizer_available")),
                     bool(pre.get("fed_today")), bool(pre.get("cared_today")), wheat,
                     int(pre.get("pending_care_bonus", 0) or 0),
                     int(now["prices"].get(PRODUCT[pre["animal"]], 0))])
        return None

    def refresh(farm, day):
        p = seat_of(farm)
        if p != seat:
            return orig_refresh(farm, day)
        size = len(farm["tiles"])
        pre = {}
        for yy in range(size):
            for xx in range(size):
                t = farm["tiles"][yy][xx]
                if isinstance(t, dict) and "animal" in t:
                    pre[(xx, yy)] = dict(t)
        orig_refresh(farm, day)
        for (xx, yy), t0 in pre.items():
            a = t0["animal"]
            spec = engine.ANIMALS[a]
            key = f"{xx},{yy},{t0['placed_day']},{a}"
            t1 = farm["tiles"][yy][xx]
            escaped = not (isinstance(t1, dict) and t1.get("animal"))
            since = day + 1 - t0["placed_day"] - spec["first_yield_day"]
            prod = since >= 0 and since % spec["interval"] == 0
            bank = int(t0.get("pending_care_bonus", 0) or 0)
            fed = bool(t0.get("fed_today"))
            row = {"d": day, "fed": fed, "cared": bool(t0.get("cared_today")),
                   "prod": prod, "bank": bank, "esc": escaped,
                   "fa": bool(t0.get("fertilizer_available")),
                   "y0": int(t0.get("yield_units", 0)),
                   "price": int(now["prices"].get(PRODUCT[a], 0)),
                   "wheat": int(now["prices"].get("WHEAT", 0))}
            if not escaped and prod:
                bonus = bank if fed else 0
                added = int(t1["yield_units"]) - row["y0"]
                row["added"] = added
                row["paid"] = max(0, bonus - (1 + bonus - added))
                row["cap"] = 1 + bonus - added
            days.setdefault(key, []).append(row)

    engine._apply_unit_action = apply
    engine._daily_refresh_animals = refresh
    try:
        env = make("kaggriculture", configuration={**CONFIG, "seed": seed}, debug=False)
        env.reset()
        for t in range(719):
            now["step"] = t
            now["farms"] = []
            now["prices"] = dict(env.state[0].observation.market["prices"])
            a0 = tapes[0][t + 1] if t + 1 < len(tapes[0]) else {}
            a1 = tapes[1][t + 1] if t + 1 < len(tapes[1]) else {}
            env.step([a0, a1])
    finally:
        engine._apply_unit_action = orig_apply
        engine._daily_refresh_animals = orig_refresh
    rewards = [float(env.state[i].reward or 0) for i in (0, 1)]
    end = {}
    for row in env.state[0].observation.farms[seat]["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                end[t["animal"]] = end.get(t["animal"], 0) + 1
    return {"rewards": rewards, "days": days, "acts": acts, "end_herd": end}


def run_one(args):
    job, group = args
    out = OUT / group / f"ep{job['episode_id']}.json"
    if out.exists():
        return str(out), "cached"
    started = time.time()
    focus = job["focus"]
    ours, theirs = _unpack(job["ours"]), _unpack(job["theirs"])
    tapes = [ours, theirs] if focus == 0 else [theirs, ours]
    try:
        res = daylog(job["seed"], tapes, focus)
    except Exception as err:
        return str(out), f"error {type(err).__name__}: {err}"
    exp = job["expect"]
    res["exact"] = (res["rewards"][focus] == exp["focus"]
                    and res["rewards"][1 - focus] == exp["other"])
    res["meta"] = {k: v for k, v in job.items() if k not in ("ours", "theirs")}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res), encoding="utf-8")
    return str(out), f"ok exact={res['exact']} {time.time() - started:.1f}s"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--group", required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    jobs = list(_jobs(args.group))
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"{len(jobs)} games in group {args.group}", flush=True)
    if args.workers <= 1:
        for j in jobs:
            print(*run_one((j, args.group)), flush=True)
    else:
        with Pool(args.workers, maxtasksperchild=4) as pool:
            for r in pool.imap_unordered(run_one, [(j, args.group) for j in jobs]):
                print(*r, flush=True)


if __name__ == "__main__":
    main()
