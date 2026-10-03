"""Day-by-day trace of one live game: what the farm holds and what it did.

Instrumentation, not intuition. Wraps the engine's own `_apply_unit_action`
so every unit action is counted at source, then prints a per-day table of
portfolio, labour and money for both seats.

    python -m tools.analysis.trace_day candidates.candidate_j:agent candidates.candidate_g:agent --seed 11
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.eval.measure_panel import resolve  # noqa: E402

TURNS = 24
GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")


def run(spec: str, reference: str, seed: int, seat: int = 0) -> dict[str, Any]:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as K

    acts: list[Counter] = [Counter(), Counter()]
    moves = [0, 0]
    # The engine hands `farm` to the action applier, so identify the seat by
    # object identity against the farms list captured at initialize time.
    farms_ref: list[Any] = []
    raw_apply = K._apply_unit_action

    def apply(farm, private, idx, action, board_size, day, tpd, shed_capacity=100):
        who = 0
        for i, f in enumerate(farms_ref):
            if f is farm:
                who = i
        if isinstance(action, list) and action:
            op = action[0]
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                moves[who] += 1
            elif op != "PASS":
                # Count only actions that actually change something.
                before = repr(farm["tiles"][private and 0 or 0])  # cheap no-op
                acts[who][op] += 1
            else:
                acts[who]["PASS"] += 1
        return raw_apply(farm, private, idx, action, board_size, day, tpd,
                         shed_capacity)

    raw_init = K._initialize

    def init(state, env):
        raw_init(state, env)
        farms_ref.clear()
        farms_ref.extend(state[0].observation.farms)

    K._apply_unit_action = apply
    K._initialize = init
    try:
        mine, theirs = resolve(spec), resolve(reference)
        players = [mine, theirs] if seat == 0 else [theirs, mine]
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": seed,
                                  "runTimeout": 36000, "actTimeout": 60},
                   debug=True)
        env.run(players)
    finally:
        K._apply_unit_action = raw_apply
        K._initialize = raw_init

    return {"env": env, "acts": acts, "moves": moves}


def _obs(step: list[dict[str, Any]]) -> dict[str, Any]:
    for view in step:
        o = view.get("observation")
        if isinstance(o, dict) and o.get("farms"):
            return o
    return {}


def portfolio(farm: dict[str, Any]) -> dict[str, int]:
    out = Counter()
    for row in farm.get("tiles") or []:
        for tile in row:
            if tile == "LOCKED":
                out["locked"] += 1
            elif tile is None:
                out["empty"] += 1
            elif isinstance(tile, dict):
                if "animal" in tile:
                    out["animals"] += 1
                    out[tile["animal"]] += 1
                elif tile.get("kind") == "PLANT":
                    out["plants"] += 1
                    out[tile["crop"]] += 1
                elif tile.get("kind") == "WEED":
                    out["weed"] += 1
                else:
                    out["pen"] += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("reference")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--seat", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    out = run(args.spec, args.reference, args.seed, args.seat)
    env, acts, moves = out["env"], out["acts"], out["moves"]
    steps = env.steps
    me, you = args.seat, 1 - args.seat

    print(f"seed {args.seed}  seat {args.seat}  {args.spec} vs {args.reference}")
    print(f"{'day':>3} {'money':>9} {'opp':>9} {'pl':>3} {'an':>3} "
          f"{'pen':>3} {'wd':>3} {'em':>3} {'hands':>5} {'shed':>4} | "
          f"{'crops'}")
    for day in range(0, 30):
        i = min(day * TURNS + TURNS - 1, len(steps) - 1)
        o = _obs(steps[i])
        if not o:
            continue
        farms = o["farms"]
        p = portfolio(farms[me])
        priv = steps[i][me].get("observation", {}).get("private") or {}
        shed = priv.get("shed") or {}
        crops = " ".join(f"{c[:3]}{p[c]}" for c in
                         ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                          "GOOSE", "COW", "SHEEP") if p.get(c))
        print(f"{day:3d} {farms[me]['money']:9,.0f} {farms[you]['money']:9,.0f} "
              f"{p['plants']:3d} {p['animals']:3d} {p['pen']:3d} {p['weed']:3d} "
              f"{p['empty']:3d} {len(farms[me].get('hands') or []):5d} "
              f"{sum(shed.values()):4d} | {crops}")

    final = steps[-1]
    o = _obs(final)
    print("\nfinal market inventory (I0=10000):")
    inv = (o.get("market") or {}).get("inventory") or {}
    print("  " + "  ".join(f"{g[:4]} {inv.get(g, 0) - 10000:+d}" for g in GOODS))
    priv = final[me].get("observation", {}).get("private") or {}
    print(f"  shed left: {dict((k, v) for k, v in (priv.get('shed') or {}).items() if v)}")
    print(f"\nunit actions  mine={dict(acts[me].most_common())}")
    print(f"              walk={moves[me]}")
    print(f"opponent      theirs={dict(acts[you].most_common())}")
    print(f"              walk={moves[you]}")
    print(f"\nreward mine={final[me].get('reward')} theirs={final[you].get('reward')}")


if __name__ == "__main__":
    main()
