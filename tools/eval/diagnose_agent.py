"""Not "how often does it win" but "what is true in the games it loses".

`tools/eval/measure_panel.py` answers whether one agent beats another. It
cannot answer the question that decides what to build next: when this
agent loses, what is different about that game?

So this replays the same panel and keeps, for every game, the things that
could plausibly separate a win from a loss -- the opponent and its rating,
which seat we took, the money curve for both farms, what each side sold
and what it fetched, the market inventory we drove each good to, and the
farm we finished with. Then it groups by outcome and prints what actually
differs.

Everything here is read from the replay the simulator produces, so it
costs one extra pass over games that had to be played anyway.

    python -m tools.eval.diagnose_agent rl.candidate_f:agent --limit 16
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.eval.measure_panel import panel, resolve  # noqa: E402

GOODS = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER",
)
TURNS_PER_DAY = 24
MARKET_I0 = 10000


def _money(step: list[dict[str, Any]], side: int) -> float:
    for view in step:
        observation = view.get("observation")
        if isinstance(observation, dict) and observation.get("farms"):
            farms = observation["farms"]
            if side < len(farms) and isinstance(farms[side], dict):
                return float(farms[side].get("money", 0.0) or 0.0)
    return 0.0


def _market(step: list[dict[str, Any]]) -> dict[str, float]:
    for view in step:
        observation = view.get("observation")
        if isinstance(observation, dict) and observation.get("market"):
            stock = (observation["market"] or {}).get("inventory") or {}
            return {k: float(v) for k, v in stock.items()}
    return {}


def _farm_state(step: list[dict[str, Any]], side: int) -> dict[str, Any]:
    for view in step:
        observation = view.get("observation")
        if isinstance(observation, dict) and observation.get("farms"):
            farms = observation["farms"]
            if side >= len(farms) or not isinstance(farms[side], dict):
                break
            farm = farms[side]
            animals: Counter[str] = Counter()
            crops: Counter[str] = Counter()
            owned = 0
            for row in (farm.get("tiles") or []):
                for tile in row:
                    if tile == "LOCKED":
                        continue
                    owned += 1
                    if isinstance(tile, dict):
                        if "animal" in tile:
                            animals[str(tile["animal"])] += 1
                        elif tile.get("kind") == "PLANT":
                            crops[str(tile.get("crop", "?"))] += 1
            return {
                "money": float(farm.get("money", 0.0) or 0.0),
                "tiles": owned,
                "quadrants": len(farm.get("unlocked_quadrants") or []),
                "animals": dict(animals),
                "herd": sum(animals.values()),
                "crops": dict(crops),
                "planted": sum(crops.values()),
            }
    return {}


def _sold(steps: list[Any], side: int) -> dict[str, int]:
    """Units each side *ordered* sold. Requests, not fills -- but the
    engine clamps to the shed, so this is an upper bound that still ranks
    goods correctly against each other."""
    out: Counter[str] = Counter()
    for step in steps:
        if side >= len(step):
            continue
        action = step[side].get("action")
        if not isinstance(action, dict):
            continue
        for order in action.get("market") or []:
            if (isinstance(order, list) and len(order) > 2
                    and order[0] == "SELL"):
                try:
                    out[str(order[1])] += int(order[2])
                except (TypeError, ValueError):
                    continue
    return dict(out)


def one(job) -> dict[str, Any]:
    spec, row, seed, seat = job
    from kaggle_environments import make

    from rl.replay_agent import load_replay_agent

    mine = resolve(spec)
    theirs = load_replay_agent(Path(row["path"]))
    players = [mine, theirs] if seat == 0 else [theirs, mine]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(players)
    steps = env.toJSON()["steps"]
    final = steps[-1]
    ours = float(final[seat].get("reward") or 0.0)
    rival = float(final[1 - seat].get("reward") or 0.0)

    lead = []
    for day in range(0, 30):
        index = min(day * TURNS_PER_DAY, len(steps) - 1)
        lead.append(_money(steps[index], seat) - _money(steps[index], 1 - seat))
    market = _market(steps[-1])

    return {
        "opponent": row["name"],
        "opponent_rating": row["rating"],
        "episode": row["episode_id"],
        "seed": seed,
        "seat": seat,
        "ours": ours,
        "theirs": rival,
        "margin": ours - rival,
        "won": ours > rival,
        "status": str(final[seat].get("status")),
        "lead_by_day": lead,
        "our_farm": _farm_state(steps[-1], seat),
        "their_farm": _farm_state(steps[-1], 1 - seat),
        "our_sales": _sold(steps, seat),
        "their_sales": _sold(steps, 1 - seat),
        "market_end": {g: market.get(g, MARKET_I0) - MARKET_I0 for g in GOODS},
    }


def summarise(rows: list[dict[str, Any]], label: str) -> None:
    if not rows:
        print(f"  {label}: none")
        return
    farm = [r["our_farm"] for r in rows if r["our_farm"]]
    theirs = [r["their_farm"] for r in rows if r["their_farm"]]

    def avg(items, key):
        vals = [i[key] for i in items if key in i]
        return statistics.mean(vals) if vals else 0.0

    flooded: Counter[str] = Counter()
    for row in rows:
        for good, over in row["market_end"].items():
            flooded[good] += over
    n = len(rows)
    print(f"\n  --- {label} ({n} games) ---")
    print(f"    ours {statistics.mean(r['ours'] for r in rows):9,.0f}   "
          f"theirs {statistics.mean(r['theirs'] for r in rows):9,.0f}   "
          f"margin {statistics.mean(r['margin'] for r in rows):+9,.0f}")
    rating = statistics.mean(r["opponent_rating"] for r in rows)
    seat0 = sum(1 for r in rows if r["seat"] == 0)
    print(f"    opponent rating {rating:7.0f}   "
          f"seat0 {seat0:3d}   seat1 {n - seat0:3d}")
    for name, items in (("our farm  ", farm), ("their farm", theirs)):
        print(f"    {name} tiles {avg(items, 'tiles'):5.1f}  "
              f"herd {avg(items, 'herd'):5.1f}  "
              f"planted {avg(items, 'planted'):5.1f}  "
              f"quadrants {avg(items, 'quadrants'):4.1f}")
    lead = [statistics.mean(r["lead_by_day"][d] for r in rows)
            for d in range(30)]
    marks = [0, 5, 10, 15, 20, 25, 29]
    print("    lead by day " + "  ".join(
        f"d{d}:{lead[d]:+,.0f}" for d in marks))
    top = sorted(flooded.items(), key=lambda kv: -kv[1])[:5]
    print("    market pushed above equilibrium at the end: " + "  ".join(
        f"{g} {v / n:+,.0f}" for g, v in top))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--panel", default="ladder",
                        choices=("ladder", "elite"))
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--skip", type=int, default=8)
    parser.add_argument("--seeds", default="11,29")
    parser.add_argument("--workers", type=int, default=11)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    rows = panel(args.panel, args.limit, args.skip)
    seeds = tuple(int(s) for s in args.seeds.split(","))
    jobs = [(args.spec, row, seed, seat)
            for row in rows for seed in seeds for seat in (0, 1)]
    print(f"{args.spec} on {len(rows)} {args.panel} tapes, "
          f"{len(jobs)} games", flush=True)
    with Pool(args.workers) as pool:
        out = pool.map(one, jobs)

    wins = [r for r in out if r["won"]]
    losses = [r for r in out if not r["won"]]
    print(f"\nwon {len(wins)}/{len(out)} ({len(wins) / len(out):.1%})")
    summarise(wins, "WINS")
    summarise(losses, "LOSSES")

    if losses:
        print("\n  every loss:")
        for row in sorted(losses, key=lambda r: r["margin"]):
            print(f"    {row['opponent'][:20]:22s} "
                  f"r{row['opponent_rating']:6.0f} "
                  f"seed {row['seed']:3d} seat {row['seat']}  "
                  f"{row['ours']:9,.0f} vs {row['theirs']:9,.0f}  "
                  f"{row['margin']:+9,.0f}")
    if args.out:
        Path(args.out).write_text(
            "\n".join(json.dumps(r) for r in out), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
