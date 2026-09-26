"""Agent L for local play: Agent A's exact submitted file, plus changes.

The parent is loaded from submissions/agent-a/main.py the way Kaggle loads a
submission (compiled and exec'd into a fresh namespace; the entry point is the
last callable), so what is tested is the code that ships. Each variant gets its
own namespace, so variants never share state with each other or with an
opponent that is also Agent A.

    python -m tools.arena.arena play L A --seeds 11 29 --both-seats
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_FILE = ROOT / "submissions" / "agent-a" / "main.py"


def parent_namespace() -> tuple[dict, object]:
    """Exec Agent A exactly as Kaggle does; return (namespace, entry point)."""
    raw = PARENT_FILE.read_text(encoding="utf-8")
    env: dict = {}
    exec(compile(raw, str(PARENT_FILE), "exec"), env)
    return env, [v for v in env.values() if callable(v)][-1]


def fresh_parent():
    return parent_namespace()[1]


def _no_v219(env):
    env["_v219_qualifies"] = lambda obs, native: False


# V219 (the day-18 tomato project on SE) waits for three tomato-eating shops.
# Towns with two such shops open by day 14 build the same tomato shortfall
# (151-169 units by day 18 against 100-208 where V219 fires) and reach
# $138-202 by day 29 with nobody selling. The relaxed gate also accepts two
# shops when the shortfall at step 432 is at least `deficit`.
_SHOPS3 = ("    if sum(s in ('PIZZA_SHOP','FARMERS_MARKET') for s in "
           "obs['town']['unlocked_shops']) < 3:\n        return False\n")


def _v219_gate(env, deficit=140):
    src = PARENT_FILE.read_text(encoding="utf-8")
    start = src.index("def _v219_qualifies(obs, native):")
    end = src.index("\ndef ", start + 10)
    body = src[start:end]
    assert _SHOPS3 in body, "V219 gate text changed"
    relaxed = (
        "    _shops = sum(s in ('PIZZA_SHOP','FARMERS_MARKET') for s in "
        "obs['town']['unlocked_shops'])\n"
        "    _short = 10000 - obs['market']['inventory']['TOMATO']\n"
        f"    if _shops < 2 or (_shops < 3 and _short < {deficit}):\n"
        "        return False\n")
    exec(body.replace(_SHOPS3, relaxed), env)


def _build(name):
    env, entry = parent_namespace()
    if name == "no_v219":
        _no_v219(env)
        return entry
    if name.startswith("gate"):
        _v219_gate(env, int(name[4:] or 140))
        return entry
    from rl.se_project import se_wrap
    settings = {
        "agent": {},
        "w1": {"max_workers": 1},
        "wheat": {"carrot_every": 0},
    }[name]
    return se_wrap(entry, **settings)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    agent = _build(name)
    globals()[name] = agent
    return agent
