"""Exact animal-economy trace of real games (both tapes replayed on the seed).

Wraps the engine's own functions while a recorded game replays, and keeps,
for each seat, everything the herd costs and earns:

* herd over time: live animals of each type at every end-of-day refresh,
  purchases (BUY_ANIMAL price), placements, escapes;
* labour: every FEED / CARE / HARVEST / COLLECT_FERTILIZER a unit issued,
  whether the engine applied it or ignored it, by animal type and day;
* production at every refresh: units credited, units lost at the holding cap,
  the CARE bank paid out, lost to an unfed production day, lost to the cap,
  lost when the animal escaped, and still unpaid when the season ends;
* CARE fate: cared on an unfed day (banks nothing) vs banked;
* fertilizer: made available, collected, left to be overwritten, bought,
  sold, used (FERTILIZE applied), left over;
* wheat: fed (with the market's wheat price at that step), bought (price),
  harvested from our own fields;
* market: every unit committed (step, op, item, price) for EGG / MILK /
  WOOL / FERTILIZER / WHEAT;
* the end: products left on animal tiles, in the shed and in inventories.

The replay is exact (final money of both seats is checked against the record
and reported as `exact`).

    python -m tools.analysis.l2_animals_trace --group L --workers 1
    python -m tools.analysis.l2_animals_trace --group A --workers 1
    python -m tools.analysis.l2_animals_trace --group top30 --workers 1

One JSON per game goes to rl/data/l2/animals/games/<group>/.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import zlib
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "rl" / "data" / "l2" / "animals" / "games"
TAPES = ROOT / "rl" / "data" / "our_live_tapes"
CORPUS = ROOT / "kaggle_cache" / "corpus_v2"
SUBMISSION = {"L": 56582917, "A": 56571049}
CONFIG = {"episodeSteps": 720, "runTimeout": 36000, "actTimeout": 60}
PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
ANIMAL_OF = {v: k for k, v in PRODUCT.items()}
TRACKED = ("EGG", "MILK", "WOOL", "FERTILIZER", "WHEAT")
OPS = ("FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER")


def _unpack(blob: str):
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def _new_side() -> dict:
    d = lambda: defaultdict(int)  # noqa: E731
    return {
        "ops": defaultdict(d),          # "<ANIMAL>|<op>|ok/no" -> day -> count
        "unit_turns": 0,
        "animal_turns": 0,              # unit-turns spent on animal ops (any result)
        "bought": defaultdict(int), "bought_cost": defaultdict(float),
        "placed": defaultdict(int), "escaped": defaultdict(int),
        "escaped_yield_lost": defaultdict(int),
        "animal_days": defaultdict(int), "unfed_days": defaultdict(int),
        "herd": defaultdict(dict),      # animal -> day -> live count at refresh
        "prod_events": defaultdict(int), "prod_raw": defaultdict(int),
        "prod_added": defaultdict(int), "cap_loss": defaultdict(int),
        "base_lost_cap": defaultdict(int),
        "care_banked": defaultdict(int), "care_unfed": defaultdict(int),
        "bonus_paid": defaultdict(int), "bonus_lost_cap": defaultdict(int),
        "bonus_lost_unfed": defaultdict(int), "bonus_lost_escape": defaultdict(int),
        "bank_at_end": defaultdict(int),
        "care_by_day": defaultdict(lambda: defaultdict(int)),   # animal -> day -> banked cares
        "bonus_paid_by_day": defaultdict(lambda: defaultdict(int)),
        "fert_made": defaultdict(int), "fert_collected": defaultdict(int),
        "fert_overwritten": defaultdict(int),
        "fert_used": defaultdict(int),  # crop -> FERTILIZE applied
        "harvest_units": defaultdict(int),       # product -> units harvested from animals
        "crop_harvest": defaultdict(int),        # crop -> units harvested from plants
        "wheat_fed_value": 0.0,                  # sum of wheat sell price at each FEED
        "wheat_fed": defaultdict(int),           # animal -> wheat eaten
        "market": [],                            # (step, op, item, price) for TRACKED
        "overflow": defaultdict(int),
        "end_on_tiles": defaultdict(int), "end_shed": {}, "end_inv": defaultdict(int),
        "money_by_day": {},
    }


def _plain(obj):
    if isinstance(obj, defaultdict) or isinstance(obj, dict):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


def trace(seed: int, tapes: list) -> dict:
    """Replay both tapes on `seed`; return per-seat animal ledgers."""
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine

    sides = [_new_side(), _new_side()]
    now = {"step": 0, "farms": [], "wheat_price": 25}

    def seat_of(farm) -> int:
        for i, f in enumerate(now["farms"]):
            if f is farm:
                return i
        now["farms"].append(farm)
        return len(now["farms"]) - 1

    orig_apply = engine._apply_unit_action
    orig_refresh = engine._daily_refresh_animals
    orig_commit = engine._commit_unit
    orig_drop_eod = engine._drop_inventories_to_shed

    def apply(farm, private, idx, action, board_size, day, tpd, cap=100):
        p = seat_of(farm)
        side = sides[p]
        op = action[0] if isinstance(action, list) and action else None
        pos = engine._farmer_position(farm, idx)
        if op is None or pos is None:
            return orig_apply(farm, private, idx, action, board_size, day, tpd, cap)
        side["unit_turns"] += 1
        x, y = pos
        tile = farm["tiles"][y][x] if 0 <= y < len(farm["tiles"]) else None
        pre = dict(tile) if isinstance(tile, dict) else tile
        inv = engine._farmer_inventory(private, idx)
        inv_pre = dict(inv)
        shed_pre = sum(private["shed"].values())
        orig_apply(farm, private, idx, action, board_size, day, tpd, cap)
        post = farm["tiles"][y][x]
        animal = pre.get("animal") if isinstance(pre, dict) else None
        is_plant = isinstance(pre, dict) and pre.get("kind") == "PLANT"
        if op in OPS and not (op == "HARVEST" and is_plant):
            side["animal_turns"] += 1
            ok = False
            if animal and isinstance(post, dict):
                if op == "FEED":
                    ok = (not pre.get("fed_today")) and post.get("fed_today")
                elif op == "CARE":
                    ok = (not pre.get("cared_today")) and post.get("cared_today")
                elif op == "HARVEST":
                    ok = pre.get("yield_units", 0) > 0
                elif op == "COLLECT_FERTILIZER":
                    ok = bool(pre.get("fertilizer_available"))
            key = f"{animal or 'NONE'}|{op}|{'ok' if ok else 'no'}"
            side["ops"][key][day] += 1
            if ok and op == "FEED":
                side["wheat_fed"][animal] += 1
                side["wheat_fed_value"] += now["wheat_price"]
            if ok and op == "HARVEST":
                side["harvest_units"][PRODUCT[animal]] += int(pre.get("yield_units", 0))
            if ok and op == "COLLECT_FERTILIZER":
                side["fert_collected"][animal] += 1
        elif op == "HARVEST" and isinstance(pre, dict) and pre.get("kind") == "PLANT":
            got = sum(inv.values()) - sum(inv_pre.values())
            if got > 0:
                side["crop_harvest"][pre["crop"]] += got
        elif op == "FERTILIZE":
            if inv_pre.get("FERTILIZER", 0) > inv.get("FERTILIZER", 0):
                side["fert_used"][pre.get("crop", "?") if isinstance(pre, dict) else "?"] += 1
        elif op == "PLACE" and isinstance(post, dict) and post.get("animal") \
                and not (isinstance(pre, dict) and pre.get("animal")):
            side["placed"][post["animal"]] += 1
        elif op == "DROP":
            lost_total = sum(inv_pre.values()) - (sum(private["shed"].values()) - shed_pre)
            if lost_total > 0:
                # attribute overflow to items in inventory order (engine order)
                room = max(0, cap - shed_pre)
                for item, n in inv_pre.items():
                    take = min(n, room)
                    room -= take
                    if n - take > 0:
                        side["overflow"][item] += n - take
        return None

    def refresh(farm, day):
        p = seat_of(farm)
        side = sides[p]
        size = len(farm["tiles"])
        pre = {}
        for yy in range(size):
            for xx in range(size):
                t = farm["tiles"][yy][xx]
                if isinstance(t, dict) and "animal" in t:
                    pre[(xx, yy)] = dict(t)
        orig_refresh(farm, day)
        herd = defaultdict(int)
        for (xx, yy), t0 in pre.items():
            a = t0["animal"]
            spec = engine.ANIMALS[a]
            side["animal_days"][a] += 1
            herd[a] += 1
            fed = bool(t0.get("fed_today"))
            cared = bool(t0.get("cared_today"))
            bank = int(t0.get("pending_care_bonus", 0) or 0)
            if not fed:
                side["unfed_days"][a] += 1
            if cared and not fed:
                side["care_unfed"][a] += 1
            if t0.get("fertilizer_available"):
                side["fert_overwritten"][a] += 1
            t1 = farm["tiles"][yy][xx]
            if not (isinstance(t1, dict) and t1.get("animal")):
                side["escaped"][a] += 1
                side["bonus_lost_escape"][a] += bank
                side["escaped_yield_lost"][PRODUCT[a]] += int(t0.get("yield_units", 0))
                continue
            side["fert_made"][a] += 1
            since = day + 1 - t0["placed_day"] - spec["first_yield_day"]
            if since >= 0 and since % spec["interval"] == 0:
                bonus = bank if fed else 0
                raw = 1 + bonus
                added = int(t1["yield_units"]) - int(t0.get("yield_units", 0))
                lost = raw - added
                side["prod_events"][a] += 1
                side["prod_raw"][a] += raw
                side["prod_added"][a] += added
                side["cap_loss"][a] += lost
                paid = max(0, bonus - lost)
                side["bonus_paid"][a] += paid
                side["bonus_paid_by_day"][a][day] += paid
                side["bonus_lost_cap"][a] += bonus - paid
                side["base_lost_cap"][a] += max(0, lost - bonus)
                if not fed:
                    side["bonus_lost_unfed"][a] += bank
            if cared and fed:
                side["care_banked"][a] += 1
                side["care_by_day"][a][day] += 1
        for a in engine.ANIMALS:
            side["herd"][a][day] = herd.get(a, 0)
        side["money_by_day"][day] = float(farm["money"])

    def commit(op, item, price, farm, private, market, *rest):
        ok = orig_commit(op, item, price, farm, private, market, *rest)
        if ok:
            p = seat_of(farm)
            side = sides[p]
            if op == "BUY_ANIMAL":
                side["bought"][item] += 1
                side["bought_cost"][item] += price
            elif item in TRACKED:
                side["market"].append((now["step"], op, item, int(price)))
        return ok

    def drop_eod(private, capacity):
        # overflow at the nightly drop (seat from the private's order)
        p = now["eod_seat"]
        now["eod_seat"] += 1
        shed = private["shed"]
        room = max(0, capacity - sum(shed.values()))
        for inv in private["inventories"]:
            for item, n in inv.items():
                take = min(n, room)
                room -= take
                if n - take > 0:
                    sides[p]["overflow"][item] += n - take
        return orig_drop_eod(private, capacity)

    engine._apply_unit_action = apply
    engine._daily_refresh_animals = refresh
    engine._commit_unit = commit
    engine._drop_inventories_to_shed = drop_eod
    try:
        env = make("kaggriculture", configuration={**CONFIG, "seed": seed}, debug=False)
        env.reset()
        for t in range(719):
            now["step"] = t
            now["farms"] = []
            now["eod_seat"] = 0
            now["wheat_price"] = int(env.state[0].observation.market["prices"]["WHEAT"])
            a0 = tapes[0][t + 1] if t + 1 < len(tapes[0]) else {}
            a1 = tapes[1][t + 1] if t + 1 < len(tapes[1]) else {}
            env.step([a0, a1])
    finally:
        engine._apply_unit_action = orig_apply
        engine._daily_refresh_animals = orig_refresh
        engine._commit_unit = orig_commit
        engine._drop_inventories_to_shed = orig_drop_eod
    final = env.state
    obs0 = final[0].observation
    for p in (0, 1):
        side = sides[p]
        farm = obs0.farms[p]
        priv = final[p].observation.private
        for row in farm["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("animal"):
                    side["end_on_tiles"][PRODUCT[t["animal"]]] += int(t.get("yield_units", 0))
                    side["bank_at_end"][t["animal"]] += int(t.get("pending_care_bonus", 0) or 0)
        side["end_shed"] = {k: int(v) for k, v in priv["shed"].items() if v}
        for inv in priv["inventories"]:
            for k, v in inv.items():
                side["end_inv"][k] += int(v)
    rewards = [float(final[i].reward or 0) for i in (0, 1)]
    prices = dict(obs0.market["prices"])
    return {"rewards": rewards, "sides": [_plain(s) for s in sides],
            "final_prices": prices,
            "shops": list(obs0.town["unlocked_shops"])}


def _jobs(group: str):
    if group in SUBMISSION:
        for path in sorted(TAPES.glob("ep*.json")):
            rec = json.loads(path.read_text(encoding="utf-8"))
            if rec.get("submission") != SUBMISSION[group]:
                continue
            side = int(rec["our_side"])
            yield {"episode_id": rec["episode_id"], "seed": rec["seed"], "focus": side,
                   "ours": rec["our_actions_zlib_b64"], "theirs": rec["opp_actions_zlib_b64"],
                   "expect": {"focus": rec["rewards"]["us"], "other": rec["rewards"]["them"]},
                   "opponent": rec.get("opponent"), "opponent_rating": rec.get("opponent_rating"),
                   "won": rec.get("won")}
    elif group.startswith("top"):
        cut = int(group[3:] or 30)
        for path in sorted(CORPUS.glob("ep*.json")):
            rec = json.loads(path.read_text(encoding="utf-8"))
            if (rec.get("team_rank") or 999) > cut:
                continue
            yield {"episode_id": rec["episode_id"], "seed": rec["seed"], "focus": int(rec["seat"]),
                   "ours": rec["actions_zlib_b64"], "theirs": rec["opponent_actions_zlib_b64"],
                   "expect": {"focus": rec["rewards"].get("them"),
                              "other": rec["rewards"].get("opponent")},
                   "team": rec.get("source_team"), "team_rank": rec.get("team_rank"),
                   "opponent": rec.get("opponent"), "opponent_rating": rec.get("opponent_rating"),
                   "won": rec.get("won")}


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
        res = trace(job["seed"], tapes)
    except Exception as err:  # keep going
        return str(out), f"error {type(err).__name__}: {err}"
    exp = job["expect"]
    res["exact"] = (res["rewards"][focus] == exp["focus"]
                    and res["rewards"][1 - focus] == exp["other"])
    meta = {k: v for k, v in job.items() if k not in ("ours", "theirs")}
    res.update(meta=meta, group=group, seconds=round(time.time() - started, 1))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res), encoding="utf-8")
    return str(out), f"ok exact={res['exact']} {res['seconds']}s"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--group", required=True, help="L, A, or topN (corpus team_rank <= N)")
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
