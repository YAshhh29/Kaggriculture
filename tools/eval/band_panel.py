"""Our agents against recorded plans of teams rated 2600-2900 on the ladder.

For each team in the rating band (corpus_v2, ratings as of the corpus
snapshot) one real ladder game is picked, and each agent under test plays
that game's seed and seat against the team's exact recorded moves.

The opponent is an open-loop recording: it cannot react. A game where the
recording drifts -- the replayed team reaches less than 70% of the score it
really recorded -- no longer represents that team and is reported but not
counted. Because recordings cannot react, this panel is optimistic; the live
submissions in the lineup (live_K, live_H2, live_C2, live_J) have known
ladder ratings and show how optimistic.

Every game is also stored in the arena (seed + both tapes), so any of them
can be rendered in Kaggle's viewer:

    python -m tools.eval.band_panel A live_K live_H2 live_C2 live_J
    python -m tools.arena.arena render <game_id> --open
"""

from __future__ import annotations

import argparse
import base64
import json
import random
import re
import statistics
import sys
import time
import zlib
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CORPUS = ROOT / "kaggle_cache" / "corpus_v2"
OUT = ROOT / "rl" / "data" / "band_panel"
FIDELITY = 0.70
BANDS = ((2600, 2700), (2700, 2800), (2800, 2900))


def _unpack(blob: str):
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def _safe(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")[:24] or "team"


def pick(low: int, high: int, per_team: int, seed: int) -> list[dict]:
    by_team = defaultdict(list)
    for path in sorted(CORPUS.glob("ep*.json")):
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        score = float(r.get("team_score") or 0)
        if low <= score < high:
            by_team[r["source_team"]].append((str(path), r))
    rng = random.Random(seed)
    jobs = []
    for team in sorted(by_team):
        rows = sorted(by_team[team], key=lambda x: x[1]["episode_id"])
        for path, r in rng.sample(rows, min(per_team, len(rows))):
            jobs.append({"path": path, "team": team, "score": float(r["team_score"]),
                         "episode": r["episode_id"], "seed": r["seed"],
                         "seat": int(r["seat"]),
                         "recorded": float((r.get("rewards") or {}).get("them") or 0)})
    return jobs


def play(job):
    name, game = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    from rl.replay_agent import build_replay_agent
    from tools.arena.arena import GAMES, _pack, load

    record = json.loads(Path(game["path"]).read_text(encoding="utf-8"))
    tape = _unpack(record["actions_zlib_b64"])
    seat = game["seat"]                     # the recorded team keeps its seat
    ours_seat = 1 - seat
    agent = load(name)
    agents = [None, None]
    agents[seat] = build_replay_agent(tuple(tape))
    agents[ours_seat] = agent
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": game["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    started = time.time()
    try:
        env.run(agents)
    except Exception as error:  # a crash is a result, not an abort
        return {**game, "agent": name, "error": f"{type(error).__name__}: {error}"}
    ours = float(env.steps[-1][ours_seat].get("reward") or 0)
    theirs = float(env.steps[-1][seat].get("reward") or 0)
    names = [None, None]
    names[seat], names[ours_seat] = f"{_safe(game['team'])}_{int(game['score'])}", name
    game_id = f"band__{name}__vs__{names[seat]}__ep{game['episode']}"
    tapes = [_pack([env.steps[s][i].get("action") for s in range(len(env.steps))])
             for i in (0, 1)]
    rewards = [float(env.steps[-1][i].get("reward") or 0) for i in (0, 1)]
    GAMES.mkdir(parents=True, exist_ok=True)
    (GAMES / f"{game_id}.json").write_text(json.dumps({
        "game_id": game_id, "agents": names, "seed": game["seed"],
        "specs": ["recorded", "recorded"], "rewards": rewards,
        "statuses": [str(env.steps[-1][i].get("status")) for i in (0, 1)],
        "winner": names[0] if rewards[0] > rewards[1] else
        names[1] if rewards[1] > rewards[0] else None,
        "turn_errors": [0, 0], "played_unix": int(time.time()),
        "seconds": round(time.time() - started, 1), "tapes": tapes}),
        encoding="utf-8")
    return {**game, "agent": name, "ours": ours, "theirs": theirs,
            "won": ours > theirs, "clean": theirs >= FIDELITY * game["recorded"],
            "game_id": game_id}


def summarise(rows: list[dict], agents: list[str]) -> str:
    lines = []
    head = (f"  {'agent':10s} {'clean':>7s} {'won':>9s} {'median margin':>14s}"
            + "".join(f"{f'{lo}-{hi}':>16s}" for lo, hi in BANDS)
            + f"{'drifted':>9s}")
    lines.append(head)
    for name in agents:
        mine = [r for r in rows if r["agent"] == name and "ours" in r]
        clean = [r for r in mine if r["clean"]]
        wins = sum(r["won"] for r in clean)
        margin = statistics.median(r["ours"] - r["theirs"] for r in clean) if clean else 0
        cells = ""
        for lo, hi in BANDS:
            b = [r for r in clean if lo <= r["score"] < hi]
            cells += f"{sum(r['won'] for r in b):>7d}/{len(b):<3d} {100 * sum(r['won'] for r in b) / max(1, len(b)):3.0f}%"
        lines.append(f"  {name:10s} {len(clean):>7d} {wins:>4d} {100 * wins / max(1, len(clean)):3.0f}% "
                     f"{margin:>+14,.0f}{cells}{len(mine) - len(clean):>9d}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agents", nargs="+")
    ap.add_argument("--low", type=int, default=2600)
    ap.add_argument("--high", type=int, default=2900)
    ap.add_argument("--per-team", type=int, default=1)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--tag", default="band")
    args = ap.parse_args()

    games = pick(args.low, args.high, args.per_team, args.seed)
    teams = len({g["team"] for g in games})
    print(f"{len(games)} recorded games from {teams} teams rated "
          f"{args.low}-{args.high}; {len(args.agents)} agents; "
          f"{len(games) * len(args.agents)} games to play", flush=True)
    jobs = [(name, g) for g in games for name in args.agents]
    rows = []
    with Pool(args.workers, maxtasksperchild=1) as pool:
        for i, row in enumerate(pool.imap_unordered(play, jobs), 1):
            rows.append(row)
            if i % 25 == 0:
                print(f"  {i}/{len(jobs)} played", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{args.tag}.json"
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    errors = [r for r in rows if "error" in r]
    print(f"\nresults: {out}  (crashes: {len(errors)})\n")
    print(summarise(rows, args.agents))


if __name__ == "__main__":
    main()
