"""What the top of the ladder actually does, mechanism by mechanism.

Earlier analysis here counted *what* elite agents buy and *when*. That is
not the same as knowing how they play, and Candidate G has been built
without ever answering the questions that decide a turn:

* **weeds** -- does anyone dig them, or is DIG a waste of a worker?
* **hiring** -- the wage is fibonacci in the number hired *today* and the
  crew is wiped nightly, so when in the day do they hire, and do they
  rebuild the whole crew every morning or let it decay?
* **land** -- at what cash, not what day, does a quadrant get bought?
* **selling** -- do they sell into a rising price or dump on a schedule?
  This is the market-demand question, and it can be answered by pairing
  each sale with the market inventory at that moment.
* **labour mix** -- what share of worker turns is movement, and how does
  that compare to ours?

Everything is read from the captured tapes plus a simulator replay to
recover the state each action was taken in.

    python -m tools.data.strategy_deep_dive --games 40
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.data.profile_tapes import INDEX, TAPES, load_tape  # noqa: E402

TURNS_PER_DAY = 24
MARKET_I0 = 10000
GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")


def elite_tapes(min_rating: float, limit: int) -> list[tuple[str, list]]:
    out: list[tuple[str, list]] = []
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists() or row["episode_id"] in seen:
            continue
        if (row.get("rating") or 0) < min_rating:
            continue
        seen.add(row["episode_id"])
        out.append((row["name"], load_tape(path)))
        if len(out) >= limit:
            break
    return out


def replay_state(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run a tape against itself to recover the state behind each action."""
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent

    agent = build_replay_agent(tuple(actions))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": 11}, debug=False)
    env.run([agent, agent])
    return env.steps


def analyse(actions: list[dict[str, Any]], steps) -> dict[str, Any]:
    verbs: Counter[str] = Counter()
    hire_hours: Counter[int] = Counter()
    hires_per_day: Counter[int] = Counter()
    sell_at: dict[str, list[float]] = defaultdict(list)
    weeds_seen = 0
    digs = 0
    land_cash: list[float] = []

    for step, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        hour = step % TURNS_PER_DAY
        day = step // TURNS_PER_DAY
        for unit in [action.get("farmer"), *(action.get("hands") or [])]:
            if isinstance(unit, list) and unit:
                verbs[str(unit[0])] += 1
                if str(unit[0]) == "DIG":
                    digs += 1
        observation = None
        if step < len(steps):
            for view in steps[step]:
                candidate = view.get("observation")
                if isinstance(candidate, dict) and candidate.get("farms"):
                    observation = candidate
                    break
        stock = {}
        money = 0.0
        if observation:
            stock = (observation.get("market") or {}).get("inventory") or {}
            farms = observation.get("farms") or []
            if farms and isinstance(farms[0], dict):
                money = float(farms[0].get("money", 0) or 0)
                for row in farms[0].get("tiles") or []:
                    for tile in row:
                        if isinstance(tile, dict) and tile.get("kind") == "WEED":
                            weeds_seen += 1
        for order in action.get("market") or []:
            if not isinstance(order, list) or not order:
                continue
            verb = str(order[0])
            if verb == "HIRE":
                hire_hours[hour] += 1
                hires_per_day[day] += 1
            elif verb == "BUY_LAND":
                land_cash.append(money)
            elif verb == "SELL" and len(order) > 2 and stock:
                good = str(order[1])
                if good in GOODS:
                    sell_at[good].append(
                        float(stock.get(good, MARKET_I0)) - MARKET_I0
                    )
    total = sum(verbs.values()) or 1
    moves = sum(verbs[d] for d in ("NORTH", "SOUTH", "EAST", "WEST"))
    return {
        "verbs": verbs,
        "move_share": moves / total,
        "pass_share": verbs.get("PASS", 0) / total,
        "hire_hours": hire_hours,
        "hires_per_day": hires_per_day,
        "sell_at": sell_at,
        "weeds_seen": weeds_seen,
        "digs": digs,
        "land_cash": land_cash,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=25)
    parser.add_argument("--min-rating", type=float, default=2700.0)
    args = parser.parse_args()

    tapes = elite_tapes(args.min_rating, args.games)
    print(f"{len(tapes)} elite games\n", flush=True)
    rows = []
    for name, actions in tapes:
        rows.append(analyse(actions, replay_state(actions)))

    print("=== labour mix ===")
    print(f"  movement share  {statistics.mean(r['move_share'] for r in rows):6.1%}")
    print(f"  PASS share      {statistics.mean(r['pass_share'] for r in rows):6.1%}")
    verbs: Counter[str] = Counter()
    for r in rows:
        verbs.update(r["verbs"])
    n = len(rows)
    work = [(k, v / n) for k, v in verbs.most_common()
            if k not in ("NORTH", "SOUTH", "EAST", "WEST", "PASS")]
    print("  per game: " + "  ".join(f"{k} {v:.0f}" for k, v in work[:9]))

    print("\n=== weeds ===")
    seen = statistics.mean(r["weeds_seen"] for r in rows)
    digs = statistics.mean(r["digs"] for r in rows)
    print(f"  weed-tile sightings per game {seen:7.0f}   DIG actions {digs:5.1f}")
    print("  -> weeds are " + ("dug" if digs > 5 else "IGNORED"))

    print("\n=== hiring ===")
    hours: Counter[int] = Counter()
    for r in rows:
        hours.update(r["hire_hours"])
    top = sorted(hours.items())[:6]
    print("  hires by hour of day: "
          + "  ".join(f"h{h}:{c / n:.1f}" for h, c in top))
    per_day = [statistics.mean(r["hires_per_day"].get(d, 0) for r in rows)
               for d in range(30)]
    print("  hires per day: " + " ".join(f"{v:.0f}" for v in per_day[:15]))

    print("\n=== land ===")
    cash = [c for r in rows for c in r["land_cash"]]
    if cash:
        print(f"  cash held when a quadrant is bought: "
              f"median {statistics.median(cash):,.0f}  "
              f"min {min(cash):,.0f}  max {max(cash):,.0f}")

    print("\n=== selling against market inventory ===")
    print("  (negative = market is short of the good, price above base)")
    print(f"  {'good':12s} {'median inv at sale':>19s} {'q1':>8s} {'q3':>8s}")
    for good in GOODS:
        vals = sorted(v for r in rows for v in r["sell_at"].get(good, []))
        if len(vals) < 10:
            continue
        print(f"  {good:12s} {statistics.median(vals):19,.0f} "
              f"{vals[len(vals) // 4]:8,.0f} {vals[3 * len(vals) // 4]:8,.0f}")


if __name__ == "__main__":
    main()
