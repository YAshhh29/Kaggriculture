"""Endgame study tables from the exact replay logs.

Reads the logs written by tools.analysis.l2_endgame_bench (our 148 live A/L
games, rl/data/l2/endgame/logs), tools.analysis.l2_endgame_corpus (1312 real
top-team games, corpus_logs) and prints / saves:

  * results and close-game counts of A and L on the ladder;
  * days 25-29 SELL revenue per item, us vs opponent, units and average price;
  * revenue share by consumption phase (step % 4; phase 0 sells BEFORE the
    town eats at that step) and by hour of day 29;
  * goods destroyed by overflow (night drop / DROP into a full shed);
  * the same for the corpus teams by rating band.

    python -m tools.analysis.l2_endgame_study > rl/data/l2/endgame/study.txt
"""

from __future__ import annotations

import collections
import glob
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rl.market_front import _mf_price  # noqa: E402
from tools.analysis.l2_endgame_log import ITEMS, OUT  # noqa: E402


def summarize(g, who):
    s = {"final": g["replay"]["us" if who == 0 else "them"],
         "d25": g["money"][25][who], "d29": g["money"][29][who]}
    rev, units = collections.Counter(), collections.Counter()
    h29, phase = collections.Counter(), collections.Counter()
    for step, w, op, item, n, r, _p1, _p2 in g["sales"]:
        if w != who or op != "SELL" or step < 600:
            continue
        rev[item] += r
        units[item] += n
        if step >= 696:
            h29[step - 696] += r
        phase[step % 4] += r
    inv0 = g.get("inv_from", 0)
    lost = 0.0
    for step, w, item, n, _kind in g["discards"]:
        if w == who and step >= 480 and item in ITEMS:
            t = min(step + 1, 718) - inv0
            inv = g["inv"][t][ITEMS.index(item)] if 0 <= t < len(g["inv"]) else 10000
            lost += n * _mf_price(item, inv)
    s.update(rev=rev, units=units, h29=h29, phase=phase, lost=lost)
    return s


def table(groups):
    lines = [f"{'group':18s} {'n':>4s} {'d25 $':>7s} {'d29 $':>7s} {'final':>7s} "
             f"{'d25-29 rev':>10s} {'day29 rev':>9s} {'overflow $':>10s}"]
    for name, S in groups.items():
        lines.append(
            f"{name:18s} {len(S):4d} {st.median(x['d25'] for x in S):7.0f} "
            f"{st.median(x['d29'] for x in S):7.0f} {st.median(x['final'] for x in S):7.0f} "
            f"{st.mean(sum(x['rev'].values()) for x in S):10.0f} "
            f"{st.mean(sum(x['h29'].values()) for x in S):9.0f} {st.mean(x['lost'] for x in S):10.0f}")
    lines.append("\ndays 25-29 SELL revenue per game (mean) @ average price")
    lines.append(f"{'group':18s} " + " ".join(f"{i[:10]:>12s}" for i in ITEMS))
    for name, S in groups.items():
        cells = []
        for i in ITEMS:
            u = sum(x["units"][i] for x in S)
            r = sum(x["rev"][i] for x in S)
            cells.append(f"{r / len(S):6.0f}@{(r / u if u else 0):5.0f}")
        lines.append(f"{name:18s} " + " ".join(f"{c:>12s}" for c in cells))
    lines.append("\nrevenue share by step % 4 (days 25-29) | day-29 revenue share by hour (>=3%)")
    for name, S in groups.items():
        ph, hs = collections.Counter(), collections.Counter()
        for x in S:
            ph.update(x["phase"])
            hs.update(x["h29"])
        tp, th = sum(ph.values()), sum(hs.values())
        lines.append(f"{name:18s} " + " ".join(f"ph{p}:{100 * ph[p] / tp:3.0f}%" for p in range(4))
                     + " | " + " ".join(f"h{h}:{100 * hs[h] / th:.0f}" for h in range(23)
                                        if hs[h] / th >= 0.03))
    return "\n".join(lines)


def main() -> None:
    ours = [json.load(open(p, encoding="utf-8")) for p in glob.glob(str(OUT / "logs" / "*.json"))]
    corpus = [json.load(open(p, encoding="utf-8"))
              for p in glob.glob(str(OUT / "corpus_logs" / "*.json"))]
    print("== results of our live games (exact replays) ==")
    for agent in ("A", "L"):
        G = [g for g in ours if g["agent"] == agent]
        m = [g["live"]["us"] - g["live"]["them"] for g in G]
        print(f"{agent}: {len(G)} games, won {sum(x > 0 for x in m)}, tied {sum(x == 0 for x in m)}, "
              f"lost {sum(x < 0 for x in m)}; |margin| < 500: {sum(abs(x) < 500 for x in m)}, "
              f"< 2000: {sum(abs(x) < 2000 for x in m)}; losses {sorted(round(x) for x in m if x < 0)}")
        left = sum(sum(g["leftover"][0]["shed"].values()) + sum(g["leftover"][0]["hands"].values())
                   for g in G)
        print(f"   goods left unsold at the end (all games): {left}")
    groups = {
        "A (us)": [summarize(g, 0) for g in ours if g["agent"] == "A"],
        "L (us)": [summarize(g, 0) for g in ours if g["agent"] == "L"],
        "A/L opponents": [summarize(g, 1) for g in ours],
    }
    if corpus:
        groups.update({
            "corpus 2600-2700": [summarize(g, 0) for g in corpus
                                 if 2600 <= (g.get("team_score") or 0) < 2700],
            "corpus 2700-2800": [summarize(g, 0) for g in corpus
                                 if 2700 <= (g.get("team_score") or 0) < 2800],
            "corpus 2800+": [summarize(g, 0) for g in corpus if (g.get("team_score") or 0) >= 2800],
        })
    print("\n== endgame money (medians), revenue (means), overflow losses days 20-29 ==")
    print(table(groups))
    print("\n== goods destroyed by overflow, our side, units per night-day and item ==")
    c = collections.Counter()
    for g in ours:
        for step, who, item, n, kind in g["discards"]:
            if who == 0:
                c[(step // 24, item, kind)] += n
    for (d, item, kind), n in sorted(c.items()):
        print(f"  day {d:2d} {kind:5s} {item:11s} {n:4d} units over {len(ours)} games")


if __name__ == "__main__":
    main()
