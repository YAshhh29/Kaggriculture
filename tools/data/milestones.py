"""Step-level milestones: exactly when the best agents do each thing.

The daily build order in `rl/data/macro_plan.json` is too coarse to build
against. A farm that buys its second quadrant on step 96 and one that buys
it on step 140 look identical at day granularity and are not the same
opening at all.

So this reports, per tape, the **step** each milestone first happens, and
then the distribution across the corpus. It is the tally to build an
opening against: not "land by day 6" but "second quadrant at step 128,
interquartile 108 to 149".

Any agent can be measured on the same milestones by recording its actions
and passing them through `schedule_from_actions`, so our own opening can
be laid against the corpus opening line by line and the gaps read off.

    python -m tools.data.milestones --min-rating 2700
    python -m tools.data.milestones --agent candidates.candidate_g:agent
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.data.profile_tapes import INDEX, TAPES, load_tape  # noqa: E402

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")


def milestones(actions: list[dict[str, Any]]) -> dict[str, Any]:
    """The step each event first occurs, plus counts at fixed steps."""
    first: dict[str, int] = {}
    hires = 0
    land = 0
    animals = 0
    coops = 0
    pastures = 0
    plants = 0
    sells = 0
    at_step: dict[int, dict[str, int]] = {}
    marks = (24, 48, 72, 96, 120, 168, 240, 360, 480, 719)

    def note(key: str, step: int) -> None:
        first.setdefault(key, step)

    for step, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        for unit in [action.get("farmer"), *(action.get("hands") or [])]:
            if not isinstance(unit, list) or not unit:
                continue
            verb = str(unit[0])
            if verb == "BUILD_COOP":
                coops += 1
                note("first_coop", step)
            elif verb == "BUILD_PASTURE":
                pastures += 1
                note("first_pasture", step)
            elif verb == "PLANT":
                plants += 1
                note("first_plant", step)
                if len(unit) > 1:
                    note(f"first_plant_{unit[1]}", step)
            elif verb == "PLACE" and len(unit) > 1 and str(unit[1]) in ANIMALS:
                note(f"first_place_{unit[1]}", step)
        for order in action.get("market") or []:
            if not isinstance(order, list) or not order:
                continue
            verb = str(order[0])
            if verb == "HIRE":
                hires += 1
                note("first_hire", step)
                if hires == 4:
                    note("hire_4", step)
                if hires == 8:
                    note("hire_8", step)
            elif verb == "BUY_LAND":
                land += 1
                note(f"land_{land}", step)
            elif verb == "BUY_ANIMAL" and len(order) > 2:
                animals += int(order[2])
                note(f"buy_{order[1]}", step)
                if animals >= 4:
                    note("animals_4", step)
                if animals >= 8:
                    note("animals_8", step)
                if animals >= 12:
                    note("animals_12", step)
            elif verb == "SELL" and len(order) > 2:
                sells += 1
                note("first_sell", step)
                note(f"first_sell_{order[1]}", step)
        if step in marks:
            at_step[step] = {
                "hires": hires, "land": land, "animals": animals,
                "coops": coops, "pastures": pastures, "plants": plants,
                "hands": len(action.get("hands") or []),
            }
    return {"first": first, "at": at_step}


def schedule_from_actions(actions):
    return milestones(actions)


def record_agent(spec: str, seed: int = 11) -> list[dict[str, Any]]:
    """Play one game and keep the actions our agent issued."""
    from kaggle_environments import make

    from tools.eval.measure_panel import resolve

    captured: list[dict[str, Any]] = []
    inner = resolve(spec)

    def watched(observation, *rest):
        action = inner(observation)
        captured.append(json.loads(json.dumps(action)))
        return action

    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([watched, "starter"])
    return captured


KEYS = (
    "first_hire", "hire_4", "hire_8", "first_plant", "first_plant_WHEAT",
    "first_plant_MELON", "first_plant_CARROT", "first_plant_STRAWBERRY",
    "first_pasture", "first_coop", "buy_COW", "buy_SHEEP", "buy_GOOSE",
    "animals_4", "animals_8", "animals_12",
    "land_1", "land_2", "land_3",
    "first_sell", "first_sell_WHEAT", "first_sell_EGG",
    "first_sell_MILK", "first_sell_FERTILIZER",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-rating", type=float, default=2700.0)
    parser.add_argument("--agent", default=None)
    args = parser.parse_args()

    corpus: list[dict[str, Any]] = []
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if not path.exists() or row["episode_id"] in seen:
            continue
        if (row.get("rating") or 0) < args.min_rating:
            continue
        seen.add(row["episode_id"])
        corpus.append(milestones(load_tape(path)))

    print(f"{len(corpus)} elite tapes\n")
    mine = None
    if args.agent:
        mine = milestones(record_agent(args.agent))

    header = f"  {'milestone':24s} {'median':>7s} {'q1':>6s} {'q3':>6s} {'n':>5s}"
    if mine:
        header += f"  {'OURS':>7s}  gap"
    print("STEP at which each thing first happens  (24 steps = 1 day)")
    print(header)
    for key in KEYS:
        values = sorted(g["first"][key] for g in corpus if key in g["first"])
        if len(values) < 5:
            continue
        med = statistics.median(values)
        q1 = values[len(values) // 4]
        q3 = values[(3 * len(values)) // 4]
        line = (f"  {key:24s} {med:7.0f} {q1:6d} {q3:6d} "
                f"{len(values):5d}")
        if mine:
            ours = mine["first"].get(key)
            if ours is None:
                line += f"  {'never':>7s}  --"
            else:
                line += f"  {ours:7d}  {ours - med:+.0f}"
        print(line)

    print("\nCOUNTS at each step")
    fields = ("hands", "hires", "land", "animals", "coops", "pastures",
              "plants")
    print("  " + "step".ljust(10)
          + "".join(f"{f:>10}" for f in fields)
          + ("   | ours" if mine else ""))
    for step in (24, 48, 72, 96, 120, 168, 240, 360, 480, 719):
        rows = [g["at"][step] for g in corpus if step in g["at"]]
        if not rows:
            continue
        line = "  " + str(step).ljust(10) + "".join(
            f"{statistics.median(r[f] for r in rows):10.0f}" for f in fields
        )
        if mine and step in mine["at"]:
            line += "   | " + " ".join(
                f"{mine['at'][step][f]}" for f in fields
            )
        print(line)


if __name__ == "__main__":
    main()
