"""Round robin: real agents play each other head to head, rated by Bradley-Terry.

The corpus and live-ladder test beds replay pinned tapes, so the opponent never
answers our moves. Here both seats are live programs that react to each other,
as on the ladder. Each of our agents (--ours) plays every field agent (--field)
on every seed; --ours-vs-ours adds our agents against each other and
--field-vs-field the field among itself. Games are played and stored by
tools/arena/arena.py (arena/games/<a>__vs__<b>__s<seed>.json, one process per
game), so a re-run plays only what is missing and --score-only rates the
stored games without playing any.

The rating is a Bradley-Terry fit (MM algorithm; a win counts 1, a tie 0.5)
in 400-scale Elo units, zero at the mean of the field agents (or at --anchor),
with a 90% interval from a bootstrap over games. The final Kaggle ranking is a
Bradley-Terry fit over ladder games too, so this is the same statistic on a
known field. A weak prior (--prior virtual games, half won, against a fixed
average player) keeps an unbeaten or winless agent finite.

    python -m tools.arena.round_robin \\
        --ours file:submissions/candidate-n8/main.py file:submissions/candidate-n7/main.py \\
        --field A nb_tschinkel_2945 --seeds 11-20 --both-seats --workers 2
    python -m tools.arena.round_robin --ours N2 N2m M2 --field A \\
        nb_haodou092_harvest_ledger --ours-vs-ours --score-only

Agents are anything arena.py accepts (an alias, an nb_* public program, a
live_* anchor, module:attr, file:<path>), optionally named as NAME=SPEC. A spec
without a name takes the name of an arena alias with the same spec, so that
alias's stored games count; otherwise its package directory
(file:submissions/candidate-n8/main.py -> candidate-n8) or module and attribute
(stack.l2_combo:n6 -> l2_combo.n6). Games this tool plays are stamped with a
fingerprint of each file: agent's code; a stored game whose name now means other
code (a different spec, or a rebuilt package) is stale: it is left out of the
score and played again.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.arena import arena  # noqa: E402

SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
# kaggriculture.json: 1 s per turn plus a 60 s overage bank per game.
OVERAGE_NOTE = ("Kaggle allows 1 s per turn plus a 60 s overage bank per game; "
                "one slow turn (often the first, loading a library) spends the "
                "bank rather than losing the game")


# ---------------------------------------------------------------- agents ----

def _canon(spec: str) -> str:
    """One spelling per spec: file: paths relative to the repo, posix."""
    if not spec.startswith("file:"):
        return spec
    path = Path(spec[len("file:"):])
    full = (path if path.is_absolute() else ROOT / path).resolve()
    try:
        return "file:" + full.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return "file:" + full.as_posix()


def _known() -> dict[str, str]:
    """Every name arena.py already resolves, with its spec (as spec_of does)."""
    table = {**arena.ALIASES, **arena._public_aliases()}
    table.update({n: "file:" + v[0] for n, v in arena.LIVE_ANCHORS.items()})
    return {n: _canon(s) for n, s in table.items()}


def _check(spec: str) -> None:
    if spec.startswith("file:"):
        path = ROOT / spec[len("file:"):]
        if not path.is_file():
            raise SystemExit(f"no such file: {path}")
        return
    # A repo module is checked on disk: importing it here would load the
    # agent (and rl/__init__) in the parent, which only schedules games.
    module = spec.rsplit(":", 1)[0]
    base = ROOT.joinpath(*module.split("."))
    if (ROOT / module.split(".")[0]).exists() and not (
            base.with_suffix(".py").is_file() or (base / "__init__.py").is_file()):
        raise SystemExit(f"no such module: {module} (in {spec})")


def resolve(arg: str, known: dict[str, str]) -> tuple[str, str]:
    """(name, spec) for one --ours / --field argument."""
    name, sep, spec = arg.partition("=")
    if not sep:
        name, spec = "", arg
    if spec == "random":
        return name or "random", spec
    if ":" not in spec:                           # a name arena.py knows
        spec, name = arena.spec_of(spec), name or spec
    spec = _canon(spec)
    _check(spec)
    if not name:
        same = [n for n, s in known.items() if s == spec]
        if same:
            name = same[0]
            if len(same) > 1:
                print(f"  note: {spec} is known as {', '.join(same)}; using "
                      f"{name} (write NAME={spec} to choose)")
        elif spec.startswith("file:"):
            path = Path(spec[len("file:"):])
            name = path.parent.name if path.name == "main.py" else path.stem
        else:
            module, attr = spec.rsplit(":", 1)
            name = f"{module.rsplit('.', 1)[-1]}.{attr}"
        name = re.sub(r"[^A-Za-z0-9_.-]", "-", name)
    if not SAFE_NAME.match(name):
        raise SystemExit(f"agent name {name!r} must be letters, digits, _ . -")
    if name in known and known[name] != spec:
        raise SystemExit(f"{name!r} already means {known[name]} in arena.py; "
                         f"name {spec} differently (NAME={spec})")
    return name, spec


def fingerprint(spec: str) -> str | None:
    """Hash of a self-contained agent file; None for a module import (its
    dependencies are not tracked)."""
    if spec.startswith("file:"):
        path = ROOT / spec[len("file:"):]
    elif spec.startswith("rl.public.") and spec.endswith(":agent"):
        path = ROOT / "rl" / "public" / (spec[len("rl.public."):-len(":agent")] + ".py")
    else:
        return None
    try:
        return hashlib.sha1(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


def _register(extra: dict[str, str]) -> None:
    """Pool initializer: teach a fresh worker's arena.py our new names."""
    arena.ALIASES.update(extra)


