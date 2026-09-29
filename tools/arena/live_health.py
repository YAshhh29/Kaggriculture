"""Health of our submissions in their real ladder games: statuses and time bank.

For each episode of a submission this downloads the public replay once, keeps a
small record (our seat's final status, any non-ACTIVE/DONE status, the
overage time bank left at the end and at its lowest, both rewards) in
rl/data/live_health.jsonl, and prints a summary. An agent that is slow on
Kaggle's hardware shows it here first: the bank (60 s) drains before any turn
times out.

    KAGGLE_API_TOKEN=... python -m tools.arena.live_health --submissions 56685025 56684201
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

EPISODE_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode}.json"
OUT = ROOT / "rl" / "data" / "live_health.jsonl"
OUR_TEAM = 16724366


def episodes(token: str, submission: int) -> list[dict]:
    delay = 30.0
    for attempt in range(6):          # the listing is rate-limited (429) after bursts
        r = requests.post(EPISODE_URL, headers={"Authorization": f"Bearer {token}",
                                                "Content-Type": "application/json"},
                          json={"submissionId": submission}, timeout=120)
        if r.status_code != 429:
            break
        print(f"  listing rate-limited, retry {attempt + 1} in {delay:.0f} s", flush=True)
        time.sleep(delay)
        delay = min(delay * 2, 300.0)
    r.raise_for_status()
    out = []
    for ep in r.json().get("episodes") or []:
        agents = ep.get("agents") or []
        mine = next((a for a in agents if a.get("teamId") == OUR_TEAM
                     and a.get("submissionId") == submission), None)
        other = next((a for a in agents if a is not mine), None)
        if mine is None or other is None or mine.get("reward") is None:
            continue
        out.append({"episode_id": ep["id"], "submission": submission,
                    "seat": int(mine.get("index", 0)),
                    "opp_rating": other.get("updatedScore") or other.get("initialScore"),
                    "us": mine.get("reward"), "them": other.get("reward")})
    return out


def inspect(row: dict) -> dict:
    replay = requests.get(REPLAY_URL.format(episode=row["episode_id"]), timeout=180).json()
    seat = row["seat"]
    steps = replay.get("steps") or []
    statuses, bank = set(), []
    for step in steps:
        if seat >= len(step):
            continue
        s = step[seat]
        statuses.add(s.get("status"))
        left = (s.get("observation") or {}).get("remainingOverageTime")
        if left is not None:
            bank.append(float(left))
    final = steps[-1][seat].get("status") if steps and seat < len(steps[-1]) else None
    return dict(row, steps=len(steps), final_status=final,
                statuses=sorted(x for x in statuses if x),
                bank_end=bank[-1] if bank else None, bank_min=min(bank) if bank else None)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--submissions", type=int, nargs="+", required=True)
    ap.add_argument("--limit", type=int, default=40, help="newest games per submission to inspect")
    ap.add_argument("--pause", type=float, default=1.0)
    args = ap.parse_args()
    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        raise SystemExit("set KAGGLE_API_TOKEN in the environment (inline)")
    done = {}
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done[r["episode_id"]] = r
    with OUT.open("a", encoding="utf-8") as fh:
        for sub in args.submissions:
            rows = episodes(token, sub)[: args.limit]
            for row in rows:
                if row["episode_id"] in done:
                    continue
                try:
                    rec = inspect(row)
                except Exception as err:          # a replay not yet published
                    print(f"  {row['episode_id']}: skipped ({type(err).__name__})")
                    continue
                done[rec["episode_id"]] = rec
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                time.sleep(args.pause)
    for sub in args.submissions:
        recs = [r for r in done.values() if r["submission"] == sub]
        if not recs:
            print(f"{sub}: no games inspected")
            continue
        bad = [r for r in recs if set(r["statuses"]) - {"ACTIVE", "DONE", "INACTIVE"}]
        banks = [r["bank_min"] for r in recs if r["bank_min"] is not None]
        wins = sum((r["us"] or 0) > (r["them"] or 0) for r in recs)
        print(f"{sub}: {len(recs)} games, {wins} won | non-normal statuses in {len(bad)} "
              f"| time bank left: lowest {min(banks) if banks else '?'} s, "
              f"median lowest {sorted(banks)[len(banks) // 2] if banks else '?'} s of 60")
        for r in bad:
            print(f"   {r['episode_id']}: {r['statuses']} final {r['final_status']} us {r['us']} them {r['them']}")


if __name__ == "__main__":
    main()
