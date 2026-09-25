"""The markers that separate ladder bands, measured the same way for any agent.

Three independent studies of the current ladder (destbreso's x-ray,
georgymamarin's 2600-farms study and raykkretzschmar's findings, re-checked
on our own corpus) agree on what separates the bands: the day of the second
and third land purchase, how much of the ground is planted, the crop mix
(strawberry, tomato, carrot), herd size, how much CARE is spent, the bank
trajectory, and whether goods are dumped into a floored book.

This replays games exactly (both sides' stored actions on the game's seed)
and measures those markers for one side, from arena games of our own agents
and from corpus games of ladder teams, so the numbers are comparable.

    python -m tools.analysis.markers --arena J nb_tetsutani_demand --corpus-top 30
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CORPUS = ROOT / "kaggle_cache" / "corpus_v2"
GAMES = ROOT / "arena" / "games"
TURNS = 24
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")


def _unpack(blob: str) -> list:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def measure(job) -> dict:
    """Replay one game and read one side's markers."""
    label, seed, tapes, seat = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make

    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.reset()
    plants = {c: 0 for c in CROPS}
    care = floor_sells = 0
    land_days: list[int] = []
    prev_quadrants = None
    bank = {}
    for t in range(min(len(tapes[0]), len(tapes[1]), 719)):
        obs = env.state[0].observation
        prices = (obs.get("market") or {}).get("prices") or {}
        act = tapes[seat][t] or {}
        for u in [act.get("farmer")] + list(act.get("hands") or []):
            if isinstance(u, list) and u:
                if u[0] == "PLANT" and len(u) > 1 and u[1] in plants:
                    plants[u[1]] += 1
                elif u[0] == "CARE":
                    care += 1
        for o in act.get("market") or []:
            if (isinstance(o, list) and len(o) >= 2 and o[0] == "SELL"
                    and float(prices.get(o[1], 99)) <= 2):
                floor_sells += 1
        env.step([tapes[0][t] or {}, tapes[1][t] or {}])
        farm = env.state[0].observation["farms"][seat]
        quads = farm.get("unlocked_quadrants")
        n = len(quads) if isinstance(quads, (list, tuple)) else int(quads or 0)
        if prev_quadrants is not None and n > prev_quadrants:
            land_days += [t // TURNS] * (n - prev_quadrants)
        prev_quadrants = n
        if t % TURNS == TURNS - 1:
            bank[t // TURNS] = float(farm.get("money") or 0)
    final = [float(env.state[i].reward or 0) for i in (0, 1)]
    return {"label": label, "won": final[seat] > final[1 - seat],
            "score": final[seat],
            "land2": land_days[0] if len(land_days) >= 1 else None,
            "land3": land_days[1] if len(land_days) >= 2 else None,
            "quadrants": 1 + len(land_days),
            "plantings": sum(plants.values()), **{f"p_{c}": v for c, v in
                                                   plants.items()},
            "care": care, "floor_sells": floor_sells,
            **{f"bank_d{d}": bank.get(d) for d in (5, 8, 11, 20)}}


def jobs_from_arena(names: list[str], limit: int) -> list:
    out = []
    for name in names:
        taken = 0
        for path in sorted(GAMES.glob("*.json")):
            if taken >= limit:
                break
            try:
                r = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if "tapes" not in r or name not in r["agents"]:
                continue
            seat = r["agents"].index(name)
            out.append((name, r["seed"], [_unpack(t) for t in r["tapes"]],
                        seat))
            taken += 1
    return out


def jobs_from_corpus(lo: int, hi: int, limit: int) -> list:
    out = []
    for path in sorted(CORPUS.glob("ep*.json")):
        if len(out) >= limit:
            break
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rank = int(r.get("team_rank") or 9999)
        if not lo <= rank <= hi:
            continue
        seat = int(r["seat"])
        tapes = [None, None]
        tapes[seat] = _unpack(r["actions_zlib_b64"])
        tapes[1 - seat] = _unpack(r["opponent_actions_zlib_b64"])
        out.append((f"ladder #{lo}-{hi}", r["seed"], tapes, seat))
    return out


KEYS = ["land2", "land3", "quadrants", "plantings", "p_WHEAT", "p_STRAWBERRY",
        "p_TOMATO", "p_CARROT", "p_MELON", "care", "floor_sells",
        "bank_d5", "bank_d8", "bank_d11", "bank_d20", "score"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arena", nargs="*", default=["J", "nb_tetsutani_demand"])
    ap.add_argument("--arena-games", type=int, default=12)
    ap.add_argument("--corpus-bands", nargs="*",
                    default=["1-30", "31-100", "101-200"])
    ap.add_argument("--corpus-games", type=int, default=40)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    jobs = jobs_from_arena(args.arena, args.arena_games)
    for band in args.corpus_bands:
        lo, hi = (int(x) for x in band.split("-"))
        jobs += jobs_from_corpus(lo, hi, args.corpus_games)
    print(f"{len(jobs)} games to replay", flush=True)
    with Pool(args.workers, maxtasksperchild=4) as pool:
        rows = list(pool.imap_unordered(measure, jobs))

    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["label"], []).append(r)
    print(f"\nmedian per game (land = day of the 2nd/3rd quadrant; "
          f"plantings = PLANT actions issued)\n")
    head = f"  {'who':22s} {'n':>3} {'win%':>5} " + " ".join(
        f"{k.replace('p_', '').replace('bank_', '$')[:8]:>8}" for k in KEYS)
    print(head)
    for label, rs in groups.items():
        cells = []
        for k in KEYS:
            vals = [r[k] for r in rs if r.get(k) is not None]
            cells.append(f"{statistics.median(vals):8.0f}" if vals
                         else f"{'-':>8}")
        win = 100 * sum(r["won"] for r in rs) / len(rs)
        print(f"  {label[:22]:22s} {len(rs):3d} {win:5.0f} " + " ".join(cells))


if __name__ == "__main__":
    main()
