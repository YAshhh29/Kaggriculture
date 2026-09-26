"""Out-farm autopsy, part 5: a compact census of every live game of A and L.

Replays each live game exactly (both tapes, stock engine) with the engine books
of l2_outfarm_replay and keeps one summary row per game: the town, both farms'
units / revenue per item, plantings per crop, land purchases, wages, fertilizer
use, the tomato shortfall at step 432 (when V219 decides), whether V219 fired,
and how long the two farms stayed identical (a mirror game).

    python -m tools.analysis.l2_outfarm_census            # all A and L games
    python -m tools.analysis.l2_outfarm_census --summary  # print the tables only

Rows go to rl/data/l2/outfarm/census.jsonl (one per episode, rewritten).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_outfarm_replay import OUT, SUBMISSIONS, TAPES, load_record, replay  # noqa: E402

ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")


def side_summary(book: dict) -> dict:
    units, revenue = Counter(), Counter()
    late_units, late_rev = Counter(), Counter()
    for step, item, price in book["sales"]:
        units[item] += 1
        revenue[item] += price
        if step >= 25 * 24:
            late_units[item] += 1
            late_rev[item] += price
    seeds, animals, bought = Counter(), Counter(), Counter()
    spent = 0.0
    for step, op, item, price in book["buys"]:
        spent += price
        if op == "BUY_SEED":
            seeds[item] += 1
        elif op == "BUY_ANIMAL":
            animals[item] += 1
        else:
            bought[item] += 1
    plants = Counter(c for s, c, x, y in book["plant"])
    plants_by_day = {c: [s // 24 for s, cc, x, y in book["plant"] if cc == c] for c in ("TOMATO",)}
    harvest = Counter()
    for s, c, u, f, pd, x, y in book["harvest"]:
        harvest[c] += u
    fert = Counter(f[1] for f in book["fertilize"])
    census = book["census"]
    return {"units": dict(units), "revenue": dict(revenue),
            "late_units": dict(late_units), "late_revenue": dict(late_rev),
            "seeds": dict(seeds), "animals": dict(animals), "bought": dict(bought),
            "plants": dict(plants), "tomato_plant_days": plants_by_day["TOMATO"],
            "harvest": dict(harvest), "fertilize": dict(fert),
            "land": [[s // 24, q] for s, c, q in book["land"]],
            "wages": sum(c for s, c in book["hires"]),
            "binned": book["binned"],
            "herd_d14": sum((census.get("14") or census.get(14) or {}).get("animals", {}).values()),
            "money_by_day": {d: (census.get(str(d)) or census.get(d) or {}).get("money")
                             for d in (5, 8, 11, 14, 17, 20, 23, 26)}}


def _farm_key(c: dict) -> tuple:
    return (tuple(sorted(c.get("plants", {}).items())), tuple(sorted(c.get("animals", {}).items())),
            tuple(c.get("quadrants", [])))


def census_job(episode: int) -> dict:
    record = load_record(episode)
    run = replay(record)
    side = run["our_side"]
    us, them = run["books"][side], run["books"][1 - side]
    mirror_until = -1
    for d in range(30):
        cu, ct = us["census"].get(d) or us["census"].get(str(d)), them["census"].get(d) or them["census"].get(str(d))
        if cu and ct and _farm_key(cu) == _farm_key(ct):
            mirror_until = d
        else:
            break
    inv = run["market_inv"]
    row = {"episode_id": episode, "submission": record.get("submission"),
           "agent": SUBMISSIONS.get(record.get("submission")),
           "opponent": record.get("opponent"), "rating": record.get("opponent_rating"),
           "our_side": side, "seed": record["seed"], "exact": run["exact"],
           "us": run["rewards"][side], "them": run["rewards"][1 - side],
           "margin": run["rewards"][side] - run["rewards"][1 - side],
           "won": run["rewards"][side] > run["rewards"][1 - side],
           "shops": run["town"], "shops_by_day": run["shops_by_day"],
           "mirror_until": mirror_until,
           "tomato_short_432": -inv[432]["TOMATO"] if len(inv) > 432 else None,
           "straw_excess": {d: inv[d * 24]["STRAWBERRY"] for d in (15, 18, 21, 24, 27) if len(inv) > d * 24},
           "tomato_short": {d: -inv[d * 24]["TOMATO"] for d in (18, 21, 24, 26, 27, 28, 29) if len(inv) > d * 24},
           "sides": {"us": side_summary(us), "them": side_summary(them)}}
    return row


def run_all(workers: int) -> None:
    episodes = []
    for path in sorted(TAPES.glob("ep*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if r.get("submission") in SUBMISSIONS:
            episodes.append(r["episode_id"])
    out = OUT / "census.jsonl"
    done = {}
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done[row["episode_id"]] = row
    todo = [e for e in episodes if e not in done]
    print(f"{len(episodes)} games, {len(todo)} to replay", flush=True)
    with Pool(min(2, workers), maxtasksperchild=4) as pool:
        for row in pool.imap_unordered(census_job, todo):
            done[row["episode_id"]] = row
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"  ep{row['episode_id']} {row['agent']} exact={row['exact']} margin {row['margin']:+,.0f}",
                  flush=True)


def load_rows() -> list[dict]:
    out = OUT / "census.jsonl"
    rows = {}
    for line in out.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        rows[row["episode_id"]] = row
    return list(rows.values())


def summary() -> None:
    rows = load_rows()
    print(f"{len(rows)} games (exact replays: {sum(r['exact'] for r in rows)})")
    for agent in ("A", "L"):
        g = [r for r in rows if r["agent"] == agent]
        if not g:
            continue
        print(f"\n== {agent}: {len(g)} games, won {sum(r['won'] for r in g)}, "
              f"lost by >1000: {sum(r['margin'] < -1000 for r in g)}")
        mir = [r for r in g if r["mirror_until"] >= 17]
        print(f"  mirror through day 17: {len(mir)} games; won {sum(r['won'] for r in mir)}, "
              f"tied {sum(r['margin'] == 0 for r in mir)}, lost {sum(r['margin'] < 0 for r in mir)}; "
              f"median margin {statistics.median([r['margin'] for r in mir]) if mir else 0:+,.0f}")
        # strawberry value by town
        rows_s = []
        for r in g:
            s = r["sides"]["us"]
            n = s["units"].get("STRAWBERRY", 0)
            if n:
                rows_s.append((s["revenue"].get("STRAWBERRY", 0) / n, n, r))
        low = [x for x in rows_s if x[0] < 60]
        print(f"  our strawberries: median ${statistics.median(x[0] for x in rows_s):.0f}/unit; "
              f"{len(low)} games under $60/unit (their margin median "
              f"{statistics.median([x[2]['margin'] for x in low]) if low else 0:+,.0f}, "
              f"won {sum(x[2]['won'] for x in low)})")
        fired = [r for r in g if r["sides"]["us"]["plants"].get("TOMATO", 0) >= 10
                 and any(d == 18 for d in r["sides"]["us"]["tomato_plant_days"])]
        print(f"  V219 fired (us): {len(fired)} games; opponent planted tomato in "
              f"{sum(r['sides']['them']['plants'].get('TOMATO', 0) > 0 for r in g)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()
    if not args.summary:
        run_all(args.workers)
    summary()


if __name__ == "__main__":
    main()
