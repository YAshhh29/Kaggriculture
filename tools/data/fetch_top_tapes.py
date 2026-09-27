"""Download top players' own games: their exact moves, the seed, both results.

Input: rl/data/top_submissions.json (tools/data/climb_ladder.py). For each of
the --teams best submissions, the most recent --per episodes are listed (the
episode API gives each agent's seat), the public replay is downloaded, and a
compact record is kept in rl/data/top_tapes/ep<id>.json in the same format as
our live tapes, with "our_side" set to the TOP player's seat -- so
`our_actions_zlib_b64` is the top player's tape and the game replays exactly
with rl.replay_agent.

    KAGGLE_API_TOKEN=... python -m tools.data.fetch_top_tapes --teams 6 --per 8
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TOP = ROOT / "rl" / "data" / "top_submissions.json"
OUT = ROOT / "rl" / "data" / "top_tapes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode}.json"


def main() -> None:
    from tools.data.climb_ladder import episodes_of
    from tools.data.extract_live_tapes import extract

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--teams", type=int, default=6, help="distinct teams, best submission each")
    ap.add_argument("--per", type=int, default=8)
    ap.add_argument("--pause", type=float, default=1.0)
    args = ap.parse_args()
    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN inline")
    top = json.loads(TOP.read_text(encoding="utf-8"))
    chosen, teams = [], set()
    for sub, row in sorted(top.items(), key=lambda kv: -kv[1]["rating"]):
        if row["team"] in teams or len(row["episodes"]) < args.per:
            continue
        teams.add(row["team"])
        chosen.append((int(sub), row))
        if len(chosen) >= args.teams:
            break
    OUT.mkdir(parents=True, exist_ok=True)
    kept = 0
    for sub, row in chosen:
        payload = episodes_of(token, sub)
        names = {t["id"]: t.get("teamName", "") for t in (payload.get("teams") or [])}
        eps = []
        for ep in payload.get("episodes") or []:
            agents = ep.get("agents") or []
            mine = next((a for a in agents if a.get("submissionId") == sub), None)
            other = next((a for a in agents if a.get("submissionId") != sub), None)
            if mine is None or other is None or mine.get("reward") is None:
                continue
            eps.append((ep["id"], int(mine.get("index", 0)), other, names))
        eps.sort(key=lambda e: -e[0])
        print(f"{row['team']} ({sub}, {row['rating']:.0f}): {len(eps)} episodes, taking {min(args.per, len(eps))}",
              flush=True)
        for episode, side, other, names in eps[: args.per]:
            path = OUT / f"ep{episode}.json"
            if path.exists():
                continue
            try:
                raw = requests.get(REPLAY_URL.format(episode=episode), timeout=180)
                if raw.status_code != 200:
                    continue
                replay = raw.json()
            except Exception as error:
                print(f"  {episode}: {error}")
                continue
            rec = extract(replay, side)
            rec.update({"episode_id": episode, "submission": sub, "team": row["team"],
                        "rating": row["rating"], "opponent": names.get(other.get("teamId"), ""),
                        "opponent_rating": other.get("updatedScore") or other.get("initialScore")})
            del replay
            path.write_text(json.dumps(rec), encoding="utf-8")
            kept += 1
            r = rec["rewards"]
            print(f"  ep {episode}: {r['us']:,.0f} vs {r['them']:,.0f} ({rec['opponent'][:18]})", flush=True)
            time.sleep(args.pause)
    print(f"kept {kept} top games in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
