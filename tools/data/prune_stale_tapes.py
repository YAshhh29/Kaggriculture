"""Keep only replays from agents that are on the board now.

The replay corpus accumulates. Every fetch adds tapes, and the top of the
ladder turns over within days -- 35 of the top 45 were new names four days
after one snapshot -- so older tapes describe agents nobody plays any more.
Measuring against them is how a whole study once ran on dead opponents.

This moves every tape whose episode is not in the current match snapshot
(rl/data/top_matches.jsonl, rebuilt from each top team's current submission)
out of the live corpus into kaggle_cache/stale_tapes/, and rewrites the
index to the current episodes only. Nothing is deleted: the old index is
kept beside the new one, and the moved tapes can be removed by hand once
they are no longer wanted.

    python -m tools.data.prune_stale_tapes            # report only
    python -m tools.data.prune_stale_tapes --apply
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "rl" / "data"
TAPES = ROOT / "kaggle_cache" / "live_clones"
STALE = ROOT / "kaggle_cache" / "stale_tapes"
INDEX = DATA / "live_opponents.jsonl"
MATCHES = DATA / "top_matches.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = [json.loads(line) for line in
            MATCHES.read_text(encoding="utf-8").splitlines()]
    current = {int(r["episode_id"]) for r in rows}
    newest = max(r.get("create_time") or "" for r in rows)
    print(f"current snapshot: {len(current)} episodes, newest game {newest[:16]}")

    tapes = sorted(TAPES.glob("live_*.json"))
    stale = [p for p in tapes
             if int(p.stem.split("_")[1]) not in current]
    index = [json.loads(line) for line in
             INDEX.read_text(encoding="utf-8").splitlines()]
    keep, seen = [], set()
    for row in index:
        episode = int(row["episode_id"])
        if episode in current and episode not in seen \
                and (TAPES / f"live_{episode}.json").exists():
            seen.add(episode)
            keep.append(row)
    by_team = Counter(r.get("name") for r in keep)
    print(f"tapes held: {len(tapes)}; stale (not in snapshot): {len(stale)}; "
          f"current kept: {len(tapes) - len(stale)}")
    print(f"index rows: {len(index)} -> {len(keep)} (duplicates and stale dropped)")
    print(f"current teams with replays: {len(by_team)}; at 6 or more: "
          f"{sum(1 for n in by_team.values() if n >= 6)}")
    if not args.apply:
        print("report only; pass --apply to move stale tapes and rewrite the index")
        return

    STALE.mkdir(parents=True, exist_ok=True)
    for path in stale:
        shutil.move(str(path), STALE / path.name)
    backup = DATA / f"live_opponents.before-prune-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    shutil.copyfile(INDEX, backup)
    INDEX.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                             for r in keep), encoding="utf-8")
    print(f"moved {len(stale)} tapes to {STALE.relative_to(ROOT)}; "
          f"old index kept as {backup.name}")


if __name__ == "__main__":
    main()
