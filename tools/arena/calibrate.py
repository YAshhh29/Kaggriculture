"""Turn local tournament results into a predicted live ladder rating.

Every earlier estimate of "how strong is this agent" in this project came from
a panel whose numbers did not match the ladder: tape opponents cannot react,
and the live panel was early-September code. This measures instead against
our own submissions whose live ratings we KNOW -- anchors, loaded as the exact
files Kaggle rated (arena.LIVE_ANCHORS) -- and asks one question with an
honest answer: does a local tournament predict those known ratings?

1. Bradley-Terry strength for every agent, from local games only (a win
   counts 1, a draw 0.5), with a weak prior so an unbeaten agent stays finite.
2. A straight-line map from strength to live rating, fitted on the anchors.
3. Leave-one-out on the anchors: refit the map without each anchor in turn
   and predict it. The mean absolute error of THAT is how far any other
   prediction here can be trusted. If it is large, the tool says so.
4. A bootstrap over games gives each prediction a sampling interval.

    python -m tools.arena.calibrate
    python -m tools.arena.calibrate --agents live_J live_K nb_tschinkel_2945 ...
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.arena.arena import GAMES, LIVE_ANCHORS  # noqa: E402


def load_games(agents: set[str] | None) -> list[tuple[str, str, float]]:
    """(a, b, score of a) for every clean local game among `agents`."""
    out = []
    for path in GAMES.glob("*.json"):
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if r.get("ladder_episode") or r.get("error"):
            continue
        if any(s != "DONE" for s in r.get("statuses") or ["?"]):
            continue
        a, b = r["agents"]
        if agents and not {a, b} <= agents:
            continue
        ra, rb = r["rewards"]
        out.append((a, b, 1.0 if ra > rb else 0.0 if ra < rb else 0.5))
    return out


def bradley_terry(games: list[tuple[str, str, float]], prior: float = 0.05,
                  iters: int = 3000, lr: float = 0.5) -> dict[str, float]:
    """Strengths in natural-log odds units, mean zero."""
    names = sorted({n for g in games for n in g[:2]})
    theta = {n: 0.0 for n in names}
    for _ in range(iters):
        grad = {n: -prior * theta[n] for n in names}
        for a, b, s in games:
            p = 1.0 / (1.0 + math.exp(theta[b] - theta[a]))
            grad[a] += s - p
            grad[b] -= s - p
        count = {n: 0 for n in names}
        for a, b, _ in games:
            count[a] += 1
            count[b] += 1
        step = 0.0
        for n in names:
            delta = lr * grad[n] / max(1, count[n])
            theta[n] += delta
            step = max(step, abs(delta))
        if step < 1e-7:
            break
    mean = statistics.mean(theta.values())
    return {n: t - mean for n, t in theta.items()}


def fit_line(points: list[tuple[float, float]]) -> tuple[float, float]:
    """Least squares rating = a + b * theta."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 1e-12:
        return my, 0.0
    b = sum((x - mx) * (y - my) for x, y in points) / sxx
    return my - b * mx, b


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agents", nargs="*", default=None)
    ap.add_argument("--bootstrap", type=int, default=200)
    args = ap.parse_args()

    agents = set(args.agents) if args.agents else None
    games = load_games(agents)
    if not games:
        raise SystemExit("no clean local games found for those agents")
    theta = bradley_terry(games)
    record: dict[str, list[float]] = {n: [0.0, 0.0] for n in theta}
    for a_, b_, s_ in games:
        record[a_][0] += s_
        record[a_][1] += 1
        record[b_][0] += 1 - s_
        record[b_][1] += 1
    anchors = {}
    for n in theta:
        if n not in LIVE_ANCHORS:
            continue
        won, played = record[n]
        # An anchor that never wins (or never loses) has no finite strength:
        # the fit only knows it is below (above) everything, so it would drag
        # the line. J lost all 104 of its tournament games and alone moved the
        # leave-one-out error from ~74 to 123.
        if won == 0 or won == played:
            print(f"  anchor {n} excluded from the fit: {won:.0f}/{played:.0f} "
                  f"is unbeaten or winless, so its strength is unbounded")
            continue
        anchors[n] = LIVE_ANCHORS[n][2]
    print(f"\n{len(games)} clean local games, {len(theta)} agents, "
          f"{len(anchors)} live anchors")
    if len(anchors) < 3:
        raise SystemExit("need at least 3 anchors in the tournament to fit "
                         "a scale and still leave one out")

    a, b = fit_line([(theta[n], r) for n, r in anchors.items()])
    print(f"  map: rating = {a:.0f} + {b:.0f} x strength  "
          f"(one unit of strength = {b:.0f} rating points)")

    # Leave-one-out: is this worth anything?
    print("\n  leave-one-out on the anchors (predicted WITHOUT that anchor):")
    errors = []
    for held in anchors:
        rest = [(theta[n], r) for n, r in anchors.items() if n != held]
        la, lb = fit_line(rest)
        pred = la + lb * theta[held]
        errors.append(abs(pred - anchors[held]))
        print(f"    {held:10s} live {anchors[held]:7.1f}   predicted "
              f"{pred:7.1f}   error {pred - anchors[held]:+7.1f}")
    mae = statistics.mean(errors)
    print(f"  mean absolute error {mae:.0f} rating points")
    if mae > 250:
        print("  WARNING: local results do not predict known live ratings "
              "well; treat every prediction below as a rough ordering only")

    # Bootstrap for sampling spread.
    rng = random.Random(7)
    samples: dict[str, list[float]] = {n: [] for n in theta}
    for _ in range(args.bootstrap):
        pick = [games[rng.randrange(len(games))] for _ in games]
        t = bradley_terry(pick, iters=800)
        if any(n not in t for n in anchors):
            continue
        ba, bb = fit_line([(t[n], r) for n, r in anchors.items()])
        for n in theta:
            if n in t:
                samples[n].append(ba + bb * t[n])

    wins = {n: [0.0, 0] for n in theta}
    for x, y, s in games:
        wins[x][0] += s
        wins[x][1] += 1
        wins[y][0] += 1 - s
        wins[y][1] += 1
    print("\n  predicted live rating (5th-95th percentile over bootstrap):")
    for n in sorted(theta, key=lambda k: -theta[k]):
        pred = a + b * theta[n]
        s = sorted(samples[n])
        lo = s[int(0.05 * len(s))] if s else float("nan")
        hi = s[int(0.95 * len(s)) - 1] if s else float("nan")
        live = f"live {anchors[n]:7.1f}" if n in anchors else " " * 12
        w, g = wins[n]
        print(f"    {n:28s} {pred:7.0f}  [{lo:5.0f}, {hi:5.0f}]  {live}  "
              f"won {w:5.1f}/{g}")


if __name__ == "__main__":
    main()
