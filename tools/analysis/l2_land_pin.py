"""Replay our live games against a new agent with the nights pinned to the live game.

Each night the engine draws one random number per EMPTY tile of both farms
(weeds) and then the next town shop, from one stream. A layer that plants a
tile the live game left empty shifts that stream: different weeds on both
farms and, every third night, a different shop -- for a tomato layer, a
different tomato demand. That is noise the layer did not cause, and it is
large (tools/eval/fair_town.py documents a 17k swing from one shop).

This driver first replays the live game from both tapes and records every
night's per-tile draws and the shop list. Then, playing an agent in our seat
against the opponent's tape, it installs an engine patch that gives each
empty tile the draw it had live (a fresh, seeded draw only for tiles that
were not empty live) and restores the live shop list. With the live agent
the game is the live game (verified to the coin); with a new agent, only
the agent's own effects differ.

The engine is driven directly (tools.analysis.l2_land_fast), the agent gets
a deep-copied observation each turn, and one process plays games in turn.

    python -m tools.analysis.l2_land_pin run --factory stack.l2_null:build --label L --v219
    python -m tools.analysis.l2_land_pin run --factory rl.l2_land:build --label annex --v219
    python -m tools.analysis.l2_land_pin compare L annex
"""

from __future__ import annotations

import argparse
import copy
import importlib
import json
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_land_fast import CONFIG, FastGame, live_paths, live_record  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "land" / "replays"
PASS = {"farmer": ["PASS"], "hands": [], "market": []}


# ---------------------------------------------------------------- nights
def record_nights(seed: int, tapes: list) -> dict:
    """{day: {"weeds": [{(x,y): r} per farm], "shops": [...]}} from the live tapes."""
    from kaggle_environments.envs.kaggriculture import kaggriculture as E
    nights: dict = {}
    orig_spawn, orig_eod = E._spawn_weeds, E._end_of_day
    cur = {"day": None, "farm": 0}

    def spawn(farm, board_size, weed_chance, rng):
        draws = {}
        for y in range(board_size):
            for x in range(board_size):
                if farm["tiles"][y][x] is None:
                    r = rng.random()
                    draws[(x, y)] = r
                    if r < weed_chance:
                        farm["tiles"][y][x] = {"kind": "WEED"}
        nights.setdefault(cur["day"], {"weeds": [], "shops": None})["weeds"].append(draws)

    def eod(state, env, day):
        cur["day"] = day
        out = orig_eod(state, env, day)
        nights.setdefault(day, {"weeds": [], "shops": None})["shops"] = list(
            state[0].observation.town["unlocked_shops"])
        return out

    E._spawn_weeds, E._end_of_day = spawn, eod
    try:
        g = FastGame(seed)
        for t in range(719):
            g.step([tapes[i][t + 1] if t + 1 < len(tapes[i]) else PASS for i in (0, 1)])
    finally:
        E._spawn_weeds, E._end_of_day = orig_spawn, orig_eod
    return nights


class Pin:
    """Engine patch: live draws per tile, live shops."""

    def __init__(self, seed: int, nights: dict):
        self.seed, self.nights = seed, nights
        self.cur = {"day": None, "farm": 0}
        self.fresh = 0

    def __enter__(self):
        from kaggle_environments.envs.kaggriculture import kaggriculture as E
        self.E = E
        self.orig = (E._spawn_weeds, E._end_of_day)
        pin = self

        def spawn(farm, board_size, weed_chance, rng):
            day, f = pin.cur["day"], pin.cur["farm"]
            pin.cur["farm"] += 1
            live = pin.nights.get(day, {}).get("weeds", [])
            draws = live[f] if f < len(live) else {}
            for y in range(board_size):
                for x in range(board_size):
                    if farm["tiles"][y][x] is None:
                        r = draws.get((x, y))
                        if r is None:
                            pin.fresh += 1
                            r = random.Random(hash((pin.seed, day, f, x, y)) & 0xFFFFFFFF).random()
                        if r < weed_chance:
                            farm["tiles"][y][x] = {"kind": "WEED"}

        def eod(state, env, day):
            pin.cur["day"], pin.cur["farm"] = day, 0
            out = pin.orig[1](state, env, day)
            shops = pin.nights.get(day, {}).get("shops")
            if shops is not None:
                state[0].observation.town["unlocked_shops"][:] = shops
            return out

        E._spawn_weeds, E._end_of_day = spawn, eod
        return self

    def __exit__(self, *exc):
        self.E._spawn_weeds, self.E._end_of_day = self.orig
        return False


# ---------------------------------------------------------------- play
def observation(g: FastGame, side: int, t: int) -> dict:
    o = g.obs
    return {"player": side, "step": t, "day": t // 24, "hour": t % 24,
            "remainingOverageTime": 60,
            "farms": copy.deepcopy(o.farms), "market": copy.deepcopy(o.market),
            "town": copy.deepcopy(o.town),
            "private": copy.deepcopy(g.private(side))}


def telemetry(agent) -> dict:
    out, seen, todo = {}, set(), [agent]
    while todo:
        f = todo.pop()
        if id(f) in seen or not callable(f):
            continue
        seen.add(id(f))
        tel = getattr(f, "telemetry", None)
        if isinstance(tel, dict) and (getattr(f, "_l2_land", False)
                                      or getattr(f, "__name__", "") == "ta_agent"):
            for k, v in tel.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out[k] = v
        for cell in getattr(f, "__closure__", None) or ():
            try:
                todo.append(cell.cell_contents)
            except ValueError:
                pass
    return out


