"""Even-comparison scorecard: every agent and public program on the same corpus games.

Each agent's pinned corpus replays (tools/analysis/corpus_pin.py; labels in
CORPUS below) are merged and deduplicated by episode. Agents are compared only
on the games that every one of them has with the top team's tape intact
(drift <= --max-drift for every agent); with --min-coverage, agents with too
few clean games are dropped instead of shrinking the set. Per agent: record
with a Wilson 95% interval, margins (us - them), win% by the top team's rating
band, games with errors, and two scores:

- performance rating R on the ladder's own scale: the logistic scale s is
  fitted by maximum likelihood to the corpus's REAL games (top team vs its
  original opponent, P(top wins) = 1/(1+10^(-(r_top - r_orig)/s))), then R is
  the MLE rating whose expected wins against the top teams' ratings match the
  agent's wins (bootstrap 90% interval, games resampled);
- head-to-head: on each common game the agent with the larger margin beats the
  other (ties half; --tie-margin widens a tie), and a Bradley-Terry fit (MM)
  on those counts gives Elo-like ratings (400 scale, mean 0 or --anchor at 0).
  A small but steady money edge wins most games here, so this scale runs far
  wider than R: it ranks agents, it does not predict ladder results.

The row "real" is a reference: the original seat's real result in the same
games (corpus: the top team's real opponent; --preset live: our submitted
agent). It gets a record and an R but takes no part in the head-to-head.

    python -m tools.analysis.agent_scorecard N N6 N7 N8 --anchor N7
    python -m tools.analysis.agent_scorecard --min-coverage 0.9 'X=t710-x-c*,m98-x-c*' --json-out card.json
    python -m tools.analysis.agent_scorecard --preset live
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
REPLAYS = ROOT / "rl" / "data" / "l2" / "land" / "replays"

PUBLIC = ("2965", "hl0928", "hosen", "tsch2945", "a", "hl", "hak2887", "seyit2820",
          "jaxa2802", "dmitrii2800", "2965old", "avioon", "melon2749")

# agent -> replay label globs of its corpus_pin runs on the 901-game top-team corpus
CORPUS: dict[str, list[str]] = {
    "N": ["top-n2m-c*"],
    "N2": ["t710-n2-c*", "m98-n2-c*"],
    "N3": ["t710-n3-c*", "m98-n3-c*"],
    "N4": ["t710-n4-c*", "m98-n4-c*"],
    "N5": ["t710-n5-c*", "m98-n5-c*"],
    "N6": ["top-n6-c*"],
    "N7": ["t710-n7b-c*", "m98-n7-c*"],
    "N8": ["t710-n8a25-c*", "m98-n8-c*"],
    "L": ["t710-l-c*", "m499-l-c*"],
    "L2": ["t710-l2-c*", "m499-l2-c*"],
    "L3": ["t710-l3-c*", "m499-l3-c*"],
    "L4": ["t710-l4-c*", "m499-l4-c*"],
    "L4e": ["t710-l4e-c*", "m499-l4e-c*"],
    "L5": ["t710-l5-c*", "m499-l5-c*"],
    "M": ["t710-m-c*", "m499-m-c*"],
    "M2": ["t710-m2-c*", "m499-m2-c*"],
    **{f"p_{n}": [f"c901-p_{n}-c*"] for n in PUBLIC},
}

# agent -> l2_land_pin labels of our own 221 ladder games (n3x: 140 of N3, n2x: 81 of N2)
LIVE: dict[str, list[str]] = {
    "N3": ["n3x-n3-c*", "n2x-n3-c*"],
    "N5": ["n3x-n5-c*", "n2x-n5-c*"],
    "N6": ["n3x-n6-c*", "n2x-n6-c*"],
    "N7": ["n3x-n7", "n2x-n7"],
    "N8": ["n3x-n8a25-c*", "n2x-n8a25-c*"],
    "M2": ["n3x-m2-c*", "n2x-m2-c*"],
    "p_2965": ["n3x-p2965-c*", "n2x-p2965-c*"],
}
PRESETS = {"corpus": CORPUS, "live": LIVE}
# a complete corpus run, always pooled into the s fit (the live preset's rows carry no original-opponent ratings)
SCALE_LABELS = ["top-n6-c*"]
BANDS = (("<2450", -math.inf, 2450.0), ("2450-2600", 2450.0, 2600.0),
         ("2600-2700", 2600.0, 2700.0), ("2700+", 2700.0, math.inf))
REAL = "real"
LN10 = math.log(10.0)
BT_PRIOR = 0.5          # virtual win each way per pair keeps Bradley-Terry finite
KEEP = ("episode_id", "opponent", "opponent_rating", "team_rank", "original_opponent",
        "original_opponent_rating", "us", "them", "live", "drift", "errors")


# ---------------------------------------------------------------- loading

def _name_key(p: Path) -> tuple:
    return tuple(int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p.name))


def label_files(globs: list[str]) -> list[Path]:
    """Files of the label globs, oldest first so a rerun's rows override older ones."""
    files: set[Path] = set()
    for g in globs:
        files.update(REPLAYS.glob(g if g.endswith(".json") else g + ".json"))
    return sorted(files, key=lambda p: (p.stat().st_mtime, _name_key(p)))


