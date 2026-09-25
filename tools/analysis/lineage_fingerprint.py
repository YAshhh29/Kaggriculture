"""How much of the ladder plays the public lineage, and who plays a fixed route.

A route-replaying agent's farmer walks the same programme whatever the seed,
so its first days of farmer actions are a fingerprint. This compares, for
every game in the corpus, each side's farmer actions over the opening window
against reference agents we can run ourselves (e.g. the public 2945 Farm, our
K), and reports how often each is matched. It also measures, per team, how
much the team repeats itself across its own games -- a team that repeats
nearly everything is replaying a route; one that diverges early re-decides.

No replay needed: this reads action tapes only, so it is cheap.

    python -m tools.analysis.lineage_fingerprint --window 144
"""

from __future__ import annotations

import argparse
import base64
import itertools
import json
import statistics
import sys
import zlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CORPUS = ROOT / "kaggle_cache" / "corpus_v2"
GAMES = ROOT / "arena" / "games"


def unpack(blob: str) -> list:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def farmer_seq(actions: list, window: int) -> list[str]:
    out = []
    for a in actions[:window]:
        f = (a or {}).get("farmer") if isinstance(a, dict) else None
        out.append(json.dumps(f, separators=(",", ":")) if f else "-")
    return out


def agreement(a: list[str], b: list[str]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(x == y for x, y in zip(a[:n], b[:n])) / n


def references(names: list[str], window: int) -> dict[str, list[list[str]]]:
    """Farmer sequences of agents we ran ourselves, from stored arena games."""
    refs: dict[str, list[list[str]]] = defaultdict(list)
    for path in GAMES.glob("*.json"):
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if "tapes" not in r:
            continue
        for i, name in enumerate(r["agents"]):
            if name in names:
                refs[name].append(farmer_seq(unpack(r["tapes"][i]), window))
    return refs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=int, default=144,
                    help="opening steps compared (144 = first six days)")
    ap.add_argument("--refs", nargs="+",
                    default=["nb_tschinkel_2945", "K"])
    ap.add_argument("--match", type=float, default=0.80,
                    help="agreement counted as the same programme")
    args = ap.parse_args()

    refs = references(args.refs, args.window)
    print(f"references: " + ", ".join(f"{k} ({len(v)} games)"
                                      for k, v in refs.items()))
    # The leaderboard API leaves team names blank, so rank comes from each
    # tape, which recorded the team's rank and rating at fetch time.
    rank_of: dict[str, int] = {}

    per_team: dict[str, list[list[str]]] = defaultdict(list)
    side_best: dict[str, list[tuple[float, str]]] = defaultdict(list)
    opp_best: list[tuple[float, str, float]] = []
    n = 0
    for path in CORPUS.glob("ep*.json"):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        n += 1
        mine = farmer_seq(unpack(rec["actions_zlib_b64"]), args.window)
        theirs = farmer_seq(unpack(rec["opponent_actions_zlib_b64"]),
                            args.window)
        team = rec.get("source_team", "?")
        rank_of.setdefault(team, int(rec.get("team_rank") or 9999))
        per_team[team].append(mine)
        for seq, bucket in ((mine, side_best[team]),):
            best = max(((agreement(seq, r), k) for k, rs in refs.items()
                        for r in rs), default=(0.0, "-"))
            bucket.append(best)
        best_o = max(((agreement(theirs, r), k) for k, rs in refs.items()
                      for r in rs), default=(0.0, "-"))
        opp_best.append((best_o[0], best_o[1],
                         float(rec.get("opponent_rating") or 0)))

    print(f"\n{n} corpus games, {len(per_team)} teams, window "
          f"{args.window} steps, match threshold {args.match:.0%}\n")

    # How many OPPONENTS on the ladder play a reference programme?
    print("  opponents met by top-500 teams, matched to a reference:")
    for k in refs:
        hit = [o for o in opp_best if o[1] == k and o[0] >= args.match]
        print(f"    {k:22s} {len(hit):4d} of {len(opp_best)} "
              f"({100 * len(hit) / max(1, len(opp_best)):.0f}%)")
    bands = [(2800, 9999), (2700, 2800), (2600, 2700), (0, 2600)]
    print("  by opponent rating (share matching ANY reference):")
    for lo, hi in bands:
        sel = [o for o in opp_best if lo <= o[2] < hi]
        hit = [o for o in sel if o[0] >= args.match]
        print(f"    {lo}-{hi if hi < 9999 else '':5}: {len(hit):4d}/{len(sel):<4d}"
              f" ({100 * len(hit) / max(1, len(sel)):.0f}%)")

    # Teams: do they repeat themselves, and do they play a reference?
    print("\n  teams by rank: self-repeat across own games, and best "
          "reference match")
    rows = []
    for team, seqs in per_team.items():
        if len(seqs) < 3:
            continue
        pair = [agreement(a, b) for a, b in itertools.combinations(seqs, 2)]
        best = side_best[team]
        top = max(best) if best else (0.0, "-")
        rows.append((rank_of.get(team, 9999), team, statistics.mean(pair),
                     top))
    rows.sort()
    for rank, team, rep, top in rows[:45]:
        print(f"    #{rank:<4} {team[:26]:26s} self-repeat {rep:4.0%}   "
              f"closest ref {top[1]} {top[0]:4.0%}")
    reps = [r[2] for r in rows]
    for lo, hi in ((1, 10), (11, 30), (31, 100), (101, 500)):
        sel = [r[2] for r in rows if lo <= r[0] <= hi]
        if sel:
            print(f"    ranks {lo}-{hi}: median self-repeat "
                  f"{statistics.median(sel):.0%} over {len(sel)} teams")
    if reps:
        print(f"    all: median self-repeat {statistics.median(reps):.0%}")


if __name__ == "__main__":
    main()
