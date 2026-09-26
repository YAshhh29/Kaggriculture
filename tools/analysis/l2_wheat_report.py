"""How the 2600-2700 teams get more wheat: per-game metrics from exact traces.

Reads the traces written by tools/analysis/l2_wheat_runs.py (the team's real
game, and our agent in the team's seat against the same recorded opponent)
and measures, for the watched seat of each run:

- wheat sown, harvests, units per harvest, share of harvests fertilized, and
  the wheat units that fertilizer itself added (each in-window watering on a
  fertilized day adds 2 instead of 1, capped at 6);
- every FERTILIZE on wheat: which unit (0 = farmer, k = k-th hand of the day),
  plant age, hour, and where that unit's fertilizer came from that day
  (COLLECT_FERTILIZER from an animal, or PICKUP from the shed; FIFO);
- the fertilizer ledger (collected, bought, sold, applied by crop) and the
  wheat ledger (sold, bought, fed, prices, same-turn round trips);
- crew (hands per day, hire fees);
- how similar the two runs' actions are (a step diff only means something
  when the team plays the same programme as our agent).

    python -m tools.analysis.l2_wheat_report --side A
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TRACES = ROOT / "rl" / "data" / "l2" / "wheat" / "traces"
OUT = ROOT / "rl" / "data" / "l2" / "wheat"
CAP = {"WHEAT": 6, "CARROT": 4, "MELON": 6}


def load(episode: int, side: str) -> dict | None:
    path = TRACES / f"{episode}_{side}.json.gz"
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def fert_sources(ev: dict) -> list[list]:
    """For each successful FERTILIZE: [t, idx, crop, age, source] (FIFO per unit-day)."""
    flows = defaultdict(list)   # (day, idx) -> [(t, order, kind, n, extra)]
    for t, idx, x, y, animal, ok in ev["collect"]:
        if ok:
            flows[(t // 24, idx)].append((t, 0, "collect", 1, animal))
    for t, idx, item, n in ev["pickup"]:
        if item == "FERTILIZER":
            flows[(t // 24, idx)].append((t, 0, "pickup", n, None))
    for t, idx, lost in ev["shed_in"]:
        if lost.get("FERTILIZER"):
            flows[(t // 24, idx)].append((t, 1, "drop", lost["FERTILIZER"], None))
    for e in ev["fert"]:
        t, idx, x, y, target, age, ok = e[:7]
        if ok:
            flows[(t // 24, idx)].append((t, 1, "use", 1, (target, age)))
    out = []
    for key, items in flows.items():
        queue: list[list] = []
        for t, _, kind, n, extra in sorted(items, key=lambda r: (r[0], r[1])):
            if kind in ("collect", "pickup"):
                queue.append([kind, n])
            elif kind == "drop":
                left = n
                while left and queue:
                    take = min(left, queue[0][1])
                    queue[0][1] -= take
                    left -= take
                    if not queue[0][1]:
                        queue.pop(0)
            else:
                source = "unknown"
                if queue:
                    source = queue[0][0]
                    queue[0][1] -= 1
                    if not queue[0][1]:
                        queue.pop(0)
                out.append([t, key[1], extra[0], extra[1], source])
    return out


def metrics(d: dict) -> dict:
    ev, seat = d["events"], d["seat"]
    m: dict = {"reward": d["rewards"][seat], "opp_reward": d["rewards"][1 - seat]}
    wheat_h = [e for e in ev["harvest"] if e[2] == "WHEAT"]
    m["wheat_sown"] = sum(1 for e in ev["plant"] if e[2] == "WHEAT")
    m["wheat_harvests"] = len(wheat_h)
    m["wheat_units"] = sum(e[6] for e in wheat_h)
    m["wheat_fert_harvests"] = sum(1 for e in wheat_h if e[7] is not None and e[7] >= e[8])
    m["wheat_units_fert"] = sum(e[6] for e in wheat_h if e[7] is not None and e[7] >= e[8])
    m["wheat_units_plain"] = m["wheat_units"] - m["wheat_units_fert"]
    m["harvest_age"] = dict(Counter(str(e[5]) for e in wheat_h))
    m["harvest_units"] = dict(Counter(str(e[6]) for e in wheat_h))
    m["harvest_age_units"] = dict(Counter(f"{e[5]}:{e[6]}:{int(e[7] is not None and e[7] >= e[8])}"
                                          for e in wheat_h))
    # water: [t, idx, crop, x, y, age, yb, ya, fert_active]
    bonus = Counter()
    in_window = Counter()
    for t, idx, crop, x, y, age, yb, ya, fa in ev["water"]:
        if crop not in CAP or ya is None:
            continue
        gain = ya - yb
        plain = min(1, CAP[crop] - yb) if gain > 0 else 0
        if gain > 0:
            in_window[crop] += 1
        bonus[crop] += max(0, gain - plain)
    m["fert_bonus_units"] = dict(bonus)
    m["in_window_waterings"] = dict(in_window)
    # fertilize: [t, idx, x, y, target, age, ok, until_before, inv_before, yield_before]
    ok = [e for e in ev["fert"] if e[6]]
    m["fert_applied"] = dict(Counter(str(e[4]) for e in ok))
    m["fert_failed"] = sum(1 for e in ev["fert"] if not e[6])
    fw = [e for e in ok if e[4] == "WHEAT"]
    m["fert_wheat_by_unit"] = dict(Counter("farmer" if e[1] == 0 else "hand" for e in fw))
    m["fert_wheat_by_idx"] = dict(Counter(str(e[1]) for e in fw))
    m["fert_wheat_by_age"] = dict(Counter(str(e[5]) for e in fw))
    m["fert_wheat_by_hour"] = dict(Counter(str(e[0] % 24) for e in fw))
    m["fert_wheat_by_day"] = dict(Counter(str(e[0] // 24) for e in fw))
    m["fert_wheat_refert"] = sum(1 for e in fw if e[7] is not None and e[7] >= e[0] // 24)
    src = fert_sources(ev)
    m["fert_source"] = dict(Counter(f"{s[2]}|{s[4]}" for s in src))
    m["collected"] = sum(e[5] for e in ev["collect"])
    m["collect_by_day"] = dict(Counter(str(e[0] // 24) for e in ev["collect"] if e[5]))
    m["pickup_fert"] = sum(e[3] for e in ev["pickup"] if e[2] == "FERTILIZER")
    m["feed_ok"] = sum(e[5] for e in ev["feed"])
    # market: [t, seat, op, item, n, total]
    mk = defaultdict(lambda: [0, 0.0])
    wheat_days = defaultdict(lambda: [0, 0.0, 0, 0.0])
    round_trips = 0
    per_turn = defaultdict(lambda: [0, 0])
    opp_wheat_sells = defaultdict(int)
    for t, s, op, item, n, tot in d["market"]:
        t, s = int(t), int(s)
        if s != seat:
            if item == "WHEAT" and op == "SELL":
                opp_wheat_sells[t] += n
            continue
        mk[f"{op}|{item}"][0] += n
        mk[f"{op}|{item}"][1] += tot
        if item == "WHEAT":
            cell = wheat_days[t // 24]
            if op == "SELL":
                cell[0] += n
                cell[1] += tot
                per_turn[t][0] += n
            elif op == "BUY_PRODUCT":
                cell[2] += n
                cell[3] += tot
                per_turn[t][1] += n
    for t, (sold, bought) in per_turn.items():
        round_trips += min(sold, bought)
    m["market"] = {k: [v[0], round(v[1], 1)] for k, v in mk.items()}
    m["wheat_days"] = {str(k): [v[0], round(v[1], 1), v[2], round(v[3], 1)] for k, v in wheat_days.items()}
    m["wheat_round_trip_units"] = round_trips
    m["wheat_buy_turns_with_opp_sell"] = sum(1 for t, (s_, b) in per_turn.items()
                                             if b and opp_wheat_sells.get(t))
    hires = [h for h in d["hires"] if h[1] == seat]
    m["hires"] = len(hires)
    m["hire_fees"] = sum(h[2] for h in hires)
    per_day = Counter(h[0] // 24 for h in hires)
    m["hires_by_day"] = {str(k): v for k, v in sorted(per_day.items())}
    # money ledger: final = 3000 + sales - purchases - hires - land (land = residual)
    ledger = Counter()
    for key, (n, tot) in m["market"].items():
        op, item = key.split("|")
        if op == "SELL":
            ledger[f"sell {item}"] += tot
        elif op == "BUY_PRODUCT":
            ledger[f"buy {item}"] -= tot
        elif op == "BUY_SEED":
            ledger["seeds"] -= tot
        elif op == "BUY_ANIMAL":
            ledger["animals"] -= tot
    ledger["hires"] = -m["hire_fees"]
    ledger["land (residual)"] = m["reward"] - 3000 - sum(ledger.values())
    m["ledger"] = {k: round(v, 1) for k, v in ledger.items()}
    return m


def similarity(a: dict, b: dict, upto: int = 240) -> dict:
    """Share of steps whose unit commands are identical, and the first difference."""
    same_units = same_all = 0
    first = None
    for k in range(1, upto + 1):
        x, y = a["actions"][k] or {}, b["actions"][k] or {}
        u = (x.get("farmer"), x.get("hands")) == (y.get("farmer"), y.get("hands"))
        same_units += u
        same_all += u and x.get("market") == y.get("market")
        if first is None and x != y:
            first = k
    return {"same_units": same_units / upto, "same_all": same_all / upto, "first_diff": first}


def instead(team: dict, ours: dict) -> Counter:
    """For each team FERTILIZE on wheat at (t, idx): our unit idx's command at step t."""
    out = Counter()
    for e in team["events"]["fert"]:
        t, idx, x, y, target, age, ok = e[:7]
        if not ok or target != "WHEAT":
            continue
        mine = [o for o in ours["ops"][t] if o[0] == idx]
        if not mine:
            out["(no such unit)"] += 1
            continue
        op = mine[0][1].split(":")[0]
        same_tile = (mine[0][2], mine[0][3]) == (x, y)
        out[f"{op}{' same tile' if same_tile else ''}"] += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--side", default="A")
    ap.add_argument("--save", default=None)
    args = ap.parse_args()
    from tools.analysis.l2_wheat_runs import faithful_games
    rows = []
    for g in faithful_games():
        ep = int(g["episode"])
        team, ours = load(ep, "team"), load(ep, args.side)
        if team is None or ours is None:
            continue
        mt, mo = metrics(team), metrics(ours)
        rec = team.get("recorded") or {}
        exact = abs(mt["reward"] - float(rec.get("them") or 0)) < 0.5
        rows.append({"episode": ep, "team": g["team"], "score": g["score"],
                     "band_margin": g["ours"] - g["theirs"], "exact": exact,
                     "team_m": mt, "ours_m": mo, "sim": similarity(team, ours),
                     "instead": dict(instead(team, ours))})
    print(f"{len(rows)} games with both traces; team replay exact in "
          f"{sum(r['exact'] for r in rows)}")
    keys = ["reward", "wheat_sown", "wheat_harvests", "wheat_units", "wheat_fert_harvests",
            "wheat_units_fert", "collected", "pickup_fert", "feed_ok", "hires", "hire_fees",
            "wheat_round_trip_units", "fert_failed", "fert_wheat_refert"]
    print(f"\n  {'metric':26s} {'team med':>9s} {args.side + ' med':>9s} {'med diff':>9s} "
          f"{'mean diff':>10s}")
    for k in keys:
        t = [r["team_m"][k] for r in rows]
        o = [r["ours_m"][k] for r in rows]
        dif = [a - b for a, b in zip(t, o)]
        print(f"  {k:26s} {statistics.median(t):9.1f} {statistics.median(o):9.1f} "
              f"{statistics.median(dif):+9.1f} {statistics.mean(dif):+10.1f}")
    for k in ("fert_bonus_units",):
        t = [r["team_m"][k].get("WHEAT", 0) for r in rows]
        o = [r["ours_m"][k].get("WHEAT", 0) for r in rows]
        print(f"  {'fert bonus wheat units':26s} {statistics.median(t):9.1f} {statistics.median(o):9.1f} "
              f"{statistics.median([a - b for a, b in zip(t, o)]):+9.1f} "
              f"{statistics.mean([a - b for a, b in zip(t, o)]):+10.1f}")
    for crop in ("WHEAT", "CARROT", "STRAWBERRY", "TOMATO", "MELON"):
        t = [r["team_m"]["fert_applied"].get(crop, 0) for r in rows]
        o = [r["ours_m"]["fert_applied"].get(crop, 0) for r in rows]
        print(f"  {'fertilize ' + crop:26s} {statistics.median(t):9.1f} {statistics.median(o):9.1f} "
              f"{statistics.median([a - b for a, b in zip(t, o)]):+9.1f} "
              f"{statistics.mean([a - b for a, b in zip(t, o)]):+10.1f}")
    for key in ("SELL|FERTILIZER", "BUY_PRODUCT|FERTILIZER", "SELL|WHEAT", "BUY_PRODUCT|WHEAT"):
        for j, name in ((0, "units"), (1, "$")):
            t = [r["team_m"]["market"].get(key, [0, 0])[j] for r in rows]
            o = [r["ours_m"]["market"].get(key, [0, 0])[j] for r in rows]
            print(f"  {key + ' ' + name:26s} {statistics.median(t):9.1f} {statistics.median(o):9.1f} "
                  f"{statistics.median([a - b for a, b in zip(t, o)]):+9.1f} "
                  f"{statistics.mean([a - b for a, b in zip(t, o)]):+10.1f}")
    agg = {side: defaultdict(Counter) for side in ("team", "ours")}
    for r in rows:
        for side, m in (("team", r["team_m"]), ("ours", r["ours_m"])):
            for k in ("fert_wheat_by_unit", "fert_wheat_by_age", "fert_wheat_by_hour",
                      "fert_source", "harvest_age", "harvest_units", "harvest_age_units"):
                agg[side][k].update(m[k])
    for k in ("fert_wheat_by_unit", "fert_wheat_by_age", "fert_wheat_by_hour", "fert_source",
              "harvest_age", "harvest_units"):
        print(f"\n  {k}: team {sorted(agg['team'][k].items(), key=lambda kv: str(kv[0]).zfill(3))}")
        print(f"  {' ' * len(k)}  {args.side:4s} {sorted(agg['ours'][k].items(), key=lambda kv: str(kv[0]).zfill(3))}")
    lk = sorted({k for r in rows for m in (r["team_m"], r["ours_m"]) for k in m["ledger"]})
    print(f"\n  money ledger, team minus {args.side} in the same seat (mean / median per game):")
    for k in lk:
        dif = [r["team_m"]["ledger"].get(k, 0) - r["ours_m"]["ledger"].get(k, 0) for r in rows]
        print(f"    {k:22s} {statistics.mean(dif):+10,.0f} {statistics.median(dif):+10,.0f}")
    dif = [r["team_m"]["reward"] - r["ours_m"]["reward"] for r in rows]
    print(f"    {'final money':22s} {statistics.mean(dif):+10,.0f} {statistics.median(dif):+10,.0f}")
    dif = [r["team_m"]["opp_reward"] - r["ours_m"]["opp_reward"] for r in rows]
    print(f"    {'(opponent final)':22s} {statistics.mean(dif):+10,.0f} {statistics.median(dif):+10,.0f}")
    inst = Counter()
    for r in rows:
        inst.update(r["instead"])
    print(f"\n  what our unit does when the team's same unit fertilizes wheat: {inst.most_common(12)}")
    sims = [r["sim"]["same_units"] for r in rows]
    print(f"  similarity of unit commands, steps 1-240: median {statistics.median(sims):.2f}; "
          f">=0.9 in {sum(s >= 0.9 for s in sims)} games")
    if args.save:
        path = OUT / args.save
        path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
        print(f"saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
