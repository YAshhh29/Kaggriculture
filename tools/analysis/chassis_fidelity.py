"""Does the lineage chassis make a top team's recorded plan robust?

Replayed raw against a live opponent it never met, a strawberry-template
team's tape collapses to 34-52% of the score it really earned. yhay81's route
tapes were recorded in particular games too, yet they replay at ~100% --
because they run inside the lineage's Chassis, whose guards fund each block's
purchases, repair weeds, clamp sales to real stock and keep the shed legal.

This runs the same tape both ways against the same live opponent on the same
seed and seat: raw, and as the only route of a bare Chassis (default guards,
none of the lineage's outer reflex layers). If the chassis lifts fidelity
close to the raw-vs-own-opponent 100%, a chassis agent built on top-team
routes is viable; if not, it is not.

    python -m tools.analysis.chassis_fidelity --teams DECEM Smackaveli --live nb_tschinkel_2945
"""

from __future__ import annotations

import argparse
import base64
import importlib
import json
import statistics
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CORPUS = ROOT / "kaggle_cache" / "corpus_v2"


def _unpack(blob: str) -> list:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def _game(players, seed):
    from kaggle_environments import make
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run(players)
    return [float(env.steps[-1][i].get("reward") or 0.0) for i in (0, 1)]


def one(job):
    path, live_name, chassis_module = job
    sys.path.insert(0, str(ROOT))
    from rl.replay_agent import build_replay_agent
    from tools.arena.arena import load

    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    seat, seed = int(rec["seat"]), rec["seed"]
    tape = _unpack(rec["actions_zlib_b64"])
    recorded = float((rec.get("rewards") or {}).get("them") or 0.0)
    # Pad to the 719 acting steps the chassis expects.
    tape = (tape + [{"farmer": ["PASS"], "hands": [], "market": []}] * 720)[:720]

    out = {"team": rec.get("source_team"), "rank": rec.get("team_rank"),
           "recorded": recorded}
    for mode in ("raw", "chassis"):
        if mode == "raw":
            ours = build_replay_agent(tuple(tape))
        else:
            # Corpus tapes use Kaggle's replay convention -- the action at index
            # k was chosen while observing step k-1 -- but the Chassis plays
            # tape[step] at step `step`. Unshifted, every action lands a turn
            # late; the first run of this test did exactly that and even the
            # lineage control fell from 90% to 42%.
            route = tape[1:] + [{"farmer": ["PASS"], "hands": [],
                                 "market": []}]
            mod = importlib.import_module(f"rl.public.{chassis_module}")
            ours = mod.make_agent({0: route}, router=None)
        live = load(live_name)
        players = [None, None]
        players[seat], players[1 - seat] = ours, live
        scores = _game(players, seed)
        out[mode] = scores[seat]
        out[mode + "_live"] = scores[1 - seat]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--teams", nargs="+", required=True)
    ap.add_argument("--live", default="nb_tschinkel_2945")
    ap.add_argument("--chassis", default="nb_tschinkel_2945",
                    help="extracted module whose Chassis/make_agent to use")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--per-team", type=int, default=4)
    args = ap.parse_args()

    wanted, taken = set(args.teams), {}
    jobs = []
    for path in sorted(CORPUS.glob("ep*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        team = rec.get("source_team")
        if team in wanted and taken.get(team, 0) < args.per_team:
            taken[team] = taken.get(team, 0) + 1
            jobs.append((str(path), args.live, args.chassis))
    print(f"{len(jobs)} tapes, raw vs chassis, against live {args.live}",
          flush=True)
    with Pool(args.workers, maxtasksperchild=1) as pool:
        rows = list(pool.imap_unordered(one, jobs))

    print(f"\n  {'team':22s} {'n':>2}  {'raw fid':>7} {'chassis fid':>11}  "
          f"{'raw wins':>8} {'chassis wins':>12}")
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r["team"], []).append(r)
    for team, rs in sorted(by.items(), key=lambda kv: kv[1][0]["rank"]):
        def fid(k):
            return statistics.median(r[k] / r["recorded"] for r in rs
                                     if r["recorded"])
        print(f"  #{rs[0]['rank']:<3} {team[:18]:18s} {len(rs):2d}  "
              f"{fid('raw'):7.0%} {fid('chassis'):11.0%}  "
              f"{sum(r['raw'] > r['raw_live'] for r in rs):4d}/{len(rs):<3d} "
              f"{sum(r['chassis'] > r['chassis_live'] for r in rs):8d}/{len(rs)}")


if __name__ == "__main__":
    main()
