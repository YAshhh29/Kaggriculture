"""Adversarial robustness check of a packaged submission, played the way Kaggle plays it.

A final submission has to survive ~15 days of ladder games with no forfeit: an
exception past the guard is ERROR, a malformed action INVALID, and turns over
actTimeout (1 s) draw on a 60 s overage bank whose exhaustion is TIMEOUT. This
plays a packaged main.py in kaggle_environments' kaggriculture env with
actTimeout 1 against hostile or degenerate opponents, in both seats, and
reports what would have gone wrong on the ladder.

Loading. The file is loaded as the Kaggle agent server loads it: its text goes
through kaggle_environments.agent.get_last_callable on the FIRST act, inside
that act's timer (agent.build_agent's callable_agent), so the load -- the
packages compile and instantiate the shadow library then -- is charged to turn 0
and to the overage bank exactly as on the ladder. Each game gets a fresh load
(one episode per agent process); --reuse-process keeps one loaded instance for
every game instead, to test reset detection when a process is reused. Every
action goes through a JSON round trip, as it does between the agent server and
the game, so an action the server could not encode shows up here (locally the
env never serialises actions).

Opponents:
    random   the env's built-in random agent
    pass     PASS every turn (the env's built-in)
    broken   raises every turn: ERROR on its first act; the game goes on without it
    greedy   buys all the wheat its shed and cash allow (slot 0: rides every draw)
             and sells its whole shed, every step
    garbage  malformed but engine-safe actions: unknown ops, bad quantities,
             twelve orders, a million-unit purchase, hires every step
    <name>   a public program, rl/public/<name>.py (tools.arena.arena.load names);
             nb_haideptry_the_2965_master_hybrid_engine is in the shadow library,
             so the shadow stays in sync and its early-sale lookaheads run
    <path>   another main.py, loaded like ours

Per game: both statuses and rewards; load time and turn 0 (load included, as
the env timed it); our slowest turn and p99 after turn 0; turns over 1 s; the
overage bank left (remainingOverageTime at the end); the safety guard's
telemetry (errors = exceptions it caught and turned into PASS, repaired =
actions it had to reshape) and the HEALTH line it prints at step 718 (parsed
from the agent logs, full-length games only); every layer's error counters and
the parent's fallbacks; exceptions that escaped; JSON failures; actions that
would crash the engine's interpreter; turns whose queue had more than 10 orders
below the guard (which cuts it to 10, so the env never sees them); the
shadow's in-sync programs and slowest turn; the process's peak memory (env and
opponent included).

    python -m tools.eval.robust_check submissions/candidate-n8/main.py --opponents pass --seats 0 --episode-steps 60 --games-limit 1
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BANK_S = 60.0
MAX_ORDERS = 10
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
DEFAULT_OPPONENTS = ("random", "pass", "broken", "greedy", "garbage",
                     "nb_haideptry_the_2965_master_hybrid_engine")


# ---------------------------------------------------------------------------
# Our agent, loaded as the Kaggle agent server loads it.
# ---------------------------------------------------------------------------
def _hashable(x: Any) -> bool:
    try:
        hash(x)
        return True
    except TypeError:
        return False


def engine_hazards(action: Any) -> list[str]:
    """What in an action would make the engine's interpreter RAISE (a crashed
    episode) instead of ignoring it (kaggriculture.py: unguarded int() of a
    PICKUP/PLACE quantity, dict lookups of the item, int() of an infinite order
    quantity)."""
    if not isinstance(action, dict):
        return ["action is not a dict"]
    out = []
    hands = action.get("hands", [])
    units = [action.get("farmer", ["PASS"])] + (hands if isinstance(hands, list) else [])
    for i, c in enumerate(units):
        if not isinstance(c, list) or not c:
            continue
        if not _hashable(c[0]):
            out.append(f"unit {i}: unhashable op")
            continue
        if len(c) >= 2 and c[0] in ("PLANT", "PLACE", "PICKUP") and not _hashable(c[1]):
            out.append(f"unit {i}: unhashable item")
        if len(c) >= 3 and c[0] in ("PLACE", "PICKUP"):
            try:
                int(c[2])
            except (TypeError, ValueError, OverflowError):
                out.append(f"unit {i}: {c[0]} quantity {c[2]!r}")
    market = action.get("market", [])
    for o in (market if isinstance(market, list) else [])[:MAX_ORDERS]:
        if isinstance(o, list) and len(o) >= 3 and o[0] in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"):
            if not _hashable(o[1]):
                out.append("order: unhashable item")
            try:
                int(o[2])
            except OverflowError:
                out.append(f"order quantity {o[2]!r}")
            except (TypeError, ValueError):
                pass                      # the engine drops such an order
    return out


class KaggleFile:
    """A submission file loaded the way the Kaggle agent server loads it: the
    text goes through get_last_callable on the first act, inside that act's
    timer. Records per-turn times and what the ladder would have punished."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.raw = path.read_text(encoding="utf-8")
        self.agent = None
        self.load_s = 0.0
        self.tapped = False
        self.new_game()

    def _tap_below_guard(self) -> None:
        """Count >10-order turns where the guard cannot hide them. sf_wrap cuts the
        queue to 10 before it returns, so the action the env sees never has more;
        wrap the stack below it (the loaded entry's closure cell `agent`) instead,
        passing every action through unchanged."""
        code = getattr(self.agent, "__code__", None)
        cells = getattr(self.agent, "__closure__", None) or ()
        if code is None or "agent" not in code.co_freevars:
            return
        cell = cells[code.co_freevars.index("agent")]
        inner = cell.cell_contents
        if not callable(inner):
            return
        owner = self

        def below_guard(observation, configuration=None):
            action = inner(observation, configuration)
            market = action.get("market") if isinstance(action, dict) else None
            if isinstance(market, list) and len(market) > MAX_ORDERS:
                owner.overfull_turns += 1
            return action

        cell.cell_contents = below_guard
        self.tapped = True

    def new_game(self) -> None:
        self.turn_ms: list[float] = []
        self.exceptions: list[str] = []
        self.json_failures: list[str] = []
        self.hazards: dict[str, int] = {}
        self.overfull_turns = 0
        self.loaded_this_game = self.agent is None

    def __call__(self, observation, configuration):
        if self.agent is None:
            from kaggle_environments.agent import get_last_callable
            t0 = time.perf_counter()
            self.agent = get_last_callable(self.raw, path=str(self.path))
            self.load_s = time.perf_counter() - t0
            self._tap_below_guard()
        t0 = time.perf_counter()
        try:
            action = self.agent(observation, configuration)
        except Exception as error:              # the env marks us ERROR, as Kaggle would
            self.exceptions.append(f"step {observation.get('step')}: {type(error).__name__}: {error}"[:300])
            raise
        finally:
            self.turn_ms.append((time.perf_counter() - t0) * 1000.0)
        for h in engine_hazards(action):
            self.hazards[h] = self.hazards.get(h, 0) + 1
        market = action.get("market") if isinstance(action, dict) else None
        if not self.tapped and isinstance(market, list) and len(market) > MAX_ORDERS:
            self.overfull_turns += 1            # no sf_wrap guard found: count what the env sees
        try:                                    # what reaches the game from the agent server
            return json.loads(json.dumps(action))
        except (TypeError, ValueError) as error:
            self.json_failures.append(f"step {observation.get('step')}: {error}"[:300])
            return None


