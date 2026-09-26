"""The end-of-day tail, and how well the tape serves its animals.

Two measurements on exact replays of our live games (l2_labour_replay):

1. Tail. Every unit respawns beside the shed at dawn and hands are dismissed
   at night, so once a unit has issued its last non-PASS command of the day,
   where it ends up no longer matters to tomorrow's tape. The trailing run of
   PASS turns is labour a layer could spend *moving* without disturbing the
   tape -- if it knows the tail has begun. This counts tail turns, and, for
   the waste still standing at nightfall (fertilizer uncollected, fed animals
   uncared, animal output about to hit the holding cap, one-time crops in
   their window unwatered, plants about to die), how much a tail unit could
   have reached in time (Manhattan walking, one command per turn, greedy
   nearest-first per unit; an upper bound on what a tail layer could take).

2. Animal service. Per animal-day: fed, cared, cared-but-unfed (care that can
   never bank), banked bonus paid, lost to an unfed production day, lost to
   the cap.

    python -m tools.analysis.l2_labour_tail --submission 56582917 --label L
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments.envs.kaggriculture import kaggriculture as K

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.l2_labour_audit import (Audit, growth_left,  # noqa: E402
                                            ident)
from tools.analysis.l2_labour_replay import records, replay_record  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "labour"
TPD = 24


class TailAudit(Audit):
    def __init__(self, side):
        super().__init__(side)
        self.trace = defaultdict(dict)   # (day, idx) -> {hour: (cls, x, y)}
        self.carry = {}                  # (day, idx) -> inventory at hour 23

    def unit(self, farm, private, idx, action, day, apply):
        if farm is not self.farm:
            return apply()
        pos = K._farmer_position(farm, idx)
        before = sum(self.turns.values())
        snap = dict(self.turns)
        result = super().unit(farm, private, idx, action, day, apply)
        if pos is not None:
            cls = next((c for (c, w), n in self.turns.items()
                        if n != snap.get((c, w), 0)), "pass")
            x, y = K._farmer_position(farm, idx)
            self.trace[(day, idx)][self.step % TPD] = (cls, x, y)
            if self.step % TPD == TPD - 1:
                self.carry[(day, idx)] = dict(K._farmer_inventory(private, idx))
        return result


def animal_service(au):
    c = Counter()
    for day, snap in au.eod.items():
        for tid, t in snap.items():
            if tid[0] != "A":
                continue
            a = K.ANIMALS[t["animal"]]
            c[f"days_{t['animal']}"] += 1
            c["animal_days"] += 1
            c["fed"] += t["fed_today"]
            c["cared"] += t["cared_today"]
            c["cared_unfed"] += t["cared_today"] and not t["fed_today"]
            c["fed_uncared"] += t["fed_today"] and not t["cared_today"]
            since = day + 1 - t["placed_day"] - a["first_yield_day"]
            if since >= 0 and since % a["interval"] == 0:
                c["productions"] += 1
                bonus = t.get("pending_care_bonus", 0)
                if t["fed_today"]:
                    paid = min(a["max_held"], t["yield_units"] + 1 + bonus) \
                        - min(a["max_held"], t["yield_units"] + 1)
                    c["bonus_paid"] += max(0, paid)
                    c["bonus_lost_cap"] += bonus - max(0, paid)
                    c["base_lost_cap"] += max(0, t["yield_units"] + 1 - a["max_held"])
                else:
                    c["bonus_lost_unfed"] += bonus
                    c["unfed_productions"] += 1
    return c


def tail_reach(au, prices):
    """Waste standing at nightfall that a tail unit could have reached."""
    tails = {}
    for (day, idx), hours in au.trace.items():
        last_busy = max((h for h, (cls, _, _) in hours.items() if cls != "pass"),
                        default=-1)
        start = last_busy + 1
        if start <= TPD - 1:
            h = start if start in hours else max(hours)
            pos = hours.get(start - 1, hours.get(min(hours)))[1:]
            tails[(day, idx)] = (start, pos, TPD - start)
    tail_turns = sum(n for _, _, n in tails.values())
    by_day = defaultdict(list)
    for (day, idx), v in tails.items():
        by_day[day].append([idx, v[0], list(v[1])])
    price = lambda item, day: float(prices.get(day * TPD + 20, {}).get(item, 0) or 0)
    got = Counter()
    avail = Counter()
    for day, snap in au.eod.items():
        tasks = []
        for tid, t in snap.items():
            x, y = tid[1], tid[2]
            if tid[0] == "A":
                prod = K.ANIMALS[t["animal"]]["product"]
                if t["fertilizer_available"]:
                    tasks.append(("fert_uncollected", x, y, price("FERTILIZER", day)))
                if t["fed_today"] and not t["cared_today"]:
                    tasks.append(("care_missed_fed", x, y, price(prod, day)))
            elif tid[0] == "P":
                cd = K.CROPS[t["crop"]]
                age = day - t["planted_day"]
                if not t["watered_today"]:
                    if t["consecutive_unwatered"] >= 1:
                        tasks.append(("plant_dies", x, y, cd["seed"] + max(1, t["yield_units"])
                                      * price(t["crop"], day)))
                    elif not cd["ongoing"] and (cd["max_yield_day"] + 1) // 2 <= age \
                            <= cd["max_yield_day"] and t["yield_units"] < cd["max_yield"]:
                        tasks.append(("window_unwatered", x, y, price(t["crop"], day)))
        for d, tid, units in au.cap_waste:
            if d == day:
                tasks.append(("animal_cap", tid[1], tid[2],
                              units * price(K.ANIMALS[tid[3]]["product"], day)))
        for kind, *_r, v in tasks:
            avail[kind] += v
            avail[kind + "_n"] += 1
        # greedy: each tail unit walks to the nearest remaining task it can reach
        units = sorted(by_day.get(day, []), key=lambda u: u[1])
        left = list(tasks)
        clock = {u[0]: (u[1], tuple(u[2])) for u in units}
        progress = True
        while left and progress:
            progress = False
            for u in units:
                idx = u[0]
                t0, pos = clock[idx]
                best = None
                for j, (kind, x, y, v) in enumerate(left):
                    dist = abs(pos[0] - x) + abs(pos[1] - y)
                    done = t0 + dist           # hour of the command
                    if done <= TPD - 1 and v > 0:
                        key = (-v / (dist + 1), dist)
                        if best is None or key < best[0]:
                            best = (key, j, done, (x, y))
                if best:
                    _, j, done, xy = best
                    kind, x, y, v = left.pop(j)
                    got[kind] += v
                    got[kind + "_n"] += 1
                    clock[idx] = (done + 1, xy)
                    progress = True
    return tail_turns, len(tails), got, avail


def one(record):
    side = int(record["our_side"])
    au = TailAudit(side)
    got_r, _, _ = replay_record(record, au)
    turns, n_tails, got, avail = tail_reach(au, au.prices)
    hires = Counter()
    for (day, idx) in au.trace:
        hires[day] = max(hires[day], idx)
    return {"episode_id": record["episode_id"], "exact": got_r == record["rewards"],
            "tail_turns": turns, "tails": n_tails, "reach": dict(got),
            "avail": dict(avail), "service": dict(animal_service(au)),
            "hands_per_day": statistics.mean(hires.values()) if hires else 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", type=int, default=56582917)
    ap.add_argument("--label", default="L")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    recs = records(args.submission)
    if args.limit:
        recs = recs[: args.limit]
    t = time.time()
    games = [one(r) for _, r in recs]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"tail_{args.label}.json").write_text(json.dumps(games), encoding="utf-8")
    n = len(games)
    lines = [f"== tail/service {args.label}: {n} games, exact {sum(g['exact'] for g in games)}"]
    lines.append(f"hands per day (mean of games) {statistics.mean(g['hands_per_day'] for g in games):.1f}")
    lines.append(f"tail turns per game: mean {statistics.mean(g['tail_turns'] for g in games):.0f}, "
                 f"median {statistics.median(g['tail_turns'] for g in games):.0f} "
                 f"(unit-days with a tail: {statistics.mean(g['tails'] for g in games):.0f})")
    keys = sorted({k for g in games for k in g["avail"] if not k.endswith("_n")})
    lines.append("nightfall waste per game: available coins (count) | reachable by tail units coins (count)")
    tot_a = tot_g = 0.0
    for k in keys:
        a = statistics.mean(g["avail"].get(k, 0) for g in games)
        an = statistics.mean(g["avail"].get(k + "_n", 0) for g in games)
        r = statistics.mean(g["reach"].get(k, 0) for g in games)
        rn = statistics.mean(g["reach"].get(k + "_n", 0) for g in games)
        tot_a += a
        tot_g += r
        lines.append(f"  {k:18s} {a:7.0f} ({an:5.1f}) | {r:7.0f} ({rn:5.1f})")
    lines.append(f"  {'ALL':18s} {tot_a:7.0f}         | {tot_g:7.0f}")
    sk = sorted({k for g in games for k in g["service"]})
    lines.append("animal service per game (mean):")
    for k in sk:
        lines.append(f"  {k:20s} {statistics.mean(g['service'].get(k, 0) for g in games):8.1f}")
    text = "\n".join(lines)
    (OUT / f"tail_{args.label}.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"({time.time() - t:.0f}s)")


if __name__ == "__main__":
    main()
