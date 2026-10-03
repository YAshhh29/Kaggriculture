"""Direct check: does a newly-hired hand spend its first turns on unowned
land before reaching owned ground? Logs every hand's position, the tile
type it stands on, and its chosen action, turn by turn, for a chosen
window of the game.

Built to check a real observation from watching a replay: new hires
looked like they were spending several turns on land the farm had not
bought before ever doing anything productive. Confirmed real for a day-3
hire (three genuinely unowned tiles crossed, seven turns to first real
job) once the shed's own tile -- which is internally marked the same
"LOCKED" as true unowned ground, but is legitimately usable -- is told
apart from land that actually is unowned. See COLD_START_RADIUS in
candidate_j.py for the fix this led to.

    python -m tools.analysis.trace_new_hire --seed 11 --from 71 --to 84
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
from candidates import candidate_j as j  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--from", dest="lo", type=int, default=0)
    ap.add_argument("--to", dest="hi", type=int, default=24)
    args = ap.parse_args()

    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": args.seed,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)

    log = []

    def spy(observation, configuration=None):
        action = j.agent(observation, configuration)
        farm = observation.get("farms", [None, None])[0]
        tiles = farm.get("tiles") or []
        hands_before = [tuple(farm.get("farmer") or (0, 0))]
        hands_before += [tuple(h) for h in (farm.get("hands") or [])]
        row = []
        for idx, pos in enumerate(hands_before):
            x, y = int(pos[0]), int(pos[1])
            tile = (tiles[y][x] if 0 <= y < len(tiles)
                    and 0 <= x < len(tiles[y]) else "?")
            if j._on_shed(x, y):
                owned = "SHED"
            elif tile == "LOCKED":
                owned = "LOCKED"
            else:
                owned = "owned"
            act = ((action.get("hands") or [])[idx - 1] if idx > 0
                   else action.get("farmer"))
            row.append((idx, x, y, owned, act))
        log.append((observation.get("step"), len(hands_before), row))
        return action

    env.run([spy, "random"])

    print(f"seed {args.seed} -- per-hand position/tile/action, "
          f"steps {args.lo}-{args.hi - 1}\n")
    for step, n_hands, rows in log:
        if step is None or not (args.lo <= step < args.hi):
            continue
        print(f"step {step:3d}  hands={n_hands}")
        for idx, x, y, owned, act in rows:
            tag = "FARMER" if idx == 0 else f"hand{idx}"
            print(f"    {tag:7s} ({x:2d},{y:2d}) {owned:6s} action={act}")


if __name__ == "__main__":
    main()
