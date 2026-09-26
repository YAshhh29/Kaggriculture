"""Compare a paired run against A with Agent L's own games on the same seeds.

tools.eval.paired writes rl/data/l2/paired/<label>.json (candidate vs A on
seeds x seats). Agent L's games against A on seeds 100-159, both seats, are
stored arena records (L_fg120__vs__A__s<seed>, A__vs__L_fg120__s<seed>). This
prints, on the shared (seed, seat) games: wins, mean/median margin, the change
in our own score and in A's score, and the results that flipped.

    python -m tools.analysis.l2_shadow_compare shadow-early
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PAIRED = ROOT / "rl" / "data" / "l2" / "paired"
GAMES = ROOT / "arena" / "games"


def l_baseline(seed: int, seat: int):
    name = (f"L_fg120__vs__A__s{seed}" if seat == 0 else f"A__vs__L_fg120__s{seed}")
    path = GAMES / f"{name}.json"
    if not path.exists():
        return None
    rec = json.loads(path.read_text(encoding="utf-8"))
    li = rec["agents"].index("L_fg120")
    return {"ours": rec["rewards"][li], "theirs": rec["rewards"][1 - li],
            "margin": rec["rewards"][li] - rec["rewards"][1 - li]}


def compare(label: str, opponent: str = "A", baseline: str | None = None) -> dict:
    """Against L's arena games vs A, or (baseline=label) another paired run's
    games on the same opponent, seed and seat."""
    rows = json.loads((PAIRED / f"{label}.json").read_text(encoding="utf-8"))
    base_rows = {}
    if baseline:
        for b in json.loads((PAIRED / f"{baseline}.json").read_text(encoding="utf-8")):
            if "margin" in b:
                base_rows[(b["opponent"], b["seed"], b["seat"])] = b
    pairs = []
    for r in rows:
        if "margin" not in r or (opponent != "*" and r.get("opponent") != opponent):
            continue
        base = (base_rows.get((r["opponent"], r["seed"], r["seat"])) if baseline
                else l_baseline(r["seed"], r["seat"]))
        if base is None:
            continue
        pairs.append((r, base))
    if not pairs:
        print("no shared games")
        return {}
    d_margin = [r["margin"] - b["margin"] for r, b in pairs]
    d_ours = [r["ours"] - b["ours"] for r, b in pairs]
    d_theirs = [r["theirs"] - b["theirs"] for r, b in pairs]
    out = {
        "label": label, "games": len(pairs),
        "wins_candidate": sum(r["won"] for r, _ in pairs),
        "wins_L": sum(b["margin"] > 0 for _, b in pairs),
        "ties_candidate": sum(r["margin"] == 0 for r, _ in pairs),
        "mean_margin_candidate": statistics.mean(r["margin"] for r, _ in pairs),
        "mean_margin_L": statistics.mean(b["margin"] for _, b in pairs),
        "median_margin_candidate": statistics.median(r["margin"] for r, _ in pairs),
        "median_margin_L": statistics.median(b["margin"] for _, b in pairs),
        "mean_margin_change": statistics.mean(d_margin),
        "median_margin_change": statistics.median(d_margin),
        "margin_better": sum(d > 0 for d in d_margin),
        "margin_worse": sum(d < 0 for d in d_margin),
        "mean_own_score_change": statistics.mean(d_ours),
        "mean_opponent_score_change": statistics.mean(d_theirs),
        "flips_to_win": sum(r["won"] and b["margin"] <= 0 for r, b in pairs),
        "flips_to_loss": sum((not r["won"]) and b["margin"] > 0 for r, b in pairs),
        "worst_margin_candidate": min(r["margin"] for r, _ in pairs),
    }
    if len(d_margin) > 1:
        out["margin_change_stderr"] = statistics.stdev(d_margin) / len(d_margin) ** 0.5
    tel = [r.get("telemetry") or {} for r, _ in pairs]
    keys = sorted({k for t in tel for k in t if k.startswith(("early", "shadow"))})
    out["telemetry_mean"] = {k: round(statistics.mean(t.get(k, 0) for t in tel), 2) for k in keys}
    out["seconds_mean"] = statistics.mean(r.get("seconds", 0) for r, _ in pairs)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("labels", nargs="+")
    ap.add_argument("--baseline", default=None, help="paired label to compare with instead of L's arena games vs A")
    ap.add_argument("--opponent", default=None, help="one opponent, or * for all (default A, or * with --baseline)")
    ap.add_argument("--per-opponent", action="store_true")
    args = ap.parse_args()
    opp = args.opponent or ("*" if args.baseline else "A")
    for label in args.labels:
        if args.per_opponent:
            rows = json.loads((PAIRED / f"{label}.json").read_text(encoding="utf-8"))
            for o in sorted({r["opponent"] for r in rows}):
                res = compare(label, o, args.baseline)
                res.pop("telemetry_mean", None)
                print(o, json.dumps(res))
        print(json.dumps(compare(label, opp, args.baseline), indent=1))


if __name__ == "__main__":
    main()
