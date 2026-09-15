"""Replay our live ladder games against any version of an agent.

Each record in ``rl/data/our_live_tapes`` (``tools.data.extract_live_tapes``)
holds a live episode's seed, our seat and the opponent's recorded actions.
Playing an agent in our seat against that tape, on that seed, with the stock
engine, reproduces the live game exactly for the agent that played it --
checked to the coin on episode 109250573 -- so a new version can be judged on
the very games the old one won and lost, against the real part of the
ladder it was drawn against.

The opponent's tape cannot react. Once our play changes the books it sells
into, it can drift from what it would really have done, so every game
records how far the opponent's day-by-day money strays from the live record,
and comparisons report the games that stayed close separately.

    python -m tools.eval.live_replay run --agent h-package --label "H live"
    python -m tools.eval.live_replay run --agent h --set hire_reserve=15 \\
        --label "H hire reserve 15"
    python -m tools.eval.live_replay run --agent g --label "G"
    python -m tools.eval.live_replay compare "H live" "H hire reserve 15"
    python -m tools.eval.live_replay summary "G"
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TAPES = ROOT / "rl" / "data" / "our_live_tapes"
RUNS = ROOT / "rl" / "data" / "live_replays"
H_PACKAGE = ROOT / "submissions" / "candidate-h" / "main.py"
DAYS = (2, 5, 8, 11, 14, 17, 20, 23, 26, 29)
# An opponent whose day-by-day money strays by more than this share of its
# live money, on average, is treated as a drifted tape.
DRIFT = 0.10


def _slug(label: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in label.lower()).strip("-")


def _parse(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def build_agent(kind: str, settings: dict[str, Any]):
    """The agent to play in our seat, built inside the worker process."""
    sys.path.insert(0, str(ROOT))
    if kind == "g":
        import rl.candidate_g as G
        for key, value in settings.items():
            setattr(G, key, value)
        return G.agent
    import importlib.util
    spec = importlib.util.spec_from_file_location("h_package", H_PACKAGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if kind == "h-package":
        return module.agent
    # Re-wrap the submitted base with the current demand layer, so new layer
    # settings can be tried on exactly the base that played the ladder.
    wrapped = module.agent
    base = next(cell.cell_contents for cell in (wrapped.__closure__ or ())
                if callable(cell.cell_contents)
                and cell.cell_contents is not wrapped)
    from rl.candidate_h_demand import wrap
    merged = dict(getattr(wrapped, "demand_settings", {}) or {})
    merged.update(settings)
    return wrap(base, merged)


def play_one(job: tuple[str, dict[str, Any], str]) -> dict[str, Any]:
    kind, settings, path = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent
    from tools.data.extract_live_tapes import summarise, unpack

    record = json.loads(Path(path).read_text(encoding="utf-8"))
    side = int(record["our_side"])
    opponent = build_replay_agent(tuple(unpack(record["opp_actions_zlib_b64"])))
    try:
        agent = build_agent(kind, settings)
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720,
                                  "seed": record["seed"],
                                  "runTimeout": 36000, "actTimeout": 60},
                   debug=False)
        env.run([agent, opponent] if side == 0 else [opponent, agent])
    except Exception as error:  # one broken game must not sink the run
        return {"episode_id": record["episode_id"],
                "error": f"{type(error).__name__}: {error}"}
    days = summarise(env.steps, side)
    live_them = {row["day"]: row.get("them", {}).get("money")
                 for row in record["days"]}
    drift = []
    for row in days:
        live = live_them.get(row["day"])
        if row["day"] >= 1 and live is not None and "them" in row:
            drift.append(abs(row["them"]["money"] - live) / max(abs(live), 500.0))
    us = env.state[side].reward or 0.0
    them = env.state[1 - side].reward or 0.0
    live_days = {row["day"]: row for row in record["days"]}
    collapse = (live_days.get(5, {}).get("them", {}).get("herd", 0)
                - live_days.get(5, {}).get("us", {}).get("herd", 0)) >= 3
    return {
        "episode_id": record["episode_id"],
        "opponent": record.get("opponent"),
        "opponent_rating": record.get("opponent_rating"),
        "live": record["rewards"],
        "live_won": record.get("won"),
        "live_collapse": collapse,
        "reward": {"us": us, "them": them},
        "won": us > them,
        "status": {"us": env.state[side].status,
                   "them": env.state[1 - side].status},
        "opponent_drift": statistics.mean(drift) if drift else 0.0,
        "days": days,
    }


def run(args) -> None:
    settings = {}
    for item in args.set:
        key, _, raw = item.partition("=")
        settings[key] = _parse(raw)
    paths = sorted(str(p) for p in TAPES.glob("ep*.json"))
    if args.limit:
        paths = paths[: args.limit]
    started = time.time()
    with Pool(args.workers) as pool:
        games = pool.map(play_one, [(args.agent, settings, p) for p in paths])
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        sha = ""
    out = {"meta": {"label": args.label, "agent": args.agent,
                    "settings": settings, "git": sha,
                    "when": time.strftime("%Y-%m-%d %H:%M"),
                    "seconds": round(time.time() - started)},
           "games": games}
    RUNS.mkdir(parents=True, exist_ok=True)
    path = RUNS / f"{_slug(args.label)}.json"
    path.write_text(json.dumps(out), encoding="utf-8")
    print(f"saved {path.relative_to(ROOT)}")
    summary(out)


def _load(label: str) -> dict[str, Any]:
    return json.loads((RUNS / f"{_slug(label)}.json").read_text(encoding="utf-8"))


def _band(rating: float | None) -> str:
    r = float(rating or 0)
    return ("<2400" if r < 2400 else "2400-2600" if r < 2600
            else "2600-2800" if r < 2800 else "2800+")


def summary(run_or_label) -> None:
    data = _load(run_or_label) if isinstance(run_or_label, str) else run_or_label
    games = [g for g in data["games"] if "error" not in g]
    errors = len(data["games"]) - len(games)
    meta = data["meta"]
    wins = sum(g["won"] for g in games)
    exact = sum(1 for g in games if g["reward"] == g["live"])
    print(f"\n{meta['label']} ({meta['agent']}, settings {meta['settings']}, "
          f"commit {meta['git']}): {len(games)} games, {errors} errors")
    print(f"  wins {wins} ({wins / max(1, len(games)):.0%}), median margin "
          f"{statistics.median([g['reward']['us'] - g['reward']['them'] for g in games]):+,.0f}; "
          f"live record {sum(bool(g['live_won']) for g in games)} wins; "
          f"identical to live {exact}; opponent drifted in "
          f"{sum(g['opponent_drift'] > DRIFT for g in games)}")
    bands: dict[str, list] = {}
    for g in games:
        bands.setdefault(_band(g["opponent_rating"]), []).append(g)
    for band in ("<2400", "2400-2600", "2600-2800", "2800+"):
        rows = bands.get(band)
        if rows:
            print(f"  opponents {band:9s}: {len(rows):3d} games, won "
                  f"{sum(g['won'] for g in rows):3d}, median margin "
                  f"{statistics.median([g['reward']['us'] - g['reward']['them'] for g in rows]):+,.0f}")
    print("  day | money us/them | herd | planted | tiles | hands (medians)")
    for day in DAYS:
        cells = []
        for field in ("money", "herd", "planted", "tiles", "hands"):
            us = [r.get("us", {}).get(field) for g in games for r in g["days"]
                  if r["day"] == day and r.get("us", {}).get(field) is not None]
            them = [r.get("them", {}).get(field) for g in games for r in g["days"]
                    if r["day"] == day and r.get("them", {}).get(field) is not None]
            if us and them:
                cells.append(f"{statistics.median(us):,.0f}/{statistics.median(them):,.0f}")
        print(f"  {day:3d} | " + " | ".join(cells))


def compare(args) -> None:
    a, b = _load(args.before), _load(args.after)
    ga = {g["episode_id"]: g for g in a["games"] if "error" not in g}
    gb = {g["episode_id"]: g for g in b["games"] if "error" not in g}
    shared = sorted(set(ga) & set(gb))
    print(f"{args.after} against {args.before}, {len(shared)} shared games")
    groups = {
        "all": shared,
        "opponent stayed close in both": [e for e in shared
            if ga[e]["opponent_drift"] <= DRIFT and gb[e]["opponent_drift"] <= DRIFT],
        "live early collapse": [e for e in shared if ga[e]["live_collapse"]],
        "no live collapse": [e for e in shared if not ga[e]["live_collapse"]],
    }
    # Our own score is reported beside the margin because a tape opponent that
    # drifts loses coins it would have earned live: on episode 109250573 a
    # hire reserve raised H by 581 while the tape opponent fell from 118,849 to
    # 71,818. The own-score change is the part a live opponent cannot inflate.
    for name, eps in groups.items():
        if not eps:
            continue
        deltas = [(gb[e]["reward"]["us"] - gb[e]["reward"]["them"])
                  - (ga[e]["reward"]["us"] - ga[e]["reward"]["them"]) for e in eps]
        own = [gb[e]["reward"]["us"] - ga[e]["reward"]["us"] for e in eps]
        print(f"  {name:32s} {len(eps):3d} games | wins {sum(ga[e]['won'] for e in eps)} -> "
              f"{sum(gb[e]['won'] for e in eps)} | margin change {statistics.mean(deltas):+,.0f} "
              f"(median {statistics.median(deltas):+,.0f}), better in "
              f"{sum(d > 0 for d in deltas)}, worse in {sum(d < 0 for d in deltas)}, "
              f"identical in {sum(d == 0 for d in deltas)}")
        print(f"  {'':32s}     own score change {statistics.mean(own):+,.0f} "
              f"(median {statistics.median(own):+,.0f}), higher in "
              f"{sum(d > 0 for d in own)}, lower in {sum(d < 0 for d in own)}")
    flipped = [(e, ga[e]["won"], gb[e]["won"]) for e in shared if ga[e]["won"] != gb[e]["won"]]
    print(f"  results that flipped: {sum(1 for _, x, y in flipped if y)} to wins, "
          f"{sum(1 for _, x, y in flipped if x)} to losses")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--agent", choices=("h-package", "h", "g"), required=True)
    p_run.add_argument("--set", action="append", default=[])
    p_run.add_argument("--label", required=True)
    p_run.add_argument("--workers", type=int, default=6)
    p_run.add_argument("--limit", type=int, default=0)
    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("before")
    p_cmp.add_argument("after")
    p_sum = sub.add_parser("summary")
    p_sum.add_argument("label")
    args = parser.parse_args()
    if args.command == "run":
        run(args)
    elif args.command == "compare":
        compare(args)
    else:
        summary(args.label)


if __name__ == "__main__":
    main()
