"""Compare whole crop mixes against the contested panel.

`refit` sweeps a scalar; CROP_TILES is a tuple of (crop, cap) pairs and
needs its own comparison. Named mixes are defined below and measured on
the same panel and the same margin metric as everything else.

    python -m tools.eval.crop_mix --opponents 30
"""

from __future__ import annotations

import argparse
import json
import statistics
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIXES: dict[str, dict] = {
    "now": {},
    # The dominant plan's income sits in the books it floods -- melon,
    # carrot, strawberry, and milk/wool/fertilizer from its seventeen
    # animals. Crowding those is what moves the margin; filling the ones
    # it abandons was measured to make the margin 24,936 worse.
    "crowd melon+carrot": {
        "CROP_TILES": (("MELON", 20), ("CARROT", 28), ("STRAWBERRY", 8)),
    },
    "crowd all three": {
        "CROP_TILES": (("MELON", 20), ("CARROT", 28), ("STRAWBERRY", 20)),
    },
    "melon heavy": {
        "CROP_TILES": (("MELON", 28), ("CARROT", 16), ("STRAWBERRY", 8)),
    },
    # The three differences the engine ledger found between G and the plan
    # the ladder copies: G never buys its third quadrant, keeps one sheep
    # to the plan's six, and has four strawberry tiles to its thirty-two.
    "third quadrant": {"LAND_DAYS": (1, 5, 9)},
    "plan herd": {"HERD_MIX": {"GOOSE": 3, "COW": 8, "SHEEP": 6}},
    "plan herd+land": {
        "LAND_DAYS": (1, 5, 9),
        "HERD_MIX": {"GOOSE": 3, "COW": 8, "SHEEP": 6},
    },
    # Strawberry is the book the town eats most of in the inspected games
    # (about 417 a game) and G sells 17 of. Cash-crop seed is bought only
    # above 1,500 coins and four a day, and G holds under 400 until about
    # day 9 -- exactly when the top farms plant theirs.
    "seed floor 400": {"CROP_SEED_FLOOR": 400.0},
    "seed batch 12": {"CROP_SEED_BATCH": 12},
    "strawberry first 32": {
        "CROP_TILES": (("STRAWBERRY", 32), ("MELON", 12), ("CARROT", 16)),
    },
    "strawberry push": {
        "CROP_SEED_FLOOR": 400.0,
        "CROP_SEED_BATCH": 12,
        "CROP_TILES": (("STRAWBERRY", 32), ("MELON", 12), ("CARROT", 16)),
    },
    # Thirty-two strawberry tiles need ground G does not have: the fair-town
    # baseline shows it spending 1,000 on land against the field's 2,917.
    # The third quadrant was only ever measured with the town coupled to
    # G's empty tiles, so that verdict does not stand.
    "strawberry push + land": {
        "CROP_SEED_FLOOR": 400.0,
        "CROP_SEED_BATCH": 12,
        "CROP_TILES": (("STRAWBERRY", 32), ("MELON", 12), ("CARROT", 16)),
        "LAND_DAYS": (1, 5, 9),
    },
    # The town takes 228 tomatoes a game and G sells none.
    "strawberry push + land + tomato": {
        "CROP_SEED_FLOOR": 400.0,
        "CROP_SEED_BATCH": 12,
        "CROP_TILES": (("STRAWBERRY", 32), ("TOMATO", 12), ("MELON", 12),
                       ("CARROT", 16)),
        "LAND_DAYS": (1, 5, 9),
    },
    # Seed was never the limit: a daily trace shows the board full from day
    # 9, wheat holding 24-28 of G's 50 tiles to feed nine animals (about
    # eleven tiles' worth), and strawberry frozen at the four tiles it got
    # when the second quadrant opened on day 5. These free ground instead
    # of spending the opening purse on seed.
    "strawberry first 32 + wheat 16": {
        "CROP_TILES": (("STRAWBERRY", 32), ("MELON", 12), ("CARROT", 16)),
        "WHEAT_TILES": 16,
    },
    "strawberry first 32 + wheat 16 + land": {
        "CROP_TILES": (("STRAWBERRY", 32), ("MELON", 12), ("CARROT", 16)),
        "WHEAT_TILES": 16,
        "LAND_DAYS": (1, 5, 9),
    },
    # Under the strawberry defaults each new quadrant sits half empty for
    # days: bought on day 5 with the purse left at 9 coins, NE still has 7
    # bare tiles on day 9, and SW bought on day 9 still has 5 on day 16.
    # The top teams buy on days 6 and 11. These move the purchases later,
    # so there is cash to seed the ground once it is open. Compare against
    # a fresh "now", since the defaults changed.
    "land 1 6 11": {"LAND_DAYS": (1, 6, 11)},
    "land 1 7 11": {"LAND_DAYS": (1, 7, 11)},
    "land 1 6 10": {"LAND_DAYS": (1, 6, 10)},
    "plan shape": {
        "LAND_DAYS": (1, 5, 9),
        "HERD_MIX": {"GOOSE": 3, "COW": 8, "SHEEP": 6},
        "CROP_TILES": (("STRAWBERRY", 32), ("MELON", 12), ("CARROT", 16)),
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponents", type=int, default=30)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--min-rating", type=float, default=2800.0)
    parser.add_argument("--contested", type=float, default=15000.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--dump", default="",
                        help="directory to write each config's games to")
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    from tools.eval.wide_panel import best_tape_per_opponent, one

    field = best_tape_per_opponent(args.opponents, args.min_rating,
                                   args.contested)
    if not field:
        raise SystemExit("no contested tapes held")
    seeds = list(range(11, 11 + args.seeds))
    names = args.only or list(MIXES)
    print(f"{len(field)} contested opponents x {len(seeds)} seeds x 2 seats "
          f"= {len(field) * len(seeds) * 2} games each", flush=True)

    out: dict[str, list] = {}
    for name in names:
        jobs = [("rl.candidate_g:agent", MIXES[name], tape, seed, seat)
                for _, tape, _ in field
                for seed in seeds
                for seat in (0, 1)]
        with Pool(args.workers) as pool:
            rows = pool.map(one, jobs)
        out[name] = rows
        if args.dump:
            # One config per process is the only way the pool survives on
            # Windows, so pairing has to happen across files afterwards.
            Path(args.dump).mkdir(parents=True, exist_ok=True)
            (Path(args.dump) / (name.replace(" ", "_").replace("+", "_")
                                + ".json")).write_text(
                json.dumps({"field": [t for _, t, _ in field], "rows": rows}))
        mine = [a for a, _ in rows]
        wins = sum(1 for a, b in rows if a > b)
        margin = statistics.mean(a - b for a, b in rows)
        print(f"  {name:22s} mean {statistics.mean(mine):9,.0f}"
              f"  median {statistics.median(mine):9,.0f}"
              f"  wins {wins:3d}/{len(mine)}"
              f"  margin {margin:+9,.0f}", flush=True)

    base = names[0]
    for name in names[1:]:
        better = sum(1 for (a, _), (b, _) in zip(out[base], out[name]) if b > a)
        print(f"  {name} beats {base} on {better}/{len(out[base])}", flush=True)


if __name__ == "__main__":
    main()
