"""Before the final submission: find public programs our opponents now run.

The opponent shadow (rl/l2_shadow.py) wins every game against an exact copy of
a program in its library, and after the deadline the field is frozen for eight
days with whatever was copied by then. This finds what is missing:

1. lists the competition's public notebooks (newest first) and pulls those with
   at least --min-votes votes that are not in kaggle_cache/notebooks yet;
2. extracts the exact main.py each submits (tools/data/extract_notebook_agents);
3. replays our most recent real ladder games (rl/data/our_live_tapes, for the
   given submissions -- refresh them first with fetch_our_games and
   extract_live_tapes) and counts, per new program, the games in which it
   matched the opponent for the whole game or past day 16.

Programs with real ladder presence are candidates for the final library:

    python -m tools.packaging.package_l3 --name L5 --agree --library <...> --factory ...

    KAGGLE_API_TOKEN=... python -m tools.data.refresh_library --submissions 56601363 56601249
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
NOTEBOOKS = ROOT / "kaggle_cache" / "notebooks"
LIST = "https://www.kaggle.com/api/v1/kernels/list"


def new_notebooks(token: str, min_votes: int, pages: int = 3) -> list[str]:
    have = {p.stem for p in NOTEBOOKS.glob("*.py")}
    out = []
    for page in range(1, pages + 1):
        r = requests.get(LIST, params={"competition": "kaggriculture", "sortBy": "dateCreated",
                                       "pageSize": 100, "page": page},
                         headers={"Authorization": f"Bearer {token}"}, timeout=60)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        for k in batch:
            ref = k.get("ref", "")
            if ref and int(k.get("totalVotes") or 0) >= min_votes and ref.replace("/", "__") not in have:
                out.append(ref)
    return out


def run(cmd: list[str]) -> str:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    res = subprocess.run([sys.executable, "-u", "-m"] + cmd, cwd=ROOT, env=env,
                         capture_output=True, text=True, encoding="utf-8")
    return "\n".join(line for line in (res.stdout + res.stderr).splitlines()
                     if "pyspiel" not in line)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--submissions", type=int, nargs="+", required=True,
                    help="our live submissions whose games to scan")
    ap.add_argument("--min-votes", type=int, default=5)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN inline")

    refs = new_notebooks(token, args.min_votes)
    print(f"{len(refs)} public notebooks with >= {args.min_votes} votes not held yet")
    if refs:
        print(run(["tools.data.fetch_public_notebook", *refs, "--pause", "1.0"]))
    before = {p.stem for p in (ROOT / "rl" / "public").glob("nb_*.py")}
    stems = [r.replace("/", "__") for r in refs]
    if stems:
        print(run(["tools.data.extract_notebook_agents", *stems]))
    new = sorted({p.stem for p in (ROOT / "rl" / "public").glob("nb_*.py")} - before)
    print(f"{len(new)} new programs extracted: {new}")
    if not new:
        return
    presence = defaultdict(lambda: [0, 0])
    for sub in args.submissions:
        label = f"refresh_{sub}"
        print(run(["tools.analysis.l2_shadow_sync", "--submission", str(sub), "--candidates", *new,
                   "--workers", str(args.workers), "--label", label])[-400:])
        path = ROOT / "rl" / "data" / "l2" / "shadow" / f"sync_{label}.json"
        d = json.loads(path.read_text(encoding="utf-8"))
        rows = d if isinstance(d, list) else (d.get("rows") or d.get("games") or [])
        for r in rows:
            for name, c in r["candidates"].items():
                if "error" in c:
                    continue
                fm = c.get("first_miss")
                if fm is None:
                    presence[name][0] += 1
                elif fm >= 400:
                    presence[name][1] += 1
    print("\nnew program: whole-game syncs, synced past day 16 (our recent games)")
    for name, (a, b) in sorted(presence.items(), key=lambda kv: -(3 * kv[1][0] + kv[1][1])):
        print(f"  {name:55s} {a:4d} {b:4d}")
    print("\nCheck any candidate against A (python -m tools.arena.arena tourney <name> --vs A): "
          "a program that ties A to the coin is a copy of A and adds nothing.")


if __name__ == "__main__":
    main()
