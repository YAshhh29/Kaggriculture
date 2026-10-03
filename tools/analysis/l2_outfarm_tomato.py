"""Out-farm autopsy, part 6: what the day-18 tomato project (V219) is worth, game by game.

Needs two counterfactual runs of every live game (l2_outfarm_counter):
    --factory stack.l2_outfarm:v219_on  --label v219on   (fires whenever physically possible)
    --factory stack.l2_outfarm:v219_off --label v219off  (never fires)
Both are Agent L apart from the decision, so on - off is the value of firing in
that game, in our own score and in the margin. Features are read at step 432
(when V219 decides) from the ON run's books: tomato shortfall, tomato-eating
shop instances, the rival's standing tomato plants, whether the farms mirror.

Gate rules are then scored by the value they collect relative to never firing,
and relative to L's live gate (3 tomato shops, or 2 with shortfall >= 120).

    python -m tools.analysis.l2_outfarm_tomato
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "rl" / "data" / "l2" / "outfarm"
TOMATO_SHOPS = ("PIZZA_SHOP", "FARMERS_MARKET")


def tomato_price(short: float) -> float:
    u = max(0.0, short) / 200.0
    return max(1.0, round(60 + 24 * (u + 8 * max(0.0, u - 1) ** 2)))


def _rows(label: str) -> dict:
    path = OUT / f"counter_{label}_us.jsonl"
    rows = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            rows[r["episode_id"]] = r
    return rows


def features(episode: int, label: str = "v219on") -> dict | None:
    path = OUT / f"books_{label}_us" / f"ep{episode}.json"
    if not path.exists():
        return None
    g = json.loads(path.read_text(encoding="utf-8"))
    side = g["our_side"]
    us, them = g["books"][side], g["books"][1 - side]
    shops = g["shops_by_day"].get("18") or []
    c_us = us["census"].get("17") or {}
    c_th = them["census"].get("17") or {}
    fired = (sum(1 for s, c, x, y in us["plant"] if c == "TOMATO" and s // 24 == 18) >= 10)
    opp_tomato_sold_before = sum(1 for s, i, p in them["sales"] if i == "TOMATO" and s < 432)
    opp_tomato_after = sum(1 for s, i, p in them["sales"] if i == "TOMATO" and s >= 432)
    mirror = 0
    for d in range(18):
        a, b = us["census"].get(str(d)) or {}, them["census"].get(str(d)) or {}
        if a.get("plants") == b.get("plants") and a.get("animals") == b.get("animals"):
            mirror = d
        else:
            break
    return {"episode_id": episode, "short432": -g["market_inv"][432]["TOMATO"],
            "n18": sum(s in TOMATO_SHOPS for s in shops), "shops18": shops,
            "money432": c_us.get("money"), "quads432": len(c_us.get("quadrants", [])),
            "opp_tomato_plants": (c_th.get("plants") or {}).get("TOMATO", 0),
            "opp_tomato_sold_before": opp_tomato_sold_before,
            "opp_tomato_after": opp_tomato_after, "mirror17": mirror >= 17,
            "fired_on": fired,
            "our_tomato_rev": sum(p for s, i, p in us["sales"] if i == "TOMATO"),
            "our_tomato_units": sum(1 for s, i, p in us["sales"] if i == "TOMATO")}


def l_gate(f: dict) -> bool:
    return f["short432"] >= 83 and (f["n18"] >= 3 or (f["n18"] >= 2 and f["short432"] >= 120))


def a_gate(f: dict) -> bool:
    return f["short432"] >= 83 and f["n18"] >= 3


def forecast26(f: dict, per_plant: float = 6.0) -> float:
    """Shortfall expected when our first tomatoes arrive (day 26)."""
    return f["short432"] + 8 * (6 * f["n18"] + 1) - per_plant * f["opp_tomato_plants"]


def _l_outcomes() -> dict:
    """Agent L's own result in each game: live for L's games, replayed for A's."""
    from tools.analysis.l2_outfarm_census import load_rows
    out = {}
    for r in load_rows():
        if r["agent"] == "L":
            out[r["episode_id"]] = {"us": r["us"], "them": r["them"], "margin": r["margin"]}
    path = ROOT / "rl" / "data" / "live_replays" / "l-on-a-live-games.json"
    for g in json.loads(path.read_text(encoding="utf-8"))["games"]:
        if "error" not in g and g["episode_id"] not in out:
            out[g["episode_id"]] = {"us": g["reward"]["us"], "them": g["reward"]["them"],
                                    "margin": g["reward"]["us"] - g["reward"]["them"]}
    return out


def main() -> None:
    on, off = _rows("v219on"), _rows("v219off")
    lres = _l_outcomes()
    table = []
    for e in sorted(set(on) | set(off)):
        f = features(e, "v219on") or features(e, "v219off")
        if f is None:
            continue
        fires_l = l_gate(f)
        a = on.get(e) or (lres.get(e) if fires_l else None)
        b = off.get(e) or (lres.get(e) if not fires_l else None)
        if a is None or b is None:
            continue
        if e not in on:
            f["fired_on"] = True
        f["own"] = a["us"] - b["us"]
        f["margin"] = a["margin"] - b["margin"]
        f["opp"] = a["them"] - b["them"]
        f["off_margin"], f["on_margin"] = b["margin"], a["margin"]
        f["opponent"] = (on.get(e) or off.get(e))["opponent"]
        table.append(f)
    fired = [f for f in table if f["fired_on"]]
    print(f"{len(table)} band games with both outcomes; V219 physically possible in {len(fired)}")
    print(f"  {'ep':>10} {'n18':>3} {'s432':>5} {'f26':>5} {'oppT':>4} {'mir':>3} "
          f"{'L':>2} {'own':>7} {'margin':>7} {'opp':>7} {'off_m':>7} {'on_m':>7}  opponent")
    for f in sorted(fired, key=lambda f: (f["n18"], f["short432"])):
        print(f"  {f['episode_id']:>10} {f['n18']:>3} {f['short432']:>5} {forecast26(f):>5.0f} "
              f"{f['opp_tomato_plants']:>4} {int(f['mirror17']):>3} {int(l_gate(f)):>2} "
              f"{f['own']:>+7.0f} {f['margin']:>+7.0f} {f['opp']:>+7.0f} {f['off_margin']:>+7.0f} "
              f"{f['on_margin']:>+7.0f}  {str(f['opponent'])[:18]}")
    rules = {"never": lambda f: False, "always": lambda f: True,
             "A gate (3 shops)": a_gate, "L gate (live)": l_gate}
    for s in (200, 220, 240, 250, 260, 270, 280, 300):
        rules[f"forecast26 >= {s}"] = (lambda s: lambda f: forecast26(f) >= s)(s)
    print(f"\n  rule scores over the {len(fired)} band games where V219 can fire")
    for name, rule in rules.items():
        pick = [f for f in fired if rule(f)]
        own = sum(f["own"] for f in pick)
        mar = sum(f["margin"] for f in pick)
        wins = sum((f["on_margin"] if rule(f) else f["off_margin"]) > 0 for f in fired)
        print(f"    {name:22s} fires {len(pick):3d}: own {own:+9,.0f}  margin {mar:+9,.0f}  "
              f"wins {wins}/{len(fired)}")


if __name__ == "__main__":
    main()
