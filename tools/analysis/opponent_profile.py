"""What the agents who beat G actually do, from G's own 38 ladder games.

Reads the action tapes only (no engine), so counts are what each side
ORDERED. Market orders can fail on cash or stock, and PLANT fails without
seed, so treat these as intent, not outcome.
"""
import json, glob, statistics
from collections import Counter, defaultdict
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.data.extract_live_tapes import unpack

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
SUB = int(sys.argv[1]) if len(sys.argv) > 1 else 56272104

def profile(actions):
    out = {"hire_by_day": Counter(), "plant": Counter(), "plant_day0_2": Counter(),
           "sell_units": Counter(), "buy_seed": Counter(), "animals": Counter(),
           "buy_wheat": 0, "mix": Counter(), "first_orders": [], "land_days": []}
    for step, a in enumerate(actions):
        if not isinstance(a, dict):
            continue
        day = step // 24
        for u in [a.get("farmer")] + list(a.get("hands") or []):
            if not isinstance(u, list) or not u:
                continue
            op = u[0]
            out["mix"]["move" if op in MOVES else "pass" if op == "PASS" else "work"] += 1
            if op == "PLANT" and len(u) > 1:
                out["plant"][u[1]] += 1
                if day <= 2:
                    out["plant_day0_2"][u[1]] += 1
        for o in a.get("market") or []:
            if not isinstance(o, list) or not o:
                continue
            if len(out["first_orders"]) < 14 and day == 0:
                out["first_orders"].append((step, o))
            if o[0] == "HIRE":
                out["hire_by_day"][day] += 1
            elif o[0] == "BUY_LAND":
                out["land_days"].append(day)
            elif len(o) > 2:
                q = int(o[2])
                if o[0] == "SELL":
                    out["sell_units"][o[1]] += q
                elif o[0] == "BUY_SEED":
                    out["buy_seed"][o[1]] += q
                elif o[0] == "BUY_ANIMAL":
                    out["animals"][o[1]] += q
                elif o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
                    out["buy_wheat"] += q
    return out

games = []
for p in sorted(glob.glob(str(ROOT / "rl/data/our_live_tapes/ep*.json"))):
    r = json.loads(Path(p).read_text(encoding="utf-8"))
    if r.get("submission") != SUB:
        continue
    games.append((r, profile(unpack(r["our_actions_zlib_b64"])),
                  profile(unpack(r["opp_actions_zlib_b64"]))))

lost = [g for g in games if not g[0].get("won")]
won = [g for g in games if g[0].get("won")]
print(f"{len(games)} games: {len(won)} won, {len(lost)} lost\n")

def med(rows, f):
    v = [f(x) for x in rows]
    return statistics.median(v) if v else 0

for label, rows in (("ALL 38", games), ("the 21 G LOST", lost)):
    print(f"=== {label}: medians, G vs opponent")
    print(f"  hands hired all season   {med(rows, lambda g: sum(g[1]['hire_by_day'].values())):5.0f} vs "
          f"{med(rows, lambda g: sum(g[2]['hire_by_day'].values())):5.0f}")
    for d in (0, 1, 2, 5, 10, 20):
        print(f"    hires on day {d:<2d}         {med(rows, lambda g: g[1]['hire_by_day'][d]):5.0f} vs "
              f"{med(rows, lambda g: g[2]['hire_by_day'][d]):5.0f}")
    for what in ("move", "work", "pass"):
        print(f"  worker turns {what:5s}       {med(rows, lambda g: g[1]['mix'][what]):5.0f} vs "
              f"{med(rows, lambda g: g[2]['mix'][what]):5.0f}")
    for crop in ("WHEAT", "CARROT", "MELON", "STRAWBERRY", "TOMATO"):
        print(f"  PLANT {crop:11s}      {med(rows, lambda g: g[1]['plant'][crop]):5.0f} vs "
              f"{med(rows, lambda g: g[2]['plant'][crop]):5.0f}"
              f"   (days 0-2: {med(rows, lambda g: g[1]['plant_day0_2'][crop]):.0f} vs "
              f"{med(rows, lambda g: g[2]['plant_day0_2'][crop]):.0f})")
    for a in ("GOOSE", "COW", "SHEEP"):
        print(f"  BUY_ANIMAL {a:10s} {med(rows, lambda g: g[1]['animals'][a]):5.0f} vs "
              f"{med(rows, lambda g: g[2]['animals'][a]):5.0f}")
    print(f"  BUY_PRODUCT WHEAT units  {med(rows, lambda g: g[1]['buy_wheat']):5.0f} vs "
          f"{med(rows, lambda g: g[2]['buy_wheat']):5.0f}")
    print(f"  land bought on days      {sorted(Counter(tuple(sorted(g[1]['land_days'])) for g in rows).most_common(1)[0][0])} vs "
          f"{sorted(Counter(tuple(sorted(g[2]['land_days'])) for g in rows).most_common(1)[0][0])}")
    print()

print("=== the opening of the 3 opponents that beat G hardest")
for r, mine, opp in sorted(games, key=lambda g: g[0]['rewards']['us'] - g[0]['rewards']['them'])[:3]:
    print(f"  ep{r['episode_id']} {r.get('opponent','?')} rating {r.get('opponent_rating',0):.0f}: "
          f"G {r['rewards']['us']:,.0f} vs {r['rewards']['them']:,.0f}")
    for step, o in opp["first_orders"][:12]:
        print(f"      t{step:02d} {o}")
