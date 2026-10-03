"""Would holding MILK / WOOL out of a crashed book have paid, in real games?

Rebuilds the MILK and WOOL books of each traced game exactly (I0, the town's
consumption from the recorded shop unlocks, and every unit both seats sold,
with the engine's rule that a $1 sale does not add to inventory) and checks
the rebuild against the recorded sale prices. Then replays our seat's sales
under a hold policy while the opponent's sales stay where they were:

* a unit our seat meant to sell whose price is below `hold_below` is held
  (kept in the shed) instead, up to `cap` units held per product;
* held units are sold on any later step while the price is at least
  `release_at`;
* from day `cutoff` on nothing is held and whatever is still held is sold
  on the first step of that day.

The opponent cannot react (a tape), so the result is the direct market
effect: our revenue change and the opponent's revenue change, per game.

    python -m tools.analysis.l2_animals_hold_sim L
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GAMES = ROOT / "rl" / "data" / "l2" / "animals" / "games"

from stack.market_front import _mf_price as price_of  # noqa: E402  (engine-exact)

SHOPS = {
    "BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}


def drain_at(shops: list[str], item: str, step: int) -> int:
    """Units of `item` the town consumes at the end of `step`."""
    out = 0
    if step % 4 == 0:
        for i, shop in enumerate(shops):
            if step >= 24 * 3 * (i + 1) and item in SHOPS[shop]:
                out += 2 if len(SHOPS[shop]) == 1 else 1
    if step % 24 == 0:
        out += 1
    return out


def sales_by_step(side: dict, item: str) -> dict[int, list[int]]:
    out = defaultdict(list)
    for step, op, it, price in side["market"]:
        if op == "SELL" and it == item:
            out[step].append(price)
    return out


def simulate(game: dict, item: str, hold_below: float, release_at: float,
             cap: int, cutoff: int, check: bool = False) -> dict:
    focus = int(game["meta"]["focus"])
    ours = sales_by_step(game["sides"][focus], item)
    theirs = sales_by_step(game["sides"][1 - focus], item)
    shops = game["shops"]
    inv = 10000
    held = 0
    rev = {"us": 0.0, "them": 0.0}
    mism = 0
    held_peak = 0
    for step in range(719):
        q_us = len(ours.get(step, []))
        q_th = len(theirs.get(step, []))
        rec = sorted([(p, 0) for p in ours.get(step, [])] + [(p, 1) for p in theirs.get(step, [])],
                     key=lambda t: (-t[0], t[1]))
        # Engine order: units in descending recorded price. Two units of
        # different seats at the same price were one lockstep round (both
        # quoted the same inventory, then both added).
        rounds, k = [], 0
        while k < len(rec):
            if (k + 1 < len(rec) and rec[k][0] == rec[k + 1][0]
                    and rec[k][1] != rec[k + 1][1]):
                rounds.append((rec[k][0], (0, 1)))
                k += 2
            else:
                rounds.append((rec[k][0], (rec[k][1],)))
                k += 1
        release_all = step >= cutoff * 24 and held > 0
        for rp, who_all in rounds:
            p = price_of(item, inv)
            if check and p != rp:
                mism += len(who_all)
            sold = 0
            for who in who_all:
                if who == 0 and not check and step < cutoff * 24                         and p < hold_below and held < cap:
                    held += 1
                    continue
                rev["us" if who == 0 else "them"] += p
                sold += 1
            if p > 1:
                inv += sold
        if not check and held and (release_all or price_of(item, inv) >= release_at):
            while held and (release_all or price_of(item, inv) >= release_at):
                p = price_of(item, inv)
                rev["us"] += p
                held -= 1
                if p > 1:
                    inv += 1
        held_peak = max(held_peak, held)
        inv -= drain_at(shops, item, step)
        del q_us, q_th
    if held:        # still held at the end: sold on the last step
        while held:
            p = price_of(item, inv)
            rev["us"] += p
            held -= 1
            if p > 1:
                inv += 1
    return {"rev": rev, "mismatch": mism, "held_peak": held_peak}


def main() -> None:
    group = sys.argv[1] if len(sys.argv) > 1 else "L"
    games = []
    for path in sorted((GAMES / group).glob("ep*.json")):
        g = json.loads(path.read_text(encoding="utf-8"))
        if g.get("exact"):
            games.append(g)
    print(f"{group}: {len(games)} games")
    for item in ("WOOL", "MILK"):
        base = [simulate(g, item, 0, 1e9, 0, 30, check=True) for g in games]
        units = sum(len(sales_by_step(g["sides"][int(g["meta"]["focus"])], item)) and 1 for g in games)
        mism = sum(b["mismatch"] for b in base)
        print(f"  {item}: rebuild mismatches {mism} units over {len(games)} games "
              f"(games selling it {units})")
        for hold_below, release_at, cap, cutoff in (
                (2, 30, 40, 27), (6, 30, 40, 27), (12, 40, 40, 27), (25, 60, 40, 27),
                (2, 60, 40, 27), (6, 80, 40, 27), (12, 80, 60, 27), (6, 30, 40, 29),
                (40, 80, 40, 27)):
            du, dt = [], []
            peaks = []
            for g, b in zip(games, base):
                s = simulate(g, item, hold_below, release_at, cap, cutoff)
                du.append(s["rev"]["us"] - b["rev"]["us"])
                dt.append(s["rev"]["them"] - b["rev"]["them"])
                peaks.append(s["held_peak"])
            print(f"    hold<{hold_below:>3} release>={release_at:>3} cap {cap} cutoff d{cutoff}: "
                  f"our revenue {statistics.mean(du):+7.0f}/game (median {statistics.median(du):+5.0f},"
                  f" better {sum(d > 0 for d in du)}, worse {sum(d < 0 for d in du)}), "
                  f"opponent {statistics.mean(dt):+7.0f}, margin {statistics.mean(du) - statistics.mean(dt):+7.0f};"
                  f" held peak {statistics.mean(peaks):.1f}")


if __name__ == "__main__":
    main()
