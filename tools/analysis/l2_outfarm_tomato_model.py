"""Out-farm autopsy, part 7: a deterministic model of what V219 would earn in each live game.

For every census game, rebuilds the tomato shortfall the market would have had
on days 26-29 WITHOUT our project (our own recorded tomato sales added back)
and prices 80 fertilized tomatoes sold 20 a day into it (the town eats
6 per tomato-eating shop instance and 1 at the centre per day while we sell).
Costs are the measured project costs: SE land 4,000, seeds 500, extra wages
~3,100, fertilizer and diverted fertilizer ~500 (8,100). The rival's tomato
revenue lost to our units (units it sold on days 26-29, priced before/after
our cumulative sales) is added for the margin view. The shop-draw reshuffle
that a land purchase causes is ignored (unpredictable, zero-mean).

    python -m tools.analysis.l2_outfarm_tomato_model
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_outfarm_census import load_rows  # noqa: E402

TOMATO_SHOPS = ("PIZZA_SHOP", "FARMERS_MARKET")
COST = 8100


def price(short: float) -> float:
    u = max(0.0, short) / 200.0
    return max(1.0, round(60 + 24 * (u + 8 * max(0.0, u - 1) ** 2)))


def n_shops(r, day) -> int:
    return sum(s in TOMATO_SHOPS for s in (r["shops_by_day"].get(str(day)) or []))


def model(r: dict) -> dict:
    us, them = r["sides"]["us"], r["sides"]["them"]
    fired = us["plants"].get("TOMATO", 0) >= 10 and 18 in us["tomato_plant_days"]
    ours_late = us["late_units"].get("TOMATO", 0) if fired else 0
    opp_late = them["late_units"].get("TOMATO", 0)
    rev = opp_loss = 0.0
    cum = 0
    for d in (26, 27, 28, 29):
        s_actual = r["tomato_short"].get(str(d))
        if s_actual is None:
            continue
        # add back our own recorded sales before day d (about 20 a day from day 26)
        s0 = s_actual + (min(ours_late, 20 * (d - 26)) if fired else 0)
        c = 6 * n_shops(r, d) + 1
        for k in range(20):
            s = s0 - cum + c * k / 20.0
            rev += price(s)
            cum += 1
        # the rival's units sold that day lose the price move our cumulative sales cause
        opp_d = opp_late / 5.0
        s_mid = s0 + c / 2.0
        opp_loss += opp_d * (price(s_mid) - price(s_mid - cum + 10))
    n18 = n_shops(r, 18)
    opp_plants = sum(1 for d in them["tomato_plant_days"] if 6 <= d <= 17)
    return {"episode_id": r["episode_id"], "agent": r["agent"], "n18": n18,
            "s432": r["tomato_short_432"], "fired": fired, "rev": rev, "own": rev - COST,
            "margin": rev - COST + opp_loss, "opp_loss": opp_loss, "opp_plants": opp_plants,
            "opp_late": opp_late, "mirror": r["mirror_until"] >= 17,
            "f26": r["tomato_short_432"] + 8 * (6 * n18 + 1) - 6 * opp_plants,
            "opponent": r["opponent"]}


def l_gate(m):
    return m["s432"] >= 83 and (m["n18"] >= 3 or (m["n18"] >= 2 and m["s432"] >= 120))


def main() -> None:
    rows = [model(r) for r in load_rows()]
    print(f"{len(rows)} games; model value of firing (own / margin), 80 units, cost {COST}")
    print(f"  {'ep':>10} {'ag':2} {'n18':>3} {'s432':>4} {'f26':>4} {'oppP':>4} {'oppLate':>7} "
          f"{'L':>1} {'fired':>5} {'rev':>7} {'own':>7} {'margin':>7}")
    for m in sorted(rows, key=lambda m: (m["n18"], m["s432"])):
        if m["n18"] < 2 and m["s432"] < 150:
            continue
        print(f"  {m['episode_id']:>10} {m['agent']:2} {m['n18']:>3} {m['s432']:>4} {m['f26']:>4} "
              f"{m['opp_plants']:>4} {m['opp_late']:>7} {int(l_gate(m)):>1} {int(m['fired']):>5} "
              f"{m['rev']:>7.0f} {m['own']:>+7.0f} {m['margin']:>+7.0f}  {str(m['opponent'])[:16]}")
    rules = {"never": lambda m: False, "A gate": lambda m: m["s432"] >= 83 and m["n18"] >= 3,
             "L gate": l_gate}
    for s in (220, 230, 240, 250, 260, 270, 280):
        rules[f"f26>={s}"] = (lambda s: lambda m: m["f26"] >= s)(s)
    print("\n  rule totals over all games (model):")
    for name, rule in rules.items():
        pick = [m for m in rows if rule(m)]
        print(f"    {name:10s} fires {len(pick):3d}  own {sum(m['own'] for m in pick):+9,.0f}  "
              f"margin {sum(m['margin'] for m in pick):+9,.0f}  "
              f"negative-own firings {sum(m['own'] < 0 for m in pick)}")


if __name__ == "__main__":
    main()
