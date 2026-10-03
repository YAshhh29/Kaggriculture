"""Out-farm autopsy, part 4: play another agent in a live game's seat, with books.

Replays a live game with a live agent in OUR seat against the opponent's
recorded tape (the live_replay setup), or in the OPPONENT's seat against our
recorded tape, and keeps the same engine books as l2_outfarm_replay, so the
counterfactual farm can be compared line by line with the live one.

    python -m tools.analysis.l2_outfarm_counter --agent L --losses
    python -m tools.analysis.l2_outfarm_counter --agent A --seat them --episodes 113773538
    python -m tools.analysis.l2_outfarm_counter --factory rl.l2_x:build --label x --losses

Books go to rl/data/l2/outfarm/books_<label>_<seat>/ep<id>.json; one summary
line per game is printed and appended to rl/data/l2/outfarm/counter_<label>_<seat>.jsonl.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_outfarm_replay import OUT, load_record, replay, select_losses  # noqa: E402


def make(agent: str | None, factory: str | None):
    if factory:
        module, func = factory.rsplit(":", 1)
        return getattr(importlib.import_module(module), func)()
    if agent == "L":
        from stack.candidate_l import l_stack
        return l_stack()
    from tools.arena.arena import load
    return load(agent)


def job(args) -> dict:
    episode, agent, factory, label, where = args
    record = load_record(episode)
    side = int(record["our_side"])
    seat = side if where == "us" else 1 - side
    out = replay(record, agents={seat: make(agent, factory)})
    out.pop("shadow", None)
    out.pop("played", None)
    out["counter"] = {"label": label, "seat": seat, "where": where}
    path = OUT / f"books_{label}_{where}" / f"ep{episode}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out), encoding="utf-8")
    r = out["rewards"]
    return {"episode_id": episode, "opponent": record.get("opponent"), "label": label,
            "where": where, "live_us": record["rewards"]["us"],
            "live_them": record["rewards"]["them"],
            "us": r[side], "them": r[1 - side], "margin": r[side] - r[1 - side],
            "live_margin": record["rewards"]["us"] - record["rewards"]["them"],
            "statuses": out["statuses"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", default=None)
    ap.add_argument("--factory", default=None)
    ap.add_argument("--label", default=None)
    ap.add_argument("--seat", choices=("us", "them"), default="us")
    ap.add_argument("--episodes", type=int, nargs="*", default=[])
    ap.add_argument("--losses", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    label = args.label or args.agent
    episodes = list(args.episodes)
    if args.losses:
        episodes += [r["episode_id"] for r in select_losses()]
    episodes = sorted(set(episodes))
    log = OUT / f"counter_{label}_{args.seat}.jsonl"
    with Pool(min(2, args.workers), maxtasksperchild=1) as pool:
        for row in pool.imap_unordered(job, [(e, args.agent, args.factory, label, args.seat)
                                             for e in episodes]):
            print(json.dumps(row, ensure_ascii=False), flush=True)
            with log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