# ----------------------------------------------------------- schedule ------

def parse_seeds(tokens: list[str] | None) -> list[int] | None:
    if not tokens:
        return None
    out: list[int] = []
    for token in tokens:
        lo, sep, hi = token.partition("-")
        out += list(range(int(lo), int(hi) + 1)) if sep else [int(lo)]
    return sorted(set(out))


def make_pairs(ours: list[str], field: list[str], ours_vs_ours: bool,
               field_vs_field: bool) -> list[tuple[str, str]]:
    pairs = [(a, b) for a in ours for b in field]
    if ours_vs_ours:
        pairs += list(itertools.combinations(ours, 2))
    if field_vs_field:
        pairs += list(itertools.combinations(field, 2))
    return pairs


def make_jobs(pairs: list[tuple[str, str]], seeds: list[int],
              both_seats: bool) -> list[tuple[str, str, int]]:
    """Seed-major, so an interrupted run leaves every pair equally covered.
    With one seat per seed the seats alternate by seed parity (ours in seat 0
    on odd seeds), so a re-run over a different seed list keeps each stored
    game's seat and plays only what is missing."""
    jobs = []
    for seed in seeds:
        for a, b in pairs:
            if both_seats:
                jobs += [(a, b, seed), (b, a, seed)]
            else:
                jobs.append((a, b, seed) if seed % 2 else (b, a, seed))
    return jobs


def load_stored(pairs: list[tuple[str, str]]) -> dict[tuple[str, str, int], dict[str, Any]]:
    """Stored local games of these pairs, either seat, keyed (seat0, seat1, seed)."""
    out = {}
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            for path in arena.GAMES.glob(f"{x}__vs__{y}__s*.json"):
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                record.pop("tapes", None)
                if record.get("ladder_episode") or record.get("agents") != [x, y]:
                    continue
                out[(x, y, int(record["seed"]))] = record
    return out


def stale_reason(record: dict[str, Any], specs: dict[str, str],
                 prints: dict[str, str | None]) -> str | None:
    """Why a stored game no longer describes the named agents, if it doesn't."""
    stored_specs = record.get("specs") or [None, None]
    stored_prints = record.get("code_sha") or [None, None]
    for i, name in enumerate(record["agents"]):
        if stored_specs[i] is not None and _canon(stored_specs[i]) != specs[name]:
            return f"{name} was {stored_specs[i]}"
        if stored_prints[i] and prints.get(name) and stored_prints[i] != prints[name]:
            return f"{name} code changed ({stored_prints[i]} -> {prints[name]})"
    return None


def _stamp(game_id: str, agents: list[str], prints: dict[str, str | None]) -> None:
    """Record which code played a game this tool just stored."""
    path = arena.GAMES / f"{game_id}.json"
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    record["code_sha"] = [prints.get(n) for n in agents]
    path.write_text(json.dumps(record), encoding="utf-8")


