"""Arena: play any agent against any other and watch the game in the real viewer.

The engine ships Kaggle's own game viewer (visualizer/default/dist/index.html,
a single self-contained page). `env.render(mode="html")` injects a finished
game into it, so every game played here can be opened in a browser and
scrubbed turn by turn -- both farms, the town, the market, every hand.

Every game is stored compactly (seed + both sides' action tapes, ~100 KB) in
arena/games/. A rendered replay is ~45 MB, so games are rendered on demand:
the engine is deterministic given the seed and both action streams, so a
stored game re-renders identically. `play` renders what it plays by default;
`tourney` only stores, and you render the games you want to look at.

    python -m tools.arena.arena agents
    python -m tools.arena.arena play K nb_tschinkel_2945 --seeds 11 12
    python -m tools.arena.arena tourney K J K2 nb_tschinkel_2945 --seeds 11 12
    python -m tools.arena.arena render <game_id>
    python -m tools.arena.arena episode 105114868          # a real ladder game
    python -m tools.arena.arena index                        # rebuild the page
    python -m tools.arena.arena open                         # open the index

Agents are named by alias (see `agents`), by `module:attr`, or `random`.
Extracted public agents in rl/public/nb_*.py are picked up automatically.
"""

from __future__ import annotations

import argparse
import base64
import html
import itertools
import json
import os
import subprocess
import sys
import time
import zlib
from multiprocessing import Pool
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

ARENA = ROOT / "arena"
GAMES = ARENA / "games"
REPLAYS = ARENA / "replays"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{episode}.json"
CONFIG = {"episodeSteps": 720, "runTimeout": 36000, "actTimeout": 60}

ALIASES = {
    "K": "rl.candidate_k:agent",
    "K2": "rl.candidate_k2:agent",
    "J": "rl.candidate_j:agent",
    "J2": "rl.candidate_j2:agent",
    "H2": "rl.candidate_h2_package:agent",
    "I": "rl.candidate_i:agent",
    "aurax7": "rl.public_agents:aurax7",
    "v34": "rl.public_agents:v34",
    # Agent A: the exact packaged file (a verbatim public clone). Agent L: that
    # file plus our own layers. Agent M: bespoke.
    "A": "file:submissions/agent-a/main.py",
    "L": "rl.candidate_l:front_gate120",       # the live Agent L
    "L2": "rl.l2_combo:ship",                  # submissions/candidate-l2
    "L3": "rl.l2_combo:ship_lib",              # submissions/candidate-l3
    "L4": "rl.l2_combo:l4",
    "L4b": "rl.l2_combo:l4b",
    "L4c": "rl.l2_combo:l4c",
    "L4e": "rl.l2_combo:l4e",                # submissions/candidate-l4e
    "L5": "rl.l2_combo:l5h",                 # submissions/candidate-l5
    "L5race": "rl.l2_combo:l5e",
    "L5lib": "rl.l2_combo:l5lib",
    "M1": "rl.l2_combo:m1",
    "M2": "rl.l2_combo:m2",
    "M3": "rl.l2_combo:m3",
    "M4": "rl.l2_combo:m4",
    "M5": "rl.l2_combo:m5",
    "M7": "rl.l2_combo:m7",
    "M8": "rl.l2_combo:m8",
    "M": "rl.l2_combo:m8",                   # submissions/candidate-m
    "M9": "rl.l2_combo:m9",
    "L6": "rl.l2_combo:l6",
    "M10": "rl.l2_combo:m10",
    "N1": "rl.l2_combo:n1",
    "M11": "rl.l2_combo:m11",
    "M2": "rl.l2_combo:m11",                 # submissions/candidate-m2
    "N2": "rl.l2_combo:n2",
    "N2m": "rl.l2_combo:n2m",
    "HLq": "rl.l2_combo:hl_plain",
    "N": "rl.l2_combo:n2m",                   # submissions/candidate-n
    "N3r7": "rl.l2_combo:n3r7",
    "N3r5": "rl.l2_combo:n3r5",
    "L_se": "rl.candidate_l:agent",
    "A_noV219": "rl.candidate_l:no_v219",
    "L_gate140": "rl.candidate_l:gate140",
    "L_gate120": "rl.candidate_l:gate120",
    "L_front": "rl.candidate_l:front",
    "L_front_gate": "rl.candidate_l:front_gate",
    "L_fg140": "rl.candidate_l:front_gate140",
    "L_fg120": "rl.candidate_l:front_gate120",
    "L_fg100": "rl.candidate_l:front_gate100",
    "L_fg0": "rl.candidate_l:front_gate0",
    "L2_fw150": "rl.candidate_l:fw150",
    "L2_fw100": "rl.candidate_l:fw100",
    "L2_fw250": "rl.candidate_l:fw250",
}


