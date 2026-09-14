"""Pair configs that were run in separate processes by `crop_mix --dump`.

Each dump holds the panel it was run against and one (ours, theirs) row
per game in the same order, so a variant can be compared game by game
with the baseline -- which is the only comparison fine enough to trust
when the means move by less than a game's own noise.

    python -m tools.eval.pair_dumps DIR now
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("base")
    args = parser.parse_args()

    folder = Path(args.directory)
    base = json.loads((folder / (args.base + ".json")).read_text())
    for path in sorted(folder.glob("*.json")):
        if path.stem == args.base:
            continue
        other = json.loads(path.read_text())
        if other["field"] != base["field"]:
            print(f"  {path.stem}: different panel, not paired")
            continue
        pairs = list(zip(base["rows"], other["rows"]))
        mine = [b[0] for _, b in pairs]
        margin = statistics.mean(b[0] - b[1] for _, b in pairs)
        base_margin = statistics.mean(a[0] - a[1] for a, _ in pairs)
        wins = sum(1 for _, b in pairs if b[0] > b[1])
        score_up = sum(1 for a, b in pairs if b[0] > a[0])
        margin_up = sum(1 for a, b in pairs
                        if (b[0] - b[1]) > (a[0] - a[1]))
        print(f"  {path.stem:18s} mean {statistics.mean(mine):9,.0f}  "
              f"wins {wins:2d}/{len(pairs)}  margin {margin:+9,.0f} "
              f"({margin - base_margin:+8,.0f} vs base)  "
              f"score up {score_up}/{len(pairs)}  "
              f"margin up {margin_up}/{len(pairs)}")


if __name__ == "__main__":
    main()
