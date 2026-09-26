"""What an agent does with its land, crew and cash, day by day.

Replays an agent's stored arena games exactly (at step t the action stored at
t+1 is applied; the final score is checked against the stored one) and prints,
per day, the median over its games of: unlocked quadrants, crew size, the share
of hand-turns spent on PASS, cash at noon, and planted tiles by crop. This is
the measurement a production layer is designed from: idle hands and idle cash
are what an extra project can use.

    python -m tools.analysis.agent_profile nb_tetsutani_demand
    python -m tools.analysis.agent_profile nb_tetsutani_demand --games 12 --days 8 10 12 18 24
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

from tools.arena.arena import CONFIG, GAMES, _unpack  # noqa: E402

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")


def _plants(farm: dict) -> Counter:
    out: Counter = Counter()
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                out[t.get("crop")] += 1
            elif isinstance(t, dict) and "animal" in t:
                out["ANIMAL"] += 1
    return out


def profile(job: tuple[str, int]) -> dict | None:
    path, seat = job
    from kaggle_environments import make

    record = json.loads(Path(path).read_text(encoding="utf-8"))
    tapes = [_unpack(t) for t in record["tapes"]]
    env = make("kaggriculture", configuration={**CONFIG, "seed": record["seed"]},
               debug=False)
    env.reset()
    days: dict[int, dict] = {}
    for t in range(719):
        act = tapes[seat][t + 1] or {}
        day = t // 24
        cell = days.setdefault(day, {"hands": 0, "hand_turns": 0, "idle": 0})
        for command in act.get("hands") or []:
            cell["hand_turns"] += 1
            cell["idle"] += (not command) or command[0] == "PASS"
        env.step([tapes[0][t + 1], tapes[1][t + 1]])
        farm = env.state[0].observation["farms"][seat]
        cell["hands"] = max(cell["hands"], len(farm.get("hands") or []))
        if t % 24 == 12:
            cell["quadrants"] = len(farm.get("unlocked_quadrants") or [])
            cell["money"] = float(farm["money"])
            cell["plants"] = _plants(farm)
    final = [float(env.state[i].reward or 0) for i in (0, 1)]
    exact = [round(x) for x in final] == [round(x) for x in record["rewards"]]
    return {"game": record["game_id"], "exact": exact,
            "won": final[seat] > final[1 - seat], "days": days}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agent")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--days", type=int, nargs="*",
                    default=[2, 5, 8, 9, 10, 11, 12, 14, 17, 20, 23, 26, 29])
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    jobs = []
    for path in sorted(GAMES.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        agents = record.get("agents") or []
        if args.agent not in agents or "tapes" not in record:
            continue
        if any(not str(s).startswith("DONE") for s in record.get("statuses") or []):
            continue
        jobs.append((str(path), agents.index(args.agent)))
    jobs = jobs[: args.games]
    print(f"{len(jobs)} stored games of {args.agent}", flush=True)
    with Pool(args.workers, maxtasksperchild=2) as pool:
        rows = [r for r in pool.imap_unordered(profile, jobs) if r]
    print(f"replays exact: {sum(r['exact'] for r in rows)}/{len(rows)}; "
          f"won {sum(r['won'] for r in rows)}/{len(rows)}\n")

    def med(values):
        values = list(values)
        return statistics.median(values) if values else 0

    head = "".join(f"{c[:5]:>7}" for c in CROPS)
    print(f"  {'day':>3} {'quad':>5} {'hands':>6} {'idle%':>6} {'cash':>9}{head} {'animal':>7}")
    for d in args.days:
        cells = [r["days"][d] for r in rows if d in r["days"] and "money" in r["days"][d]]
        if not cells:
            continue
        idle = med(100 * c["idle"] / c["hand_turns"] for c in cells if c["hand_turns"])
        crops = "".join(f"{med(c['plants'].get(k, 0) for c in cells):7.0f}" for k in CROPS)
        print(f"  {d:3d} {med(c['quadrants'] for c in cells):5.0f} "
              f"{med(c['hands'] for c in cells):6.0f} {idle:6.0f} "
              f"{med(c['money'] for c in cells):9,.0f}{crops} "
              f"{med(c['plants'].get('ANIMAL', 0) for c in cells):7.0f}")


if __name__ == "__main__":
    main()
