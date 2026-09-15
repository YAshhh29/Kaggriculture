"""Measure Candidate H's demand layer against its farming base alone.

Both variants play the same current top-team replays, from the same seats
and seeds, in a fixed town, so each H game has an exact counterpart without
the layer. It reports H's margin change game by game, and optionally both
variants head to head against Candidate G.

    python -m tools.eval.measure_h --base PATH/main.py --opponents 12 --tapes 4
    python -m tools.eval.measure_h --base PATH/main.py --set rival_share=0.7
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
import uuid
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_base(path: str):
    sys.path.insert(0, str(Path(path).parent))
    try:
        spec = importlib.util.spec_from_file_location(
            "h_base_" + uuid.uuid4().hex, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(Path(path).parent))
    return module.agent


def one(job):
    base_path, settings, variant, tape, seed, seat, versus = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    from rl.candidate_h_demand import wrap
    from tools.eval.fair_town import install
    from tools.eval.measure_panel import resolve

    install()
    agent = _load_base(base_path)
    if variant == "H":
        agent = wrap(agent, settings)
    if versus == "G":
        import rl.candidate_g as G
        opponent = G.agent
    elif versus == "mirror":
        # The same base without the layer, in the other seat: the farming is
        # identical, so the game is decided by how each side sells into the
        # books both are filling.
        opponent = _load_base(base_path)
    else:
        opponent = resolve("clone:" + tape)
    agents = [agent, opponent] if seat == 0 else [opponent, agent]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run(agents)
    return (env.state[seat].reward or 0.0, env.state[1 - seat].reward or 0.0)


def _parse(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--opponents", type=int, default=12)
    parser.add_argument("--tapes", type=int, default=4)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--versus-g", type=int, default=2,
                        help="games per seat head to head against G")
    parser.add_argument("--mirror", type=int, default=0,
                        help="seeds of H against its own base, both seats")
    parser.add_argument("--set", action="append", default=[])
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    from tools.eval.inspect_g import pick_field

    settings = {}
    for item in args.set:
        key, _, raw = item.partition("=")
        settings[key] = _parse(raw)

    field = pick_field(args.opponents, args.tapes, min(3, args.tapes), 20000)
    games = [(tape, 11 + i, i % 2) for _, _, paths in field
             for i, tape in enumerate(paths)]
    print(f"{len(games)} games vs {len(field)} current top teams, "
          f"settings {settings or 'defaults'}", flush=True)
    jobs = []
    for variant in ("base", "H"):
        for tape, seed, seat in games:
            jobs.append((args.base, settings, variant, tape, seed, seat, None))
        for k in range(args.versus_g):
            for seat in (0, 1):
                jobs.append((args.base, settings, variant, None, 41 + k,
                             seat, "G"))
    mirror_jobs = [(args.base, settings, "H", None, 61 + k, seat, "mirror")
                   for k in range(args.mirror) for seat in (0, 1)]
    with Pool(args.workers) as pool:
        results = pool.map(one, jobs + mirror_jobs)
    mirror = results[len(jobs):]
    results = results[:len(jobs)]

    n = len(games)
    g = args.versus_g * 2
    base_rows, base_g = results[:n], results[n:n + g]
    h_rows, h_g = results[n + g:2 * n + g], results[2 * n + g:]
    deltas = [(h[0] - h[1]) - (b[0] - b[1]) for b, h in zip(base_rows, h_rows)]
    if n:
        for label, rows in (("base", base_rows), ("H", h_rows)):
            print(f"  {label:4s} vs replays: mean "
                  f"{statistics.mean(r[0] for r in rows):,.0f} opp "
                  f"{statistics.mean(r[1] for r in rows):,.0f} margin "
                  f"{statistics.mean(r[0] - r[1] for r in rows):+,.0f} "
                  f"wins {sum(r[0] > r[1] for r in rows)}/{n}")
        print(f"  H vs base, paired on {n} games: margin "
              f"{statistics.mean(deltas):+,.0f} a game (median "
              f"{statistics.median(deltas):+,.0f}), better in "
              f"{sum(d > 0 for d in deltas)}, worse in "
              f"{sum(d < 0 for d in deltas)}, identical in "
              f"{sum(d == 0 for d in deltas)}")
    for label, rows in (("base", base_g), ("H", h_g)):
        if rows:
            print(f"  {label:4s} vs G: " + ", ".join(
                f"{a:,.0f}-{b:,.0f}" for a, b in rows))
    if mirror:
        margins = [a - b for a, b in mirror]
        print(f"  H vs its own base head to head, {len(mirror)} games: "
              f"H wins {sum(m > 0 for m in margins)}, loses "
              f"{sum(m < 0 for m in margins)}, ties {sum(m == 0 for m in margins)}; "
              f"mean margin {statistics.mean(margins):+,.0f} (median "
              f"{statistics.median(margins):+,.0f})")


if __name__ == "__main__":
    main()
