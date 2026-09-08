"""What the top of the leaderboard's 5,875 real matches actually show.

`tools/data/fetch_leaderboard_records.py` pulls every match the top teams
have played, with both rewards and both ratings. That record answers
questions no local panel can, because it is live play between real agents
rather than our code against a recording:

* **Is reward a measure of skill?** If a strong agent scores high because
  it plays well, its reward should not depend much on who it drew. If
  reward is mostly a function of how hard the opponent contests the shared
  market, it should collapse when two strong agents meet.
* **How wide are the margins?** Section 10.8r measured our own median
  winning margin at 1,151 coins. If the top of the board wins by similar
  slivers, then a few thousand coins is the whole game up there too.
* **Does anyone at the top lose to weak opposition?** That is the shape of
  a fragile agent, and it is what we would be buying if we cloned one.

    python -m tools.data.analyse_top_matches
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / "rl" / "data" / "leaderboard.jsonl"
MATCHES = ROOT / "rl" / "data" / "top_matches.jsonl"


def load() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    board = [json.loads(x) for x in
             BOARD.read_text(encoding="utf-8").splitlines()]
    games = [json.loads(x) for x in
             MATCHES.read_text(encoding="utf-8").splitlines()]
    return board, [g for g in games if not g.get("self_play")]


def band(rating: float | None) -> str:
    if not rating:
        return "unrated"
    if rating >= 2700:
        return "2700+"
    if rating >= 2400:
        return "2400-2700"
    if rating >= 2000:
        return "2000-2400"
    if rating >= 1600:
        return "1600-2000"
    return "under 1600"


ORDER = ("2700+", "2400-2700", "2000-2400", "1600-2000",
         "under 1600", "unrated")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--floor", type=float, default=2700.0)
    args = parser.parse_args()
    board, games = load()
    print(f"{len(board)} teams, {len(games)} contested matches\n")

    print("=== A top team's own reward, by the strength of who it drew ===")
    by_band: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for game in games:
        by_band[band(game.get("opponent_rating"))].append(game)
    print(f"  {'opponent band':14s} {'games':>6s} {'our reward':>11s} "
          f"{'their reward':>13s} {'margin':>10s} {'win rate':>9s}")
    for name in ORDER:
        rows = by_band.get(name) or []
        if len(rows) < 20:
            continue
        print(f"  {name:14s} {len(rows):6d} "
              f"{statistics.mean(r['reward'] for r in rows):11,.0f} "
              f"{statistics.mean(r['opponent_reward'] for r in rows):13,.0f} "
              f"{statistics.mean(r['margin'] for r in rows):+10,.0f} "
              f"{sum(1 for r in rows if r['won']) / len(rows):9.1%}")

    wins = [g["margin"] for g in games if g["won"]]
    losses = [-g["margin"] for g in games if not g["won"]]
    print("\n=== How much a game at the top is won or lost by ===")
    print(f"  median winning margin  {statistics.median(wins):9,.0f}")
    print(f"  median losing margin   {statistics.median(losses):9,.0f}")
    for cut in (500, 1000, 2500, 5000, 10000):
        near = sum(1 for m in losses if m <= cut)
        print(f"  losses inside {cut:6,d} coins: {near:5d} "
              f"({near / max(1, len(losses)):5.1%} of losses)")

    print("\n=== Upsets: a 2700+ team beaten by a much weaker opponent ===")
    upsets = [
        g for g in games
        if not g["won"] and (g.get("opponent_rating") or 0) < 2400
        and (g.get("rating") or 0) >= args.floor
    ]
    rated = [
        g for g in games
        if (g.get("opponent_rating") or 0) < 2400
        and (g.get("rating") or 0) >= args.floor
    ]
    if rated:
        share = len(upsets) / len(rated)
        print(f"  {len(upsets)} losses in {len(rated)} games against "
              f"sub-2400 opposition = {share:.1%}")

    print("\n=== Per team: reward when contested vs uncontested ===")
    print(f"  {'team':24s} {'rating':>7s} {'vs 2700+':>17s} "
          f"{'vs under 2400':>17s}")
    for row in board[:20]:
        mine = [g for g in games if g["team_id"] == row["team_id"]]
        hard = [g for g in mine if (g.get("opponent_rating") or 0) >= 2700]
        easy = [g for g in mine if (g.get("opponent_rating") or 0) < 2400]
        if len(hard) < 5 or len(easy) < 5:
            continue
        name = row["name"].encode("ascii", "replace").decode()[:22]
        print(f"  {name:24s} {row['rating']:7.1f} "
              f"{statistics.mean(g['reward'] for g in hard):9,.0f} "
              f"({sum(1 for g in hard if g['won']) / len(hard):4.0%}) "
              f"{statistics.mean(g['reward'] for g in easy):9,.0f} "
              f"({sum(1 for g in easy if g['won']) / len(easy):4.0%})")


if __name__ == "__main__":
    main()
