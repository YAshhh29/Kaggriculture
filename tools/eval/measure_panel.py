"""Measure a candidate against a panel of *current* opponents.

Two panels, both built from live Kaggle play by
`tools.data.fetch_live_opponents`, and the difference between them is the
point of this module:

* **ladder** -- the 1917-2108 submissions our own agent actually meets.
  This is the honest answer to "will the next game be a win", because it
  is the field we are drawn against.
* **elite**  -- the 2765-2882 submissions at the top of the leaderboard.
  This is the honest answer to "is this agent worth 2500", because a
  rating is earned by beating the people who hold one.

Reporting only the first was the flaw the panel work started from, and
reporting only the second would be the mirror of it. Both are printed.

Three things this deliberately does that the older harnesses did not:

* **paired seats.** Every tape is played from seat 0 and seat 1 at the
  same seed. The market is one shared inventory, so seat order changes who
  sells into a glut first, and averaging one seat flatters whichever side
  the tape was recorded on.
* **margin, not reward.** Reward is dominated by the opponent, not by us:
  the leaders score 67-80k against *themselves* and 113-177k against a
  weak draw. Mean reward therefore measures who you were drawn against.
  Margin measures play.
* **near losses.** The live ladder is decided in the last few thousand
  coins -- median winning margin 1,151, median losing margin 2,889 -- so
  the count of losses inside 2,500 coins is the size of the prize a
  market-side improvement is playing for.

    python -m tools.eval.measure_panel --panel elite \
        rl.candidate_d:agent rl.candidate_e:agent rl.candidate_f:agent
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
TAPES = ROOT / "kaggle_cache" / "live_clones"
INDEX = ROOT / "rl" / "data" / "live_opponents.jsonl"
ELITE_FLOOR = 2500.0


def _round_robin(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reorder so that taking a prefix takes one tape per team in turn."""
    by_team: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_team.setdefault(row["name"], []).append(row)
    ordered: list[dict[str, Any]] = []
    depth = 0
    while len(ordered) < len(rows):
        added = False
        for team in sorted(by_team):
            if depth < len(by_team[team]):
                ordered.append(by_team[team][depth])
                added = True
        if not added:
            break
        depth += 1
    return ordered


def panel(kind: str, limit: int = 0, skip: int = 0) -> list[dict[str, Any]]:
    """Tapes on disk, filtered by the rating of the team that recorded them.

    `limit` trims the panel by taking one tape per team in turn rather
    than by truncating the file. Truncating would hand back several games
    of the top one or two teams and call that a panel; round-robin keeps
    the breadth of opponents, which is the only thing a small panel can
    still be honest about.

    `skip` drops that many tapes from the front of the same ordering, so
    `--limit 8` selects a candidate and `--skip 8` then confirms it on
    opposition it was not selected against. Screening and confirming on
    one panel is how a route search talks itself into a route.
    """
    rows: list[dict[str, Any]] = []
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        path = TAPES / f"live_{row['episode_id']}.json"
        if not path.exists() or row["episode_id"] in seen:
            continue
        if kind == "elite" and row["rating"] < ELITE_FLOOR:
            continue
        if kind == "ladder" and row["rating"] >= ELITE_FLOOR:
            continue
        seen.add(row["episode_id"])
        row["path"] = str(path)
        rows.append(row)
    if skip or (limit and len(rows) > limit):
        rows = _round_robin(rows)[skip:]
        if limit:
            rows = rows[:limit]
    return rows


def team_tapes(team: str) -> list[Path]:
    """Every captured tape of one team, oldest episode first."""
    found: list[tuple[int, Path]] = []
    seen: set[int] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["name"] != team or row["episode_id"] in seen:
            continue
        path = TAPES / f"live_{row['episode_id']}.json"
        if path.exists():
            seen.add(row["episode_id"])
            found.append((int(row["episode_id"]), path))
    return [path for _, path in sorted(found)]


def resolve(spec: str):
    """Build the agent a spec names.

    * `module:attr`                      -- a coded agent
    * `clone:<tape>`                     -- one tape behind the A+B guards
    * `raw:<tape>`                       -- one tape, no guards at all
    * `portfolio:<team>:<chooser>[:raw]` -- every tape that team recorded,
      switched between at block boundaries by the named chooser
    * `tuned:<module>:<attr>:<K=V,...>`  -- a coded agent with module-level
      constants overridden, so a sweep needs no edit to the agent itself
    """
    from rl.candidate_a import build_candidate_a_agent
    from rl.candidate_b import build_candidate_b_agent
    from rl.replay_agent import load_clone_actions, load_replay_agent

    def guarded(inner):
        return build_candidate_b_agent(
            baseline=build_candidate_a_agent(baseline=inner)
        )

    if spec.startswith("clone:"):
        return guarded(load_replay_agent(Path(spec.split(":", 1)[1])))
    if spec.startswith("raw:"):
        return load_replay_agent(Path(spec.split(":", 1)[1]))
    if spec.startswith("portfolio:"):
        import rl.route_portfolio as portfolio

        parts = spec.split(":")
        team, chooser_name = parts[1], parts[2]
        bare = len(parts) > 3 and parts[3] == "raw"
        routes = [load_clone_actions(p) for p in team_tapes(team)]
        if not routes:
            raise SystemExit(f"no tapes captured for team {team!r}")
        chooser = getattr(portfolio, chooser_name.removeprefix("sticky_"))
        if chooser_name.startswith("sticky_"):
            chooser = portfolio.sticky(chooser)
        inner = portfolio.build_portfolio_agent(routes, chooser=chooser)
        return inner if bare else guarded(inner)
    if spec.startswith("tuned:"):
        _, name, attribute, overrides = spec.split(":", 3)
        module = importlib.import_module(name)
        for pair in overrides.split(","):
            key, _, raw = pair.partition("=")
            current = getattr(module, key)
            # Several of the knobs worth sweeping default to None
            # (`MIXED_CAP`, `HERD_FORCE`), so the existing value cannot
            # always supply the type. Fall back to parsing the literal.
            if raw in ("None", "none"):
                value: Any = None
            elif isinstance(current, bool):
                value = raw not in ("0", "False", "false")
            elif isinstance(current, int):
                value = int(raw)
            elif isinstance(current, float):
                value = float(raw)
            else:
                try:
                    value = int(raw)
                except ValueError:
                    try:
                        value = float(raw)
                    except ValueError:
                        value = raw
            setattr(module, key, value)
        return getattr(module, attribute)
    module_name, attribute = spec.rsplit(":", 1)
    return getattr(importlib.import_module(module_name), attribute)


