"""Out-farm autopsy, part 3: where does the opponent decide differently from A?

Replays a live game exactly (both recorded tapes) while a fresh copy of Agent A
watches a seat: at every step it gets exactly the observation that seat's
player got and its answer is recorded, never played. In our own seat A played
live, so the shadow must reproduce our tape action for action (the check that
the method is sound). In the opponent's seat, every step where the shadow's
answer differs from the opponent's recorded action is a decision the opponent
made differently from A *in the same state*.

    python -m tools.analysis.l2_outfarm_shadow --episodes 113773538
    python -m tools.analysis.l2_outfarm_shadow --losses --agent A

Writes rl/data/l2/outfarm/shadow/ep<id>__<agent>.json and prints the first
divergences and a per-day count by kind (farmer / hands / market content /
market order only).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_outfarm_replay import OUT, load_record, replay, select_losses  # noqa: E402


def _norm(action) -> dict:
    if not isinstance(action, dict):
        return {"farmer": ["PASS"], "hands": [], "market": [], "bad": str(action)[:80]}
    return {"farmer": list(action.get("farmer") or ["PASS"]),
            "hands": [list(h or ["PASS"]) for h in (action.get("hands") or [])],
            "market": [list(o) for o in (action.get("market") or [])]}


def diff(shadow, played) -> dict | None:
    a, b = _norm(shadow), _norm(played)
    out = {}
    if a["farmer"] != b["farmer"]:
        out["farmer"] = [a["farmer"], b["farmer"]]
    ha, hb = a["hands"], b["hands"]
    if ha != hb:
        idx = [i for i in range(max(len(ha), len(hb)))
               if (ha[i] if i < len(ha) else None) != (hb[i] if i < len(hb) else None)]
        out["hands"] = [[i, ha[i] if i < len(ha) else None, hb[i] if i < len(hb) else None]
                        for i in idx]
    if a["market"] != b["market"]:
        same_content = sorted(map(json.dumps, a["market"])) == sorted(map(json.dumps, b["market"]))
        out["market_order" if same_content else "market"] = [a["market"], b["market"]]
    return out or None


UNIT_OPS = ("PLANT", "HARVEST", "WATER", "FERTILIZE", "FEED", "COLLECT_FERTILIZER", "CARE",
            "DIG", "BUILD_COOP", "BUILD_PASTURE", "PLACE", "PICKUP", "DROP")


def semantic(action) -> Counter:
    """What an action asks for, independent of which hand does it or order."""
    a = _norm(action)
    out: Counter = Counter()
    for cmd in [a["farmer"], *a["hands"]]:
        if not cmd:
            continue
        op = cmd[0]
        if op == "PLANT" and len(cmd) > 1:
            out["PLANT " + str(cmd[1])] += 1
        elif op in UNIT_OPS:
            out[op] += 1
    for o in a["market"]:
        if not o:
            continue
        op = o[0]
        if op in ("HIRE", "BUY_LAND"):
            out[op] += 1
        elif op in ("SELL", "BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT") and len(o) >= 3:
            try:
                out[f"{op} {o[1]}"] += max(0, int(o[2]))
            except (TypeError, ValueError):
                pass
    return +out


def semantic_rows(shadow_log, played) -> list:
    rows = []
    for step, (s, p) in enumerate(zip(shadow_log, played)):
        cs, cp = semantic(s), semantic(p)
        if cs != cp:
            keys = sorted(set(cs) | set(cp))
            rows.append([step, {k: [cs.get(k, 0), cp.get(k, 0)] for k in keys
                                if cs.get(k, 0) != cp.get(k, 0)}])
    return rows


def build(agent: str):
    if agent.startswith("L"):
        from rl.candidate_l import l_stack
        return l_stack()
    from tools.arena.arena import load
    return load(agent)


def shadow_job(job) -> dict:
    episode, agent = job
    record = load_record(episode)
    side = int(record["our_side"])
    run = replay(record, shadows={0: build(agent), 1: build(agent)}, books=False)
    out = {"episode_id": episode, "agent": agent, "our_side": side,
           "opponent": record.get("opponent"), "exact": run["exact"], "seats": {}}
    for seat in (0, 1):
        rows = []
        for step, (s, p) in enumerate(zip(run["shadow"][seat], run["played"][seat])):
            d = diff(s, p)
            if d:
                rows.append([step, d])
        out["seats"][str(seat)] = {"role": "us" if seat == side else "them",
                                   "steps": len(run["played"][seat]),
                                   "diffs": rows,
                                   "semantic": semantic_rows(run["shadow"][seat],
                                                             run["played"][seat])}
    path = OUT / "shadow" / f"ep{episode}__{agent}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out), encoding="utf-8")
    return out


def summarise(out: dict, first: int = 12) -> list[str]:
    lines = [f"\n=== ep{out['episode_id']} vs {out['opponent']}: shadow {out['agent']} "
             f"(replay exact: {out['exact']})"]
    for seat in ("0", "1"):
        info = out["seats"][seat]
        rows = info["diffs"]
        kinds = Counter(k for _, d in rows for k in d)
        lines.append(f"  seat {seat} ({info['role']}): {len(rows)} of {info['steps']} steps differ; "
                     f"by kind {dict(kinds)}; first at step "
                     f"{rows[0][0] if rows else None}")
        by_day = Counter(step // 24 for step, _ in rows)
        lines.append("    per day: " + " ".join(f"d{d}:{by_day.get(d, 0)}" for d in range(30)))
        for step, d in rows[:first]:
            text = json.dumps(d, ensure_ascii=False)
            lines.append(f"    step {step} (d{step // 24} h{step % 24}): {text[:400]}")
        sem = info.get("semantic") or []
        # Totals over the game of what the shadow asked for and the player did.
        tot: dict = {}
        for step, d in sem:
            for k, (a, b) in d.items():
                cell = tot.setdefault(k, [0, 0, step])
                cell[0] += a
                cell[1] += b
        keep = sorted(tot.items(), key=lambda kv: kv[1][2])
        lines.append(f"    semantic: {len(sem)} steps differ in content; totals over differing "
                     f"steps (shadow A / player, first step):")
        for k, (a, b, s0) in keep[:30]:
            lines.append(f"      {k:28s} {a:6d} / {b:<6d} first d{s0 // 24} h{s0 % 24}")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--episodes", type=int, nargs="*", default=[])
    ap.add_argument("--losses", action="store_true")
    ap.add_argument("--agent", default="A")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--first", type=int, default=12)
    args = ap.parse_args()
    episodes = list(args.episodes)
    if args.losses:
        episodes += [r["episode_id"] for r in select_losses()]
    episodes = sorted(set(episodes))
    with Pool(min(2, args.workers), maxtasksperchild=1) as pool:
        for out in pool.imap_unordered(shadow_job, [(e, args.agent) for e in episodes]):
            print("\n".join(summarise(out, args.first)), flush=True)


if __name__ == "__main__":
    main()
