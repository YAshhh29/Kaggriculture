"""What is different about the live games we lose.

Every prior diagnosis in this project compared our agents against frozen
recordings, and the live record showed that instrument inverts the very
ordering it was used to make: the panel put Candidate F 18.7 points above
Candidate D, and live D holds ~1744 against F's ~1687.

These are real games against opponents that could respond to us. For each
one `tools/data/fetch_our_games.py` keeps both farms day by day -- money,
herd, planted tiles, hands, quadrants -- plus the market inventory of all
nine goods and our own action mix.

The questions it answers are the ones a fix has to be built on:

* **when** does the gap open, and is it the same day in every loss;
* **what does the winner have that we do not** at that moment -- more
  animals, more ground, more crew, or simply more money;
* **what is the market doing** while it happens.

    python -m tools.data.analyse_our_games
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GAMES = ROOT / "rl" / "data" / "our_games.jsonl"
GOODS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")
MARKS = (5, 8, 10, 12, 15, 18, 21, 25, 29)


def load(label: str | None) -> list[dict[str, Any]]:
    rows = [json.loads(x) for x in
            GAMES.read_text(encoding="utf-8").splitlines()]
    return [r for r in rows if not label or r.get("label") == label]


def at(row: dict[str, Any], day: int) -> dict[str, Any] | None:
    for entry in row.get("days") or []:
        if entry["day"] == day:
            return entry
    return None


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def block(rows: list[dict[str, Any]], title: str) -> None:
    if not rows:
        print(f"\n  {title}: none")
        return
    print(f"\n  === {title} ({len(rows)} games) ===")
    print(f"    our reward {mean([r['our_reward'] for r in rows]):9,.0f}   "
          f"theirs {mean([r['their_reward'] for r in rows]):9,.0f}   "
          f"opponent rating "
          f"{mean([r['opponent_rating'] for r in rows]):6.0f}")
    print(f"    {'day':>4} {'our money':>10} {'their money':>12} "
          f"{'gap':>10} | {'our herd':>9} {'their herd':>11} "
          f"| {'our plant':>10} {'their plant':>12}")
    for day in MARKS:
        cells = [at(r, day) for r in rows]
        cells = [c for c in cells if c and c["us"] and c["them"]]
        if not cells:
            continue
        om = mean([c["us"]["money"] for c in cells])
        tm = mean([c["them"]["money"] for c in cells])
        print(f"    {day:>4} {om:10,.0f} {tm:12,.0f} {om - tm:+10,.0f} | "
              f"{mean([c['us']['herd'] for c in cells]):9.1f} "
              f"{mean([c['them']['herd'] for c in cells]):11.1f} | "
              f"{mean([c['us']['planted'] for c in cells]):10.1f} "
              f"{mean([c['them']['planted'] for c in cells]):12.1f}")
    end = [at(r, 29) for r in rows]
    end = [c for c in end if c]
    if end:
        print("    market at day 29: " + "  ".join(
            f"{g} {mean([c['market'][g] for c in end]):+6.0f}"
            for g in GOODS))
    verbs: Counter[str] = Counter()
    for row in rows:
        verbs.update(row.get("verbs") or {})
    total = sum(verbs.values()) or 1
    top = [(k, v) for k, v in verbs.most_common(10)
           if k not in ("NORTH", "SOUTH", "EAST", "WEST")][:7]
    print(f"    our actions: " + "  ".join(
        f"{k} {v / len(rows):.0f}" for k, v in top)
        + f"   (PASS {verbs.get('PASS', 0) / len(rows):.0f})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default=None)
    args = parser.parse_args()
    rows = load(args.label)
    if not rows:
        raise SystemExit("no traces yet")

    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_label[row.get("label") or "?"].append(row)

    for label in sorted(by_label):
        group = by_label[label]
        wins = [r for r in group if r["won"]]
        losses = [r for r in group if not r["won"]]
        print(f"\n################ {label}: {len(group)} live games, "
              f"{len(wins)} won ################")
        block(wins, "WINS")
        block(losses, "LOSSES")


if __name__ == "__main__":
    main()
