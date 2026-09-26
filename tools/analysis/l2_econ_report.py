"""Aggregate the replay ledgers (tools/analysis/l2_econ_replay.py) into numbers.

Reads rl/data/l2/econ/games/*.json and prints, for our side (A or L) and for
their opponents:

  * price paths: each item's morning price by day (median, p10, p90 across
    games), from the market inventory the engine actually held
  * realised sale prices (volume-weighted) and units sold, per item
  * labour: unit actions per game split into moves / PASS / ignored / useful,
    hands per day and wage bill
  * per-crop and per-animal labour and output from the tile ledgers
  * leaks: shed overflow, decay, dead plants, escapes, uncollected
    fertilizer, capped care, terminal residue

Writes rl/data/l2/econ/summary.json (the realistic price paths are read by
tools/analysis/l2_econ_value.py and l2_econ_market.py).

    python -m tools.analysis.l2_econ_report
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import kaggle_environments.envs.kaggriculture.kaggriculture as E  # noqa: E402

GAMES = ROOT / "rl" / "data" / "l2" / "econ" / "games"
OUT = ROOT / "rl" / "data" / "l2" / "econ" / "summary.json"
ITEMS = E.PRODUCTS
SUBS = {56582917: "L", 56571049: "A"}
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}


def q(xs, f):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * f
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def med(xs):
    return q(xs, 0.5)


def load():
    games = []
    for f in sorted(GAMES.glob("ep*.json")):
        g = json.loads(f.read_text(encoding="utf-8"))
        g["agent"] = SUBS.get(g.get("submission"), str(g.get("submission")))
        games.append(g)
    return games


def morning_price(g, item, day):
    if day == 0:
        return E.market_price(item, 10000)
    return E.market_price(item, g["inv_path"][item][day * 24 - 1])


def price_paths(games):
    out = {}
    for item in ITEMS:
        rows = []
        for d in range(30):
            ps = [morning_price(g, item, d) for g in games]
            invs = [10000 if d == 0 else g["inv_path"][item][d * 24 - 1] for g in games]
            rows.append({"day": d, "p10": q(ps, .1), "p50": med(ps), "p90": q(ps, .9),
                         "inv50": med(invs), "inv10": q(invs, .1), "inv90": q(invs, .9)})
        out[item] = rows
    return out


def sales(games, who):
    """who: 'us' or 'them'. Per item: units/game, revenue/game, VWAP, by phase."""
    units = defaultdict(list)
    rev = defaultdict(list)
    phase = defaultdict(lambda: [0, 0.0])
    buys = defaultdict(lambda: [0, 0.0])
    buy_phase = defaultdict(lambda: [0, 0.0])
    floor = Counter()
    for g in games:
        p = g["our_side"] if who == "us" else 1 - g["our_side"]
        u, r = Counter(), Counter()
        for pl, step, op, item, price in g["market_log"]:
            if pl != p:
                continue
            if op == "SELL":
                u[item] += 1
                r[item] += price
                ph = "d0-9" if step < 240 else ("d10-19" if step < 480 else "d20-29")
                phase[(item, ph)][0] += 1
                phase[(item, ph)][1] += price
                if price == 1:
                    floor[item] += 1
            elif op == "BUY_PRODUCT":
                buys[item][0] += 1
                buys[item][1] += price
                ph = "d0-9" if step < 240 else ("d10-19" if step < 480 else "d20-29")
                buy_phase[(item, ph)][0] += 1
                buy_phase[(item, ph)][1] += price
        for item in ITEMS:
            units[item].append(u[item])
            rev[item].append(r[item])
    n = len(games)
    table = {}
    for item in ITEMS:
        tu, tr = sum(units[item]), sum(rev[item])
        table[item] = {"units_per_game": tu / n, "revenue_per_game": tr / n,
                       "vwap": tr / tu if tu else None, "floor_units_per_game": floor[item] / n,
                       "by_phase": {ph: (phase[(item, ph)][1] / phase[(item, ph)][0]
                                         if phase[(item, ph)][0] else None)
                                    for ph in ("d0-9", "d10-19", "d20-29")},
                       "units_by_phase": {ph: phase[(item, ph)][0] / n for ph in ("d0-9", "d10-19", "d20-29")},
                       "bought_by_phase": {ph: buy_phase[(item, ph)][0] / n for ph in ("d0-9", "d10-19", "d20-29")},
                       "bought_per_game": buys[item][0] / n,
                       "buy_vwap": buys[item][1] / buys[item][0] if buys[item][0] else None}
    return table


def spend(games, who):
    seeds, animals, hires_cost = Counter(), Counter(), []
    land_days = defaultdict(list)
    hands_by_day = [[] for _ in range(30)]
    wage_by_day = [[] for _ in range(30)]
    for g in games:
        p = g["our_side"] if who == "us" else 1 - g["our_side"]
        for pl, step, op, item, price in g["market_log"]:
            if pl == p and op == "BUY_SEED":
                seeds[item] += price
            elif pl == p and op == "BUY_ANIMAL":
                animals[item] += 1
        wages = Counter()
        for pl, step, cost, ok in g["hires"]:
            if pl == p and ok:
                wages[step // 24] += cost
        hires_cost.append(sum(wages.values()))
        for d in range(30):
            wage_by_day[d].append(wages[d])
            hands_by_day[d].append(g["sides"][p]["hands_by_day"][d])
        k = 0
        for pl, step, cost, ok in g["land"]:
            if pl == p and ok:
                land_days[["NE", "SW", "SE"][k]].append(step // 24)
                k += 1
    n = len(games)
    return {"seed_spend_per_game": {k: v / n for k, v in seeds.items()},
            "animals_bought_per_game": {k: v / n for k, v in animals.items()},
            "wages_per_game": statistics.mean(hires_cost),
            "hands_by_day": [med(x) for x in hands_by_day],
            "wage_by_day": [med(x) for x in wage_by_day],
            "land_days": {k: {"share": len(v) / n, "median_day": med(v)} for k, v in land_days.items()}}


def labour(games, who):
    tot = Counter()
    noops = Counter()
    for g in games:
        s = g["sides"][g["our_side"] if who == "us" else 1 - g["our_side"]]
        for k, v in s["verbs"].items():
            tot[k] += v
        for k, v in s["noops"].items():
            noops[k] += v
    n = len(games)
    all_actions = sum(tot.values())
    moves = sum(tot[m] for m in MOVES)
    passes = tot["PASS"]
    ignored = sum(v for k, v in noops.items() if k not in MOVES)
    ignored_moves = sum(v for k, v in noops.items() if k in MOVES)
    useful = all_actions - moves - passes - ignored
    return {"actions_per_game": all_actions / n, "moves": moves / n, "pass": passes / n,
            "ignored_non_move": ignored / n, "ignored_moves": ignored_moves / n,
            "useful": useful / n,
            "by_verb": {k: tot[k] / n for k in sorted(tot, key=lambda k: -tot[k])},
            "ignored_by_verb": {k: noops[k] / n for k in sorted(noops, key=lambda k: -noops[k])}}


def crops(games, who):
    out = {}
    for crop in E.CROPS:
        cyc = []
        for g in games:
            s = g["sides"][g["our_side"] if who == "us" else 1 - g["our_side"]]
            for pl in s["plants"]:
                if pl["crop"] == crop and pl["day"] <= 26:
                    cyc.append(pl)
        if not cyc:
            continue
        harvested = [sum(h[1] for h in c["harvest"]) for c in cyc]
        n_h = [len(c["harvest"]) for c in cyc]
        first_age = [c["harvest"][0][0] for c in cyc if c["harvest"]]
        last_age = [c["harvest"][-1][0] for c in cyc if c["harvest"]]
        waters = [len(c["water"]) for c in cyc]
        ferts = [len(c["fert"]) for c in cyc]
        never = sum(1 for c in cyc if not c["harvest"])
        out[crop] = {"cycles_per_game": len(cyc) / len(games),
                     "units_per_cycle": statistics.mean(harvested),
                     "harvested_share": 1 - never / len(cyc),
                     "water_per_cycle": statistics.mean(waters),
                     "fert_per_cycle": statistics.mean(ferts),
                     "fertilized_share": sum(1 for f in ferts if f) / len(cyc),
                     "harvests_per_cycle": statistics.mean(n_h),
                     "first_harvest_age": Counter(first_age).most_common(4),
                     "last_harvest_age": Counter(last_age).most_common(4),
                     "units_per_harvested_cycle": (statistics.mean([h for h, c in zip(harvested, cyc) if c["harvest"]])
                                                   if len(cyc) > never else 0)}
    return out


def herd(games, who):
    out = {}
    for animal in E.ANIMALS:
        rows = []
        for g in games:
            s = g["sides"][g["our_side"] if who == "us" else 1 - g["our_side"]]
            for a in s["animals"]:
                if a["animal"] == animal:
                    days = max(1, 29 - a["day"])
                    rows.append((days, a))
        if not rows:
            continue
        ad = sum(d for d, _ in rows)
        out[animal] = {"per_game": len(rows) / len(games),
                       "placed_day_median": med([a["day"] for _, a in rows]),
                       "animal_days_per_game": ad / len(games),
                       "feed_per_day": sum(a["feed"] for _, a in rows) / ad,
                       "care_per_day": sum(a["care"] for _, a in rows) / ad,
                       "collect_per_day": sum(a["collect"] for _, a in rows) / ad,
                       "harvest_per_day": sum(a["harvest"] for _, a in rows) / ad,
                       "units_per_day": sum(a["units"] for _, a in rows) / ad,
                       "units_per_harvest": (sum(a["units"] for _, a in rows)
                                             / max(1, sum(a["harvest"] for _, a in rows)))}
    return out


def leaks(games, who):
    keys = ("overflow", "decay_loss", "weed_loss", "weed_deaths", "decay_deaths", "escapes")
    tot = {k: Counter() for k in keys}
    other = Counter()
    residue = Counter()
    for g in games:
        s = g["sides"][g["our_side"] if who == "us" else 1 - g["our_side"]]
        for k in keys:
            for item, v in s[k].items():
                tot[k][item] += v
        for k in ("manure_made", "manure_wasted", "care_capped", "care_paid", "ongoing_capped"):
            other[k] += s[k]
        for part in ("shed", "carried", "tiles"):
            for item, v in s["residue"][part].items():
                residue[f"{part}:{item}"] += v
    n = len(games)
    return {**{k: {i: v / n for i, v in c.items()} for k, c in tot.items()},
            **{k: v / n for k, v in other.items()},
            "residue": {k: v / n for k, v in residue.most_common()}}


def shops(games):
    c = Counter()
    for g in games:
        for s in g["shops"]:
            c[s] += 1
    return {k: v / len(games) for k, v in c.most_common()}


def results(games):
    us = [g["sides"][g["our_side"]]["final"] for g in games]
    them = [g["sides"][1 - g["our_side"]]["final"] for g in games]
    wins = sum(1 for a, b in zip(us, them) if a > b)
    return {"games": len(games), "exact": sum(1 for g in games if g["exact"]),
            "wins": wins, "median_us": med(us), "median_them": med(them),
            "median_opp_rating": med([g.get("opponent_rating") or 0 for g in games])}


def cheap_sales(games, who, cutoff=10):
    """Units we sold at <= cutoff dollars, and the price the same book showed
    24 and 48 steps later (ignoring what our own held units would have done)."""
    out = defaultdict(lambda: {"units": 0, "revenue": 0, "later24": [], "later48": []})
    for g in games:
        p = g["our_side"] if who == "us" else 1 - g["our_side"]
        for pl, step, op, item, price in g["market_log"]:
            if pl != p or op != "SELL" or price > cutoff:
                continue
            row = out[item]
            row["units"] += 1
            row["revenue"] += price
            for lag, key in ((24, "later24"), (48, "later48")):
                t = step + lag
                if t < 718:
                    row[key].append(E.market_price(item, g["inv_path"][item][t]))
    n = len(games)
    return {item: {"units_per_game": r["units"] / n, "median_price_24_later": med(r["later24"]),
                   "median_price_48_later": med(r["later48"]),
                   "share_above_50_after_48": (sum(1 for x in r["later48"] if x > 50) / len(r["later48"])
                                               if r["later48"] else None)}
            for item, r in out.items()}


def endgame_waste(games, who):
    """From the tapes: CARE on days 28-29 and FEED on day 29 can never pay
    (the day-29 night refresh never runs, so a bonus banked on day 28 has no
    production left to land on). Counted as requested actions."""
    import base64
    import zlib
    tapes = {}
    for f in (ROOT / "rl" / "data" / "our_live_tapes").glob("ep*.json"):
        tapes[f.stem] = f
    c = Counter()
    for g in games:
        f = tapes.get(f"ep{g['episode_id']}")
        if f is None:
            continue
        rec = json.loads(f.read_text(encoding="utf-8"))
        blob = rec["our_actions_zlib_b64"] if who == "us" else rec["opp_actions_zlib_b64"]
        tape = json.loads(zlib.decompress(base64.b64decode(blob)).decode())
        for step in range(28 * 24, 719):
            a = tape[step + 1] if step + 1 < len(tape) else {}
            units = [a.get("farmer") or []] + list(a.get("hands") or [])
            day = step // 24
            for u in units:
                if not u:
                    continue
                if u[0] == "CARE":
                    c[f"CARE d{day}"] += 1
                if u[0] == "FEED" and day == 29:
                    c["FEED d29"] += 1
                if u[0] == "WATER" and day == 29:
                    c["WATER d29"] += 1
    return {k: v / len(games) for k, v in c.items()}


def money_flow(games, who):
    """Mean per game: revenue by item, spend by kind; checks the books balance."""
    flow = Counter()
    finals = []
    for g in games:
        p = g["our_side"] if who == "us" else 1 - g["our_side"]
        for pl, step, op, item, price in g["market_log"]:
            if pl != p:
                continue
            if op == "SELL":
                flow[f"sell {item}"] += price
            elif op == "BUY_PRODUCT":
                flow[f"buy {item}"] -= price
            elif op == "BUY_SEED":
                flow["seeds"] -= price
            elif op == "BUY_ANIMAL":
                flow["animals"] -= price
        for pl, step, cost, ok in g["hires"]:
            if pl == p and ok:
                flow["wages"] -= cost
        for pl, step, cost, ok in g["land"]:
            if pl == p and ok:
                flow["land"] -= cost
        finals.append(g["sides"][p]["final"])
    n = len(games)
    out = {k: v / n for k, v in sorted(flow.items(), key=lambda kv: kv[1])}
    out["start"] = 3000
    out["check_sum"] = 3000 + sum(flow.values()) / n
    out["mean_final"] = statistics.mean(finals)
    return out


def leak_value(S, who):
    """Upper-bound dollar value of execution leaks: each lost unit at our
    whole-game VWAP for that item (fertilizer at its whole-game VWAP too),
    escapes at the animal's price, dead plants at their seed price."""
    sales = S[f"sales_{who}"]
    lk = S[f"leaks_{who}"]

    def vwap(item):
        return sales[item]["vwap"] or E.market_price(item, 10000)
    overflow = sum(n * vwap(i) for i, n in lk["overflow"].items())
    manure = lk["manure_wasted"] * vwap("FERTILIZER")
    capped = lk["care_capped"] * statistics.mean(vwap(i) for i in ("MILK", "WOOL", "EGG"))
    escapes = sum(n * E.ANIMALS[a]["cost"] for a, n in lk["escapes"].items())
    dead = sum(n * E.CROPS[c]["seed"] for c, n in lk["weed_deaths"].items()) + \
        sum(n * vwap(c) for c, n in lk["weed_loss"].items()) + \
        sum(n * vwap(c) for c, n in lk["decay_loss"].items())
    return {"overflow": overflow, "manure_uncollected": manure, "care_capped": capped,
            "escapes": escapes, "dead_or_decayed": dead,
            "total": overflow + manure + capped + escapes + dead}