def _public_aliases() -> dict[str, str]:
    out = {}
    for path in sorted((ROOT / "rl" / "public").glob("*.py")):
        if path.stem.startswith(("nb_", "ours_")):
            out[path.stem] = f"rl.public.{path.stem}:agent"
    return out


# Our own live submissions, as the exact files Kaggle rated. Each was matched
# to its submission by byte count against the API's totalBytes, so these are
# the rated code itself, not "probably the same" local source. Ratings as
# read 2026-09-26. They anchor the scale that turns local tournament results
# into a predicted live rating (tools/arena/calibrate.py).
LIVE_ANCHORS = {
    "live_J": ("submissions/candidate-j/main.py", 56489751, 685.3),
    "live_C2": ("submissions/candidate-c2/main.py", 56498060, 1049.7),
    "live_F": ("submissions/candidate-f/main.py", 56439601, 1343.7),
    "live_I": ("submissions/candidate-i/main.py", 56317289, 1381.4),
    "live_K": ("submissions/candidate-k/main.py", 56493502, 1467.1),
    "live_H2": ("submissions/candidate-h2/main.py", 56434220, 1576.2),
}


def spec_of(name: str) -> str:
    if name == "random" or ":" in name:
        return name
    if name in LIVE_ANCHORS:
        return "file:" + LIVE_ANCHORS[name][0]
    table = {**ALIASES, **_public_aliases()}
    if name not in table:
        raise SystemExit(f"unknown agent {name!r}; run `agents` for the list")
    return table[name]


def load(name: str):
    spec = spec_of(name)
    if spec == "random":
        return "random"
    if spec.startswith("file:"):
        # Loaded exactly the way Kaggle loads a submission.
        from kaggle_environments.agent import get_last_callable
        path = ROOT / spec[len("file:"):]
        return get_last_callable(path.read_text(encoding="utf-8"),
                                 path=str(path))
    module_name, attr = spec.rsplit(":", 1)
    import importlib
    target = getattr(importlib.import_module(module_name), attr)
    # A zero-argument callable is a factory (rl.l2_combo:ship_lib etc.): build
    # the agent. Passing the factory itself as the agent made it raise every
    # turn, the opponent scored 0, and a head-to-head read +164k.
    # A factory's arguments all have defaults (rl.l2_combo:l4e(window=8)).
    code = getattr(target, "__code__", None)
    required = (code.co_argcount - len(target.__defaults__ or ())) if code is not None else None
    if required == 0 and not code.co_flags & 0x04:
        return target()
    return target


def _pack(obj: Any) -> str:
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.b64encode(zlib.compress(raw, 9)).decode()