# ---------------------------------------------------------------------------
# Opponents.
# ---------------------------------------------------------------------------
def broken_agent(observation, configuration=None):
    raise RuntimeError("robust_check: broken opponent")


def greedy_agent(observation, configuration=None):
    """Buy all the wheat the shed and cash allow (slot 0, so it rides every draw
    step) and sell the whole shed, every step."""
    me = int(observation["player"])
    farm = observation["farms"][me]
    private = observation.get("private") or {}
    shed = {k: int(v) for k, v in (private.get("shed") or {}).items() if int(v) > 0}
    prices = observation["market"]["prices"]
    room = 100 - sum(shed.values())
    buy = min(room, int(float(farm["money"]) // max(1, int(prices.get("WHEAT", 25)))))
    market = [["BUY_PRODUCT", "WHEAT", buy]] if buy > 0 else []
    market += [["SELL", item, shed[item]] for item in PRODUCTS if shed.get(item)]
    return {"farmer": ["PASS"], "hands": [["PASS"] for _ in farm.get("hands") or []],
            "market": market[:MAX_ORDERS]}


def garbage_agent(observation, configuration=None):
    """Malformed but engine-safe (nothing here crashes the interpreter)."""
    step = int(observation.get("step", 0))
    return {"farmer": ["DANCE", step] if step % 2 else ["PLACE"],
            "hands": [["NORTH", "fast"], [], "x", ["PLANT"], None, ["WEST"], ["HARVEST", 3]],
            "market": [["BUY_PRODUCT", "WHEAT", 10 ** 6], ["SELL"], "HIRE", ["BUY_SEED", "GOLD", 3],
                       ["SELL", "WHEAT", "abc"], ["BUY_ANIMAL", "COW", -5], ["SELL", "MILK", 2.5], [],
                       ["HIRE"], ["BUY_LAND"], ["SELL", "WHEAT", 7], ["HIRE"]]}


def opponent(name: str):
    if name in ("random", "pass"):
        return name                             # the env's built-in agents
    if name == "broken":
        return broken_agent
    if name == "greedy":
        return greedy_agent
    if name == "garbage":
        return garbage_agent
    path = Path(name) if Path(name).is_absolute() else ROOT / name
    if name.endswith(".py") and path.exists():
        return KaggleFile(path)
    from tools.arena.arena import load          # public programs and our aliases
    return load(name)


# ---------------------------------------------------------------------------
# Telemetry.
# ---------------------------------------------------------------------------
def peak_rss_mb() -> float | None:
    """Peak resident memory of this process (env and opponent included)."""
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak / (2 ** 20 if sys.platform == "darwin" else 2 ** 10)
    except ImportError:
        pass
    try:
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        k32 = ctypes.WinDLL("kernel32")
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        c = Counters()
        c.cb = ctypes.sizeof(Counters)
        if k32.K32GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb):
            return c.PeakWorkingSetSize / 2 ** 20
    except Exception:
        pass
    return None


def layer_telemetry(agent) -> tuple[dict[str, float], Any]:
    """Every error / fallback counter below the guard ({'layer.key': n}), found
    by walking the layer closures from the loaded entry point, and the shadow
    layer (the function carrying .shadows), if any."""
    errors: dict[str, float] = {}
    shadow, seen, todo = None, set(), [agent]
    while todo:
        f = todo.pop()
        if id(f) in seen or not callable(f):
            continue
        seen.add(id(f))
        name = getattr(f, "__name__", type(f).__name__)
        tel = getattr(f, "telemetry", None) if f is not agent else None   # the guard: reported as "guard"
        if isinstance(tel, dict):
            for k, v in tel.items():
                if "error" in k and isinstance(v, (int, float)) and not isinstance(v, bool):
                    errors[f"{name}.{k}"] = v
        if hasattr(f, "shadows"):
            shadow = f
        impl = (getattr(f, "__globals__", None) or {}).get("_IMPL")
        diag = getattr(getattr(impl, "chassis", None), "diagnostics", None)
        if isinstance(diag, dict):
            for k, v in diag.items():
                errors[f"parent.{k}"] = v
        for cell in getattr(f, "__closure__", None) or ():
            try:
                todo.append(cell.cell_contents)
            except ValueError:
                pass
    return errors, shadow


def shadow_summary(shadow) -> dict[str, Any] | None:
    if shadow is None:
        return None
    tel = shadow.telemetry
    live = [sh.program for sh in shadow.shadows if sh.in_sync]
    lost = {}
    for sh in shadow.shadows:
        at = sh.stats.get("lost_at")
        if at is not None:
            lost[sh.program] = [at, str(sh.stats.get("lost_reason"))[:60]]
    return {"programs": len(shadow.shadows), "in_sync_at_end": live,
            "max_ms": round(float(tel.get("shadow_max_ms", 0.0)), 1),
            "slow_turns_300ms": tel.get("shadow_slow_turns", 0),
            "sync_turns": tel.get("shadow_sync_turns", 0),
            "early_sales": tel.get("early_sales", 0) + tel.get("early_now_sales", 0),
            "lost": lost}


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(math.ceil(q * len(ordered))) - 1)]


