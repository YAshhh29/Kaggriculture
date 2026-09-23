"""Measure a candidate against four fixed strong opponents. NOT the ladder.

READ THIS BEFORE QUOTING A NUMBER FROM HERE. This panel measures whether
a change helps against four specific opponents. It does NOT tell you how
you would rank, and its roster is not a sample of any rating band:

    checked 2026-09-23 against the live board (top 136 teams fetched)
    * h2 is rated 2265 -- BELOW the 2600-2900 band, not above it
    * aurax7 and v34 are published NOTEBOOK code; neither author appears
      anywhere in the top 136 live teams, so their true current rating is
      unverified and may be far from "top-200"
    * i was never on the ladder at all -- it is ours, calibrated only by
      a local result against v34

So zero of the four are confirmed members of the 2600-2900 band, which is
where the real field sits: rank 23 is 2900 and rank 136 is 2711, so that
band is most of the visible board. For a number about THAT population use
`broad_panel`, which replays kaggle_cache/top200_tapes -- 498 of its 561
tapes are teams rated 2600-2899, across 197 distinct teams. This panel's
earlier claim to represent "a field that starts at 2760 for rank 200" was
never verified and is what caused a whole session of results to be
reported against the wrong population.

Still useful for what it is: fast, live (opponents react, unlike
broad_panel's open-loop recordings), and a fixed bar for A/B comparisons.

The four:

    aurax7      aurax7 / kaggriculture-shop-router-reactive-v7, a published
                notebook agent played live from its own source. Described
                here as "top-200" when it was added; that was never checked
                against a rating and did not hold up when it finally was.
    v34         ahmedberatozer / kaggriculture-v34-observed-market-timing,
                an earlier agent of the same lineage
    h2          our submission 56272262, live rating 2265, which sits about
                800 coins a game behind aurax7 over 32 games
    i           our route-replay agent, level with v34 (-6 coins over 16)

Both seats, a fixed seed set, and `actTimeout 60` on every game because the
default silently freezes an agent mid-game under load and the result still
looks complete.

    python -m tools.eval.strong_panel rl.candidate_j:agent --seeds 6
    python -m tools.eval.strong_panel rl.candidate_j:agent --against aurax7 h2
"""

from __future__ import annotations

import argparse
import statistics
import sys
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.eval.measure_panel import resolve  # noqa: E402

OPPONENTS = {
    "aurax7": ("rl.public_agents:aurax7", "published top-200 agent"),
    "v34": ("rl.public_agents:v34", "published agent, same lineage"),
    "h2": ("rl.candidate_h2_package:agent", "ours, live rating 2265"),
    "i": ("rl.candidate_i:agent", "ours, route replay"),
}
SEEDS = (11, 29, 53, 97, 131, 173, 211, 257, 307, 353, 401, 449)


def play(job) -> dict[str, Any]:
    spec, reference, seed, seat = job
    from kaggle_environments import make

    mine = resolve(spec)
    theirs = resolve(reference)
    players = [mine, theirs] if seat == 0 else [theirs, mine]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run(players)
    final = env.steps[-1]
    ours = float(final[seat].get("reward") or 0.0)
    rival = float(final[1 - seat].get("reward") or 0.0)
    return {"reference": reference, "ours": ours, "theirs": rival,
            "won": ours > rival, "status": str(final[seat].get("status"))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--seeds", type=int, default=6)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--against", nargs="+", default=list(OPPONENTS))
    args = parser.parse_args()

    seeds = SEEDS[: max(1, args.seeds)]
    jobs = []
    for name in args.against:
        if name not in OPPONENTS:
            raise SystemExit(f"unknown opponent {name!r}; "
                             f"choose from {', '.join(OPPONENTS)}")
        reference = OPPONENTS[name][0]
        jobs += [(args.spec, reference, seed, seat)
                 for seed in seeds for seat in (0, 1)]

    with Pool(args.workers) as pool:
        results = pool.map(play, jobs)

    print(f"\n{args.spec} against strong opponents, "
          f"{len(seeds)} seeds x 2 seats each\n")
    print(f"  {'opponent':10s} {'what it is':32s} {'wins':>7s} "
          f"{'ours':>10s} {'theirs':>10s} {'margin':>10s}")
    for name in args.against:
        reference, what = OPPONENTS[name]
        rows = [r for r in results if r["reference"] == reference]
        if not rows:
            continue
        wins = sum(r["won"] for r in rows)
        ours = statistics.median(r["ours"] for r in rows)
        theirs = statistics.median(r["theirs"] for r in rows)
        margin = statistics.median(r["ours"] - r["theirs"] for r in rows)
        print(f"  {name:10s} {what:32s} {wins:3d}/{len(rows):<3d} "
              f"{ours:10,.0f} {theirs:10,.0f} {margin:+10,.0f}")
    bad = [r for r in results if r["status"] != "DONE"]
    if bad:
        print(f"\n  WARNING: {len(bad)} games did not finish cleanly")


if __name__ == "__main__":
    main()