def one(job) -> tuple[float, float, str]:
    spec, opponent, seed, seat = job
    from kaggle_environments import make
    from rl.replay_agent import load_replay_agent

    mine = resolve(spec)
    theirs = load_replay_agent(Path(opponent))
    players = [mine, theirs] if seat == 0 else [theirs, mine]
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run(players)
    final = env.toJSON()["steps"][-1]
    return (
        float(final[seat].get("reward") or 0.0),
        float(final[1 - seat].get("reward") or 0.0),
        str(final[seat].get("status")),
    )


def measure(
    spec: str,
    label: str,
    rows: list[dict[str, Any]],
    seeds: tuple[int, ...],
    workers: int,
) -> dict[str, Any]:
    jobs = [
        (spec, row["path"], seed, seat)
        for row in rows
        for seed in seeds
        for seat in (0, 1)
    ]
    with Pool(workers) as pool:
        out = pool.map(one, jobs)
    mine = [a for a, _, _ in out]
    margins = [a - b for a, b, _ in out]
    wins = sum(1 for m in margins if m > 0)
    near = sum(1 for m in margins if -2500.0 < m <= 0.0)
    errors = sum(1 for _, _, status in out if status != "DONE")
    print(
        f"  {label:34s} coins {statistics.mean(mine):9,.0f}  "
        f"W {wins:3d}/{len(out)} ({wins / len(out):5.1%})  "
        f"margin med {statistics.median(margins):+9,.0f}  "
        f"mean {statistics.mean(margins):+9,.0f}  "
        f"near-loss {near:3d}" + (f"  ERR {errors}" if errors else ""),
        flush=True,
    )
    return {
        "label": label,
        "spec": spec,
        "games": len(out),
        "coins": statistics.mean(mine),
        "wins": wins,
        "win_rate": wins / len(out),
        "margin_median": statistics.median(margins),
        "margin_mean": statistics.mean(margins),
        "near_losses": near,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specs", nargs="*")
    parser.add_argument("--panel", default="both",
                        choices=("ladder", "elite", "both"))
    parser.add_argument("--seeds", default="11,29")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--label", action="append", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--limit", type=int, default=0,
                        help="cap panel size, one tape per team in turn")
    parser.add_argument("--skip", type=int, default=0,
                        help="drop this many tapes from the front, to "
                             "confirm on opposition not selected against")
    parser.add_argument(
        "--screen", default=None, choices=("elite", "ladder"),
        help="also screen every tape of this band as a clone candidate",
    )
    args = parser.parse_args()

    seeds = tuple(int(s) for s in args.seeds.split(","))
    specs = list(args.specs)
    labels = list(args.label or [])
    if len(labels) < len(specs):
        labels += [s.split(":")[-1] if ":" in s else s
                   for s in specs[len(labels):]]
    if args.screen:
        for row in panel(args.screen):
            specs.append("clone:" + row["path"])
            labels.append(f"{row['rating']:.0f} {row['name'][:14]} "
                          f"ep{row['episode_id']}")
    kinds = ("ladder", "elite") if args.panel == "both" else (args.panel,)
    results = []
    for kind in kinds:
        rows = panel(kind, args.limit, args.skip)
        if not rows:
            print(f"{kind}: no tapes on disk", flush=True)
            continue
        teams = len({row["name"] for row in rows})
        low = min(row["rating"] for row in rows)
        high = max(row["rating"] for row in rows)
        print(
            f"\n=== {kind} panel: {len(rows)} tapes, {teams} teams, "
            f"rated {low:.0f}-{high:.0f}, "
            f"{len(rows) * len(seeds) * 2} games each ===",
            flush=True,
        )
        for spec, label in zip(args.specs, labels):
            row = measure(spec, label, rows, seeds, args.workers)
            row["panel"] = kind
            results.append(row)
    if args.out:
        Path(args.out).write_text(
            "\n".join(json.dumps(r) for r in results), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