# ---------------------------------------------------------------------------
# One game.
# ---------------------------------------------------------------------------
def play(ours: KaggleFile, opp_name: str, seat: int, seed: int, steps: int,
         act_timeout: float) -> dict[str, Any]:
    from kaggle_environments import make

    ours.new_game()
    guard_before = dict(getattr(ours.agent, "telemetry", None) or {})
    opp = opponent(opp_name)
    agents = [ours, opp] if seat == 0 else [opp, ours]
    env = make("kaggriculture", configuration={"episodeSteps": steps, "actTimeout": act_timeout,
                                               "runTimeout": 36000, "seed": seed}, debug=False)
    started = time.perf_counter()
    crash = None
    try:
        env.run(agents)
    except Exception as error:                  # an engine crash, or the run deadline
        crash = f"{type(error).__name__}: {error}"[:300]
    wall = time.perf_counter() - started
    final = env.steps[-1]
    logs = [step[seat] if len(step) > seat and isinstance(step[seat], dict) else {} for step in env.logs]
    durations = [float(x["duration"]) for x in logs if "duration" in x]
    health, stderr = None, []
    for x in logs:
        for line in (x.get("stdout") or "").splitlines():
            if line.startswith("HEALTH "):
                try:
                    health = json.loads(line[len("HEALTH "):])
                except ValueError:
                    health = line[:300]
        if x.get("stderr"):
            stderr.append(x["stderr"][-300:])
    guard = dict(getattr(ours.agent, "telemetry", None) or {})
    for k in ("turns", "errors", "repaired", "slow_turns"):   # this game's share (--reuse-process)
        if isinstance(guard.get(k), (int, float)) and isinstance(guard_before.get(k), (int, float)):
            guard[k] = guard[k] - guard_before[k]
    layer_errors, shadow = layer_telemetry(ours.agent) if ours.agent is not None else ({}, None)
    after0 = ours.turn_ms[1:]
    remaining = final[seat]["observation"].get("remainingOverageTime")
    row = {
        "agent": str(ours.path.relative_to(ROOT)) if ours.path.is_relative_to(ROOT) else str(ours.path),
        "opponent": opp_name, "seat": seat, "seed": seed, "episode_steps": steps, "act_timeout": act_timeout,
        "steps_played": len(env.steps) - 1,
        "status": [s["status"] for s in final], "reward": [s["reward"] for s in final],
        "crash": crash, "wall_s": round(wall, 1),
        "load_s": round(ours.load_s, 2) if ours.loaded_this_game else 0.0,
        "turn0_s": round(durations[0], 2) if durations else None,
        "turn0_agent_ms": round(ours.turn_ms[0], 1) if ours.turn_ms else None,
        "max_ms": round(max(after0), 1) if after0 else 0.0,
        "max_ms_step": (ours.turn_ms.index(max(after0), 1) if after0 else None),
        "p99_ms": round(_pct(after0, 0.99), 1), "mean_ms": round(statistics.mean(after0), 1) if after0 else 0.0,
        "turns_over_1s": sum(d > act_timeout for d in durations[1:]),
        "bank_left_s": round(float(remaining), 2) if remaining is not None else None,
        "bank_used_s": round(BANK_S - float(remaining), 2) if remaining is not None else None,
        "guard": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in guard.items() if k != "name"},
        "health_line": health,
        "layer_errors": {k: v for k, v in layer_errors.items() if v},
        "exceptions": ours.exceptions[:5], "json_failures": ours.json_failures[:5],
        "engine_hazards": ours.hazards, "overfull_turns": ours.overfull_turns,
        "stderr": stderr[:3], "shadow": shadow_summary(shadow),
        "peak_rss_mb": (round(peak_rss_mb()) if peak_rss_mb() is not None else None),
    }
    row["problems"] = problems(row, act_timeout)
    return row