def _play(job: tuple[str, str, int]) -> dict[str, Any]:
    """arena.play_one, with SystemExit (spec_of's "unknown agent") made a
    crash result: uncaught, it would kill the worker and hang the pool."""
    try:
        return arena.play_one(job)
    except SystemExit as error:
        a, b, seed = job
        return {"game_id": f"{a}__vs__{b}__s{seed}", "agents": [a, b],
                "seed": seed, "rewards": [0.0, 0.0],
                "statuses": ["CRASH", "CRASH"], "winner": None,
                "error": f"SystemExit: {error}"}


def play(jobs: list[tuple[str, str, int]], workers: int, extra: dict[str, str],
         prints: dict[str, str | None]) -> list[dict[str, Any]]:
    """Play the jobs; return the crashed ones (arena stores no crash)."""
    crashed = []
    # One process per game, as arena.py tourney: agents keep module state.
    with Pool(workers, initializer=_register, initargs=(extra,),
              maxtasksperchild=1) as pool:
        for k, result in enumerate(pool.imap_unordered(_play, jobs), 1):
            if result.get("error"):
                crashed.append(result)
                note = f"  CRASH {result['error']}"
            else:
                _stamp(result["game_id"], result["agents"], prints)
                note = (f"  ms_max {result.get('ms_max')}"
                        f"  errors {result.get('turn_errors')}")
            print(f"  [{k}/{len(jobs)}] {' vs '.join(result['agents']):60s} "
                  f"s{result['seed']}: {result['rewards'][0]:9,.0f} : "
                  f"{result['rewards'][1]:9,.0f}  {result['statuses']}{note}",
                  flush=True)
    return crashed


# ------------------------------------------------------- Bradley-Terry -----

def bt_fit(ia: np.ndarray, ib: np.ndarray, sa: np.ndarray, k: int,
           weights: np.ndarray, prior: float, tol: float = 1e-8,
           max_iter: int = 20000) -> np.ndarray:
    """Hunter's MM for Bradley-Terry; ratings in 400*log10 units.

    Each agent also plays `prior` virtual games, scoring half, against a fixed
    player of strength 1, which keeps every strength finite and positive."""
    wins = np.zeros(k)
    np.add.at(wins, ia, weights * sa)
    np.add.at(wins, ib, weights * (1.0 - sa))
    games = np.zeros((k, k))
    np.add.at(games, (ia, ib), weights)
    games = games + games.T
    p = np.ones(k)
    for _ in range(max_iter):
        denom = (games / (p[:, None] + p[None, :])).sum(axis=1) + prior / (p + 1.0)
        new = (wins + prior / 2.0) / denom
        done = float(np.max(np.abs(np.log(new / p)))) < tol
        p = new
        if done:
            break
    return 400.0 * np.log10(p)


def rate(games: list[dict[str, Any]], names: list[str], zero: list[int],
         prior: float, draws: int, seed: int) -> dict[str, np.ndarray]:
    index = {n: i for i, n in enumerate(names)}
    ia = np.array([index[g["agents"][0]] for g in games])
    ib = np.array([index[g["agents"][1]] for g in games])
    sa = np.array([g["score"] for g in games], dtype=float)
    k = len(names)

    def centred(weights):
        r = bt_fit(ia, ib, sa, k, weights, prior)
        return r - r[zero].mean()

    point = centred(np.ones(len(games)))
    rng = np.random.default_rng(seed)
    boot = np.array([centred(np.bincount(rng.integers(0, len(games), len(games)),
                                         minlength=len(games)).astype(float))
                     for _ in range(draws)]) if draws else point[None, :]
    return {"rating": point, "lo": np.percentile(boot, 5, axis=0),
            "hi": np.percentile(boot, 95, axis=0),
            "above_zero": (boot > 0).mean(axis=0)}


# -------------------------------------------------------------- report -----

def _wlt(scores: list[float]) -> str:
    w = sum(s == 1.0 for s in scores)
    l_ = sum(s == 0.0 for s in scores)
    return f"{w}-{l_}-{len(scores) - w - l_}"


