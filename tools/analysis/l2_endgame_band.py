"""Endgame per-item revenue on the faithful band games.

The band panel plays our agents against the recorded moves of teams rated
2600-2900 (arena/games/band__<agent>__vs__<team>__ep<id>.json: seed + both
packed tapes, env step t applies tape[t + 1]). Only 2600-2700 recordings
replay faithfully (their score in our replay >= 90% of their real score), so
only those are used. Each game is replayed exactly and logged with
tools.analysis.l2_endgame_bench.log_game (who 0 = our agent, who 1 = team).

    python -m tools.analysis.l2_endgame_band --workers 2
"""

from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_endgame_log import ITEMS, OUT  # noqa: E402

PANELS = [ROOT / "rl" / "data" / "band_panel" / "band_2600_2700_front.json",
          ROOT / "rl" / "data" / "band_panel" / "band_2600_2900.json"]
GAMES = ROOT / "arena" / "games"


def job(row):
    from tools.analysis.l2_endgame_bench import log_game
    game = json.loads((GAMES / f"{row['game_id']}.json").read_text(encoding="utf-8"))
    ours = 1 - int(row["seat"])
    record = {"episode_id": row["game_id"], "seed": game["seed"], "our_side": ours,
              "our_actions_zlib_b64": game["tapes"][ours],
              "opp_actions_zlib_b64": game["tapes"][1 - ours],
              "rewards": {"us": float(game["rewards"][ours]),
                          "them": float(game["rewards"][1 - ours])},
              "submission": None}
    out = log_game(record)
    return {"game_id": row["game_id"], "agent": row["agent"], "team": row["team"],
            "score": row["score"], "exact": out["exact"], "final": out["replay"],
            "sales": [s for s in out["sales"] if s[0] >= 600],
            "discards": out["discards"], "money": out["money"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    rows, seen = [], set()
    for panel in PANELS:
        for r in json.loads(panel.read_text(encoding="utf-8")):
            if (r.get("agent") in ("A", "L_front") and "ours" in r
                    and 2600 <= r["score"] < 2700 and r["theirs"] >= 0.9 * r["recorded"]
                    and r["game_id"] not in seen
                    and (GAMES / f"{r['game_id']}.json").exists()):
                seen.add(r["game_id"])
                rows.append(r)
    print(f"{len(rows)} faithful band games", flush=True)
    with Pool(args.workers) as pool:
        logs = pool.map(job, rows)
    path = OUT / "band_endgame.json"
    path.write_text(json.dumps(logs), encoding="utf-8")
    print(f"saved {path.relative_to(ROOT)}; exact replays {sum(g['exact'] for g in logs)}/{len(logs)}")
    for agent in ("A", "L_front"):
        G = [g for g in logs if g["agent"] == agent]
        if not G:
            continue
        print(f"\n{agent} vs faithful 2600-2700 teams: {len(G)} games, won "
              f"{sum(g['final']['us'] > g['final']['them'] for g in G)}; "
              f"median margin {statistics.median(g['final']['us'] - g['final']['them'] for g in G):+,.0f}")
        print(f"  days 25-29 SELL revenue per game (mean): {'item':11s} us / team / diff (median diff)")
        tot = [0.0, 0.0]
        for item in ITEMS:
            per = []
            for g in G:
                r = [0.0, 0.0]
                for s in g["sales"]:
                    if s[2] == "SELL" and s[3] == item:
                        r[s[1]] += s[5]
                per.append(r)
            u = statistics.mean(p[0] for p in per)
            t = statistics.mean(p[1] for p in per)
            tot[0] += u
            tot[1] += t
            print(f"    {item:11s} {u:7.0f} / {t:7.0f} / {u - t:+6.0f} ({statistics.median(p[0] - p[1] for p in per):+.0f})")
        print(f"    {'TOTAL':11s} {tot[0]:7.0f} / {tot[1]:7.0f} / {tot[0] - tot[1]:+6.0f}")
        d29 = [(g["money"][29][0], g["money"][29][1]) for g in G]
        print(f"  money at day 25 start (median) us {statistics.median(g['money'][25][0] for g in G):,.0f} "
              f"team {statistics.median(g['money'][25][1] for g in G):,.0f}; day 29 us "
              f"{statistics.median(x[0] for x in d29):,.0f} team {statistics.median(x[1] for x in d29):,.0f}")


if __name__ == "__main__":
    main()
