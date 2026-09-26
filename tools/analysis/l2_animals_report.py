"""Aggregate the animal-economy traces (tools/analysis/l2_animals_trace.py).

For each group (L live games, A live games, top-30 corpus teams, and the
opponents of L / A), per animal type, per game on average:

* herd: animals bought, animal-days, purchase day;
* labour: FEED / CARE / HARVEST / COLLECT_FERTILIZER applied and refused;
* output: units credited, CARE bank paid out, lost at the cap, lost to an
  unfed production day, lost to escapes, still unpaid at the end, cares on
  unfed days (bank nothing);
* market: product units sold, revenue, average price, units sold at <= $5,
  products left unsold at the end;
* wheat eaten (and its market value at each feed), fertilizer collected;
* net value per animal-day and per animal action:
      product revenue + fertilizer collected x that seat's average
      fertilizer sale price - wheat eaten at market value - purchase cost.

    python -m tools.analysis.l2_animals_report
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAMES = ROOT / "rl" / "data" / "l2" / "animals" / "games"
OUT = ROOT / "rl" / "data" / "l2" / "animals"
TYPES = ("GOOSE", "COW", "SHEEP")
PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def _ops(side, animal, op, res="ok", days=None):
    cell = side["ops"].get(f"{animal}|{op}|{res}", {})
    return sum(v for d, v in cell.items() if days is None or int(d) in days)


def seat_row(game: dict, seat: int) -> dict:
    s = game["sides"][seat]
    sales = defaultdict(lambda: [0, 0.0, 0])      # item -> units, revenue, units <= 5
    buys = defaultdict(lambda: [0, 0.0])
    for step, op, item, price in s["market"]:
        if op == "SELL":
            c = sales[item]
            c[0] += 1
            c[1] += price
            c[2] += price <= 5
        elif op == "BUY_PRODUCT":
            buys[item][0] += 1
            buys[item][1] += price
    fert_price = (sales["FERTILIZER"][1] / sales["FERTILIZER"][0]
                  if sales["FERTILIZER"][0] else 60.0)
    wheat_sale = (sales["WHEAT"][1] / sales["WHEAT"][0] if sales["WHEAT"][0] else 25.0)
    row = {"reward": game["rewards"][seat], "fert_price": fert_price,
           "fert_sold": sales["FERTILIZER"][0], "fert_sold_rev": sales["FERTILIZER"][1],
           "fert_bought": buys["FERTILIZER"][0], "fert_bought_cost": buys["FERTILIZER"][1],
           "fert_used": sum(s["fert_used"].values()),
           "fert_collected": sum(s["fert_collected"].values()),
           "wheat_bought": buys["WHEAT"][0], "wheat_bought_cost": buys["WHEAT"][1],
           "wheat_sold": sales["WHEAT"][0], "wheat_sale_price": wheat_sale,
           "wheat_harvested": s["crop_harvest"].get("WHEAT", 0),
           "wheat_fed": sum(s["wheat_fed"].values()),
           "wheat_fed_value": s["wheat_fed_value"],
           "unit_turns": s["unit_turns"], "animal_turns": s["animal_turns"],
           "types": {}}
    total_fed = max(1, row["wheat_fed"])
    for a in TYPES:
        days = s["animal_days"].get(a, 0)
        if not days and not s["bought"].get(a):
            continue
        prod = PRODUCT[a]
        u, rev, floor = sales[prod]
        fed = s["wheat_fed"].get(a, 0)
        wheat_val = s["wheat_fed_value"] * fed / total_fed
        fert = s["fert_collected"].get(a, 0)
        cost = s["bought_cost"].get(a, 0.0)
        actions = sum(_ops(s, a, op, res)
                      for op in ("FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER")
                      for res in ("ok", "no"))
        net = rev + fert * fert_price - wheat_val - cost
        herd = s["herd"].get(a, {})
        first_day = min((int(d) for d, n in herd.items() if n), default=None)
        unsold = (s["end_shed"].get(prod, 0) + s["end_inv"].get(prod, 0)
                  + s["end_on_tiles"].get(prod, 0))
        cares = _ops(s, a, "CARE")
        row["types"][a] = {
            "bought": s["bought"].get(a, 0), "cost": cost, "animal_days": days,
            "first_day": first_day, "peak": max(herd.values(), default=0),
            "feed": _ops(s, a, "FEED"), "feed_no": _ops(s, a, "FEED", "no"),
            "care": cares, "care_no": _ops(s, a, "CARE", "no"),
            "care_d28plus": _ops(s, a, "CARE", days={28, 29}),
            "harvest": _ops(s, a, "HARVEST"), "harvest_no": _ops(s, a, "HARVEST", "no"),
            "collect": _ops(s, a, "COLLECT_FERTILIZER"),
            "collect_no": _ops(s, a, "COLLECT_FERTILIZER", "no"),
            "actions": actions,
            "made": s["prod_added"].get(a, 0), "raw": s["prod_raw"].get(a, 0),
            "prod_events": s["prod_events"].get(a, 0),
            "bonus_paid": s["bonus_paid"].get(a, 0),
            "care_banked": s["care_banked"].get(a, 0),
            "care_unfed": s["care_unfed"].get(a, 0),
            "bonus_lost_cap": s["bonus_lost_cap"].get(a, 0),
            "base_lost_cap": s["base_lost_cap"].get(a, 0),
            "bonus_lost_unfed": s["bonus_lost_unfed"].get(a, 0),
            "bonus_lost_escape": s["bonus_lost_escape"].get(a, 0),
            "bank_at_end": s["bank_at_end"].get(a, 0),
            "escaped": s["escaped"].get(a, 0), "unfed_days": s["unfed_days"].get(a, 0),
            "harvested": s["harvest_units"].get(prod, 0),
            "sold": u, "revenue": rev, "avg_price": rev / u if u else 0.0,
            "sold_floor": floor, "unsold": unsold,
            "wheat": fed, "wheat_value": wheat_val,
            "fert": fert, "fert_overwritten": s["fert_overwritten"].get(a, 0),
            "fert_value": fert * fert_price, "net": net,
        }
    return row


def load_group(group: str, which: str = "focus") -> list[dict]:
    rows = []
    for path in sorted((GAMES / group).glob("ep*.json")):
        g = json.loads(path.read_text(encoding="utf-8"))
        if not g.get("exact"):
            continue
        focus = int(g["meta"]["focus"])
        seat = focus if which == "focus" else 1 - focus
        r = seat_row(g, seat)
        r["episode_id"] = g["meta"]["episode_id"]
        r["won"] = (g["rewards"][focus] > g["rewards"][1 - focus]) == (which == "focus")
        r["margin"] = (g["rewards"][seat] - g["rewards"][1 - seat])
        r["opponent_rating"] = g["meta"].get("opponent_rating")
        r["team"] = g["meta"].get("team") if which == "focus" else g["meta"].get("opponent")
        rows.append(r)
    return rows


def mean(xs):
    xs = list(xs)
    return statistics.mean(xs) if xs else 0.0


def summarize(rows: list[dict], label: str) -> dict:
    out = {"label": label, "games": len(rows),
           "reward": mean(r["reward"] for r in rows),
           "fert_price": mean(r["fert_price"] for r in rows),
           "fert_collected": mean(r["fert_collected"] for r in rows),
           "fert_sold": mean(r["fert_sold"] for r in rows),
           "fert_bought": mean(r["fert_bought"] for r in rows),
           "fert_used": mean(r["fert_used"] for r in rows),
           "wheat_fed": mean(r["wheat_fed"] for r in rows),
           "wheat_fed_value": mean(r["wheat_fed_value"] for r in rows),
           "wheat_bought": mean(r["wheat_bought"] for r in rows),
           "wheat_bought_cost": mean(r["wheat_bought_cost"] for r in rows),
           "wheat_harvested": mean(r["wheat_harvested"] for r in rows),
           "animal_turns": mean(r["animal_turns"] for r in rows),
           "unit_turns": mean(r["unit_turns"] for r in rows),
           "types": {}}
    for a in TYPES:
        cells = [r["types"][a] for r in rows if a in r["types"]]
        if not cells:
            continue
        keys = cells[0].keys()
        agg = {k: mean(c[k] for c in cells if c[k] is not None) for k in keys}
        agg["games_with"] = len(cells)
        tot = lambda k: sum(c[k] for c in cells)  # noqa: E731
        days = tot("animal_days") or 1
        agg["net_per_animal_day"] = tot("net") / days
        agg["net_per_action"] = tot("net") / max(1, tot("actions"))
        agg["rev_per_animal_day"] = tot("revenue") / days
        agg["care_per_animal_day"] = tot("care") / days
        agg["units_per_care"] = tot("bonus_paid") / max(1, tot("care"))
        agg["care_wasted_share"] = 1 - tot("bonus_paid") / max(1, tot("care"))
        agg["avg_price_all"] = tot("revenue") / max(1, tot("sold"))
        # value of the CARE bonus at the average sale price of that game's product
        agg["care_bonus_value"] = mean(c["bonus_paid"] * c["avg_price"] for c in cells)
        agg["value_per_care"] = (sum(c["bonus_paid"] * c["avg_price"] for c in cells)
                                 / max(1, tot("care")))
        out["types"][a] = agg
    return out


def fmt(summary: dict) -> str:
    s = summary
    lines = [f"\n=== {s['label']}: {s['games']} games, mean reward {s['reward']:,.0f}",
             f"  labour: {s['animal_turns']:.0f} animal-op turns of {s['unit_turns']:.0f}"
             f" unit-turns; wheat fed {s['wheat_fed']:.0f} (market value"
             f" {s['wheat_fed_value']:,.0f}), wheat bought {s['wheat_bought']:.0f} for"
             f" {s['wheat_bought_cost']:,.0f}, wheat harvested {s['wheat_harvested']:.0f}",
             f"  fertilizer: collected {s['fert_collected']:.0f}, used {s['fert_used']:.0f},"
             f" sold {s['fert_sold']:.0f} at avg ${s['fert_price']:.0f}, bought"
             f" {s['fert_bought']:.0f}"]
    for a, t in s["types"].items():
        lines.append(
            f"  {a:5s} in {t['games_with']:3d} games | bought {t['bought']:.1f} (peak"
            f" {t['peak']:.1f}, first day {t['first_day']:.1f}) cost {t['cost']:,.0f} |"
            f" animal-days {t['animal_days']:.0f}")
        lines.append(
            f"        ops ok: FEED {t['feed']:.0f} CARE {t['care']:.0f} HARVEST"
            f" {t['harvest']:.0f} COLLECT {t['collect']:.0f} | refused: FEED"
            f" {t['feed_no']:.1f} CARE {t['care_no']:.1f} HARVEST {t['harvest_no']:.1f}"
            f" COLLECT {t['collect_no']:.1f} | CARE/animal-day {t['care_per_animal_day']:.2f}")
        lines.append(
            f"        made {t['made']:.0f} (bonus paid {t['bonus_paid']:.0f}; care banked"
            f" {t['care_banked']:.0f}, cared-unfed {t['care_unfed']:.1f}, CARE on d28-29"
            f" {t['care_d28plus']:.1f}; lost: cap {t['bonus_lost_cap'] + t['base_lost_cap']:.1f},"
            f" unfed-prod {t['bonus_lost_unfed']:.1f}, escape {t['bonus_lost_escape']:.1f},"
            f" unpaid at end {t['bank_at_end']:.1f}); units per CARE {t['units_per_care']:.2f}")
        lines.append(
            f"        sold {t['sold']:.0f} for {t['revenue']:,.0f} (avg ${t['avg_price_all']:.0f};"
            f" at <=$5: {t['sold_floor']:.1f}; unsold at end {t['unsold']:.1f}) | wheat"
            f" {t['wheat']:.0f} (${t['wheat_value']:,.0f}) | fert {t['fert']:.0f}"
            f" (${t['fert_value']:,.0f}), overwritten {t['fert_overwritten']:.1f} |"
            f" escaped {t['escaped']:.2f}")
        lines.append(
            f"        NET {t['net']:,.0f}/game = ${t['net_per_animal_day']:.1f} per animal-day,"
            f" ${t['net_per_action']:.1f} per animal action; revenue/animal-day"
            f" ${t['rev_per_animal_day']:.1f}; CARE bonus worth ${t['care_bonus_value']:,.0f}"
            f"/game = ${t['value_per_care']:.1f} per CARE at avg price")
    return "\n".join(lines)


def main() -> None:
    groups = list(sys.argv[1:]) or ["L", "A", "top30"]
    report, text = {}, []
    for g in groups:
        if not (GAMES / g).exists():
            continue
        rows = load_group(g, "focus")
        if not rows:
            continue
        label = {"L": "L (live)", "A": "A (live)"}.get(g, f"corpus {g}")
        s = summarize(rows, label)
        report[g] = s
        text.append(fmt(s))
        if g in ("L", "A"):
            won = [r for r in rows if r["won"]]
            lost = [r for r in rows if not r["won"]]
            for sub, name in ((won, "won"), (lost, "lost")):
                if sub:
                    ss = summarize(sub, f"{label} games {name}")
                    report[f"{g}_{name}"] = ss
                    text.append(fmt(ss))
            opp = load_group(g, "other")
            so = summarize(opp, f"opponents of {g}")
            report[f"{g}_opp"] = so
            text.append(fmt(so))
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "_".join(groups)
    (OUT / f"report_{tag}.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    out = "\n".join(text)
    (OUT / f"report_{tag}.txt").write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
