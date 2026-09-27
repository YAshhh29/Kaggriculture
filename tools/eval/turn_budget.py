"""Per-turn time of an agent against an opponent, against Kaggle's budget.

Kaggle gives each agent 1 s a turn plus a 60 s overage bank for the whole
game; every second over 1 s is drawn from the bank, and an empty bank is a
timeout. This plays full games and reports the slowest turn, the turns over
1 s, and the bank used (excess over 1 s summed; the first turn, which loads
the file, is reported separately).

    python -m tools.eval.turn_budget rl.l2_combo:l6 nb_haodou092_harvest_ledger --seeds 11 105
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from kaggle_environments import make

    from tools.arena.arena import CONFIG, load
    ap = argparse.ArgumentParser()
    ap.add_argument("factory")
    ap.add_argument("opponent")
    ap.add_argument("--seeds", type=int, nargs="+", default=[11])
    args = ap.parse_args()
    mod, fn = args.factory.split(":")
    for seed in args.seeds:
        for seat in (0, 1):
            ours = getattr(importlib.import_module(mod), fn)()
            times: list[float] = []

            def timed(o, c=None, _f=ours):
                t0 = time.perf_counter()
                try:
                    return _f(o, c)
                finally:
                    times.append(time.perf_counter() - t0)
            agents = [timed, load(args.opponent)] if seat == 0 else [load(args.opponent), timed]
            env = make("kaggriculture", configuration={**CONFIG, "seed": seed}, debug=False)
            env.run(agents)
            rest = times[1:]
            over = [t for t in rest if t > 1.0]
            print(f"seed {seed} seat {seat}: {env.state[seat].reward:,.0f} vs {env.state[1 - seat].reward:,.0f} | "
                  f"slowest {max(rest):.2f} s, mean {sum(rest) / len(rest) * 1000:.0f} ms, "
                  f"turns over 1 s {len(over)}, bank used {sum(t - 1.0 for t in over):.1f} s of 60",
                  flush=True)


if __name__ == "__main__":
    main()
