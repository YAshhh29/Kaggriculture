"""Per-item late-game revenue, us minus them, across many real games.

Runs tools.analysis.endgame_fills on our close live games (|margin| below
--close) for the given submissions and adds up, per item, the difference in
sales revenue (net of product purchases) from --from-day on, split into won
and lost games, plus the revenue each side took in the last N steps.

    python -m tools.analysis.endgame_items --submissions 56601363 56601249
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def one(args):
    ep, from_day, tail = args
    from tools.analysis.endgame_fills import fills
    try:
        rec, log = fills(ep)
    except Exception as error:
        return {"ep": ep, "error": repr(error)}
    per = defaultdict(float)
    last = defaultdict(float)
    units = defaultdict(int)
    for step, who, op, item, price in log:
        if step // 24 < from_day or op not in ("SELL", "BUY_PRODUCT"):
            continue
        s = (1 if who == "us" else -1) * (price if op == "SELL" else -price)
        per[item] += s
        if op == "SELL":
            units[f"{item}:{who}"] += 1
            if step >= 720 - tail:
                last[f"{item}:{who}"] += price
    return {"ep": ep, "won": rec["rewards"]["us"] > rec["rewards"]["them"],
            "margin": rec["rewards"]["us"] - rec["rewards"]["them"],
            "per": dict(per), "last": dict(last), "units": dict(units),
            "opponent": rec.get("opponent")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions", type=int, nargs="+", required=True)
    ap.add_argument("--close", type=float, default=3000)
    ap.add_argument("--from-day", type=int, default=24)
    ap.add_argument("--tail", type=int, default=8, help="steps counted as the final dump")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "rl" / "data" / "l2" / "eval" / "endgame_items.json"))
    args = ap.parse_args()
    eps = []
    for p in sorted((ROOT / "rl" / "data" / "our_live_tapes").glob("ep*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if (r.get("submission") in args.submissions
                and abs(r["rewards"]["us"] - r["rewards"]["them"]) < args.close):
            eps.append(r["episode_id"])
    print(f"{len(eps)} close games", flush=True)
    with Pool(args.workers) as pool:
        rows = pool.map(one, [(e, args.from_day, args.tail) for e in eps])
    Path(args.out).write_text(json.dumps(rows), encoding="utf-8")
    bad = [r for r in rows if "error" in r]
    if bad:
        print(f"{len(bad)} games failed: {bad[:3]}")
    rows = [r for r in rows if "error" not in r]
    items = sorted({k for r in rows for k in r["per"]})
    for lab, sel in (("LOST", [r for r in rows if not r["won"]]), ("WON", [r for r in rows if r["won"]])):
        if not sel:
            continue
        print(f"{lab}: {len(sel)} games, median margin "
              f"{sorted(r['margin'] for r in sel)[len(sel) // 2]:+.0f}; "
              f"from day {args.from_day}, us - them per game:")
        n = len(sel)
        for it in items:
            v = [r["per"].get(it, 0.0) for r in sel]
            lu = sum(r["last"].get(f"{it}:us", 0.0) for r in sel) / n
            lt = sum(r["last"].get(f"{it}:them", 0.0) for r in sel) / n
            uu = sum(r["units"].get(f"{it}:us", 0) for r in sel) / n
            ut = sum(r["units"].get(f"{it}:them", 0) for r in sel) / n
            print(f"   {it:10s} mean {sum(v) / n:+8.1f}  worse in {sum(x < 0 for x in v):3d}/{n}"
                  f"   units sold us {uu:6.1f} them {ut:6.1f}"
                  f"   last {args.tail} steps $ us {lu:7.1f} them {lt:7.1f}")


if __name__ == "__main__":
    main()