def play(factory: str, path: Path) -> dict:
    seed, side, tp, rec = live_record(path)
    nights = record_nights(seed, tp)
    module, func = factory.rsplit(":", 1)
    agent = getattr(importlib.import_module(module), func)()
    cfg = dict(CONFIG)
    started = time.time()
    errors = 0
    slowest = 0.0
    with Pin(seed, nights) as pin:
        g = FastGame(seed)
        daily = []
        for t in range(719):
            t0 = time.time()
            try:
                ours = agent(observation(g, side, t), cfg)
            except Exception:
                errors += 1
                ours = PASS
            slowest = max(slowest, time.time() - t0)
            acts = [None, None]
            acts[side] = ours
            acts[1 - side] = tp[1 - side][t + 1] if t + 1 < len(tp[1 - side]) else PASS
            g.step(acts)
            if t % 24 == 23:
                daily.append([float(f["money"]) for f in g.obs.farms])
    money = g.money()
    return {"episode_id": rec["episode_id"], "opponent": rec.get("opponent"),
            "opponent_rating": rec.get("opponent_rating"), "live": rec["rewards"],
            "us": money[side], "them": money[1 - side], "won": money[side] > money[1 - side],
            "exact_live": money[side] == rec["rewards"]["us"] and money[1 - side] == rec["rewards"]["them"],
            "errors": errors, "fresh_draws": pin.fresh, "seconds": round(time.time() - started, 1),
            "slowest_turn": round(slowest, 3), "telemetry": telemetry(agent),
            "daily": [[round(a), round(b)] for a, b in (d if side == 0 else d[::-1] for d in daily)]}


def v219_paths(paths):
    """Games where our side bought SE on day 18 live (V219 fired)."""
    from tools.analysis.l2_land_fast import replay
    out = []
    for p in paths:
        seed, side, tp, _ = live_record(p)
        for t, g, _a in replay(seed, tp):
            if t == 18 * 24 + 23:
                if "SE" in g.obs.farms[side]["unlocked_quadrants"]:
                    out.append(p)
                break
    return out


def run(args) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = live_paths(args.submission)
    if args.v219:
        paths = v219_paths(paths)
    if args.episodes:
        paths = [p for p in paths if any(str(e) in p.name for e in args.episodes)]
    if args.limit:
        paths = paths[:args.limit]
    dest = OUT / f"{args.label}.json"
    import os
    pids = ROOT / "rl" / "data" / "l2" / "eval" / "pids"
    pids.mkdir(parents=True, exist_ok=True)
    (pids / f"{args.label}.pid").write_text(str(os.getpid()), encoding="utf-8")
    rows = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() and args.resume else []
    done = {r["episode_id"] for r in rows}
    t0 = time.time()
    for p in paths:
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec["episode_id"] in done:
            continue
        row = play(args.factory, p)
        rows.append(row)
        dest.write_text(json.dumps(rows, indent=1), encoding="utf-8")
        print(f"  {row['episode_id']}: us {row['us']:,.0f} them {row['them']:,.0f} "
              f"(live {row['live']['us']:,.0f}/{row['live']['them']:,.0f}) "
              f"{'EXACT' if row['exact_live'] else ''} err {row['errors']} fresh {row['fresh_draws']} "
              f"{row['seconds']}s slowest {row['slowest_turn']}s {row['telemetry']}", flush=True)
    print(f"{args.label}: {len(rows)} games in {time.time() - t0:.0f}s -> {dest.relative_to(ROOT)}")


def compare(args) -> None:
    a = {r["episode_id"]: r for r in json.loads((OUT / f"{args.before}.json").read_text(encoding="utf-8"))}
    b = {r["episode_id"]: r for r in json.loads((OUT / f"{args.after}.json").read_text(encoding="utf-8"))}
    shared = sorted(set(a) & set(b))
    own = [b[e]["us"] - a[e]["us"] for e in shared]
    them = [b[e]["them"] - a[e]["them"] for e in shared]
    margin = [o - t for o, t in zip(own, them)]
    print(f"{args.after} vs {args.before}: {len(shared)} shared games")
    print(f"  wins {sum(a[e]['won'] for e in shared)} -> {sum(b[e]['won'] for e in shared)}; "
          f"flipped to wins {sum(1 for e in shared if b[e]['won'] and not a[e]['won'])}, "
          f"to losses {sum(1 for e in shared if a[e]['won'] and not b[e]['won'])}")
    print(f"  own score change mean {statistics.mean(own):+,.0f} median {statistics.median(own):+,.0f} "
          f"(higher {sum(x > 0 for x in own)}, lower {sum(x < 0 for x in own)}, same {sum(x == 0 for x in own)})")
    print(f"  opponent change mean {statistics.mean(them):+,.0f}; margin change mean "
          f"{statistics.mean(margin):+,.0f} median {statistics.median(margin):+,.0f}")
    print("  per game (own, margin): " + ", ".join(f"{e}:{o:+,.0f}/{m:+,.0f}" for e, o, m in
                                                   sorted(zip(shared, own, margin), key=lambda z: z[1])))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--factory", required=True)
    r.add_argument("--label", required=True)
    r.add_argument("--submission", type=int, default=56582917)
    r.add_argument("--v219", action="store_true")
    r.add_argument("--episodes", nargs="*", default=[])
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--resume", action="store_true")
    c = sub.add_parser("compare")
    c.add_argument("before")
    c.add_argument("after")
    a = ap.parse_args()
    run(a) if a.cmd == "run" else compare(a)


if __name__ == "__main__":
    main()