def _unpack(blob: str) -> Any:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def _timed(agent, bucket: list[float]):
    # Kaggle calls an agent with only as many arguments as it declares
    # (kaggle_environments/agent.py truncates to __code__.co_argcount). Several
    # of our own submissions end in a one-argument decide(observation); calling
    # those with (observation, configuration) raised every turn, the farm stood
    # still, and two live-rated anchors scored exactly the 3,000 they started
    # with. The wrapper must pass what Kaggle passes.
    code = getattr(agent, "__code__", None)
    arity = code.co_argcount if code is not None else 2

    def wrapped(observation, configuration=None):
        start = time.perf_counter()
        try:
            return agent(*(observation, configuration)[:arity])
        except Exception:
            # The engine swallows an agent's exception and still reports the
            # game DONE, so a raising agent looks like a quiet one. Count it.
            wrapped.errors += 1
            raise
        finally:
            bucket.append((time.perf_counter() - start) * 1000.0)
    wrapped.errors = 0
    return wrapped


def _make(seed: int):
    from kaggle_environments import make
    return make("kaggriculture", configuration={**CONFIG, "seed": seed},
                debug=False)


def _agents_field(names: list[str]) -> list[dict[str, Any]]:
    # The viewer reads info.Agents[i].name -- lowercase -- while Kaggle's own
    # replay files store "Name". Without the lowercase key every game,
    # including genuine ladder replays, is labelled "Player 1" / "Player 2".
    return [{"index": i, "name": n, "Name": n, "ThumbnailUrl": None}
            for i, n in enumerate(names)]


def _label(env, names: list[str]) -> None:
    """Put the agents' names where the viewer and Kaggle replays keep them."""
    info = dict(getattr(env, "info", None) or {})
    info["Agents"] = _agents_field(names)
    info["TeamNames"] = list(names)
    env.info = info


def play_one(job: tuple[str, str, int]) -> dict[str, Any]:
    """One game, stored compactly; a crash becomes a result, not an abort."""
    try:
        return _play_one(job)
    except Exception as error:  # one broken agent must not end a tourney
        a_name, b_name, seed = job
        return {"game_id": f"{a_name}__vs__{b_name}__s{seed}",
                "agents": [a_name, b_name], "seed": seed,
                "rewards": [0.0, 0.0], "statuses": ["CRASH", "CRASH"],
                "winner": None, "error": f"{type(error).__name__}: {error}"}


def _play_one(job: tuple[str, str, int]) -> dict[str, Any]:
    a_name, b_name, seed = job
    sys.path.insert(0, str(ROOT))
    times: list[list[float]] = [[], []]
    agents = []
    for i, name in enumerate((a_name, b_name)):
        agent = load(name)
        agents.append(agent if agent == "random" else _timed(agent, times[i]))
    started = time.time()
    env = _make(seed)
    env.run(agents)
    final = env.steps[-1]
    rewards = [float(final[i].get("reward") or 0.0) for i in (0, 1)]
    statuses = [str(final[i].get("status")) for i in (0, 1)]
    turn_errors = [getattr(a, "errors", 0) for a in agents]
    for i in (0, 1):
        # An agent that raised is not DONE whatever the engine says.
        if turn_errors[i] and statuses[i] == "DONE":
            statuses[i] = f"RAISED_{turn_errors[i]}"
    tapes = [_pack([env.steps[s][i].get("action") for s in range(len(env.steps))])
             for i in (0, 1)]
    game_id = f"{a_name}__vs__{b_name}__s{seed}"
    record = {
        "game_id": game_id, "agents": [a_name, b_name],
        "specs": [spec_of(a_name), spec_of(b_name)], "seed": seed,
        "rewards": rewards, "statuses": statuses,
        "winner": (a_name if rewards[0] > rewards[1] else
                   b_name if rewards[1] > rewards[0] else None),
        "turn_errors": turn_errors,
        "ms_mean": [round(sum(t) / len(t), 1) if t else None for t in times],
        "ms_max": [round(max(t), 1) if t else None for t in times],
        "seconds": round(time.time() - started, 1),
        "played_unix": int(time.time()),
        "tapes": tapes,
    }
    GAMES.mkdir(parents=True, exist_ok=True)
    (GAMES / f"{game_id}.json").write_text(json.dumps(record), encoding="utf-8")
    return {k: v for k, v in record.items() if k != "tapes"}