def sales_by_day(games, who, item):
    c = Counter()
    for g in games:
        p = g["our_side"] if who == "us" else 1 - g["our_side"]
        for pl, step, op, it, price in g["market_log"]:
            if pl == p and op == "SELL" and it == item:
                c[step // 24] += 1
    return {d: c[d] / len(games) for d in sorted(c)}


def summarise(games):
    return {"results": results(games), "prices": price_paths(games),
            "sales_us": sales(games, "us"), "sales_them": sales(games, "them"),
            "spend_us": spend(games, "us"), "spend_them": spend(games, "them"),
            "labour_us": labour(games, "us"), "labour_them": labour(games, "them"),
            "crops_us": crops(games, "us"), "crops_them": crops(games, "them"),
            "herd_us": herd(games, "us"), "herd_them": herd(games, "them"),
            "leaks_us": leaks(games, "us"), "leaks_them": leaks(games, "them"),
            "shops": shops(games), "cheap_us": cheap_sales(games, "us"),
            "endgame_us": endgame_waste(games, "us"),
            "flow_us": money_flow(games, "us"), "flow_them": money_flow(games, "them"),
            "melon_days_us": sales_by_day(games, "us", "MELON"),
            "melon_days_them": sales_by_day(games, "them", "MELON")}


def fmt(x, d=1):
    return "-" if x is None else f"{x:,.{d}f}"


def show(label, S):
    r = S["results"]
    print(f"\n==== {label}: {r['games']} games ({r['exact']} reproduced exactly), won {r['wins']}, "
          f"median money {fmt(r['median_us'], 0)} vs {fmt(r['median_them'], 0)}, "
          f"median opp rating {fmt(r['median_opp_rating'], 0)}")
    print("\nMorning price by day, median across games (p10-p90 on days 10/20/29):")
    print("item        " + " ".join(f"d{d:<4d}" for d in (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 29)))
    for item in ITEMS:
        rows = S["prices"][item]
        print(f"{item:11s} " + " ".join(f"{rows[d]['p50']:<5.0f}" for d in (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 29))
              + f"   d10 {rows[10]['p10']:.0f}-{rows[10]['p90']:.0f} d20 {rows[20]['p10']:.0f}-{rows[20]['p90']:.0f}"
              f" d29 {rows[29]['p10']:.0f}-{rows[29]['p90']:.0f}")
    for who in ("us", "them"):
        print(f"\nSales ({who}): units/game, revenue/game, VWAP (d0-9 / d10-19 / d20-29), floor units")
        for item in ITEMS:
            t = S[f"sales_{who}"][item]
            if not t["units_per_game"] and not t["bought_per_game"]:
                continue
            ph = t["by_phase"]
            print(f"  {item:11s} {t['units_per_game']:7.1f} {t['revenue_per_game']:9,.0f}  vwap {fmt(t['vwap'])}"
                  f" ({fmt(ph['d0-9'], 0)}/{fmt(ph['d10-19'], 0)}/{fmt(ph['d20-29'], 0)})"
                  f" floor {t['floor_units_per_game']:.1f}  bought {t['bought_per_game']:.1f} @ {fmt(t['buy_vwap'])}")
    for who in ("us", "them"):
        L = S[f"labour_{who}"]
        sp = S[f"spend_{who}"]
        print(f"\nLabour ({who}): {L['actions_per_game']:.0f} unit-actions/game = moves {L['moves']:.0f}, "
              f"PASS {L['pass']:.0f}, ignored {L['ignored_non_move']:.0f} (+{L['ignored_moves']:.0f} moves off-board), "
              f"useful {L['useful']:.0f}; wages {sp['wages_per_game']:.0f}/game")
        print("   by verb: " + ", ".join(f"{k} {v:.0f}" for k, v in L["by_verb"].items()))
        print("   ignored: " + ", ".join(f"{k} {v:.1f}" for k, v in L["ignored_by_verb"].items()))
        print(f"   hands by day (median): {sp['hands_by_day']}")
        print(f"   land: {sp['land_days']}; animals bought/game {sp['animals_bought_per_game']}")
        print(f"   seed spend/game: { {k: round(v) for k, v in sp['seed_spend_per_game'].items()} }")
    for who in ("us", "them"):
        print(f"\nCrops ({who}):")
        for crop, c in S[f"crops_{who}"].items():
            print(f"  {crop:10s} cycles/game {c['cycles_per_game']:5.1f} units/cycle {c['units_per_cycle']:.2f} "
                  f"harvested {c['harvested_share']:.0%} water/cycle {c['water_per_cycle']:.1f} "
                  f"fert/cycle {c['fert_per_cycle']:.2f} (fertilized {c['fertilized_share']:.0%}) "
                  f"harvests/cycle {c['harvests_per_cycle']:.2f} first age {c['first_harvest_age']} last {c['last_harvest_age']}")
        print(f"Herd ({who}):")
        for a, h in S[f"herd_{who}"].items():
            print(f"  {a:6s} {h['per_game']:.1f}/game placed d{h['placed_day_median']} animal-days {h['animal_days_per_game']:.0f}: "
                  f"per animal-day feed {h['feed_per_day']:.2f} care {h['care_per_day']:.2f} collect {h['collect_per_day']:.2f} "
                  f"harvest {h['harvest_per_day']:.2f} units {h['units_per_day']:.2f} ({h['units_per_harvest']:.1f}/harvest)")
        lk = S[f"leaks_{who}"]
        print(f"Leaks ({who}): overflow {lk['overflow']}\n   decay {lk['decay_loss']} weed-loss {lk['weed_loss']} "
              f"weed deaths {lk['weed_deaths']} decay deaths {lk['decay_deaths']} escapes {lk['escapes']}\n"
              f"   manure made {lk['manure_made']:.0f} wasted {lk['manure_wasted']:.0f}; care paid {lk['care_paid']:.0f} "
              f"capped {lk['care_capped']:.1f}; ongoing capped {lk['ongoing_capped']:.1f}\n   residue {lk['residue']}")
    print(f"\nShops per game: {S['shops']}")
    print("\nOur sales at <= $10: units/game, and the median price the same book showed 24 / 48 steps later")
    for item, r in S["cheap_us"].items():
        print(f"  {item:11s} {r['units_per_game']:6.1f}/game  +24 steps: {fmt(r['median_price_24_later'], 0)}  "
              f"+48: {fmt(r['median_price_48_later'], 0)}  (share > $50 after 48: {fmt(r['share_above_50_after_48'], 2)})")
    for who in ("us", "them"):
        f = S[f"flow_{who}"]
        print(f"\nMoney flow per game, mean ({who}): " + ", ".join(f"{k} {v:,.0f}" for k, v in f.items()))
    print(f"\nEndgame actions that can never pay (requested, per game): {S['endgame_us']}")
    for who in ("us", "them"):
        print(f"Units sold by phase ({who}): " + "; ".join(
            f"{it} {S[f'sales_{who}'][it]['units_by_phase']}" for it in ("FERTILIZER", "STRAWBERRY", "MILK", "WOOL", "MELON")))
        print(f"Bought by phase ({who}): " + "; ".join(
            f"{it} {S[f'sales_{who}'][it]['bought_by_phase']}" for it in ("WHEAT", "FERTILIZER")))


def main() -> None:
    games = load()
    groups = {"L": [g for g in games if g["agent"] == "L"],
              "A": [g for g in games if g["agent"] == "A"]}
    groups["A+L"] = groups["A"] + groups["L"]
    out = {}
    for label, gs in groups.items():
        if not gs:
            continue
        out[label] = summarise(gs)
        out[label]["leak_value_us"] = leak_value(out[label], "us")
        out[label]["leak_value_them"] = leak_value(out[label], "them")
        show(label, out[label])
        print(f"Leak value per game, upper bound (us): { {k: round(v) for k, v in out[label]['leak_value_us'].items()} }")
        print(f"Leak value per game, upper bound (them): { {k: round(v) for k, v in out[label]['leak_value_them'].items()} }")
        print(f"Melon units sold by day (us): { {d: round(v, 1) for d, v in out[label]['melon_days_us'].items()} }")
        print(f"Melon units sold by day (them): { {d: round(v, 1) for d, v in out[label]['melon_days_them'].items()} }")
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
