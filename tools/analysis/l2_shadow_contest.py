"""How much market value is contestable in near-mirror games, and who gets it.

Replays L_fg120-vs-A arena games exactly (both tapes, both seats) and, at every
turn, re-runs the engine's market with an exact replica (rl/l2_shadow.py,
checked against the engine every turn) to log each committed unit with its
slot. For every turn and item that BOTH players trade in the same direction
(both sell, or both buy wheat) it prices, with the engine's price function and
lockstep, the per-item margin (L's revenue minus A's):

  first   L's units all settle before A's (L in an earlier slot)
  tie     both in the same slot (unit-by-unit interleave)
  second  A's units all settle before L's
  actual  what the game did

and classifies the turn by where the two orders actually sat (L ahead, tie in
slot 0, tie in a later slot, L behind). Then two counterfactuals, each static
(the opponent's later play is held fixed):

  reorder   the best permutation of L's own priced orders against A's actual
            queue that turn (what exact knowledge of A's queue adds);
  earlier   L moves the contested units to the previous turn (only units that
            were already in L's shed then), front-running A's whole order at
            the cost of any consumption tick in between.

    python -m tools.analysis.l2_shadow_contest --workers 2
    python -m tools.analysis.l2_shadow_contest --games L_fg120__vs__A__s100

Writes rl/data/l2/shadow/contest.json (per-game rows and per-event records).
"""

from __future__ import annotations

import argparse
import copy
import json
import statistics
import sys
import time
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rl.l2_shadow import (_SH_PARAMS, _SH_SHOPS, sh_best_order,  # noqa: E402
                          sh_lockstep_margin, sh_market, sh_price, sh_units)
from tools.analysis.l2_shadow_replay import GAMES, OUT, Replay, load_game  # noqa: E402

L_NAME = "L_fg120"
MAX_LAG = 6
CASH = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")


def consumption(shops, step) -> dict:
    out = defaultdict(int)
    if step % 4 == 0:
        for shop in shops:
            products = _SH_SHOPS[shop]
            for item in products:
                out[item] += 2 if len(products) == 1 else 1
    if step % 24 == 0:
        for item in _SH_PARAMS:
            if item != "FERTILIZER":
                out[item] += 1
    return out


def item_path(item, orders_by_step, inv0, cons):
    """Per-item lockstep over consecutive turns.

    orders_by_step: list over turns of (ours, theirs), each a list of
    (slot, op, units) for this one item -- units that were feasible (already
    committed, or checked against the shed); cons: the town's consumption of
    the item after each turn. Returns [our revenue, their revenue]."""
    inv = inv0
    rev = [0.0, 0.0]
    for k, (ours, theirs) in enumerate(orders_by_step):
        slots = sorted({s for s, _, _ in ours} | {s for s, _, _ in theirs})
        for s in slots:
            rem = [None, None]
            for p, orders in enumerate((ours, theirs)):
                q = [(op, n) for sl, op, n in orders if sl == s]
                if q:
                    rem[p] = [q[0][0], sum(n for _, n in q)]
            while any(r is not None and r[1] > 0 for r in rem):
                quote = [None, None]
                for p in (0, 1):
                    r = rem[p]
                    if r is None or r[1] <= 0:
                        continue
                    quote[p] = sh_price(item, inv if r[0] == "SELL" else inv - 1)
                for p in (0, 1):
                    if quote[p] is None:
                        continue
                    r = rem[p]
                    if r[0] == "SELL":
                        rev[p] += quote[p]
                        if quote[p] > 1:
                            inv += 1
                    else:
                        rev[p] -= quote[p]
                        inv -= 1
                    r[1] -= 1
        inv -= cons[k]
    return rev


def turn_units(log, player, item):
    """(slot, op, units) actually committed by a player for an item this turn."""
    out = defaultdict(int)
    ops = {}
    for slot, p, op, it, price in log:
        if p == player and it == item and op in ("SELL", "BUY_PRODUCT"):
            out[slot] += 1
            ops[slot] = op
    return [(s, ops[s], n) for s, n in sorted(out.items())]


