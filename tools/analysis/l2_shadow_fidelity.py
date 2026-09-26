"""Can a program be shadowed and cloned? Exactness checks on real games.

For a live game whose opponent is an exact copy of a program (found by
l2_shadow_sync), this replays the game and checks, for that program:

  tracked   an in-game OpponentShadow (private state reconstructed, never
            read from the replay) predicts every opponent action exactly;
  clone     a second instance, cloned from the shadow's state each turn
            (rl.l2_shadow.sh_clone_into), plays the next turn exactly like
            the original -- what the one-turn lookahead relies on.

    python -m tools.analysis.l2_shadow_fidelity --pairs 113722929:nb_haideptry_2965 ...
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_shadow_replay import OUT, TAPES, Replay, load_game, norm  # noqa: E402


def factory_for(program):
    if program == "A":
        from rl.candidate_l import parent_namespace
        return parent_namespace
    path = ROOT / "rl" / "public" / f"{program}.py"

    def make():
        env = {"__name__": f"shadow_{program}", "__file__": str(path)}
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), env)
        return env, env["agent"]
    return make


def check(job) -> dict:
    episode, program = job
    sys.path.insert(0, str(ROOT))
    from rl.l2_shadow import OpponentShadow, sh_clone_into, sh_clone_plan
    g = load_game(TAPES / f"ep{episode}.json")
    side = g["our_side"]
    opp = 1 - side
    cfg = g["config"]
    make = factory_for(program)
    tracker = OpponentShadow(program=program, factory=make)
    env1, e1 = make()
    env2, e2 = make()
    plan = None
    rp = Replay(g["seed"])
    miss_track = miss_clone = 0
    first_track = first_clone = None
    clone_ms = 0.0
    started = time.time()
    for t in range(719):
        real = norm(g["tapes"][opp][t + 1])
        info = tracker.observe(rp.observation(side), cfg)
        if info["in_sync"] and norm(info["pred"]) != real:
            miss_track += 1
            first_track = first_track if first_track is not None else t
        tracker.record_own_action(g["tapes"][side][t + 1])
        o = rp.observation(opp)
        if t > 0:
            out2 = norm(e2(o, cfg))
        out1 = norm(e1(o, cfg))
        if t > 0 and out1 != out2:
            miss_clone += 1
            first_clone = first_clone if first_clone is not None else t
        a = time.perf_counter()
        if plan is None:
            plan = sh_clone_plan(env1)
        sh_clone_into(env1, env2, plan)
        clone_ms += (time.perf_counter() - a) * 1000.0
        rp.step(g["tapes"][0][t + 1], g["tapes"][1][t + 1])
    return {"episode": episode, "program": program, "tracker": tracker.summary(),
            "tracked_pred_misses": miss_track, "first_tracked_miss": first_track,
            "clone_misses": miss_clone, "first_clone_miss": first_clone,
            "clone_ms": round(clone_ms / 719, 2), "plan_state_names": len(plan["names"]),
            "plan_shared": plan["shared"], "seconds": round(time.time() - started)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pairs", nargs="+", required=True, help="episode:program")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--label", default="fidelity")
    args = ap.parse_args()
    jobs = [(int(p.split(":")[0]), p.split(":")[1]) for p in args.pairs]
    rows = []
    with Pool(args.workers, maxtasksperchild=1) as pool:
        for row in pool.imap_unordered(check, jobs):
            rows.append(row)
            print(json.dumps(row), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{args.label}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