def _replay_env(record: dict[str, Any]):
    """Re-run a stored game from its tapes; deterministic, so it is the game."""
    from rl.replay_agent import build_replay_agent
    env = _make(record["seed"])
    env.run([build_replay_agent(tuple(_unpack(t))) for t in record["tapes"]])
    got = [float(env.steps[-1][i].get("reward") or 0.0) for i in (0, 1)]
    if [round(x) for x in got] != [round(x) for x in record["rewards"]]:
        print(f"  warning: re-render scored {got}, stored game scored "
              f"{record['rewards']} -- an agent was not deterministic "
              f"or the engine changed", flush=True)
    return env


def render(game_id: str) -> Path:
    record = json.loads((GAMES / f"{game_id}.json").read_text(encoding="utf-8"))
    env = _replay_env(record)
    _label(env, record["agents"])
    REPLAYS.mkdir(parents=True, exist_ok=True)
    out = REPLAYS / f"{game_id}.html"
    out.write_text(env.render(mode="html"), encoding="utf-8")
    return out


def render_episode(ref: str) -> Path:
    """A real ladder game, from an episode id or a downloaded replay file."""
    import requests
    from kaggle_environments.utils import get_player
    from kaggle_environments.envs.kaggriculture import kaggriculture as K

    path = Path(ref)
    if path.is_file():
        replay = json.loads(path.read_text(encoding="utf-8"))
    else:
        response = requests.get(REPLAY_URL.format(episode=ref), timeout=300)
        response.raise_for_status()
        replay = response.json()
    info = replay.get("info") or {}
    names = [a.get("Name") or a.get("name") or f"P{i + 1}"
             for i, a in enumerate(info.get("Agents") or [])] or ["P1", "P2"]
    info["TeamNames"] = names
    info["Agents"] = _agents_field(names)
    replay["info"] = info
    window_kaggle = {"debug": False, "playing": True, "step": 0,
                     "controls": True, "environment": replay, "logs": []}
    page = get_player(window_kaggle, K.html_renderer(None, "html"))
    REPLAYS.mkdir(parents=True, exist_ok=True)
    episode = info.get("EpisodeId") or path.stem
    safe = "_".join("".join(c if c.isalnum() else "-" for c in n)[:20]
                    for n in names)
    out = REPLAYS / f"ladder_{episode}__{safe}.html"
    out.write_text(page, encoding="utf-8")
    rewards = replay.get("rewards") or []
    record = {"game_id": out.stem, "agents": names, "seed": info.get("seed"),
              "rewards": rewards, "statuses": replay.get("statuses") or [],
              "winner": (names[0] if rewards and rewards[0] > rewards[1] else
                         names[1] if rewards and rewards[1] > rewards[0]
                         else None),
              "ladder_episode": episode, "played_unix": int(time.time())}
    GAMES.mkdir(parents=True, exist_ok=True)
    (GAMES / f"{out.stem}.json").write_text(json.dumps(record),
                                            encoding="utf-8")
    return out