def analyse(job) -> dict:
    game_id = job
    sys.path.insert(0, str(ROOT))
    g = load_game(GAMES / f"{game_id}.json")
    li = g["agents"].index(L_NAME)
    ai = 1 - li
    rp = Replay(g["seed"])
    started = time.time()
    turns = []            # per-turn records needed for the one-turn-back counterfactual
    events = []
    reorder_gain = 0.0
    reorder_turns = 0
    replica_miss = 0
    for t in range(719):
        pub = rp.public()
        privs = [rp.private(0), rp.private(1)]
        acts = [g["tapes"][0][t + 1] or {}, g["tapes"][1][t + 1] or {}]
        farms = copy.deepcopy(pub["farms"])
        pv = copy.deepcopy(privs)
        day = t // 24
        for p in (0, 1):
            sh_units(farms[p], pv[p], acts[p], day)
        shed_at_market = [dict(pv[0]["shed"]), dict(pv[1]["shed"])]
        inv0 = {k: int(v) for k, v in pub["market"]["inventory"].items()}
        inv = dict(inv0)
        log = []
        queues = [(a.get("market") or []) for a in acts]
        sh_market(farms, pv, queues, inv, log)
        shops = list(pub["town"]["unlocked_shops"])
        cons = consumption(shops, t)
        rec = {"t": t, "inv0": inv0, "cons": dict(cons), "shed": shed_at_market,
               "units": {}, "queues": queues}
        for item in _SH_PARAMS:
            u = [turn_units(log, p, item) for p in (0, 1)]
            if u[0] or u[1]:
                rec["units"][item] = u
        turns.append(rec)
        # contested items: both trade the item in the same direction this turn
        contested = []
        for item, u in rec["units"].items():
            ul, ua = u[li], u[ai]
            if not ul or not ua:
                continue
            if {op for _, op, _ in ul} != {op for _, op, _ in ua} or len({op for _, op, _ in ul}) != 1:
                continue
            contested.append(item)
        for item in contested:
            ul, ua = rec["units"][item][li], rec["units"][item][ai]
            op = ul[0][1]
            ql, qa = sum(n for _, _, n in ul), sum(n for _, _, n in ua)

            def run(ours, theirs, item=item):
                r = item_path(item, [(ours, theirs)], inv0[item], [0])
                return r[0] - r[1], r[0], r[1]
            first = run([(0, op, ql)], [(1, op, qa)])
            tie = run([(0, op, ql)], [(0, op, qa)])
            second = run([(1, op, ql)], [(0, op, qa)])
            actual = run(ul, ua)
            sl, sa = ul[0][0], ua[0][0]
            cat = ("L_ahead" if sl < sa else "L_behind" if sl > sa else
                   "tie_slot0" if sl == 0 else "tie_later")
            ev = {"t": t, "item": item, "op": op, "ql": ql, "qa": qa, "slot_l": sl,
                  "slot_a": sa, "cat": cat, "first": first[0], "tie": tie[0],
                  "second": second[0], "actual": actual[0],
                  "price": sh_price(item, inv0[item])}
            # earlier turns: only units that sat unsold in L's shed since then
            if cat != "L_ahead" and op == "SELL":
                best = (0.0, 0, 0)
                avail = None
                for k in range(1, MAX_LAG + 1):
                    if t - k < 0:
                        break
                    prev = turns[t - k]
                    sold = sum(n for _, o, n in prev["units"].get(item, [[], []])[li] if o == "SELL")
                    here = prev["shed"][li].get(item, 0) - sold
                    avail = here if avail is None else min(avail, here)
                    move = max(0, min(ql, avail))
                    if k == 1:
                        ev["movable"] = move
                    if move <= 0:
                        break
                    seq_act, seq_cf, cons_seq = [], [], []
                    for j in range(t - k, t):
                        pu = turns[j]["units"].get(item, [[], []])
                        pl, pa = list(pu[li]), list(pu[ai])
                        seq_act.append((pl, pa))
                        if j == t - k:
                            seq_cf.append(([(0, "SELL", move)] + [(s + 1, o, n) for s, o, n in pl], pa))
                        else:
                            seq_cf.append((pl, pa))
                        cons_seq.append(turns[j]["cons"].get(item, 0))
                    rest, left = [], move
                    for s, o, n in ul:
                        take = min(n, left)
                        left -= take
                        if n - take > 0:
                            rest.append((s, o, n - take))
                    seq_act.append((ul, ua))
                    seq_cf.append((rest, ua))
                    cons_seq.append(0)
                    inv_start = turns[t - k]["inv0"][item]
                    act_rev = item_path(item, seq_act, inv_start, cons_seq)
                    cf_rev = item_path(item, seq_cf, inv_start, cons_seq)
                    gain = (cf_rev[0] - cf_rev[1]) - (act_rev[0] - act_rev[1])
                    if k == 1:
                        ev["earlier_gain"] = gain
                        ev["earlier_own_gain"] = cf_rev[0] - act_rev[0]
                        ev["tick_between"] = cons_seq[0]
                    if gain > best[0]:
                        best = (gain, k, move)
                ev["earlier_best"] = best[0]
                ev["earlier_best_lag"] = best[1]
            events.append(ev)
        if contested:
            stocks = [shed_at_market[li], shed_at_market[ai]]
            _, gain = sh_best_order(queues[li], queues[ai], inv0, stocks[0], stocks[1])
            if gain > 0.5:
                reorder_gain += gain
                reorder_turns += 1
        # check the replica against the engine
        rp.step(acts[0], acts[1])
        seen = rp.public()
        if any(float(farms[p]["money"]) != float(seen["farms"][p]["money"]) for p in (0, 1)):
            replica_miss += 1
        for rec_old in turns[:-2]:
            rec_old.pop("queues", None)
    final = rp.rewards()
    return {"game_id": game_id, "seed": g["seed"], "l_seat": li,
            "margin": final[li] - final[ai], "rewards": final,
            "stored": g["rewards"], "replica_money_misses": replica_miss,
            "reorder_gain": reorder_gain, "reorder_turns": reorder_turns,
            "events": events, "seconds": round(time.time() - started, 1)}


