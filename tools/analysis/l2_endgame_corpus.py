"""Replay the corpus of real top-team ladder games exactly and log both sides'
market activity (endgame study).

kaggle_cache/corpus_v2/ep*.json holds real games of top-500 teams with both
players' action tapes and the seed, so the stock engine reproduces them
exactly (checked against the recorded rewards). Each game is logged with
tools.analysis.l2_endgame_bench.log_game (who 0 = the recorded team, who 1 =
its real opponent); the per-step inventory is kept from day 24 on only.

    python -m tools.analysis.l2_endgame_corpus log --workers 2
"""

from __future__ import annotations

import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_endgame_log import OUT  # noqa: E402

CORPUS = ROOT / "kaggle_cache" / "corpus_v2"
LOGS = OUT / "corpus_logs"


def as_record(raw: dict) -> dict:
    return {"episode_id": raw["episode_id"], "seed": raw["seed"],
            "our_side": int(raw["seat"]),
            "our_actions_zlib_b64": raw["actions_zlib_b64"],
            "opp_actions_zlib_b64": raw["opponent_actions_zlib_b64"],
            "rewards": {"us": float(raw["rewards"]["them"]),
                        "them": float(raw["rewards"]["opponent"])},
            "opponent": raw.get("opponent"),
            "opponent_rating": raw.get("opponent_rating"),
            "submission": None}


def job(path: str):
    from tools.analysis.l2_endgame_bench import log_game
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        out = log_game(as_record(raw))
    except Exception as error:  # a broken record must not sink the run
        return raw.get("episode_id"), repr(error)
    out["inv"] = out["inv"][576:]
    out["inv_from"] = 576
    out.update(team=raw.get("source_team"), team_score=raw.get("team_score"),
               team_rank=raw.get("team_rank"))
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / Path(path).name).write_text(json.dumps(out, separators=(",", ":")),
                                        encoding="utf-8")
    return raw.get("episode_id"), out["exact"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("log")
    p.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    paths = [str(p) for p in sorted(CORPUS.glob("ep*.json"))
             if not (LOGS / p.name).exists()]
    print(f"{len(paths)} corpus games to log", flush=True)
    with Pool(args.workers, maxtasksperchild=50) as pool:
        done = pool.map(job, paths, chunksize=8)
    exact = sum(1 for _, ok in done if ok is True)
    print(f"logged {len(done)}: exact {exact}, not exact "
          f"{sum(1 for _, ok in done if ok is False)}, errors "
          f"{sum(1 for _, ok in done if isinstance(ok, str))}")


if __name__ == "__main__":
    main()