def _records() -> list[dict[str, Any]]:
    out = []
    for path in sorted(GAMES.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        record.pop("tapes", None)
        out.append(record)
    return out


def standings(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table: dict[str, dict[str, Any]] = {}
    for r in records:
        if r.get("ladder_episode"):
            continue
        for i, name in enumerate(r["agents"]):
            row = table.setdefault(name, {"agent": name, "games": 0, "wins": 0,
                                          "draws": 0, "score": 0.0,
                                          "margin": 0.0, "errors": 0})
            mine, theirs = r["rewards"][i], r["rewards"][1 - i]
            row["games"] += 1
            row["wins"] += mine > theirs
            row["draws"] += mine == theirs
            row["score"] += mine
            row["margin"] += mine - theirs
            row["errors"] += r["statuses"][i] != "DONE"
    rows = list(table.values())
    for row in rows:
        g = max(1, row["games"])
        row["win_rate"] = row["wins"] / g
        row["mean_score"] = row["score"] / g
        row["mean_margin"] = row["margin"] / g
    rows.sort(key=lambda r: (-r["win_rate"], -r["mean_margin"]))
    return rows


def build_index() -> Path:
    records = _records()
    rendered = {p.stem for p in REPLAYS.glob("*.html")}
    table = standings(records)
    esc = html.escape

    def watch(r):
        gid = r["game_id"]
        if gid in rendered:
            return f'<a href="replays/{esc(gid)}.html">watch</a>'
        return (f'<code title="render it first">python -m tools.arena.arena '
                f'render {esc(gid)}</code>')

    stand_rows = "".join(
        f"<tr><td>{i + 1}</td><td>{esc(r['agent'])}</td><td>{r['games']}</td>"
        f"<td>{r['wins']}</td><td>{100 * r['win_rate']:.0f}%</td>"
        f"<td>{r['mean_score']:,.0f}</td><td>{r['mean_margin']:+,.0f}</td>"
        f"<td>{r['errors']}</td></tr>" for i, r in enumerate(table))
    game_rows = "".join(
        f"<tr><td>{esc(' vs '.join(r['agents']))}</td>"
        f"<td>{r.get('seed')}</td>"
        f"<td>{' : '.join(f'{x:,.0f}' for x in r.get('rewards') or [])}</td>"
        f"<td>{esc(str(r.get('winner') or 'draw'))}</td>"
        f"<td>{'ladder' if r.get('ladder_episode') else 'local'}</td>"
        f"<td>{watch(r)}</td></tr>"
        for r in sorted(records, key=lambda r: -r.get("played_unix", 0)))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Kaggriculture Arena</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{ --bg:#f7f5ef; --fg:#1f2421; --muted:#6b6f69; --line:#dcd8cc;
        --accent:#2f6b3a; --card:#ffffff; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#15171a; --fg:#e7e5df; --muted:#9a9d97; --line:#2c2f33;
          --accent:#7fc58a; --card:#1c1f23; }} }}
body {{ margin:0; background:var(--bg); color:var(--fg);
       font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:22px; margin:0 0 4px; }} h2 {{ font-size:17px; margin:28px 0 8px; }}
p.sub {{ color:var(--muted); margin:0 0 16px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
        overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }}
th,td {{ text-align:left; padding:7px 10px; border-bottom:1px solid var(--line);
        white-space:nowrap; }}
th {{ color:var(--muted); font-weight:600; font-size:13px; }}
a {{ color:var(--accent); font-weight:600; }}
code {{ font-size:12px; color:var(--muted); }}
</style></head><body><main>
<h1>Kaggriculture Arena</h1>
<p class="sub">{len(records)} games stored. Standings count local games only;
ladder episodes are real Kaggle games, shown for watching.</p>
<h2>Standings</h2>
<div class="card"><table><tr><th>#</th><th>agent</th><th>games</th><th>wins</th>
<th>win rate</th><th>mean score</th><th>mean margin</th><th>errors</th></tr>
{stand_rows}</table></div>
<h2>Games</h2>
<div class="card"><table><tr><th>match</th><th>seed</th><th>score</th>
<th>winner</th><th>kind</th><th></th></tr>{game_rows}</table></div>
</main></body></html>"""
    ARENA.mkdir(parents=True, exist_ok=True)
    out = ARENA / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


def _open(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # noqa: S606 -- local file, the user's browser
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("agents")
    p = sub.add_parser("play")
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--seeds", type=int, nargs="+", default=[11])
    p.add_argument("--both-seats", action="store_true")
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--open", action="store_true")
    t = sub.add_parser("tourney")
    t.add_argument("agents", nargs="+")
    t.add_argument("--seeds", type=int, nargs="+", default=[11, 12])
    t.add_argument("--workers", type=int, default=8)
    t.add_argument("--vs", default=None,
                   help="play every listed agent against this one only")
    t.add_argument("--skip-existing", action="store_true",
                   help="do not replay games already in arena/games")
    r = sub.add_parser("render"); r.add_argument("game_id")
    r.add_argument("--open", action="store_true")
    e = sub.add_parser("episode"); e.add_argument("ref")
    e.add_argument("--open", action="store_true")
    sub.add_parser("index")
    sub.add_parser("open")
    args = ap.parse_args()

    if args.cmd == "agents":
        for name, spec in {**ALIASES, **_public_aliases()}.items():
            print(f"  {name:32s} {spec}")
        for name, (path, ref, rating) in LIVE_ANCHORS.items():
            print(f"  {name:32s} file:{path}  (submission {ref}, "
                  f"live {rating})")
        return
    if args.cmd == "play":
        jobs = [(args.a, args.b, s) for s in args.seeds]
        if args.both_seats:
            jobs += [(args.b, args.a, s) for s in args.seeds]
        for job in jobs:
            result = play_one(job)
            print(f"  {' vs '.join(result['agents'])} seed {result['seed']}: "
                  f"{result['rewards'][0]:,.0f} : {result['rewards'][1]:,.0f} "
                  f"-> {result['winner'] or 'draw'}  "
                  f"(status {result['statuses']}, max ms {result['ms_max']})")
            if not args.no_render:
                out = render(result["game_id"])
                print(f"    watch: {out}")
                if args.open:
                    _open(out)
        build_index()
        return
    if args.cmd == "tourney":
        pairs = ([(a, args.vs) for a in args.agents if a != args.vs] if args.vs
                 else list(itertools.combinations(args.agents, 2)))
        jobs = [(a, b, s) for a, b in pairs for s in args.seeds]
        jobs += [(b, a, s) for a, b in pairs for s in args.seeds]
        if args.skip_existing:
            before = len(jobs)
            jobs = [j for j in jobs
                    if not (GAMES / f"{j[0]}__vs__{j[1]}__s{j[2]}.json").exists()]
            print(f"  skipping {before - len(jobs)} games already stored")
        print(f"  {len(jobs)} games ({len(pairs)} pairs x {len(args.seeds)} "
              f"seeds x 2 seats) on {args.workers} workers", flush=True)
        # One process per game. Agents keep module-level state (route
        # cursors, commitment tables, caches), and a worker that plays two
        # games in a row would carry the first game's state into the second.
        with Pool(args.workers, maxtasksperchild=1) as pool:
            for result in pool.imap_unordered(play_one, jobs):
                note = f"  ERROR {result['error']}" if result.get("error") else ""
                print(f"    {' vs '.join(result['agents']):48s} "
                      f"s{result['seed']}: {result['rewards'][0]:9,.0f} : "
                      f"{result['rewards'][1]:9,.0f}  {result['statuses']}"
                      f"{note}", flush=True)
        names = set(args.agents)
        mine = [r for r in _records()
                if set(r["agents"]) <= names and r.get("seed") in args.seeds]
        print("\n  standings (this tourney):")
        for i, row in enumerate(standings(mine)):
            print(f"  {i + 1:2d}. {row['agent']:30s} {row['wins']:3d}/"
                  f"{row['games']:<3d} {100 * row['win_rate']:4.0f}%  "
                  f"mean {row['mean_score']:9,.0f}  margin "
                  f"{row['mean_margin']:+9,.0f}  errors {row['errors']}")
        build_index()
        return
    if args.cmd == "render":
        out = render(args.game_id)
        print(f"  watch: {out}")
        build_index()
        if args.open:
            _open(out)
        return
    if args.cmd == "episode":
        out = render_episode(args.ref)
        print(f"  watch: {out}")
        build_index()
        if args.open:
            _open(out)
        return
    if args.cmd == "index":
        print(f"  {build_index()}")
        return
    if args.cmd == "open":
        _open(build_index())


if __name__ == "__main__":
    main()
