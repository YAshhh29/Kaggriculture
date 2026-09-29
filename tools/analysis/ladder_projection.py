"""Project each agent's ladder rating and leaderboard rank from our REAL ladder games
replayed with that agent in our seat (tools.analysis.l2_land_pin live-ladder labels).

Our 221 real ladder games are two sets: 140 games of submission N3 (set n3x, rated
2315.1) and 81 of submission N2 (set n2x, rated 2290.0; 2026-09-29 16:00 UTC). Each
set was replayed with other agents against the opponents' tapes (labels
n3x-<agent>-c*, n2x-<agent>-c*).

Method
  1. Load each agent's labels (AGENTS below; --agents NAME=glob,... overrides). Rows
     with "skip" are not games; an episode in several files counts once (first file in
     sorted order). The set is taken from the file name (n3x-/n2x-), else from the
     row's submission in rl/data/our_games.jsonl. The opponent's rating is the row's
     opponent_rating (its rating when the game was played), else our_games.jsonl's.
  2. Logistic scale from the live truth. The real result of a game is
     live.us > live.them (what N3 or N2 really did). Over every episode of each set
     (the union of all n3x-*/n2x-* files present) the MLE rating of the real results,
     with P(win) = 1 / (1 + 10^(-(R - r_opp) / s)), should equal the real rating. One s
     cannot do this for both sets (on the 09-29 labels no s in the range reaches n3x's
     2315.1: its MLE bottoms out near 2324), so s only sets the scale of the shifts; the
     level is anchored per set in step 3. One s
     is fitted over both sets by least squares on the two rating errors (log-grid then
     golden section over s in [20, 20000]). If the minimum sits on the search boundary
     or an MLE is infinite (all games won or lost), s falls back to 400 and the output
     says so.
  3. Per agent and set, on the games the agent played: R_agent = MLE of the agent's
     results (us > them), R_real = MLE of the real results on the SAME games, shift =
     R_agent - R_real (the most robust number: same games, same opponents, same s),
     projected = the set's real rating + shift. Over both sets: projected is the
     games-weighted mean of the per-set projections, R the MLE on the pooled games.
     90% intervals: 500 bootstrap resamples of games, drawn within each set and paired
     (the agent and the real results share the resample); s is held fixed.
  4. Rank: leaderboard (kaggle_cache/corpus_0930/leaderboard.json, our team excluded)
     rank = 1 + number of teams with a higher score; below the last listed score the
     rank is ">700". The rank band is the ranks of the projected interval's ends.
  5. Caveats are printed with the table.
  6. Markdown to stdout; --json-out writes everything as JSON.

usage:
    python -m tools.analysis.ladder_projection --agents N7,N8
    python -m tools.analysis.ladder_projection --agents "N7,N9=n?x-n9-c*" --json-out out.json
    python -m tools.analysis.ladder_projection          # every AGENTS entry with files present
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
REPLAYS = ROOT / "rl" / "data" / "l2" / "land" / "replays"
OUR_GAMES = ROOT / "rl" / "data" / "our_games.jsonl"
LEADERBOARD = ROOT / "kaggle_cache" / "corpus_0930" / "leaderboard.json"
OUR_TEAM = 16724366

# set -> (submitted agent, submission id, real rating, games behind that rating)
REAL = {"n3x": ("N3", 56650417, 2315.1, 140), "n2x": ("N2", 56634151, 2290.0, 175)}
SETS = tuple(REAL)

AGENTS = {
    "N7": ["n3x-n7.json", "n2x-n7.json"],
    "N8": ["n3x-n8a25-c*.json", "n2x-n8a25-c*.json"],
    "N6": ["n3x-n6-c*.json", "n2x-n6-c*.json"],
    "N3": ["n3x-n3-c*.json", "n2x-n3-c*.json"],
    "N5": ["n3x-n5-c*.json", "n2x-n5-c*.json"],
    "M2": ["n3x-m2-c*.json", "n2x-m2-c*.json"],
    "P2965": ["n3x-p2965-c*.json", "n2x-p2965-c*.json"],
}
FALLBACK_S = 400.0
S_RANGE = (20.0, 20000.0)
CAVEATS = [
    "Pinned replays cannot make the opponent react: it replays its recorded moves, "
    "whatever our agent does (only the town and the weeds are kept as they were live).",
    "Opponent ratings are those at game time; they have moved since, and some opponents "
    "were fresh submissions far from their settled rating (lowest {lo:.0f}).",
    "s is fitted to two points (N3 and N2 ratings; N2's {r2:.1f} rests on {n2} games, of "
    "which {g2} are set n2x); the intervals hold s and the real ratings fixed.",
    "The leaderboard is a snapshot ({lb}); the final ranking is a Bradley-Terry fit over "
    "~2 weeks of post-deadline games between each team's latest two submissions, "
    "against a field that keeps improving.",
    "With 81-140 games per set the absolute R is noisy; the paired shift is the robust number.",
]


# ---------------------------------------------------------------- data
def our_games() -> dict:
    out = {}
    if OUR_GAMES.exists():
        for line in OUR_GAMES.read_text(encoding="utf-8").splitlines():
            if line.strip():
                g = json.loads(line)
                out[g["episode_id"]] = {"submission": g.get("submission"),
                                        "opponent_rating": g.get("opponent_rating")}
    return out


def set_of(path: Path, row: dict, og: dict) -> str | None:
    for s in SETS:
        if path.name.startswith(s + "-"):
            return s
    sub = og.get(row["episode_id"], {}).get("submission")
    return next((s for s, v in REAL.items() if v[1] == sub), None)


def load(globs: list, og: dict) -> tuple:
    """{episode: game} for the files matching globs, plus coverage notes."""
    files = sorted({p for g in globs for p in REPLAYS.glob(g if g.endswith(".json") else g + ".json")})
    games, notes = {}, {"files": [p.name for p in files], "no_rating": 0, "no_set": 0, "dup": 0, "unreadable": []}
    for p in files:
        try:
            rows = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):  # l2_land_pin rewrites in-progress files in place (not atomic)
            notes["unreadable"].append(p.name)
            continue
        for r in rows:
            if "skip" in r or "us" not in r or "live" not in r:
                continue
            e = r["episode_id"]
            if e in games:
                notes["dup"] += 1
                continue
            opp = r.get("opponent_rating")
            if opp is None:
                opp = og.get(e, {}).get("opponent_rating")
            s = set_of(p, r, og)
            if opp is None:
                notes["no_rating"] += 1
                continue
            if s is None:
                notes["no_set"] += 1
                continue
            games[e] = {"set": s, "opp": float(opp), "won": float(r["us"] > r["them"]),
                        "real": float(r["live"]["us"] > r["live"]["them"]),
                        "errors": int(r.get("errors") or 0), "opponent": r.get("opponent")}
    return games, notes


def leaderboard() -> tuple:
    lb = json.loads(LEADERBOARD.read_text(encoding="utf-8"))
    scores = sorted((float(r["score"]) for r in lb["rows"] if r.get("team_id") != OUR_TEAM), reverse=True)
    when = datetime.fromtimestamp(lb.get("fetched_at_unix", 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return scores, len(lb["rows"]), when


def rank_of(x: float, scores: list, listed: int) -> str:
    if not math.isfinite(x):
        return "?"
    if x < scores[-1]:
        return f">{listed}"
    return str(1 + sum(sc > x for sc in scores))


# ---------------------------------------------------------------- rating
def mle(opp: np.ndarray, win: np.ndarray, s: float) -> np.ndarray:
    """MLE rating per row of (B, n) arrays: solves sum P(win) = wins by bisection.
    nan where every game was won or lost (the MLE is infinite)."""
    opp, win = np.atleast_2d(opp), np.atleast_2d(win)
    w, n = win.sum(1), win.shape[1]
    lo = opp.min(1) - (math.log10(n + 1) + 2) * s
    hi = opp.max(1) + (math.log10(n + 1) + 2) * s
    for _ in range(64):
        mid = (lo + hi) / 2
        p = 1.0 / (1.0 + np.power(10.0, -(mid[:, None] - opp) / s))
        up = p.sum(1) < w
        lo, hi = np.where(up, mid, lo), np.where(up, hi, mid)
    r = (lo + hi) / 2
    return np.where((w > 0) & (w < n), r, np.nan)


def calibrate(cal: dict, fixed: float | None) -> dict:
    """s such that the MLE of the real results on each set equals its real rating."""
    def fit(s):
        return {k: float(mle(np.array(v["opp"]), np.array(v["real"]), s)[0]) for k, v in cal.items()}

    def err(s):
        rs = fit(s)
        return sum((rs[k] - REAL[k][2]) ** 2 for k in rs) if all(map(math.isfinite, rs.values())) else math.inf

    note = ""
    if fixed is not None:
        s, ok, note = fixed, True, "given with --scale"
    else:
        grid = np.exp(np.linspace(math.log(S_RANGE[0]), math.log(S_RANGE[1]), 61))
        errs = [err(g) for g in grid]
        i = int(np.argmin(errs))
        ok = 0 < i < len(grid) - 1 and math.isfinite(errs[i])
        if ok:
            a, b = math.log(grid[i - 1]), math.log(grid[i + 1])
            g = (math.sqrt(5) - 1) / 2
            for _ in range(60):
                c, d = b - g * (b - a), a + g * (b - a)
                if err(math.exp(c)) < err(math.exp(d)):
                    b = d
                else:
                    a = c
            s = math.exp((a + b) / 2)
        else:
            s, note = FALLBACK_S, (f"did not converge (least-squares minimum at s={grid[i]:.0f}, "
                                   f"the edge of [{S_RANGE[0]:.0f}, {S_RANGE[1]:.0f}]); fell back to s=400")
    rs = fit(s)
    return {"s": s, "converged": ok, "note": note or "converged",
            "sets": {k: {"games": len(v["opp"]), "real_won": int(sum(v["real"])), "mle": rs[k],
                         "real_rating": REAL[k][2], "error": rs[k] - REAL[k][2]} for k, v in cal.items()}}


def pct(a: np.ndarray) -> list:
    a = a[np.isfinite(a)]
    return [float(np.percentile(a, 5)), float(np.percentile(a, 95))] if len(a) else [math.nan, math.nan]


def project(games: dict, s: float, boot: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    per, draws = {}, {}
    for k in SETS:
        gs = [g for g in games.values() if g["set"] == k]
        if not gs:
            continue
        opp = np.array([g["opp"] for g in gs])
        wa, wr = np.array([g["won"] for g in gs]), np.array([g["real"] for g in gs])
        ra, rr = float(mle(opp, wa, s)[0]), float(mle(opp, wr, s)[0])
        idx = rng.integers(0, len(gs), size=(boot, len(gs)))
        ba, br = mle(opp[idx], wa[idx], s), mle(opp[idx], wr[idx], s)
        draws[k] = {"opp": opp[idx], "wa": wa[idx], "proj": REAL[k][2] + ba - br, "n": len(gs)}
        per[k] = {"games": len(gs), "won": int(wa.sum()), "real_won": int(wr.sum()),
                  "gained": int(((wa == 1) & (wr == 0)).sum()), "lost": int(((wa == 0) & (wr == 1)).sum()),
                  "R": ra, "R_ci": pct(ba), "R_real": rr, "shift": ra - rr, "shift_ci": pct(ba - br),
                  "projected": REAL[k][2] + ra - rr, "projected_ci": pct(REAL[k][2] + ba - br)}
    if not per:
        return {"sets": {}}
    n = sum(v["games"] for v in per.values())
    opp = np.array([g["opp"] for g in games.values()])
    wa, wr = np.array([g["won"] for g in games.values()]), np.array([g["real"] for g in games.values()])
    proj_b = sum(d["proj"] * d["n"] for d in draws.values()) / n
    real_b = sum(REAL[k][2] * d["n"] for k, d in draws.items()) / n
    ra_b = mle(np.concatenate([d["opp"] for d in draws.values()], 1),
               np.concatenate([d["wa"] for d in draws.values()], 1), s)
    proj = sum(v["projected"] * v["games"] for v in per.values()) / n
    real = sum(REAL[k][2] * v["games"] for k, v in per.items()) / n
    return {"sets": per, "games": n, "won": int(wa.sum()), "real_won": int(wr.sum()),
            "gained": sum(v["gained"] for v in per.values()), "lost": sum(v["lost"] for v in per.values()),
            "R": float(mle(opp, wa, s)[0]), "R_ci": pct(ra_b), "R_real": float(mle(opp, wr, s)[0]),
            "shift": proj - real, "shift_ci": pct(proj_b - real_b),
            "projected": proj, "projected_ci": pct(proj_b), "real_rating_weighted": real}


# ---------------------------------------------------------------- output
def f0(x) -> str:
    return "n/a" if x is None or not math.isfinite(x) else f"{x:.0f}"


def sg(x) -> str:
    return "n/a" if x is None or not math.isfinite(x) else f"{x:+.0f}"


def ci(v, fmt=f0) -> str:
    return f"[{fmt(v[0])}, {fmt(v[1])}]"


def parse_agents(spec: str | None) -> dict:
    if not spec:
        return dict(AGENTS)
    out: dict = {}
    for part in (p.strip() for p in spec.split(",") if p.strip()):
        name, _, glob = part.partition("=")
        if glob:
            out.setdefault(name, []).append(glob)
        elif name in AGENTS:
            out.setdefault(name, []).extend(AGENTS[name])
        else:
            sys.exit(f"unknown agent {name!r}: give NAME=glob (known: {', '.join(AGENTS)})")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--agents", default=None,
                    help="comma list of NAME (from AGENTS) or NAME=glob under the replays dir; "
                         "repeat a NAME to add globs (default: every AGENTS entry)")
    ap.add_argument("--boot", type=int, default=500, help="bootstrap resamples")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--scale", type=float, default=None, help="use this s instead of fitting it")
    ap.add_argument("--rating-n3x", type=float, default=REAL["n3x"][2])
    ap.add_argument("--rating-n2x", type=float, default=REAL["n2x"][2])
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()
    for k in SETS:
        v = REAL[k]
        REAL[k] = (v[0], v[1], getattr(args, f"rating_{k}"), v[3])

    og = our_games()
    everything, cal_notes = load([f"{k}-*.json" for k in SETS], og)
    cal = {k: {"opp": [g["opp"] for g in everything.values() if g["set"] == k],
               "real": [g["real"] for g in everything.values() if g["set"] == k]} for k in SETS}
    if not all(v["opp"] for v in cal.values()):
        sys.exit("no live-ladder replays for both sets under " + str(REPLAYS))
    c = calibrate(cal, args.scale)
    s = c["s"]
    scores, listed, when = leaderboard()

    results, coverage = {}, {}
    for name, globs in parse_agents(args.agents).items():
        games, notes = load(globs, og)
        coverage[name] = {**notes, **{k: sum(g["set"] == k for g in games.values()) for k in SETS},
                          "errors": sum(g["errors"] for g in games.values()),
                          "games_with_errors": sum(g["errors"] > 0 for g in games.values())}
        if games:
            results[name] = project(games, s, args.boot, args.seed)
            p = results[name]
            p["rank"] = rank_of(p["projected"], scores, listed)
            p["rank_band"] = [rank_of(p["projected_ci"][1], scores, listed), rank_of(p["projected_ci"][0], scores, listed)]

    print("## Ladder projection from our real ladder games (pinned replays)\n")
    cs = c["sets"]
    print(f"Logistic scale s = {s:.1f} ({c['note']}). MLE of the real results: "
          + "; ".join(f"{k} ({REAL[k][0]}) {f0(v['mle'])} vs real {REAL[k][2]:.1f} "
                      f"({v['real_won']}/{v['games']} won, error {sg(v['error'])})" for k, v in cs.items()))
    print(f"Leaderboard {LEADERBOARD.relative_to(ROOT).as_posix()} fetched {when}: {listed} teams, "
          f"{scores[0]:.1f} .. {scores[-1]:.1f}. Real today: "
          + ", ".join(f"{REAL[k][0]} {REAL[k][2]:.1f} = rank {rank_of(REAL[k][2], scores, listed)}" for k in SETS)
          + f". Bootstrap {args.boot} paired resamples, 90% intervals.\n")
    print("| agent | games n3x, n2x | won (real) | +won/-lost | R [90%] | shift vs real [90%] "
          "| projected [90%] | rank | rank band |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, cov in coverage.items():
        cov_s = ", ".join(f"{cov[k]}/{len(cal[k]['opp'])}" for k in SETS)
        p = results.get(name)
        if not p:
            print(f"| {name} | {cov_s} | no games ({len(cov['files'])} files) | | | | | | |")
            continue
        print(f"| {name} | {cov_s} | {p['won']} ({p['real_won']}) | +{p['gained']}/-{p['lost']} "
              f"| {f0(p['R'])} {ci(p['R_ci'])} | {sg(p['shift'])} {ci(p['shift_ci'], sg)} "
              f"| **{f0(p['projected'])}** {ci(p['projected_ci'])} | {p['rank']} "
              f"| {p['rank_band'][0]}-{p['rank_band'][1]} |")
    print("\nPer set (R_real = MLE of the real results on the same games):\n")
    print("| agent | set | games | won (real) | R [90%] | R_real | shift [90%] | projected [90%] |")
    print("|---|---|---|---|---|---|---|---|")
    for name, p in results.items():
        for k, v in p["sets"].items():
            print(f"| {name} | {k} | {v['games']} | {v['won']} ({v['real_won']}) | {f0(v['R'])} {ci(v['R_ci'])} "
                  f"| {f0(v['R_real'])} | {sg(v['shift'])} {ci(v['shift_ci'], sg)} "
                  f"| {f0(v['projected'])} {ci(v['projected_ci'])} |")
    notes = [f"{n}: {', '.join(f'{v} {k}' for k, v in cov.items() if k in ('dup', 'no_rating', 'no_set') and v)}"
             for n, cov in coverage.items() if any(cov[k] for k in ('dup', 'no_rating', 'no_set'))]
    errs = [f"{n} {cov['errors']} errors in {cov['games_with_errors']} games"
            for n, cov in coverage.items() if cov["errors"]]
    errs += [f"{n}: unreadable (being written?) {', '.join(v['unreadable'])}"
             for n, v in [("calibration", cal_notes), *coverage.items()] if v["unreadable"]]
    if notes or errs:
        print("\nData notes: " + "; ".join(notes + errs) + " (duplicates counted once).")
    fmt = {"lo": min(g["opp"] for g in everything.values()), "lb": when, "r2": REAL["n2x"][2],
           "n2": REAL["n2x"][3], "g2": len(cal["n2x"]["opp"])}
    print("\nCaveats:")
    for cv in CAVEATS:
        print("- " + cv.format(**fmt))

    if args.json_out:
        out = {"calibration": c, "leaderboard": {"path": str(LEADERBOARD), "fetched": when, "teams": listed,
                                                 "top": scores[0], "last": scores[-1]},
               "real": {k: {"agent": v[0], "submission": v[1], "rating": v[2],
                            "rank": rank_of(v[2], scores, listed)} for k, v in REAL.items()},
               "boot": args.boot, "seed": args.seed, "coverage": coverage, "agents": results,
               "caveats": [cv.format(**fmt) for cv in CAVEATS]}
        Path(args.json_out).write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
