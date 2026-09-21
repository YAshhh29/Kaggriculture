"""What the flock actually returns, and what it drops on the floor.

`_daily_refresh_animals` is stricter than it looks:

    if days_since_first >= 0 and days_since_first % interval == 0:
        bonus = tile.pop("pending_care_bonus", 0) if tile["fed_today"] else 0
        tile["yield_units"] = min(max_held, yield_units + 1 + bonus)
        tile["pending_care_bonus"] = 0
    if tile["cared_today"] and tile["fed_today"]:
        tile["pending_care_bonus"] += 1

so a care day only ever pays if the animal is still fed on the production
day that follows it, the accrued bonus is wiped whether or not it was
collected, and everything above `max_held` is lost because the produce was
not carried away in time. Three separate ways to work for nothing:

    banked      care days that turned into a unit, as they should
    starved     care days wiped because the production day was not fed
    overflowed  units lost to `max_held` -- the animal was full
    escaped     animals lost outright at two unfed days

    python -m tools.analysis.herd_service rl.candidate_j:agent --tapes 4
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


class Herd:
    """One seat's animal book, counted inside the engine's own refresh."""

    def __init__(self) -> None:
        self.banked = 0
        self.starved = 0
        self.overflowed = 0
        self.escaped = 0
        self.produced = 0
        self.fed_days = 0
        self.care_days = 0
        self.animal_days: Counter = Counter()
        # An animal can go hungry two ways, and they need different repairs:
        # nobody carried grain to it, or there was no grain to carry.
        self.hungry_with_grain = 0
        self.hungry_without_grain = 0


def run(spec: str, tape: Path, animals: dict) -> tuple[Herd, Herd, float, float]:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    record = json.loads(tape.read_text(encoding="utf-8"))
    opponent = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    books = (Herd(), Herd())
    raw_refresh = engine._daily_refresh_animals
    seat_of: dict[int, int] = {}
    grain_of: dict[int, int] = {}

    def refresh(farm, day):
        seat = seat_of.get(id(farm))
        if seat is None:
            return raw_refresh(farm, day)
        book = books[seat]
        grain = grain_of.get(seat, 0)
        size = len(farm["tiles"])
        # Read every animal before the engine settles the day, because the
        # refresh mutates the tile in place and replaces an escaped one.
        before = {}
        for y in range(size):
            for x in range(size):
                tile = farm["tiles"][y][x]
                if isinstance(tile, dict) and "animal" in tile:
                    before[(x, y)] = dict(tile)
        result = raw_refresh(farm, day)
        for (x, y), was in before.items():
            now = farm["tiles"][y][x]
            kind = animals[was["animal"]]
            if not (isinstance(now, dict) and "animal" in now):
                book.escaped += 1
                continue
            book.animal_days[was["animal"]] += 1
            if was["fed_today"]:
                book.fed_days += 1
            elif grain > 0:
                book.hungry_with_grain += 1
            else:
                book.hungry_without_grain += 1
            if was["cared_today"] and was["fed_today"]:
                book.care_days += 1
            since = (day + 1) - was["placed_day"] - kind["first_yield_day"]
            if since < 0 or since % kind["interval"] != 0:
                continue
            pending = int(was.get("pending_care_bonus", 0) or 0)
            if not was["fed_today"]:
                # The production day was missed and the accrued care with it.
                book.starved += pending
                continue
            wanted = int(was["yield_units"]) + 1 + pending
            got = int(now["yield_units"])
            book.produced += got - int(was["yield_units"])
            book.banked += pending
            if wanted > kind["max_held"]:
                book.overflowed += wanted - kind["max_held"]
        return result

    raw_interpreter = env.interpreter

    def interpreter(state, e):
        farms = state[0].observation.farms
        seat_of.clear()
        seat_of.update({id(farm): seat for seat, farm in enumerate(farms)})
        # Grain on hand at the top of the step, shed and crew together: an
        # animal that goes hungry while this is positive was not short of
        # wheat, it was short of somebody willing to walk it over.
        for seat, s in enumerate(state):
            # The very first call arrives before `_initialize` has filled
            # the private book, so every field here is optional.
            private = s.observation.get("private") or {}
            carried = sum(int(bag.get("WHEAT", 0) or 0)
                          for bag in (private.get("inventories") or []))
            grain = int((private.get("shed") or {}).get("WHEAT", 0))
            grain_of[seat] = grain + carried
        return raw_interpreter(state, e)

    engine._daily_refresh_animals = refresh
    env.interpreter = interpreter
    try:
        env.run([resolve(spec), opponent])
    finally:
        engine._daily_refresh_animals = raw_refresh
    final = env.steps[-1]
    return (books[0], books[1],
            float(final[0].get("reward") or 0.0),
            float(final[1].get("reward") or 0.0))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--tapes", type=int, default=4)
    args = parser.parse_args()

    from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS

    tapes = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    ours, theirs = Herd(), Herd()
    scores = [0.0, 0.0]
    for tape in tapes[: args.tapes]:
        mine, yours, a, b = run(args.spec, tape, ANIMALS)
        for source, total in ((mine, ours), (yours, theirs)):
            total.banked += source.banked
            total.starved += source.starved
            total.overflowed += source.overflowed
            total.escaped += source.escaped
            total.produced += source.produced
            total.fed_days += source.fed_days
            total.care_days += source.care_days
            total.hungry_with_grain += source.hungry_with_grain
            total.hungry_without_grain += source.hungry_without_grain
            total.animal_days.update(source.animal_days)
        scores[0] += a
        scores[1] += b

    games = max(1, args.tapes)
    print(f"\n{args.spec}: the flock over {games} games "
          f"({scores[0] / games:,.0f} to {scores[1] / games:,.0f} a game)\n")
    print(f"  {'':24s} {'ours':>9s} {'theirs':>9s}")
    for label, a, b in (
            ("animal-days held", sum(ours.animal_days.values()),
             sum(theirs.animal_days.values())),
            ("days fed", ours.fed_days, theirs.fed_days),
            ("days fed and cared", ours.care_days, theirs.care_days),
            ("units produced", ours.produced, theirs.produced),
            ("care banked as units", ours.banked, theirs.banked),
            ("care wiped, unfed day", ours.starved, theirs.starved),
            ("units lost, animal full", ours.overflowed, theirs.overflowed),
            ("animals escaped", ours.escaped, theirs.escaped),
            ("hungry, grain was there", ours.hungry_with_grain,
             theirs.hungry_with_grain),
            ("hungry, no grain at all", ours.hungry_without_grain,
             theirs.hungry_without_grain)):
        print(f"  {label:24s} {a:9d} {b:9d}")

    print("\n  animal-days by kind:")
    for kind in sorted(set(ours.animal_days) | set(theirs.animal_days)):
        print(f"    {kind:12s} {ours.animal_days.get(kind, 0):6d} "
              f"{theirs.animal_days.get(kind, 0):6d}")

    if sum(ours.animal_days.values()):
        rate = ours.produced / sum(ours.animal_days.values())
        other = theirs.produced / max(1, sum(theirs.animal_days.values()))
        print(f"\n  units per animal-day: {rate:.2f} against {other:.2f}")


if __name__ == "__main__":
    main()
