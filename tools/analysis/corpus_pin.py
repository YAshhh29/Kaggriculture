"""Play a candidate against the top of the ladder: fresh top-500 games, pinned.

Each corpus record is a real game of a top-500 team (tools/data/fetch_corpus).
The candidate takes the seat of that team's opponent and plays against the
team's recorded moves, with every night's weeds and shops held to the real
game (tools/analysis/l2_land_pin), so two candidates meet the same town.

The top team's tape was recorded against someone else. Once our play differs
the market differs, and its recorded purchases can fail; `drift` is the mean
relative gap between its replayed and its real money by day. Games whose
recording collapses are noise (memory: replay-opponents-desync), so compare
candidates on games where every arm stays below a drift bound
(tools/analysis/pin_compare.py --max-drift).

The original game is replayed first from both tapes; a record that does not
reproduce its real rewards to the coin is skipped.

    python -m tools.analysis.corpus_pin run --factory rl.l2_combo:n4r \\
        --corpus kaggle_cache/corpus_0929 --label top-n4r --chunk 1/8
    python -m tools.analysis.pin_compare top-n2m top-n4r --max-drift 0.05
"""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_land_fast import CONFIG, FastGame, corpus_record, replay  # noqa: E402
from tools.analysis.l2_land_pin import OUT, PASS, Pin, observation, record_nights  # noqa: E402


def _telemetry(agent) -> dict:
    """Numeric telemetry of our own layers (annex, draw_last), for the log."""
    out, seen, todo = {}, set(), [agent]
    while todo:
        f = todo.pop()
        if id(f) in seen or not callable(f):
            continue
        seen.add(id(f))
        name = getattr(f, "__name__", "")
        tel = getattr(f, "telemetry", None)
        if isinstance(tel, dict) and name in ("ta_agent", "dl_agent"):
            for k, v in tel.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out[f"{name[:2]}_{k}"] = v
        for cell in getattr(f, "__closure__", None) or ():
            try:
                todo.append(cell.cell_contents)
            except ValueError:
                pass
    return out


def original(seed: int, tapes: list) -> tuple[list, list]:
    """Daily money of both seats in the real game, and its final money."""
    daily, g = [], None
    for t, g, _ in replay(seed, tapes):
        if t % 24 == 23:
            daily.append([float(f["money"]) for f in g.obs.farms])
    return daily, g.money()


def play(factory: str, path: Path, side: str = "opponent") -> dict:
    seed, seat, tp, rec = corpus_record(path)
    daily0, final0 = original(seed, tp)
    real = [0.0, 0.0]
    real[seat], real[1 - seat] = rec["rewards"]["them"], rec["rewards"]["opponent"]
    base = {"episode_id": rec["episode_id"], "opponent": rec.get("source_team"),
            "opponent_rating": rec.get("team_score"), "team_rank": rec.get("team_rank"),
            "original_opponent": rec.get("opponent"),
            "original_opponent_rating": rec.get("opponent_rating")}
    if [round(x) for x in final0] != [round(x) for x in real]:
        return dict(base, skip="inexact")
    ours = 1 - seat if side == "opponent" else seat
    nights = record_nights(seed, tp)
    module, func = factory.rsplit(":", 1)
    agent = getattr(importlib.import_module(module), func)()
    cfg = dict(CONFIG)
    started, errors, slowest = time.time(), 0, 0.0
    daily = []
    # per-item net trade (sales minus product purchases) of both sides, by 5-day
    # block, logged from the engine's own fills
    from kaggle_environments.envs.kaggriculture import kaggriculture as E
    trade = {"us": {}, "them": {}}
    cur = {"step": 0, "farms": None}
    orig_pm, orig_cu = E._process_market, E._commit_unit

    def pm(state, env):
        cur["step"] = int(state[0].observation.step)
        cur["farms"] = list(state[0].observation.farms)
        return orig_pm(state, env)

    def cu(op, item, price, farm, private, market, cap=100):
        ok = orig_cu(op, item, price, farm, private, market, cap)
        if ok and op in ("SELL", "BUY_PRODUCT") and cur["farms"] is not None:
            who = "us" if cur["farms"][ours] is farm else "them"
            key = f"{item}:{cur['step'] // 120}"
            trade[who][key] = trade[who].get(key, 0.0) + (price if op == "SELL" else -price)
        return ok

    E._process_market, E._commit_unit = pm, cu
    try:
        return _play_pinned(agent, cfg, seed, nights, tp, ours, rec, base, daily0, real, trade,
                            started)
    finally:
        E._process_market, E._commit_unit = orig_pm, orig_cu