def problems(row: dict[str, Any], act_timeout: float) -> list[str]:
    """What would have cost a ladder game (or points) in this game."""
    out = []
    seat = row["seat"]
    if row["crash"]:
        out.append("env crash")
    if row["status"][seat] != "DONE":
        out.append(f"our status {row['status'][seat]}")
    if row["exceptions"]:
        out.append("exception escaped the guard")
    if row["json_failures"]:
        out.append("action not JSON-encodable")
    if row["engine_hazards"]:
        out.append("action would crash the engine")
    if row["overfull_turns"]:
        out.append(f"{row['overfull_turns']} turns queued >10 orders (the tail is dropped)")
    if row["guard"].get("errors"):
        out.append(f"guard caught {row['guard']['errors']} exceptions (PASS turns)")
    if row["guard"].get("repaired"):
        out.append(f"guard repaired {row['guard']['repaired']} actions")
    if row["layer_errors"]:
        out.append("layer errors")
    if row["bank_left_s"] is not None and row["bank_left_s"] < BANK_S / 2:
        out.append(f"overage bank below {BANK_S / 2:.0f} s")
    if row["max_ms"] > act_timeout * 1000.0:
        out.append("turn over actTimeout after turn 0")
    return out


def line(row: dict[str, Any]) -> str:
    seat = row["seat"]
    sh = row["shadow"]
    shadow = (f" | shadow {len(sh['in_sync_at_end'])}/{sh['programs']} in sync, max {sh['max_ms']:.0f} ms"
              if sh else "")
    rew = [f"{r:,.0f}" if isinstance(r, (int, float)) else str(r) for r in row["reward"]]
    return (f"{Path(row['agent']).parent.name} vs {row['opponent'][:28]} seat {seat} seed {row['seed']} "
            f"({row['steps_played']} steps, {row['wall_s']:.0f} s)\n"
            f"  status {row['status'][seat]}/{row['status'][1 - seat]}  reward {rew[seat]} vs {rew[1 - seat]}"
            f"{'  CRASH ' + row['crash'] if row['crash'] else ''}\n"
            f"  load {row['load_s']:.1f} s, turn 0 {row['turn0_s']} s (agent {row['turn0_agent_ms']} ms) | "
            f"after turn 0: max {row['max_ms']:.0f} ms (step {row['max_ms_step']}), p99 {row['p99_ms']:.0f}, "
            f"mean {row['mean_ms']:.0f}, over {row['act_timeout']:g} s: {row['turns_over_1s']} | bank left {row['bank_left_s']} s\n"
            f"  guard errors {row['guard'].get('errors')}, repaired {row['guard'].get('repaired')}, "
            f"last_error {row['guard'].get('last_error')!r} | layer errors {row['layer_errors'] or 0} | "
            f"escaped {len(row['exceptions'])}, json {len(row['json_failures'])}, hazards {sum(row['engine_hazards'].values())}, "
            f">10 orders below guard {row['overfull_turns']}{shadow} | peak RSS {row['peak_rss_mb']} MB\n"
            f"  health {row['health_line'] if row['health_line'] is not None else '(printed at step 718 only)'}\n"
            f"  => {'OK' if not row['problems'] else 'CHECK: ' + '; '.join(row['problems'])}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agents", nargs="+", help="packaged main.py file(s), e.g. submissions/candidate-n8/main.py")
    ap.add_argument("--opponents", nargs="+", default=list(DEFAULT_OPPONENTS))
    ap.add_argument("--seats", type=int, nargs="+", default=[0, 1], choices=[0, 1])
    ap.add_argument("--seeds", type=int, nargs="+", default=[11])
    ap.add_argument("--episode-steps", type=int, default=720)
    ap.add_argument("--act-timeout", type=float, default=1.0)
    ap.add_argument("--games-limit", type=int, default=0, help="stop after this many games (0: all)")
    ap.add_argument("--reuse-process", action="store_true",
                    help="one loaded instance per agent for every game (tests reset on a reused process)")
    ap.add_argument("--out", default=None, help="write the rows as JSON here")
    args = ap.parse_args()

    jobs = [(a, seed, seat, opp) for a in args.agents for seed in args.seeds
            for seat in args.seats for opp in args.opponents]
    if args.games_limit > 0:
        jobs = jobs[:args.games_limit]
    print(f"{len(jobs)} game(s): actTimeout {args.act_timeout:g} s, {args.episode_steps} steps, "
          f"{'one process per agent' if args.reuse_process else 'fresh load per game'}", flush=True)
    rows, loaded = [], {}
    for agent_path, seed, seat, opp in jobs:
        path = Path(agent_path) if Path(agent_path).is_absolute() else ROOT / agent_path
        ours = loaded.get(path) if args.reuse_process else None
        if ours is None:
            ours = KaggleFile(path)
            if args.reuse_process:
                loaded[path] = ours
        row = play(ours, opp, seat, seed, args.episode_steps, args.act_timeout)
        rows.append(row)
        print(line(row), flush=True)
        del ours
        gc.collect()
    bad = [r for r in rows if r["problems"]]
    print(f"\n{len(rows) - len(bad)}/{len(rows)} games clean; worst turn after turn 0 "
          f"{max((r['max_ms'] for r in rows), default=0):.0f} ms; lowest bank left "
          f"{min((r['bank_left_s'] for r in rows if r['bank_left_s'] is not None), default=None)} s", flush=True)
    if args.out:
        out = Path(args.out) if Path(args.out).is_absolute() else ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rows, indent=1, default=str), encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
