"""Land census of real ladder games, from exact replays.

For every step of a game (replayed exactly with tools.analysis.l2_land_fast)
this records, for the side under study:

* the code of each of its 100 tiles before the step's actions
  ('.' empty, '#' locked, 'x' weed, w/c/t/s/m plant by crop, G/M/S goose/
  cow/sheep, O/P empty coop/pasture);
* every unit's action and whether the engine applied it -- judged by running
  the engine's own `_apply_unit_action` on a duplicate of the state, in the
  engine's order and with its atomic-PLANT rule, and comparing the unit's
  position, the tile it stood on, its inventory, the shed and the seeds.

Games: L's live ladder games (submission 56582917), A's (56571049), and the
corpus games of top-30 teams (both the team and its opponent). One file per
game-side under rl/data/l2/land/census/.

    python -m tools.analysis.l2_land_census --set L
    python -m tools.analysis.l2_land_census --set A
    python -m tools.analysis.l2_land_census --set top30
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_land_fast import (CORPUS, corpus_record,  # noqa: E402
                                         live_paths, live_record, replay)

OUT = ROOT / "rl" / "data" / "l2" / "land" / "census"
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
CROP = {"WHEAT": "w", "CARROT": "c", "TOMATO": "t", "STRAWBERRY": "s", "MELON": "m"}
ANIMAL = {"GOOSE": "G", "COW": "M", "SHEEP": "S"}


def code(tile) -> str:
    if tile is None:
        return "."
    if tile == "LOCKED":
        return "#"
    if isinstance(tile, dict):
        k = tile.get("kind")
        if k == "WEED":
            return "x"
        if k == "PLANT":
            return CROP.get(tile.get("crop"), "?")
        if "animal" in tile and tile.get("animal"):
            return ANIMAL.get(tile["animal"], "?")
        if k == "COOP":
            return "O"
        if k == "PASTURE":
            return "P"
    return "?"


def pack(obj) -> str:
    return base64.b64encode(zlib.compress(json.dumps(obj, separators=(",", ":")).encode(), 9)).decode()


def unpack(blob: str):
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def classify(E, farm, private, action, day) -> list:
    """[(op, applied, x, y)] per existing unit, engine-exact."""
    if not isinstance(action, dict):
        action = {}
    farmer = action.get("farmer", ["PASS"])
    hands = action.get("hands", []) or []
    if not isinstance(hands, list):
        hands = []
    f = {"tiles": [[dict(t) if isinstance(t, dict) else t for t in row] for row in farm["tiles"]],
         "farmer": list(farm["farmer"]), "hands": [list(h) for h in farm["hands"]]}
    p = {"shed": dict(private["shed"]), "seeds": dict(private["seeds"]),
         "inventories": [dict(i) for i in private["inventories"]]}
    units = [farmer, *hands]
    demand = {}
    for a in units:
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
            demand[a[1]] = demand.get(a[1], 0) + 1
    seeds0 = private.get("seeds", {})
    blocked = {c for c, n in demand.items() if n > seeds0.get(c, 0)}
    out = []
    n_units = 1 + len(f["hands"])
    for idx in range(n_units):
        a = units[idx] if idx < len(units) else ["PASS"]
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT" and a[1] in blocked:
            a_eff = ["PASS"]
        else:
            a_eff = a
        op = a[0] if isinstance(a, list) and a and isinstance(a[0], str) else "PASS"
        pos = f["farmer"] if idx == 0 else f["hands"][idx - 1]
        x, y = int(pos[0]), int(pos[1])
        before = (x, y, dict(f["tiles"][y][x]) if isinstance(f["tiles"][y][x], dict) else f["tiles"][y][x],
                  dict(p["inventories"][idx]) if idx < len(p["inventories"]) else {},
                  dict(p["shed"]), dict(p["seeds"]))
        E._apply_unit_action(f, p, idx, a_eff, 10, day, 24, 100)
        pos2 = f["farmer"] if idx == 0 else f["hands"][idx - 1]
        after = (int(pos2[0]), int(pos2[1]), f["tiles"][y][x],
                 p["inventories"][idx] if idx < len(p["inventories"]) else {},
                 p["shed"], p["seeds"])
        applied = before != after
        if op == "PLANT" and len(a) >= 2 and a[1] in blocked:
            op = "PLANT!"   # cancelled by the atomic rule
        elif op == "PLANT" and len(a) >= 2:
            op = "PLANT:" + str(a[1])
        out.append((op, int(applied), x, y))
    return out


def census_game(seed: int, tapes: list, sides: tuple[int, ...]) -> dict:
    from kaggle_environments.envs.kaggriculture import kaggriculture as E
    timeline = {s: [[] for _ in range(100)] for s in sides}
    units = {s: [] for s in sides}
    quads = {s: [] for s in sides}
    g = None
    for t, g, acts in replay(seed, tapes):
        farms = g.obs.farms
        for s in sides:
            tiles = farms[s]["tiles"]
            for y in range(10):
                row = tiles[y]
                for x in range(10):
                    timeline[s][y * 10 + x].append(code(row[x]))
            if acts is not None:
                units[s].append(classify(E, farms[s], g.private(s), acts[s], t // 24))
            if t % 24 == 0:
                quads[s].append(list(farms[s]["unlocked_quadrants"]))
    money = g.money()
    return {"money": money,
            "sides": {s: {"timeline": pack(["".join(c) for c in timeline[s]]),
                          "units": pack(units[s]), "quadrants": quads[s]} for s in sides}}


def run_set(name: str, limit: int = 0) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []
    if name in ("L", "A"):
        sub = 56582917 if name == "L" else 56571049
        for p in live_paths(sub):
            jobs.append(("live", p))
    elif name == "top30":
        for p in sorted(CORPUS.glob("ep*.json")):
            try:
                r = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if int(r.get("team_rank") or 9999) <= 30:
                jobs.append(("corpus", p))
    if limit:
        jobs = jobs[:limit]
    t0 = time.time()
    done = 0
    for kind, p in jobs:
        dest = OUT / f"{name}_{p.stem}.json"
        if dest.exists():
            continue
        if kind == "live":
            seed, side, tp, r = live_record(p)
            meta = {"episode_id": r["episode_id"], "our_side": side, "live": r["rewards"],
                    "won": r.get("won"), "opponent": r.get("opponent"),
                    "opponent_rating": r.get("opponent_rating"), "seed": seed}
            res = census_game(seed, tp, (side, 1 - side))
            meta["exact"] = (res["money"][side] == r["rewards"]["us"]
                             and res["money"][1 - side] == r["rewards"]["them"])
            meta["focus"], meta["other"] = side, 1 - side
        else:
            seed, seat, tp, r = corpus_record(p)
            meta = {"episode_id": r["episode_id"], "team": r.get("source_team"),
                    "rank": r.get("team_rank"), "opponent": r.get("opponent"),
                    "opponent_rating": r.get("opponent_rating"), "seed": seed}
            res = census_game(seed, tp, (seat, 1 - seat))
            meta["exact"] = abs(res["money"][seat] - float((r.get("rewards") or {}).get("them") or 0)) < 1
            meta["focus"], meta["other"] = seat, 1 - seat
        res["meta"] = meta
        res["sides"] = {str(k): v for k, v in res["sides"].items()}
        dest.write_text(json.dumps(res), encoding="utf-8")
        done += 1
        if done % 10 == 0:
            print(f"  {name}: {done}/{len(jobs)} in {time.time() - t0:.0f}s", flush=True)
    print(f"{name}: {done} new games written, {len(jobs)} in set, {time.time() - t0:.0f}s")


def load_set(name: str) -> list[dict]:
    out = []
    for p in sorted(OUT.glob(f"{name}_ep*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", required=True, choices=("L", "A", "top30"))
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    run_set(a.set, a.limit)