def _group(e):
    if e["item"] in CASH:
        return "cash"
    return f"{e['item'].lower()}_{'buy' if e['op'] == 'BUY_PRODUCT' else 'sell'}"


def summarise(rows: list[dict]) -> dict:
    n = max(1, len(rows))
    ev = [e for r in rows for e in r["events"]]
    out = {"games": len(rows), "events_per_game": len(ev) / n,
           "replica_money_misses": sum(r["replica_money_misses"] for r in rows),
           "reorder_gain_per_game": sum(r["reorder_gain"] for r in rows) / n,
           "reorder_turns_per_game": sum(r["reorder_turns"] for r in rows) / n}
    groups = defaultdict(lambda: defaultdict(list))
    for e in ev:
        groups[_group(e)][e["cat"]].append(e)
        groups[_group(e)]["ALL"].append(e)
    table = {}
    for gname, cats in sorted(groups.items()):
        table[gname] = {}
        for c, es in sorted(cats.items()):
            table[gname][c] = {
                "events": round(len(es) / n, 1),
                "first_minus_tie": round(sum(e["first"] - e["tie"] for e in es) / n, 1),
                "captured_actual_minus_tie": round(sum(e["actual"] - e["tie"] for e in es) / n, 1),
                "left_first_minus_actual": round(sum(e["first"] - e["actual"] for e in es) / n, 1),
                "movable_1turn_events": round(sum(1 for e in es if e.get("movable", 0) > 0) / n, 1),
                "earlier_1turn_net": round(sum(e.get("earlier_gain", 0.0) for e in es) / n, 1),
                "earlier_1turn_positive_only": round(sum(max(0.0, e.get("earlier_gain", 0.0)) for e in es) / n, 1),
                "earlier_best_lag_positive": round(sum(e.get("earlier_best", 0.0) for e in es) / n, 1),
            }
    out["per_game_by_group"] = table
    items = defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0.0])
    for e in ev:
        c = items[f"{e['item']}|{e['op']}"]
        c[0] += 1
        c[1] += e["first"] - e["tie"]
        c[2] += e["actual"] - e["tie"]
        c[3] += e["first"] - e["actual"]
        c[4] += e.get("earlier_best", 0.0)
    out["per_game_by_item"] = {k: {"events": round(v[0] / n, 1),
                                   "first_minus_tie": round(v[1] / n, 1),
                                   "captured": round(v[2] / n, 1),
                                   "left": round(v[3] / n, 1),
                                   "earlier_best_positive": round(v[4] / n, 1)}
                               for k, v in sorted(items.items(), key=lambda kv: -kv[1][1])}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--games", nargs="*", default=None)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--label", default="contest")
    args = ap.parse_args()
    games = args.games or sorted(
        [p.stem for p in GAMES.glob(f"{L_NAME}__vs__A__s*.json")]
        + [p.stem for p in GAMES.glob(f"A__vs__{L_NAME}__s*.json")])
    print(f"{len(games)} games, {args.workers} workers", flush=True)
    rows = []
    with Pool(args.workers, maxtasksperchild=4) as pool:
        for row in pool.imap_unordered(analyse, games):
            rows.append(row)
            print(f"  {row['game_id']:28s} margin {row['margin']:+7.0f} "
                  f"events {len(row['events']):4d} reorder {row['reorder_gain']:+7.0f} "
                  f"replica misses {row['replica_money_misses']} {row['seconds']}s", flush=True)
    summary = summarise(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{args.label}.json"
    path.write_text(json.dumps({"summary": summary, "games": rows}), encoding="utf-8")
    print(f"saved {path.relative_to(ROOT)}")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
