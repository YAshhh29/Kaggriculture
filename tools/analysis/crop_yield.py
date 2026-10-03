"""What each plant was worth when it was pulled up.

A once-harvested crop banks one unit when it is sown and one more for every
watering inside `[(max_yield_day + 1) // 2 .. max_yield_day]`, doubled on a
fertilized day, capped at `max_yield`. Wheat therefore pays 6 units if it is
watered and manured across days 2 to 4, and 1 if it is pulled on the day it
first bears. The plant costs the same seed and the same sowing turn either
way, so the number that matters is not how much was harvested but how much
was harvested per plant.

This hooks `_apply_unit_action` and reads the tile the worker is standing on
just before the engine clears it, which is the only moment both the crop and
its accrued units are still on the board.

    python -m tools.analysis.crop_yield candidates.candidate_j:agent --tapes 3
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rl.replay_agent import build_replay_agent  # noqa: E402
from tools.eval.measure_panel import resolve  # noqa: E402


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


class Book:
    def __init__(self) -> None:
        self.units: Counter = Counter()
        self.pulls: Counter = Counter()
        self.age: Counter = Counter()
        self.early: Counter = Counter()
        self.sown: Counter = Counter()
        # Waterings that landed inside the yield window, where the engine
        # actually adds units, and the manure that doubles each of them.
        self.in_window: Counter = Counter()
        self.wasted_water: Counter = Counter()
        self.manured: Counter = Counter()


def run(spec: str, tape: Path, crops: dict) -> tuple[Book, Book, float, float]:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    record = json.loads(tape.read_text(encoding="utf-8"))
    opponent = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    books = (Book(), Book())
    seat_of: dict[int, int] = {}
    raw_unit = engine._apply_unit_action

    def unit(farm, private, idx, action, board_size, day, turns_per_day,
             shed_capacity=100):
        seat = seat_of.get(id(farm))
        op = action[0] if isinstance(action, list) and action else None
        if seat is None or op not in ("HARVEST", "PLANT", "WATER",
                                      "FERTILIZE"):
            return raw_unit(farm, private, idx, action, board_size, day,
                            turns_per_day, shed_capacity)
        book = books[seat]
        where = (farm["farmer"] if idx == 0
                 else (farm["hands"][idx - 1] if idx - 1 < len(farm["hands"])
                       else None))
        if where is None:
            return raw_unit(farm, private, idx, action, board_size, day,
                            turns_per_day, shed_capacity)
        x, y = int(where[0]), int(where[1])
        # A copy: HARVEST sets `tile["yield_units"] = 0` on this very dict,
        # so a reference taken here reads back as an empty plant.
        standing = farm["tiles"][y][x]
        before = dict(standing) if isinstance(standing, dict) else standing
        result = raw_unit(farm, private, idx, action, board_size, day,
                          turns_per_day, shed_capacity)
        after = farm["tiles"][y][x]
        if op == "PLANT":
            if isinstance(after, dict) and after.get("kind") == "PLANT":
                book.sown[after["crop"]] += 1
            return result
        if op in ("WATER", "FERTILIZE"):
            if not (isinstance(before, dict) and before.get("kind") == "PLANT"):
                return result
            crop = str(before.get("crop", ""))
            spec = crops.get(crop)
            if spec is None:
                return result
            if op == "FERTILIZE":
                book.manured[crop] += 1
                return result
            if before.get("watered_today"):
                return result
            age = day - int(before.get("planted_day", day))
            if spec["ongoing"]:
                return result
            start = (spec["max_yield_day"] + 1) // 2
            if start <= age <= spec["max_yield_day"]:
                book.in_window[crop] += 1
            else:
                book.wasted_water[crop] += 1
            return result
        # A harvest that took nothing left the tile untouched.
        if not (isinstance(before, dict) and before.get("kind") == "PLANT"):
            return result
        crop = str(before.get("crop", ""))
        took = int(before.get("yield_units", 0) or 0)
        if isinstance(after, dict) and after.get("kind") == "PLANT":
            took -= int(after.get("yield_units", 0) or 0)
        if took <= 0:
            return result
        age = day - int(before.get("planted_day", day))
        book.units[crop] += took
        book.pulls[crop] += 1
        book.age[crop] += age
        spec = crops.get(crop)
        if spec and not spec["ongoing"] and age < spec["max_yield_day"]:
            book.early[crop] += 1
        return result

    raw_interpreter = env.interpreter

    def interpreter(state, e):
        seat_of.clear()
        seat_of.update({id(farm): seat for seat, farm
                        in enumerate(state[0].observation.farms)})
        return raw_interpreter(state, e)

    engine._apply_unit_action = unit
    env.interpreter = interpreter
    try:
        env.run([resolve(spec), opponent])
    finally:
        engine._apply_unit_action = raw_unit
    final = env.steps[-1]
    return (books[0], books[1],
            float(final[0].get("reward") or 0.0),
            float(final[1].get("reward") or 0.0))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--tapes", type=int, default=3)
    args = parser.parse_args()

    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

    tapes = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    ours, theirs = Book(), Book()
    scores = [0.0, 0.0]
    for tape in tapes[: args.tapes]:
        mine, yours, a, b = run(args.spec, tape, CROPS)
        for source, total in ((mine, ours), (yours, theirs)):
            total.units.update(source.units)
            total.pulls.update(source.pulls)
            total.age.update(source.age)
            total.early.update(source.early)
            total.sown.update(source.sown)
            total.in_window.update(source.in_window)
            total.wasted_water.update(source.wasted_water)
            total.manured.update(source.manured)
        scores[0] += a
        scores[1] += b

    games = max(1, args.tapes)
    print(f"\n{args.spec}: yield per plant over {games} games "
          f"({scores[0] / games:,.0f} to {scores[1] / games:,.0f} a game)\n")
    print(f"  {'crop':12s} {'cap':>4s} | {'sown':>5s} {'units':>6s} "
          f"{'per plant':>10s} {'water':>6s} {'dung':>6s} | {'sown':>5s} "
          f"{'units':>6s} {'per plant':>10s} {'water':>6s} {'dung':>6s}")
    for crop, spec in CROPS.items():
        row = []
        for book in (ours, theirs):
            pulls = book.pulls.get(crop, 0)
            sown = book.sown.get(crop, 0)
            units = book.units.get(crop, 0)
            row.append((sown, units, units / max(1, sown),
                        book.in_window.get(crop, 0) / max(1, sown),
                        book.manured.get(crop, 0) / max(1, sown)))
        a, b = row
        print(f"  {crop:12s} {spec['max_yield']:4d} | {a[0]:5d} {a[1]:6d} "
              f"{a[2]:10.2f} {a[3]:6.2f} {a[4]:6.2f} | {b[0]:5d} {b[1]:6d} "
              f"{b[2]:10.2f} {b[3]:6.2f} {b[4]:6.2f}")
    print("\n  'early' counts once-harvested plants pulled before their last "
          "yield day,\n  which is where a six-unit wheat becomes a two-unit "
          "wheat.")


if __name__ == "__main__":
    main()