def report(games: list[dict[str, Any]], ours: list[str], field: list[str],
           crashed: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    ours_set = set(ours)
    names = [n for n in ours + field if any(n in g["agents"] for g in games)]
    missing = [n for n in ours + field if n not in names]
    if missing:
        print(f"\n  no scored games for: {', '.join(missing)}")
    if not games:
        raise SystemExit("no games to score")
    if args.anchor:
        if args.anchor not in names:
            raise SystemExit(f"--anchor {args.anchor} has no scored games")
        zero_names = [args.anchor]
    else:
        zero_names = [n for n in names if n not in ours_set] or names
    zero = [names.index(n) for n in zero_names]
    fit = rate(games, names, zero, args.prior, args.boot, args.boot_seed)

    per: dict[str, list[float]] = defaultdict(list)
    for g in games:
        per[g["agents"][0]].append(g["score"])
        per[g["agents"][1]].append(1.0 - g["score"])
    zero_label = args.anchor or ("mean of the field" if zero_names != names
                                 else "mean of all agents")
    print(f"\n  Bradley-Terry ratings (Elo units, 0 = {zero_label}); "
          f"90% interval from {args.boot} bootstrap draws over {len(games)} games")
    print(f"  {'#':>3} {'agent':52s} {'role':5s} {'games':>5} {'W-L-T':>10} "
          f"{'score':>6} {'rating':>7} {'90% interval':>15} {'P(>0)':>6}")
    order = sorted(range(len(names)), key=lambda i: -fit["rating"][i])
    table = []
    for rank, i in enumerate(order, 1):
        n = names[i]
        s = per[n]
        role = "ours" if n in ours_set else "field"
        print(f"  {rank:3d} {n[:52]:52s} {role:5s} {len(s):5d} {_wlt(s):>10} "
              f"{100 * sum(s) / len(s):5.1f}% {fit['rating'][i]:+7.0f} "
              f"[{fit['lo'][i]:+6.0f},{fit['hi'][i]:+6.0f}] "
              f"{fit['above_zero'][i]:6.2f}")
        table.append({"agent": n, "role": role, "games": len(s),
                      "score": sum(s) / len(s),
                      "rating": round(float(fit["rating"][i]), 1),
                      "lo": round(float(fit["lo"][i]), 1),
                      "hi": round(float(fit["hi"][i]), 1),
                      "p_above_zero": round(float(fit["above_zero"][i]), 3)})

    # Each of ours against each opponent.
    records = []
    for a in ours:
        print(f"\n  {a} vs each opponent (margin = our money minus theirs)")
        print(f"    {'opponent':52s} {'games':>5} {'W-L-T':>10} {'score':>6} "
              f"{'mean margin':>12} {'our mean':>10}")
        for b in [n for n in field + ours if n != a]:
            mine = [g for g in games if set(g["agents"]) == {a, b}]
            if not mine:
                continue
            seat = [g["agents"].index(a) for g in mine]
            scores = [g["score"] if s == 0 else 1.0 - g["score"]
                      for g, s in zip(mine, seat)]
            margins = [g["rewards"][s] - g["rewards"][1 - s] for g, s in zip(mine, seat)]
            money = [g["rewards"][s] for g, s in zip(mine, seat)]
            print(f"    {b[:52]:52s} {len(mine):5d} {_wlt(scores):>10} "
                  f"{100 * sum(scores) / len(scores):5.1f}% "
                  f"{statistics.mean(margins):+12,.0f} {statistics.mean(money):10,.0f}")
            records.append({"agent": a, "opponent": b, "games": len(mine),
                            "wlt": _wlt(scores), "score": sum(scores) / len(scores),
                            "mean_margin": statistics.mean(margins)})

    # Health: statuses, turn errors, turn times.
    statuses: dict[str, Counter] = defaultdict(Counter)
    errors: Counter = Counter()
    ms_max: dict[str, list[float]] = defaultdict(list)
    ms_mean: dict[str, list[float]] = defaultdict(list)
    flags: dict[str, list[str]] = defaultdict(list)
    for g in games:
        ours_game = bool(ours_set & set(g["agents"]))
        for i, n in enumerate(g["agents"]):
            status = (g.get("statuses") or ["?", "?"])[i]
            err = (g.get("turn_errors") or [0, 0])[i] or 0
            slow = (g.get("ms_max") or [None, None])[i]
            if status != "DONE":
                statuses[n][status] += 1
                if ours_game:
                    flags["status not DONE"].append(f"{g['game_id']}  {n}: {status}")
            errors[n] += err
            if err and ours_game:
                flags["turn_errors > 0"].append(f"{g['game_id']}  {n}: {err}")
            if slow is not None:
                ms_max[n].append(slow)
                if slow > args.slow_ms and ours_game:
                    flags[f"ms_max > {args.slow_ms:.0f}"].append(
                        f"{g['game_id']}  {n}: {slow:,.0f} ms")
            mean = (g.get("ms_mean") or [None, None])[i]
            if mean is not None:
                ms_mean[n].append(mean)
    for c in crashed:
        for n in c["agents"]:
            statuses[n]["CRASH"] += 1
        flags["crashed (not stored)"].append(f"{c['game_id']}: {c.get('error')}")

    print("\n  statuses other than DONE:")
    if not statuses:
        print("    none")
    for n in names:
        if statuses[n]:
            print(f"    {n:52s} " + ", ".join(f"{s} x{c}" for s, c in
                                               statuses[n].most_common()))
    print("\n  turn errors (total), turn time (ms: max, median of per-game max, "
          f"mean), games with a turn over {args.slow_ms:.0f} ms:")
    for n in names:
        tops = ms_max[n]
        print(f"    {n[:52]:52s} {'ours ' if n in ours_set else 'field'} "
              f"errors {errors[n]:5d}   max "
              f"{(max(tops) if tops else float('nan')):8,.0f}   median "
              f"{(statistics.median(tops) if tops else float('nan')):8,.0f}   mean "
              f"{(statistics.mean(ms_mean[n]) if ms_mean[n] else float('nan')):6.1f}"
              f"   slow {sum(t > args.slow_ms for t in tops):4d}/{len(tops)}")

    print("\n  flags on games involving our agents:")
    if not flags:
        print("    none")
    for kind, items in flags.items():
        print(f"    {kind}: {len(items)} game-seats")
        shown = items if args.flag_limit == 0 else items[:args.flag_limit]
        for item in shown:
            print(f"      {item}")
        if len(shown) < len(items):
            print(f"      ... {len(items) - len(shown)} more (--flag-limit 0 lists all)")
    if any(k.startswith("ms_max") for k in flags):
        print(f"    ({OVERAGE_NOTE})")
    return {"ratings": table, "records": records,
            "statuses": {n: dict(c) for n, c in statuses.items() if c},
            "turn_errors": dict(errors), "flags": {k: v for k, v in flags.items()},
            "ms_max": {n: max(v) for n, v in ms_max.items() if v}}


# ---------------------------------------------------------------- main -----

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ours", nargs="+", required=True,
                    help="our agents: arena names or specs, optionally NAME=SPEC")
    ap.add_argument("--field", nargs="*", default=[],
                    help="opponents: arena names or specs, optionally NAME=SPEC")
    ap.add_argument("--seeds", nargs="+", default=None,
                    help="seeds or ranges (11 12 20-29); required to play. "
                         "Scoring uses only these seeds; with --score-only and "
                         "no --seeds, every stored seed")
    ap.add_argument("--both-seats", action="store_true",
                    help="play each pair in both seats on every seed "
                         "(otherwise the seats alternate from seed to seed)")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--ours-vs-ours", action="store_true",
                    help="also play our agents against each other")
    ap.add_argument("--field-vs-field", action="store_true",
                    help="also play the field agents against each other")
    ap.add_argument("--score-only", action="store_true",
                    help="play nothing; rate the stored games")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan (games to play, stored, stale) and stop")
    ap.add_argument("--anchor", default=None,
                    help="agent rated 0 (default: the mean of the field is 0)")
    ap.add_argument("--prior", type=float, default=1.0,
                    help="virtual games per agent, half won, against an "
                         "average player (must be > 0)")
    ap.add_argument("--boot", type=int, default=500, help="bootstrap draws")
    ap.add_argument("--boot-seed", type=int, default=0)
    ap.add_argument("--drop-faulty", action="store_true",
                    help="leave out of the rating any game with a status "
                         "other than DONE")
    ap.add_argument("--slow-ms", type=float, default=1000.0,
                    help="flag games whose slowest turn is above this")
    ap.add_argument("--flag-limit", type=int, default=12,
                    help="flagged games listed per kind (0 = all)")
    ap.add_argument("--json", type=Path, default=None,
                    help="also write the ratings and records to this file")
    args = ap.parse_args()
    if args.prior <= 0:
        raise SystemExit("--prior must be > 0")

    known = _known()
    resolved: dict[str, str] = {}
    lists: dict[str, list[str]] = {"ours": [], "field": []}
    for role in ("ours", "field"):
        for arg in getattr(args, role):
            name, spec = resolve(arg, known)
            if resolved.get(name, spec) != spec:
                raise SystemExit(f"{name!r} given for two specs")
            resolved[name] = spec
            if name not in lists[role]:
                lists[role].append(name)
    ours, field = lists["ours"], lists["field"]
    both = set(ours) & set(field)
    if both:
        raise SystemExit(f"in both --ours and --field: {', '.join(sorted(both))}")
    extra = {n: s for n, s in resolved.items() if n not in known}
    arena.ALIASES.update(extra)
    prints = {n: fingerprint(s) for n, s in resolved.items()}
    print("  agents:")
    for n, s in resolved.items():
        role = "ours " if n in ours else "field"
        print(f"    {role} {n:52s} {s}" + (f"  [{prints[n]}]" if prints[n] else ""))

    pairs = make_pairs(ours, field, args.ours_vs_ours, args.field_vs_field)
    if not pairs:
        raise SystemExit("no pairs: give --field, or --ours-vs-ours with two of ours")
    seeds = parse_seeds(args.seeds)
    stored = load_stored(pairs)
    crashed: list[dict[str, Any]] = []

    if not args.score_only:
        if not seeds:
            raise SystemExit("--seeds is required to play (or pass --score-only)")
        jobs = make_jobs(pairs, seeds, args.both_seats)
        todo, stale = [], 0
        for job in jobs:
            record = stored.get(job)
            if record is None:
                todo.append(job)
            elif stale_reason(record, resolved, prints):
                todo.append(job)
                stale += 1
        seconds = [r["seconds"] for r in stored.values() if r.get("seconds")]
        eta = (f", about {len(todo) * statistics.mean(seconds) / max(1, args.workers) / 3600:.1f} h "
               f"at {statistics.mean(seconds):.0f} s a game" if seconds and todo else "")
        print(f"\n  plan: {len(pairs)} pairs x {len(seeds)} seeds x "
              f"{2 if args.both_seats else 1} seat(s) = {len(jobs)} games; "
              f"{len(jobs) - len(todo)} stored, {stale} stale to replay, "
              f"{len(todo)} to play on {args.workers} workers{eta}", flush=True)
        if args.dry_run:
            return
        if todo:
            crashed = play(todo, args.workers, extra, prints)
            stored = load_stored(pairs)
    elif args.dry_run:
        print(f"\n  --score-only: {len(stored)} stored games for {len(pairs)} pairs")
        return

    games, stale_notes, unverified, faulty = [], Counter(), 0, 0
    for key in sorted(stored, key=lambda k: (k[2], k[0], k[1])):
        record = stored[key]
        if seeds and key[2] not in seeds:
            continue
        reason = stale_reason(record, resolved, prints)
        if reason:
            stale_notes[reason] += 1
            continue
        if any(s != "DONE" for s in record.get("statuses") or ["?"]):
            faulty += 1
            if args.drop_faulty:
                continue
        if any(prints.get(n) for n in record["agents"]) and not record.get("code_sha"):
            unverified += 1
        ra, rb = record["rewards"]
        record["score"] = 1.0 if ra > rb else 0.0 if ra < rb else 0.5
        games.append(record)

    print(f"\n  coverage: {len(games)} games scored over {len(pairs)} pairs"
          + (f" (seeds {seeds[0]}..{seeds[-1]}, {len(seeds)} seeds)" if seeds
             else " (every stored seed)"))
    for reason, count in stale_notes.most_common():
        print(f"    left out {count} stale game(s): {reason}")
    if unverified:
        print(f"    {unverified} game(s) played before code fingerprints; their "
              f"file: agents' code is assumed unchanged")
    if faulty:
        print(f"    {faulty} game(s) with a status other than DONE "
              + ("left out (--drop-faulty)" if args.drop_faulty else "kept"))
    count = Counter(frozenset(g["agents"]) for g in games)
    per_seed = 2 if args.both_seats else 1
    short = [(a, b, count[frozenset((a, b))]) for a, b in pairs
             if (seeds and count[frozenset((a, b))] < len(seeds) * per_seed)
             or not count[frozenset((a, b))]]
    for a, b, c in short:
        want = f"/{len(seeds) * per_seed}" if seeds else ""
        print(f"    short: {a} vs {b}: {c}{want} games")

    summary = report(games, ours, field, crashed, args)
    if args.json:
        summary.update({"agents": resolved, "fingerprints": prints,
                        "seeds": seeds, "games": len(games)})
        args.json.write_text(json.dumps(summary, indent=1), encoding="utf-8")
        print(f"\n  wrote {args.json}")


if __name__ == "__main__":
    main()
