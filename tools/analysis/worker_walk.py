"""How G's workers move, and where its pens end up. Facts, not opinions.

usage: walk.py EPISODE SEAT SEED
"""
import sys, json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import candidates.candidate_g as G
from tools.eval import inspect_g
from tools.data.profile_tapes import TAPES

MOVES = ("NORTH", "SOUTH", "EAST", "WEST")
SHED = [(4, 4), (5, 4), (4, 5), (5, 5)]
dist = lambda x, y: min(abs(x-a)+abs(y-b) for a, b in SHED)
man = lambda a, b: abs(a[0]-b[0]) + abs(a[1]-b[1])

ep, seat, seed = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
OV = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
for k, v in OV.items():
    setattr(G, k, v)
print("overrides", OV)
intents = {}
per_step = {}
orig_step, orig_agent = G.step_toward, G.agent

def step_wrapper(start, cell, act):
    intents.setdefault(tuple(start), []).append((tuple(cell), list(act)))
    return orig_step(start, cell, act)

def agent_wrapper(obs):
    intents.clear()
    act = orig_agent(obs)
    step = int(obs.get("step", 0))
    farm = G._farm(obs)
    pos = G._positions(farm)
    workers = [act.get("farmer")] + list(act.get("hands") or [])
    rows = []
    for w, (p, a) in enumerate(zip(pos, workers)):
        a = a or ["PASS"]
        target = None
        if a[0] in MOVES and intents.get(tuple(p)):
            target = intents[tuple(p)][0][0]
        rows.append({"w": w, "at": tuple(p), "act": list(a), "target": target})
    per_step[step] = rows
    return act

G.step_toward, G.agent = step_wrapper, agent_wrapper
try:
    env, _ = inspect_g.play("candidates.candidate_g:agent", OV,
                            str(TAPES / f"live_{ep}.json"), seed, seat)
finally:
    G.step_toward, G.agent = orig_step, orig_agent

print(f"G {env.state[seat].reward:,.0f} vs {env.state[1-seat].reward:,.0f}")

# 1. What worker turns are spent on.
kinds = Counter()
moves_total = moves_bad = 0
for step, rows in per_step.items():
    for r in rows:
        op = r["act"][0]
        kinds["move" if op in MOVES else ("pass" if op == "PASS" else "work")] += 1
        if op in MOVES and r["target"]:
            moves_total += 1
            d = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}[op]
            after = (r["at"][0] + d[0], r["at"][1] + d[1])
            if man(after, r["target"]) >= man(r["at"], r["target"]):
                moves_bad += 1
total = sum(kinds.values())
print(f"\nworker turns: {total:,}")
for k, v in kinds.most_common():
    print(f"  {k:5s} {v:6,d}  {v/total:5.1%}")
print(f"moves with a known target: {moves_total:,}; moves NOT reducing the "
      f"distance to it: {moves_bad:,} ({moves_bad/max(1,moves_total):.1%})")

# 2. Do workers keep changing their mind? Target churn per worker.
last_target = {}
churn = switches = 0
for step in sorted(per_step):
    for r in per_step[step]:
        if r["act"][0] in MOVES and r["target"]:
            prev = last_target.get(r["w"])
            if prev is not None and prev != r["target"]:
                switches += 1
            last_target[r["w"]] = r["target"]
            churn += 1
        elif r["act"][0] not in MOVES:
            last_target.pop(r["w"], None)
print(f"consecutive travelling turns: {churn:,}; of those the destination "
      f"changed mid-walk {switches:,} times ({switches/max(1,churn):.1%})")

# 3. Layout at the end: pens, crops, empties.
steps = env.steps
def tiles_at(i):
    return steps[i][0]["observation"]["farms"][seat]["tiles"]
for day in (10, 20, 29):
    i = min(day * 24 + 23, len(steps) - 1)
    pens, wheat, crop, empty, owned = [], [], [], [], 0
    for y, row in enumerate(tiles_at(i)):
        for x, t in enumerate(row):
            if t == "LOCKED":
                continue
            owned += 1
            if t is None:
                empty.append(dist(x, y))
            elif isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE"):
                pens.append(dist(x, y))
            elif isinstance(t, dict) and "animal" in t:
                pens.append(dist(x, y))
            elif isinstance(t, dict) and t.get("kind") == "PLANT":
                (wheat if t["crop"] == "WHEAT" else crop).append(dist(x, y))
    f = lambda v: f"{len(v):2d} @ {sum(v)/len(v):4.1f}" if v else " 0 @  -  "
    print(f"day {day:2d}: owned {owned:3d} | pens+animals {f(pens)} | wheat "
          f"{f(wheat)} | crops {f(crop)} | EMPTY {f(empty)} "
          f"({len(empty)/owned:.0%} of our land)")