def load_rows(globs: list[str]) -> tuple[dict, dict]:
    """episode -> trimmed game row, plus load info (files, duplicate rows, unreadable files)."""
    rows: dict = {}
    info = {"globs": globs, "files": 0, "duplicates": 0, "conflicts": 0, "unreadable": []}
    for p in label_files(globs):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            info["unreadable"].append(p.name)          # a chunk being written right now
            continue
        info["files"] += 1
        for r in data if isinstance(data, list) else []:
            if (not isinstance(r, dict) or "skip" in r or r.get("episode_id") is None
                    or r.get("us") is None or r.get("them") is None):
                continue
            ep = r["episode_id"]
            old = rows.get(ep)
            if old is not None:
                info["duplicates"] += 1
                info["conflicts"] += int((old["us"], old["them"]) != (r["us"], r["them"]))
            rows[ep] = {k: r[k] for k in KEEP if k in r}
    return rows, info


def drift(r: dict) -> float:
    d = r.get("drift")
    return 0.0 if d is None else float(d)


def rating(r: dict) -> float:
    x = r.get("opponent_rating")
    return math.nan if x is None else float(x)


def select(tokens: list[str], table: dict) -> tuple[list[str], dict]:
    """Agent names to score: named ones (else the whole map) plus NAME=glob,glob definitions."""
    table = dict(table)
    extra = []
    for t in tokens:
        if "=" in t:
            name, globs = t.split("=", 1)
            if not name or not globs or name == REAL:
                raise SystemExit(f"bad agent definition {t!r}: use NAME=glob1,glob2 (name not {REAL!r})")
            table[name] = [g for g in globs.split(",") if g]
            extra.append(name)
    named = [t for t in tokens if "=" not in t]
    unknown = [t for t in named if t not in table]
    if unknown:
        raise SystemExit(f"unknown agent(s) {unknown}; known: {', '.join(table)}")
    names = named + extra if named else list(table)
    return list(dict.fromkeys(names)), table


# ---------------------------------------------------------------- statistics

