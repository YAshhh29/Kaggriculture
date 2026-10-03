"""Does the farm buy what this particular town happens to want?

The town draws its shops at random with replacement, so every episode has
a different appetite: a game with two YARN_STOREs eats four wool every
four steps and a game with none eats one a day from the town centre. Wool
ends a season worth 239 coins or 1 depending on that draw.

`candidates/demand.py` records the measurement that makes this the most important
number in the project: the correlation between a town's wool demand and
the sheep a team buys runs +0.672 for teams rated 2850 and above, +0.323
between 2400 and 2849, and +0.000 below 2400. Agents that ignore the draw
are structurally stuck outside the top of the ladder, however well they
play the rest of the game.

So this plays a spread of tapes, reads each town's actual shop set, and
asks whether the herd followed it -- for us and for the top-200 team in
the other seat, on the same board.

    python -m tools.analysis.demand_fit candidates.candidate_j:agent --tapes 12
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from candidates.demand import demand_rate  # noqa: E402
from rl.replay_agent import build_replay_agent  # noqa: E402
from tools.eval.measure_panel import resolve  # noqa: E402

ANIMAL_PRODUCT = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}


def _unpack(blob: str) -> tuple:
    return tuple(json.loads(zlib.decompress(base64.b64decode(blob)).decode()))


def _correlation(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    top = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    left = sum((x - mx) ** 2 for x in xs) ** 0.5
    right = sum((y - my) ** 2 for y in ys) ** 0.5
    if left == 0 or right == 0:
        return 0.0
    return top / (left * right)


def run(spec: str, tape: Path) -> dict:
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    record = json.loads(tape.read_text(encoding="utf-8"))
    opponent = build_replay_agent(_unpack(record["actions_zlib_b64"]))
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    bought = [{}, {}]
    farms: dict[int, int] = {}
    raw_commit = engine._commit_unit

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        ok = raw_commit(op, item, price, farm, private, market, shed_capacity)
        if ok and op == "BUY_ANIMAL":
            seat = farms.get(id(farm))
            if seat is not None:
                bought[seat][item] = bought[seat].get(item, 0) + 1
        return ok

    raw_interpreter = env.interpreter

    def interpreter(state, e):
        farms.clear()
        farms.update({id(f): seat for seat, f
                      in enumerate(state[0].observation.farms)})
        return raw_interpreter(state, e)

    engine._commit_unit = commit
    env.interpreter = interpreter
    try:
        env.run([resolve(spec), opponent])
    finally:
        engine._commit_unit = raw_commit

    final = env.steps[-1][0]["observation"]
    rate = demand_rate(final)
    return {
        "shops": list((final.get("town") or {}).get("unlocked_shops") or []),
        "rate": rate,
        "ours": bought[0],
        "theirs": bought[1],
        "our_score": float(env.steps[-1][0].get("reward") or 0.0),
        "their_score": float(env.steps[-1][1].get("reward") or 0.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--tapes", type=int, default=12)
    args = parser.parse_args()

    tapes = sorted(Path(ROOT, "kaggle_cache", "top200_tapes").glob("ep*.json"))
    rows = [run(args.spec, tape) for tape in tapes[: args.tapes]]

    print(f"\n{args.spec}: does the herd follow the town, {len(rows)} games\n")
    print(f"  {'game':>5s} {'wool/day':>9s} {'sheep':>6s} {'milk/day':>9s} "
          f"{'cows':>5s} | {'sheep':>6s} {'cows':>5s}  shops")
    for n, row in enumerate(rows):
        wool = row["rate"].get("WOOL", 0.0) * 24
        milk = row["rate"].get("MILK", 0.0) * 24
        yarn = sum(1 for s in row["shops"] if s == "YARN_STORE")
        print(f"  {n:5d} {wool:9.1f} {row['ours'].get('SHEEP', 0):6d} "
              f"{milk:9.1f} {row['ours'].get('COW', 0):5d} | "
              f"{row['theirs'].get('SHEEP', 0):6d} "
              f"{row['theirs'].get('COW', 0):5d}  {yarn} yarn, "
              f"{len(row['shops'])} shops")

    print("\n  correlation between the town's appetite and the herd bought:")
    print(f"    {'':22s} {'ours':>8s} {'theirs':>8s}")
    for animal, product in (("SHEEP", "WOOL"), ("COW", "MILK"),
                            ("GOOSE", "EGG")):
        want = [r["rate"].get(product, 0.0) for r in rows]
        mine = [float(r["ours"].get(animal, 0)) for r in rows]
        yours = [float(r["theirs"].get(animal, 0)) for r in rows]
        print(f"    {product + ' -> ' + animal:22s} "
              f"{_correlation(want, mine):+8.3f} "
              f"{_correlation(want, yours):+8.3f}")
    print("\n  +0.672 is the figure for teams rated 2850 and above; +0.000 is"
          "\n  the figure for everything below 2400.")
    print("\n  Read the 'theirs' column as nothing at all. That opponent is a"
          "\n  frozen action tape: it replays decisions taken in a game whose"
          "\n  town drew different shops, so it cannot answer this one. Its"
          "\n  near-zero score is construction, not weakness -- and the same"
          "\n  caveat applies to every panel in this repo. The opponents"
          "\n  cannot adapt to the board we make.")


if __name__ == "__main__":
    main()
