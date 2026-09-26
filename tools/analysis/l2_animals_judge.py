"""Judge every CARE and FEED in the per-animal day logs (l2_animals_daylog).

CARE on day d (applied):
    unfed      the animal was not fed on day d -> banks nothing
    unpaid     banked, but no later production refresh (last refresh is the
               end of day 28) or the animal escaped first
    lost_unfed banked, but the animal was unfed on the production day that
               should pay it -> the whole bank resets
    lost_cap   banked, paid into a full tile -> truncated at max_held
    paid       credited one extra unit on production day p; split by the
               product price at p (<= $5 glut, $6-49, $50+)

FEED on day d (applied):
    bank       the animal was also cared that day (lets the CARE bank)
    payout     a production day with a bank > 0 (lets the bank pay)
    survive    the previous or the next day was unfed (prevents escape)
    idle       none of those: the wheat bought nothing

Also prints, for CAREs that were wasted, what else the unit could have
done on that tile at that moment (fertilizer available -> COLLECT; product
on the tile -> HARVEST), and at what hour and on which day they happen.

    python -m tools.analysis.l2_animals_judge L
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DAYLOG = ROOT / "rl" / "data" / "l2" / "animals" / "daylog"
OUT = ROOT / "rl" / "data" / "l2" / "animals"
LAST_REFRESH = 28


def judge_game(g: dict) -> dict:
    care = Counter()
    feed = Counter()
    care_by_type = defaultdict(Counter)
    feed_by_type = defaultdict(Counter)
    wasted_ctx = Counter()
    wasted_day = Counter()
    wasted_hour = Counter()
    feed_wasted_value = [0.0, 0.0]
    rows_by_key = {k: {r["d"]: r for r in rows} for k, rows in g["days"].items()}
    # applied CAREs / FEEDs by (key, day)
    for a in g["acts"]:
        step, idx, op, key = a[0], a[1], a[2], a[3]
        if key is None or len(a) < 7 or not a[4]:
            continue
        d = step // 24
        rows = rows_by_key.get(key, {})
        animal = key.split(",")[3]
        today = rows.get(d)
        if op == "CARE":
            if today is None:           # day 29 (no refresh) or escaped before
                verdict = "unpaid"
            elif not today["fed"]:
                verdict = "unfed"
            else:
                verdict = "unpaid"
                for p in range(d + 1, LAST_REFRESH + 1):
                    r = rows.get(p)
                    if r is None or r["esc"]:
                        break
                    if r["prod"]:
                        if not r["fed"]:
                            verdict = "lost_unfed"
                        elif r.get("cap", 0) > 0 and r.get("paid", 0) < r["bank"]:
                            verdict = "lost_cap"
                        else:
                            price = r["price"]
                            verdict = ("paid_glut" if price <= 5 else
                                       "paid_low" if price < 50 else "paid")
                        break
            care[verdict] += 1
            care_by_type[animal][verdict] += 1
            if verdict in ("unfed", "unpaid", "lost_unfed", "lost_cap"):
                y0, fa = a[6], a[7]
                wasted_ctx["fert_available" if fa else "no_fert"] += 1
                wasted_ctx["product_on_tile" if y0 > 0 else "empty_tile"] += 1
                wasted_day[d] += 1
                wasted_hour[step % 24] += 1
        elif op == "FEED":
            # What the FEED bought: a bank payout today, a CARE that banks
            # and is later paid, or survival; otherwise the wheat was wasted.
            if today is None:
                verdict = "wasted"
            else:
                prev = rows.get(d - 1)
                nxt = rows.get(d + 1)
                prev_unfed = prev is not None and not prev["fed"]
                next_unfed = nxt is not None and not nxt["fed"]
                care_fate = None
                if today["cared"]:
                    care_fate = "unpaid"
                    for p in range(d + 1, LAST_REFRESH + 1):
                        r = rows.get(p)
                        if r is None or r["esc"]:
                            break
                        if r["prod"]:
                            if not r["fed"]:
                                care_fate = "lost"
                            elif r.get("cap", 0) > 0 and r.get("paid", 0) < r["bank"]:
                                care_fate = "lost"
                            else:
                                care_fate = "glut" if r["price"] <= 5 else "paid"
                            break
                if today["prod"] and today.get("paid", 0) > 0:
                    verdict = "payout"
                elif care_fate == "paid":
                    verdict = "care_paid"
                elif prev_unfed or next_unfed:
                    verdict = "survive"
                elif care_fate == "glut":
                    verdict = "care_glut"
                else:
                    verdict = "wasted"
                if verdict == "wasted":
                    feed_wasted_value[0] += today["wheat"]
                if verdict == "care_glut":
                    feed_wasted_value[1] += today["wheat"]
            feed[verdict] += 1
            feed_by_type[animal][verdict] += 1
    return {"care": care, "feed": feed, "care_by_type": care_by_type,
            "feed_by_type": feed_by_type, "wasted_ctx": wasted_ctx,
            "wasted_day": wasted_day, "wasted_hour": wasted_hour,
            "feed_wasted_value": feed_wasted_value}


def main() -> None:
    group = sys.argv[1] if len(sys.argv) > 1 else "L"
    files = sorted((DAYLOG / group).glob("ep*.json"))
    tot = defaultdict(Counter)
    by_type = defaultdict(lambda: defaultdict(Counter))
    n = 0
    fwv = [0.0, 0.0]
    for path in files:
        g = json.loads(path.read_text(encoding="utf-8"))
        if not g.get("exact"):
            continue
        n += 1
        j = judge_game(g)
        for k in ("care", "feed", "wasted_ctx", "wasted_day", "wasted_hour"):
            tot[k].update(j[k])
        fwv[0] += j["feed_wasted_value"][0]
        fwv[1] += j["feed_wasted_value"][1]
        for k in ("care_by_type", "feed_by_type"):
            for a, c in j[k].items():
                by_type[k][a].update(c)
    lines = [f"{group}: {n} exact games (per game)"]
    for k in ("care", "feed"):
        s = sum(tot[k].values())
        lines.append(f"  {k.upper():5s} applied {s / n:6.1f}: " + ", ".join(
            f"{v}: {c / n:.1f} ({c / s:.0%})" for v, c in tot[k].most_common()))
        for a, c in sorted(by_type[f"{k}_by_type"].items()):
            s2 = sum(c.values())
            lines.append(f"      {a:5s} {s2 / n:6.1f}: " + ", ".join(
                f"{v}: {x / n:.1f}" for v, x in c.most_common()))
    lines.append(f"  wheat value of wasted FEEDs {fwv[0] / n:,.0f}/game; of FEEDs whose"
                 f" CARE was paid into a <=$5 book {fwv[1] / n:,.0f}/game")
    lines.append("  wasted-CARE context: " + ", ".join(
        f"{v}: {c / n:.1f}" for v, c in tot["wasted_ctx"].most_common()))
    lines.append("  wasted-CARE by day: " + " ".join(
        f"{d}:{c / n:.1f}" for d, c in sorted(tot["wasted_day"].items())))
    lines.append("  wasted-CARE by hour: " + " ".join(
        f"{h}:{c / n:.1f}" for h, c in sorted(tot["wasted_hour"].items())))
    text = "\n".join(lines)
    (OUT / f"judge_{group}.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
