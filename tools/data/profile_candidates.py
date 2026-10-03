"""Profile our own agents with the same lens used on the leaders.

`tools/data/profile_tapes.py` reduces a captured opponent to a strategy
fingerprint -- crew, land, seed and animal mix, task counts, idleness. This
records our own candidates playing real games and reduces them the same
way, so the two can be laid side by side.

That comparison is the point. Reading the live corpus this way showed the
1917-2108 field is largely one public baseline run unmodified -- fourteen
of twenty-four teams post an identical fingerprint of 198 wheat seeds, 5
carrot, no geese -- while all nine teams above 2765 buy 31-55 carrot and
2-3 geese. Knowing which side of that line our own agents fall on says
more about what to change than any amount of win-rate tuning against the
field they already beat.

    python -m tools.data.profile_candidates candidates.candidate_e:agent
"""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from tools.data.profile_tapes import (  # noqa: E402
    INDEX,
    TAPES,
    load_tape,
    profile,
    report,
)


def record(job) -> dict[str, Any]:
    """Play one game and keep the actions our side actually issued."""
    spec, opponent, seed, seat = job
    from kaggle_environments import make

    from rl.replay_agent import load_replay_agent
    from tools.eval.measure_panel import resolve

    inner = resolve(spec)
    captured: list[dict[str, Any]] = []

    def watched(observation, *rest):
        action = inner(observation)
        captured.append(json.loads(json.dumps(action)))
        return action

    theirs = load_replay_agent(Path(opponent))
    players = [watched, theirs] if seat == 0 else [theirs, watched]
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run(players)
    final = env.toJSON()["steps"][-1]
    out = profile(captured)
    out["reward"] = float(final[seat].get("reward") or 0.0)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specs", nargs="+")
    parser.add_argument("--games", type=int, default=6)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    rows = [json.loads(line)
            for line in INDEX.read_text(encoding="utf-8").splitlines()]
    tapes: list[str] = []
    seen: set[str] = set()
    for row in rows:
        path = TAPES / ("live_" + str(row["episode_id"]) + ".json")
        if path.exists() and row["name"] not in seen:
            seen.add(row["name"])
            tapes.append(str(path))
    tapes = tapes[: max(1, args.games // 2)]

    for spec in args.specs:
        jobs = [
            (spec, tape, 11, seat) for tape in tapes for seat in (0, 1)
        ][: args.games]
        with Pool(min(args.workers, len(jobs))) as pool:
            profiles = pool.map(record, jobs)
        report(spec, profiles, [p["reward"] for p in profiles])


if __name__ == "__main__":
    main()
