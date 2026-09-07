"""What real Kaggle sides actually do in their first ten days.

Reads the cached replay corpus indexed by
`rl/data/candidate_d_corpus_index.jsonl` -- 245 episodes, 490 sides -- and
reports the opening of the strongest and the median sides side by side.

The result is the interesting part, and it is not what anyone expected:
**the whole field opens the same way.** The top twenty sides average
141,731 coins and the middle twenty average 77,772, and their first ten
days are almost indistinguishable -- four animals standing by day one,
twelve by day ten, the second quadrant on day six, and roughly 34 wheat,
25 strawberry and 12 melon planted. The opening is a solved problem that
everyone has solved, so it is **not** where rank is won.

It is, however, where Agent E was losing: E stood 0 animals on day one
and 3 on day eight against the field's 4 and 10.

Transplanting the book into E was tried and cost 11,500 coins, because
buying four animals on day one consumes exactly the cash E needs for its
day-one second quadrant, and that quadrant measured +8,000 on its own. An
opening is not portable between architectures -- it only pays alongside
the rest of the play it was recorded with.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(r"C:\Users\Oyash\Desktop\Kaggriculture")
CACHE = ROOT / "kaggle_cache"
IDX = ROOT / "rl" / "data" / "candidate_d_corpus_index.jsonl"


def rewards_index():
    """(reward, replay_file, player) for both sides of every indexed episode."""
    out = []
    for line in IDX.read_text().splitlines():
        d = json.loads(line)
        if d.get("type") != "episode":
            continue
        f = d["replay_file"]; ours = int(d["our_side"])
        out.append((float(d["our_reward"]), f, ours))
        out.append((float(d["opponent_reward"]), f, 1 - ours))
    return out


def opening(steps, p, upto_day=10):
    buys = Counter(); plants = Counter(); hires = 0; land_days = []
    herd = {}; money = {}; plant_n = {}
    prev_q = 1
    for i, st in enumerate(steps):
        obs = st[0].get("observation") or {}
        day = int(obs.get("day", 0))
        if day > upto_day:
            break
        act = st[p].get("action") if p < len(st) else None
        if isinstance(act, dict):
            for o in (act.get("market") or []):
                if not (isinstance(o, list) and o):
                    continue
                if o[0] == "BUY_ANIMAL" and len(o) >= 3:
                    buys[str(o[1])] += int(o[2])
                elif o[0] == "BUY_SEED" and len(o) >= 3:
                    buys["seed:" + str(o[1])] += int(o[2])
                elif o[0] == "HIRE":
                    hires += 1
            for u in [act.get("farmer")] + list(act.get("hands") or []):
                if isinstance(u, list) and len(u) >= 2 and u[0] == "PLANT":
                    plants[str(u[1])] += 1
        farms = obs.get("farms") or []
        if p < len(farms) and isinstance(farms[p], dict):
            f = farms[p]; tl = f.get("tiles") or []
            q = len(f.get("unlocked_quadrants") or [])
            if q > prev_q:
                land_days.append(day); prev_q = q
            if i % 24 == 0:
                herd[day] = sum(1 for r in tl for t in r
                                if isinstance(t, dict) and "animal" in t)
                money[day] = int(f.get("money", 0))
                plant_n[day] = sum(1 for r in tl for t in r
                                   if isinstance(t, dict) and t.get("kind") == "PLANT")
    return buys, plants, hires, land_days, herd, money, plant_n


def report(rows, label):
    agg_h = defaultdict(list); agg_m = defaultdict(list); agg_p = defaultdict(list)
    buys = Counter(); plants = Counter(); hires = []; lands = []
    by_file = defaultdict(list)
    for reward, f, p in rows:
        by_file[f].append(p)
    n = 0
    for f, players in by_file.items():
        path = CACHE / f
        if not path.exists():
            continue
        steps = json.loads(path.read_text()).get("steps") or []
        for p in players:
            b, pl, h, ld, hd, md, pd = opening(steps, p)
            buys.update(b); plants.update(pl); hires.append(h); lands.append(ld)
            for d, v in hd.items(): agg_h[d].append(v)
            for d, v in md.items(): agg_m[d].append(v)
            for d, v in pd.items(): agg_p[d].append(v)
            n += 1
        del steps
    if not n:
        return
    print(f"\n=== {label}  ({n} sides, mean reward {sum(r[0] for r in rows)/len(rows):,.0f}) ===")
    print(f"  animals bought by day 10: "
          f"{dict(sorted((k, round(v/n,1)) for k,v in buys.items() if not k.startswith('seed')))}")
    print(f"  seeds bought by day 10  : "
          f"{dict(sorted((k[5:], round(v/n,1)) for k,v in buys.items() if k.startswith('seed')))}")
    print(f"  PLANT actions by day 10 : {dict(sorted((k, round(v/n,1)) for k,v in plants.items()))}")
    print(f"  hire orders by day 10   : {sum(hires)/n:.0f}")
    first = sorted(l[0] for l in lands if l)
    second = sorted(l[1] for l in lands if len(l) > 1)
    print(f"  2nd quadrant day (median): {first[len(first)//2] if first else '-'}  "
          f"({len(first)}/{n} bought one by day 10)")
    print(f"  3rd quadrant day (median): {second[len(second)//2] if second else '-'}  "
          f"({len(second)}/{n})")
    for agg, name in ((agg_h, "herd"), (agg_p, "plants"), (agg_m, "money")):
        print(f"  {name:7s} " + " ".join(
            f"d{d}:{sum(agg[d])/len(agg[d]):.0f}" for d in sorted(agg) if d <= 10))


if __name__ == "__main__":
    rows = rewards_index()
    rows.sort(key=lambda r: -r[0])
    print(f"{len(rows)} sides indexed | best {rows[0][0]:,.0f} | "
          f"median {rows[len(rows)//2][0]:,.0f} | worst {rows[-1][0]:,.0f}")
    report(rows[:20], "TOP 20 SIDES")
    mid = len(rows)//2
    report(rows[mid-10:mid+10], "MIDDLE 20 SIDES")
