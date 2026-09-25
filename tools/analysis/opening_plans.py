"""What each top team does in its first days, read from its own action tapes.

The fingerprint study found the gap between the top 30 and the public lineage
is visible in the opening: the top teams run a different production plan. This
reduces each team's opening to the decisions that make up a plan -- hires,
land, seed by crop, animals by type, feed bought, what it plants and builds --
and prints them beside the lineage's, so the difference is concrete rather
than a similarity score.

Market orders are intent: a BUY that the purse could not cover fails in the
engine, so these are what a team asked for. That is the plan, which is the
question here.

    python -m tools.analysis.opening_plans --days 6 --top 45
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CORPUS = ROOT / "kaggle_cache" / "corpus_v2"
GAMES = ROOT / "arena" / "games"
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")


def unpack(blob: str) -> list:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def plan_of(actions: list, steps: int) -> dict[str, float]:
    out: Counter = Counter()
    first_land = None
    for t, a in enumerate(actions[:steps]):
        if not isinstance(a, dict):
            continue
        for o in a.get("market") or []:
            if not (isinstance(o, list) and o):
                continue
            op = o[0]
            qty = 1
            if len(o) >= 3:
                try:
                    qty = int(o[2])
                except (TypeError, ValueError):
                    qty = 0
            if op == "HIRE":
                out["hires"] += 1
            elif op == "BUY_LAND":
                out["land"] += 1
                first_land = t if first_land is None else first_land
            elif op == "BUY_SEED" and len(o) >= 2:
                out[f"seed_{o[1]}"] += qty
            elif op == "BUY_ANIMAL" and len(o) >= 2:
                out[f"animal_{o[1]}"] += qty
            elif op == "BUY_PRODUCT" and len(o) >= 2:
                out[f"buy_{o[1]}"] += qty
            elif op == "SELL" and len(o) >= 2:
                out["sell_orders"] += 1
        units = [a.get("farmer")] + list(a.get("hands") or [])
        for u in units:
            if not (isinstance(u, list) and u):
                continue
            if u[0] == "PLANT" and len(u) >= 2:
                out[f"plant_{u[1]}"] += 1
            elif u[0] in ("BUILD_COOP", "BUILD_PASTURE"):
                out[u[0].lower()] += 1
            elif u[0] == "PLACE" and len(u) >= 2:
                out[f"place_{u[1]}"] += 1
    out["first_land_step"] = first_land if first_land is not None else -1
    return dict(out)


COLUMNS = (["hires", "land", "first_land_step"]
           + [f"seed_{c}" for c in CROPS]
           + [f"plant_{c}" for c in CROPS]
           + [f"animal_{a}" for a in ANIMALS]
           + ["build_coop", "build_pasture", "buy_WHEAT", "sell_orders"])
SHORT = {"hires": "hire", "land": "land", "first_land_step": "land@",
         **{f"seed_{c}": f"s{c[:3].lower()}" for c in CROPS},
         **{f"plant_{c}": f"p{c[:3].lower()}" for c in CROPS},
         **{f"animal_{a}": a[:3].lower() for a in ANIMALS},
         "build_coop": "coop", "build_pasture": "past",
         "buy_WHEAT": "bwht", "sell_orders": "sells"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=6)
    ap.add_argument("--top", type=int, default=45)
    ap.add_argument("--refs", nargs="+", default=["nb_tschinkel_2945"])
    args = ap.parse_args()
    steps = args.days * 24

    teams: dict[tuple, list[dict]] = defaultdict(list)
    for path in CORPUS.glob("ep*.json"):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rank = int(rec.get("team_rank") or 9999)
        if rank > args.top:
            continue
        key = (rank, rec.get("source_team", "?"), rec.get("team_score", 0))
        teams[key].append(plan_of(unpack(rec["actions_zlib_b64"]), steps))

    refs: dict[str, list[dict]] = defaultdict(list)
    for path in GAMES.glob("*.json"):
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for i, name in enumerate(r.get("agents") or []):
            if name in args.refs and "tapes" in r:
                refs[name].append(plan_of(unpack(r["tapes"][i]), steps))

    head = f"  {'rank':>4} {'team':22s} {'n':>2} " + " ".join(
        f"{SHORT[c]:>5}" for c in COLUMNS)
    print(f"\nfirst {args.days} days (steps 0-{steps - 1}), median per game; "
          f"market columns are orders requested\n")
    print(head)

    def row(label: str, plans: list[dict]) -> str:
        cells = []
        for c in COLUMNS:
            vals = [p.get(c, 0) for p in plans]
            if c == "first_land_step":
                vals = [v for v in vals if v >= 0] or [-1]
            cells.append(f"{statistics.median(vals):5.0f}")
        return f"  {label} {len(plans):2d} " + " ".join(cells)

    for name, plans in refs.items():
        print(row(f"{'ref':>4} {name[:22]:22s}", plans))
    print()
    for (rank, team, score), plans in sorted(teams.items()):
        print(row(f"{rank:4d} {team[:22]:22s}", plans))


if __name__ == "__main__":
    main()