def _play_pinned(agent, cfg, seed, nights, tp, ours, rec, base, daily0, real, trade, started):
    errors, slowest, daily = 0, 0.0, []
    with Pin(seed, nights) as pin:
        g = FastGame(seed)
        for t in range(719):
            t0 = time.time()
            try:
                act = agent(observation(g, ours, t), cfg)
            except Exception:
                errors += 1
                act = PASS
            slowest = max(slowest, time.time() - t0)
            acts = [None, None]
            acts[ours] = act
            acts[1 - ours] = tp[1 - ours][t + 1] if t + 1 < len(tp[1 - ours]) else PASS
            g.step(acts)
            if t % 24 == 23:
                daily.append([float(f["money"]) for f in g.obs.farms])
    money = g.money()
    them = 1 - ours
    gaps = [abs(d[them] - o[them]) / max(abs(o[them]), 500.0)
            for d, o in zip(daily[1:], daily0[1:])]
    return dict(base, us=money[ours], them=money[them], won=money[ours] > money[them],
                live={"us": real[ours], "them": real[them]},
                drift=round(statistics.mean(gaps), 4) if gaps else 0.0,
                errors=errors, fresh_draws=pin.fresh, seconds=round(time.time() - started, 1),
                slowest_turn=round(slowest, 3), telemetry=_telemetry(agent),
                daily=[[round(d[ours]), round(d[them])] for d in daily],
                trade={w: {k: round(v) for k, v in t.items()} for w, t in trade.items()})


def run(args) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = sorted(Path(args.corpus).glob("ep*.json"))
    if args.min_rating:
        keep = []
        for p in paths:
            try:
                r = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if float(r.get("team_score") or 0) >= args.min_rating:
                keep.append(p)
        paths = keep
    if args.episodes:
        want = {str(e) for e in args.episodes}
        paths = [p for p in paths if p.stem[2:] in want]
    i, n = (int(x) for x in args.chunk.split("/"))
    paths = paths[i - 1::n]
    if args.limit:
        paths = paths[:args.limit]
    dest = OUT / f"{args.label}-c{i}.json"
    import os
    pids = ROOT / "rl" / "data" / "l2" / "eval" / "pids"
    pids.mkdir(parents=True, exist_ok=True)
    (pids / f"{args.label}-c{i}.pid").write_text(str(os.getpid()), encoding="utf-8")
    rows = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else []
    done = {r["episode_id"] for r in rows}
    t0 = time.time()
    for p in paths:
        try:
            ep = int(p.stem[2:])
        except ValueError:
            continue
        if ep in done:
            continue
        try:
            row = play(args.factory, p, args.side)
        except Exception as error:  # one broken record must not stop the night
            row = {"episode_id": ep, "skip": f"error {type(error).__name__}: {error}"[:200]}
        rows.append(row)
        dest.write_text(json.dumps(rows), encoding="utf-8")
        if "skip" in row:
            print(f"  {ep}: skipped ({row['skip']})", flush=True)
        else:
            print(f"  {ep}: vs {row['opponent']} ({row['opponent_rating']:.0f}) us {row['us']:,.0f} "
                  f"them {row['them']:,.0f} {'WON' if row['won'] else 'lost'} drift {row['drift']} "
                  f"err {row['errors']} {row['seconds']}s", flush=True)
    print(f"{args.label}-c{i}: {len(rows)} rows in {time.time() - t0:.0f}s -> {dest.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--factory", required=True)
    r.add_argument("--label", required=True)
    r.add_argument("--corpus", default=str(ROOT / "kaggle_cache" / "corpus_0929"))
    r.add_argument("--chunk", default="1/1", help="i/n: every n-th record from the i-th")
    r.add_argument("--side", choices=("opponent", "team"), default="opponent",
                   help="play the top team's opponent (default) or the top team itself")
    r.add_argument("--min-rating", type=float, default=0.0)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--episodes", nargs="*", default=[], help="only these episode ids")
    args = ap.parse_args()
    if args.cmd == "run":
        run(args)


if __name__ == "__main__":
    main()