def _sig(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


def _bisect(f, lo: np.ndarray, hi: np.ndarray, iters: int = 50) -> np.ndarray:
    """Root of a decreasing vector function on [lo, hi], clamped to the ends."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        pos = f(mid) > 0
        lo, hi = np.where(pos, mid, lo), np.where(pos, hi, mid)
    return (lo + hi) / 2


def boot_weights(n: int, draws: int, rng: np.random.Generator) -> np.ndarray:
    """Row 0 all ones (the fit itself), then one row of resample counts per bootstrap draw."""
    idx = rng.integers(0, n, size=(draws, n)) + np.arange(draws)[:, None] * n
    counts = np.bincount(idx.ravel(), minlength=draws * n).reshape(draws, n)
    return np.vstack([np.ones((1, n)), counts]).astype(float)


S_LO, S_HI = 20.0, 5000.0


def fit_scale(d: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """MLE s per weight row for P(y=1) = 1/(1+10^(-d/s)), clamped to [S_LO, S_HI]."""
    def score(t):                     # d loglik / d beta at beta = exp(t); decreasing in t
        return (w * d * (y - _sig(np.exp(t)[:, None] * d))).sum(axis=1)
    rows = w.shape[0]
    t = _bisect(score, np.full(rows, math.log(LN10 / S_HI)), np.full(rows, math.log(LN10 / S_LO)))
    return LN10 / np.exp(t)


def fit_rating(y: np.ndarray, r: np.ndarray, w: np.ndarray, beta: float) -> tuple[np.ndarray, float, float]:
    """MLE rating per weight row: sum w (y - P(win | R, r)) = 0, clamped to [min r - 2000, max r + 2000]."""
    ok = np.isfinite(r)
    if not ok.any():
        return np.full(w.shape[0], math.nan), math.nan, math.nan
    w = w * ok
    rr = np.where(ok, r, 0.0)
    lo, hi = float(rr[ok].min()) - 2000.0, float(rr[ok].max()) + 2000.0
    rows = w.shape[0]

    def score(x):
        return (w * (y - _sig(beta * (x[:, None] - rr)))).sum(axis=1)
    return _bisect(score, np.full(rows, lo), np.full(rows, hi), 45), lo, hi


def bradley_terry(wins: np.ndarray, iters: int = 3000, tol: float = 1e-7) -> np.ndarray:
    """Elo-scale ratings (mean 0) per draw from wins[d, i, j] = times i beat j, by Hunter's MM."""
    k = wins.shape[1]
    off = 1.0 - np.eye(k)
    w = (wins + BT_PRIOR) * off
    n = w + w.transpose(0, 2, 1)
    tot = w.sum(axis=2)
    logp = np.zeros(tot.shape)
    for _ in range(iters):
        p = np.exp(logp)
        new = np.log(tot / (n / (p[:, :, None] + p[:, None, :])).sum(axis=2))
        new -= new.mean(axis=1, keepdims=True)
        done = float(np.max(np.abs(new - logp))) < tol
        logp = new
        if done:
            break
    return logp * 400.0 / LN10


def wilson(k: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def agent_card(rows: dict, eps: list, w: np.ndarray, beta: float) -> dict:
    m = np.array([rows[e]["us"] - rows[e]["them"] for e in eps], dtype=float)
    r = np.array([rating(rows[e]) for e in eps])
    y = (m > 0).astype(float)
    n, wins = len(eps), int(y.sum())
    fits, lo, hi = fit_rating(y, r, w, beta)
    boot = fits[1:]
    bands = {}
    for name, a, b in BANDS:
        sel = (r >= a) & (r < b)
        bands[name] = {"games": int(sel.sum()), "wins": int(y[sel].sum()),
                       "win_rate": float(y[sel].mean()) if sel.any() else None}
    worst = sorted(range(n), key=lambda i: m[i])[:3]
    return {
        "games": n, "wins": wins, "win_rate": wins / n, "wilson95": list(wilson(wins, n)),
        "margin_mean": float(m.mean()), "margin_median": float(np.median(m)),
        "margin_p10": float(np.percentile(m, 10)),
        "worst": [{"episode_id": eps[i], "opponent": rows[eps[i]].get("opponent"),
                   "opponent_rating": rows[eps[i]].get("opponent_rating"), "margin": float(m[i])}
                  for i in worst],
        "bands": bands,
        "errors_games": sum(1 for e in eps if (rows[e].get("errors") or 0) > 0),
        "rating": float(fits[0]),
        "rating_90": [float(np.percentile(boot, 5)), float(np.percentile(boot, 95))] if len(boot) else None,
        "rating_bound": ("upper" if fits[0] > hi - 1 else "lower" if fits[0] < lo + 1 else None),
        "_margins": m,
    }


def real_outcomes(rowsets) -> tuple[np.ndarray, np.ndarray]:
    """(r_top - r_orig, top team won) of each distinct real game in the rows."""
    games = {}
    for rows in rowsets:
        for ep, r in rows.items():
            live = r.get("live") or {}
            a, b = r.get("opponent_rating"), r.get("original_opponent_rating")
            if a is None or b is None or live.get("us") is None or live.get("them") is None:
                continue
            games[ep] = (float(a) - float(b), 1.0 if live["them"] > live["us"] else 0.0)
    arr = np.array(list(games.values()), dtype=float).reshape(-1, 2)
    return arr[:, 0], arr[:, 1]


# ---------------------------------------------------------------- output

def money(x: float) -> str:
    return f"{x:+,.0f}"


def pct(x) -> str:
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f}%"


def rating_cell(c: dict) -> str:
    if math.isnan(c["rating"]):
        return "-"
    mark = {"upper": ">", "lower": "<"}.get(c["rating_bound"], "")
    ci = f" [{c['rating_90'][0]:.0f}, {c['rating_90'][1]:.0f}]" if c["rating_90"] else ""
    return f"{mark}{c['rating']:.0f}{ci}"


def table(head: list[str], rows: list[list[str]], align: str = "") -> str:
    align = align or "l" + "r" * (len(head) - 1)
    sep = ["---:" if a == "r" else "---" for a in align]
    return "\n".join("| " + " | ".join(x) + " |" for x in [head, sep] + rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("agents", nargs="*",
                    help="agents of the preset map (default: all), and/or NAME=glob1,glob2 "
                         "definitions of label globs under rl/data/l2/land/replays (.json optional)")
    ap.add_argument("--preset", choices=sorted(PRESETS), default="corpus",
                    help="corpus: the 901 top-team games; live: our own ladder games")
    ap.add_argument("--max-drift", type=float, default=0.15,
                    help="a game counts only if every agent's replay drift is at most this")
    ap.add_argument("--min-coverage", type=float, default=None,
                    help="drop agents with fewer clean games than this (a count, or a fraction of the "
                         "best-covered agent's when <= 1) instead of shrinking the set")
    ap.add_argument("--anchor", help="agent pinned at 0 in the head-to-head ratings (default: mean 0)")
    ap.add_argument("--scale", type=float, default=None, help="use this logistic scale s instead of fitting it")
    ap.add_argument("--boot", type=int, default=500, help="bootstrap draws (games resampled)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tie-margin", type=float, default=0.0,
                    help="head-to-head: margins within this many coins of each other are a tie (half each)")
    ap.add_argument("--matrix-top", type=int, default=10, help="agents shown in the pairwise matrix")
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()
    if args.boot < 1:
        ap.error("--boot must be at least 1")

    names, labels = select(args.agents, PRESETS[args.preset])
    rows, info = {}, {}
    for a in names:
        rows[a], info[a] = load_rows(labels[a])
        info[a]["present"] = len(rows[a])
        info[a]["clean"] = sum(drift(r) <= args.max_drift for r in rows[a].values())

    kept = [a for a in names if info[a]["present"]]
    dropped = {a: "no games" for a in names if not info[a]["present"]}
    threshold = None
    if args.min_coverage is not None and kept:
        best = max(info[a]["clean"] for a in kept)
        threshold = args.min_coverage * best if args.min_coverage <= 1 else args.min_coverage
        for a in list(kept):
            if info[a]["clean"] < threshold:
                dropped[a] = f"{info[a]['clean']} clean < {threshold:.0f}"
                kept.remove(a)
    if args.anchor and args.anchor not in kept:
        raise SystemExit(f"anchor {args.anchor!r} is not among the scored agents {kept}")

    common: set = set()
    if kept:
        common = set.intersection(*({e for e, r in rows[a].items() if drift(r) <= args.max_drift}
                                    for a in kept))
    eps = sorted(common)
    union = set().union(*(rows[a] for a in kept)) if kept else set()

    out = ["## Agent scorecard", "",
           f"Preset {args.preset}, drift <= {args.max_drift}, "
           + (f"min coverage {threshold:.0f} clean games" if threshold is not None else "strict common set"), "",
           "### Coverage", ""]
    cov = []
    for a in names:
        i = info[a]
        status = "used" if a in kept else f"dropped: {dropped[a]}"
        cov.append([a, ", ".join(i["globs"]), str(i["files"]) + (f" (+{len(i['unreadable'])} unreadable)"
                                                                   if i["unreadable"] else ""),
                    str(i["present"]), str(i["clean"]), f"{i['duplicates']} ({i['conflicts']})", status])
    out.append(table(["agent", "labels", "files", "games", f"drift<={args.max_drift}",
                      "dup rows (differing)", "status"], cov, "lllrrrl"))
    out.append("")
    limiting = min(kept, key=lambda a: info[a]["clean"]) if kept else None
    out.append(f"Comparison set: **{len(eps)} games** present with drift <= {args.max_drift} for all "
               f"{len(kept)} agents (union of their games {len(union)}"
               + (f"; smallest clean coverage {limiting} {info[limiting]['clean']}" if limiting else "") + ").")
    result = {"preset": args.preset, "max_drift": args.max_drift, "min_coverage": args.min_coverage,
              "coverage_threshold": threshold, "coverage": info, "dropped": dropped, "agents_used": kept,
              "set": {"games": len(eps), "union": len(union), "episodes": eps}}
    if not eps:
        out.append("\nNo common games: pass --min-coverage (e.g. 0.8) or fewer agents.")
        print("\n".join(out))
        _write(args.json_out, result)
        return

    # ---- logistic scale from the real games
    rng = np.random.default_rng(args.seed)
    scale_info: dict = {}
    if args.scale:
        s = float(args.scale)
        scale_info = {"s": s, "source": "--scale"}
    else:
        # the real games do not depend on the agents: always pool a complete corpus run, so s (and
        # every R) is the same whichever agents are selected (N7 N8 alone saw 803 games, s 188 vs 203)
        d, y = real_outcomes([*(rows[a] for a in kept), load_rows(SCALE_LABELS)[0]])
        source = f"loaded rows + {', '.join(SCALE_LABELS)}"
        if len(d) < 50:
            s = 400.0
            scale_info = {"s": s, "source": "default (no real games with both ratings)"}
        else:
            fits = fit_scale(d, y, boot_weights(len(d), args.boot, rng))
            s = float(fits[0])

            def loglik(sc):
                p = np.clip(_sig(LN10 / sc * d), 1e-12, 1 - 1e-12)
                return float(np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
            scale_info = {"s": s, "s_90": [float(np.percentile(fits[1:], 5)), float(np.percentile(fits[1:], 95))],
                          "source": source, "games": len(d), "top_win_rate": float(y.mean()),
                          "mean_gap": float(d.mean()), "loglik_per_game": loglik(s), "loglik_s400": loglik(400.0),
                          "clamped": bool(s <= S_LO + 1 or s >= S_HI - 1)}
    beta = LN10 / s
    result["scale"] = scale_info
    if "s_90" in scale_info:
        si = scale_info
        line = (f"Logistic scale **s = {s:.0f}** (90% {si['s_90'][0]:.0f}-{si['s_90'][1]:.0f}), fitted on "
                f"{si['games']} distinct real games ({si['source']}): top team won {pct(si['top_win_rate'])}, "
                f"mean gap r_top - r_orig {si['mean_gap']:+.0f}; log-lik/game {si['loglik_per_game']:.4f} "
                f"(s=400: {si['loglik_s400']:.4f})" + (" -- clamped at the search bound" if si["clamped"] else "") + ".")
    else:
        line = f"Logistic scale **s = {s:.0f}** ({scale_info['source']})."
    out += ["", "### Performance rating scale", "", line]

    # ---- per-agent cards on the common set
    w = boot_weights(len(eps), args.boot, rng)
    cards = {a: agent_card(rows[a], eps, w, beta) for a in kept}
    ref = rows[kept[0]]
    real_rows = {}
    for e in eps:
        live = ref[e].get("live") or {}
        if live.get("us") is not None and live.get("them") is not None:
            real_rows[e] = {**ref[e], "us": live["us"], "them": live["them"], "errors": 0}
    if len(real_rows) == len(eps):
        cards[REAL] = agent_card(real_rows, eps, w, beta)
        origs = [ref[e].get("original_opponent_rating") for e in eps]
        origs = [x for x in origs if x is not None]
        cards[REAL]["mean_original_rating"] = float(np.mean(origs)) if origs else None

    # ---- head-to-head
    h2h_names = list(kept)
    bt = None
    if len(h2h_names) >= 2:
        mm = np.stack([cards[a]["_margins"] for a in h2h_names], axis=1)          # (games, k)
        gap = mm[:, :, None] - mm[:, None, :]
        beat = (gap > args.tie_margin) + 0.5 * (np.abs(gap) <= args.tie_margin)
        k = len(h2h_names)
        beat[:, np.arange(k), np.arange(k)] = 0.0
        wins = np.tensordot(w, beat, axes=(1, 0))                                   # (1 + boot, k, k)
        elo = bradley_terry(wins)
        if args.anchor:
            elo = elo - elo[:, [h2h_names.index(args.anchor)]]
        bt = {a: {"rating": float(elo[0, i]),
                  "rating_90": [float(np.percentile(elo[1:, i], 5)), float(np.percentile(elo[1:, i], 95))],
                  "score": float(wins[0, i].sum() / (len(eps) * (k - 1)))}
              for i, a in enumerate(h2h_names)}
        for a in h2h_names:
            cards[a]["h2h"] = bt[a]
        result["h2h"] = {"anchor": args.anchor, "prior": BT_PRIOR, "tie_margin": args.tie_margin, "ratings": bt,
                         "pairwise": {a: {b: float(wins[0, i, j]) for j, b in enumerate(h2h_names) if j != i}
                                      for i, a in enumerate(h2h_names)}}

    order = sorted(kept, key=lambda a: -cards[a]["rating"] if not math.isnan(cards[a]["rating"]) else math.inf)
    shown = order + ([REAL] if REAL in cards else [])

    out += ["", f"### Results on the {len(eps)} common games", ""]
    res = []
    for a in shown:
        c = cards[a]
        lo, hi = c["wilson95"]
        h = c.get("h2h")
        res.append([a + ("*" if a == REAL else ""), str(c["games"]), str(c["wins"]),
                    f"{pct(c['win_rate'])} [{100 * lo:.1f}, {100 * hi:.1f}]",
                    money(c["margin_mean"]), money(c["margin_median"]), money(c["margin_p10"]),
                    str(c["errors_games"]) if a != REAL else "-", rating_cell(c),
                    f"{h['rating']:+.0f} [{h['rating_90'][0]:+.0f}, {h['rating_90'][1]:+.0f}]" if h else "-"])
    out.append(table(["agent", "games", "wins", "win% [95%]", "mean margin", "median", "p10",
                      "err games", f"R [90%] (s={s:.0f})", "H2H [90%]"], res))
    if REAL in cards:
        mo = cards[REAL].get("mean_original_rating")
        out.append(f"\n\\* {REAL}: the original seat's real result in these games"
                   + (f" (mean original-opponent rating {mo:.0f}, a check on R's calibration)" if mo else "") + ".")

    out += ["", "### Win% by the top team's rating band", ""]
    bands = []
    for a in shown:
        bands.append([a] + [f"{b['wins']}/{b['games']} {pct(b['win_rate'])}" if b["games"] else "-"
                            for b in cards[a]["bands"].values()])
    out.append(table(["agent"] + [f"{n} (n={cards[kept[0]]['bands'][n]['games']})" for n, _, _ in BANDS], bands))

    out += ["", "### Worst 3 games", ""]
    worst = [[a, "; ".join(f"{x['episode_id']} vs {str(x['opponent'] or '?')[:18].strip()}"
                           f" ({(x['opponent_rating'] or 0):.0f}) {money(x['margin'])}" for x in cards[a]["worst"])]
             for a in shown]
    out.append(table(["agent", "episode vs top team (rating) margin"], worst, "ll"))

    if bt:
        ranked = sorted(h2h_names, key=lambda a: -bt[a]["rating"])
        out += ["", "### Head-to-head (per-game margins, Bradley-Terry, 400 scale, "
                + (f"{args.anchor} = 0)" if args.anchor else "mean 0)"), ""]
        out.append(table(["#", "agent", "rating", "90%", "mean pairwise score"],
                         [[str(i + 1), a, f"{bt[a]['rating']:+.0f}",
                           f"[{bt[a]['rating_90'][0]:+.0f}, {bt[a]['rating_90'][1]:+.0f}]", pct(bt[a]["score"])]
                          for i, a in enumerate(ranked)], "rlrrr"))
        top = ranked[:max(2, args.matrix_top)]
        idx = {a: i for i, a in enumerate(h2h_names)}
        out += ["", f"Pairwise: % of the {len(eps)} games where the row agent's margin beats the column's (ties half"
                + (f", a tie within {args.tie_margin:,.0f} coins" if args.tie_margin else "") + ")"
                + (f"; top {len(top)} of {len(ranked)}" if len(top) < len(ranked) else "") + ".", ""]
        mat = [[a] + ["-" if a == b else f"{100 * wins[0, idx[a], idx[b]] / len(eps):.0f}" for b in top]
               for a in top]
        out.append(table([""] + top, mat))

    print("\n".join(out))
    for c in cards.values():
        c.pop("_margins", None)
    result["agents"] = cards
    _write(args.json_out, result)


def _write(path: Path | None, result: dict) -> None:
    if path is None:
        return
    path = path if path.is_absolute() else ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=1, default=float), encoding="utf-8")
    print(f"\n(wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path})")


if __name__ == "__main__":
    main()
