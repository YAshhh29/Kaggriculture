"""Package Candidate I: a frozen route-following agent over top-of-ladder tapes.

Candidate I replays recorded routes. Its portfolio is a set of *recorded
action tapes* that real leaderboard teams produced in real games, captured into
``kaggle_cache/top200_tapes/``. This script is where the portfolio is chosen,
where the shops each tape played under are recovered, and where the whole thing
is frozen into a standalone ``submissions/candidate-i/main.py``.

Three things happen here, in order:

1. **Selection.** ``SELECTION`` below lists the episodes that ship, each with
   the reason it was taken. Every entry is a game the recording team *won*.
   Paper evidence -- team rank, recorded final score, margin over a strong
   opponent -- narrowed the field; direct measurement chose from it. Paper
   evidence alone is a poor instrument here and the numbers in ``SELECTION``
   say so: the rank-2 team's best winning tape collapses to a median of 14k
   off its own seed, while a rank-162 tape holds 96k, because the tape that
   holds is the one whose SELL orders are written as "sell everything I have"
   rather than as exact counts that a drifted farm can no longer fill.

2. **Shop recovery.** The shops a tape played under are not in the tape. They
   are recovered exactly, by replaying that episode -- both recorded sides, on
   its own seed -- through the real engine and reading
   ``town["unlocked_shops"]`` off the finished game. The replay also has to
   reproduce the recorded final scores to the cent, which is the check that the
   tape and the seed still belong together.

3. **Routing table.** The recovered signatures are grouped into a map from the
   ordered pair of shops the town unlocks first -- all Agent I can see when it
   commits at the start of day 6 -- to the route that should run. A route wins
   a cell when its own game's opening pair matches, and otherwise when its
   recorded demand profile is closest, with measured strength as the tiebreak,
   so a weak tape never takes a cell from a strong one on a thin similarity.

Then the payload is written into ``candidates/candidate_i.py`` and the packaged file is
emitted and checked: it must import with this repository off ``sys.path``, must
expose ``agent``, and must issue byte-identical actions to the source module
over a full 720-step game.

    python -m tools.packaging.prepare_candidate_i_submission
    python -m tools.packaging.prepare_candidate_i_submission --refresh-shops
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import re
import sys
import time
import zlib
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "candidates" / "candidate_i.py"
TAPES = ROOT / "kaggle_cache" / "top200_tapes"
OUT = ROOT / "submissions" / "candidate-i"
SHOP_CACHE = Path(__file__).resolve().parent / "candidate_i_shops.json"

# --------------------------------------------------------------------------- selection
# episode -> why this tape is in the portfolio.
#
# `dev_median_own` is this tape's median own score as a fixed guarded replay
# against the packaged Candidate H2, both seats, on the development seed panel
# (rl-local measurement, seeds 11/29/53/97/131/173/211/257). It is the number
# that decided the portfolio; the paper columns are recorded from the captured
# episode and are there to show what the paper evidence claimed.
SELECTION: list[dict] = []

SHOPS = {
    "BAKERY": ["EGG", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
# How much a perfect shop match is allowed to outweigh measured strength when
# the routing table is filled in. Chosen on the development panel: see
# `--report` and the notes in candidates/candidate_i.py.
SHOP_WEIGHT = 1.0

NOTICE = """Candidate I

Candidate I is a replay agent. It does not contain an original playing policy.
Its route portfolio is a set of action sequences recorded from public
Kaggriculture episodes played by the teams named in manifest.json, captured
from the public episode API into kaggle_cache/top200_tapes/ and replayed
unchanged apart from two mechanical guards (suppression of SELL orders the shed
cannot fill, and terminal liquidation). Credit for the play belongs to those
teams. The only code in main.py is this project's replay chassis.
"""


# --------------------------------------------------------------------------- helpers
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tape_record(ep: int) -> dict:
    return json.loads((TAPES / f"ep{ep}.json").read_text(encoding="utf-8"))


def decode_actions(blob: str) -> list:
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode("utf-8"))


def demand_vector(shops) -> dict:
    """Units per shop tick the town pulls of each product, for a shop multiset."""
    demand = {item: 0.0 for item in PRODUCTS}
    for shop in shops:
        goods = SHOPS.get(shop)
        if not goods:
            continue
        weight = 2.0 if len(goods) == 1 else 1.0
        for item in goods:
            demand[item] += weight
    return demand


def cosine(a: dict, b: dict) -> float:
    dot = sum(a[k] * b[k] for k in a)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


# --------------------------------------------------------------------------- shop recovery
def _replay_one(ep: int) -> dict:
    """Replay an episode from both recorded sides on its own seed."""
    from kaggle_environments import make

    record = tape_record(ep)
    mine = decode_actions(record["actions_zlib_b64"])
    theirs = decode_actions(record["opponent_actions_zlib_b64"])
    seat = int(record["seat"])

    def build(actions):
        def decide(observation, configuration=None):
            index = int(observation.get("step", 0)) + 1
            if index >= len(actions):
                return {"farmer": ["PASS"], "hands": [], "market": []}
            planned = actions[index]
            return {"farmer": list(planned.get("farmer") or ["PASS"]),
                    "hands": [list(a) for a in (planned.get("hands") or [])],
                    "market": [list(o) for o in (planned.get("market") or [])]}
        return decide

    players = [build(mine), build(theirs)] if seat == 0 else [build(theirs), build(mine)]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": record["seed"],
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run(players)
    final = env.steps[-1]
    own = float(final[seat].get("reward") or 0.0)
    opponent = float(final[1 - seat].get("reward") or 0.0)
    shops = list(env.steps[-1][0]["observation"]["town"]["unlocked_shops"])
    return {
        "ep": ep,
        "shops": shops,
        "reproduced_own": own,
        "reproduced_opponent": opponent,
        "exact": (abs(own - float(record["rewards"]["them"])) < 1e-6
                  and abs(opponent - float(record["rewards"]["opponent"])) < 1e-6),
    }


def recover_shops(eps: list[int], jobs: int, use_cache: bool) -> dict:
    cache = {}
    if use_cache and SHOP_CACHE.exists():
        cache = {int(k): v for k, v in json.loads(SHOP_CACHE.read_text("utf-8")).items()}
    missing = [ep for ep in eps if ep not in cache]
    if missing:
        print(f"replaying {len(missing)} episode(s) to recover shop signatures ...")
        started = time.time()
        with Pool(min(jobs, len(missing))) as pool:
            for row in pool.map(_replay_one, missing):
                cache[row["ep"]] = row
        print(f"  {time.time() - started:.0f}s")
    bad = [ep for ep in eps if not cache[ep]["exact"]]
    if bad:
        raise SystemExit(f"tapes did not reproduce their recorded scores: {bad}")
    SHOP_CACHE.write_text(json.dumps({str(k): v for k, v in sorted(cache.items())}, indent=1),
                          encoding="utf-8")
    return {ep: cache[ep] for ep in eps}


# --------------------------------------------------------------------------- routing table
def build_shop_map(meta: list[dict], strengths: list[float]) -> dict:
    """Ordered opening shop pair -> route index.

    Agent I commits at the start of day 6, when the town has revealed exactly
    two shops, so the table is keyed on that ordered pair and nothing else.
    A route's claim on a cell is its measured strength (z-scored across the
    portfolio, so the units are portfolio standard deviations) plus
    ``SHOP_WEIGHT`` times how well the opening pair *it* played under matches
    the cell: 1.0 for the same ordered pair, 0.95 for the same pair reversed,
    and the cosine between the two pairs' town-demand vectors otherwise.
    """
    mean = sum(strengths) / len(strengths)
    spread = (sum((s - mean) ** 2 for s in strengths) / len(strengths)) ** 0.5 or 1.0
    z = [(s - mean) / spread for s in strengths]
    table = {}
    names = sorted(SHOPS)
    for first in names:
        for second in names:
            cell = demand_vector([first, second])
            best, best_score = 0, None
            for idx, entry in enumerate(meta):
                own = tuple(entry["shops"][:2])
                if own == (first, second):
                    similarity = 1.0
                elif own == (second, first):
                    similarity = 0.95
                else:
                    similarity = cosine(cell, demand_vector(own))
                score = z[idx] + SHOP_WEIGHT * similarity
                if best_score is None or score > best_score:
                    best, best_score = idx, score
            table[f"{first}|{second}"] = best
    return table


# --------------------------------------------------------------------------- payload
def build_payload(jobs: int, use_cache: bool) -> dict:
    if not SELECTION:
        raise SystemExit("SELECTION is empty: nothing to package")
    eps = [entry["ep"] for entry in SELECTION]
    recovered = recover_shops(eps, jobs, use_cache)
    routes, meta = [], []
    for entry in SELECTION:
        ep = entry["ep"]
        record = tape_record(ep)
        actions = decode_actions(record["actions_zlib_b64"])
        if len(actions) != 720:
            raise SystemExit(f"ep{ep}: expected 720 action records, got {len(actions)}")
        routes.append(actions)
        meta.append({
            "ep": ep,
            "team": record["source_team"],
            "team_rank": record["team_rank"],
            "team_score": record["team_score"],
            "recorded_own": record["rewards"]["them"],
            "recorded_opponent": record["rewards"]["opponent"],
            "recorded_opponent_name": record["opponent"],
            "recorded_seat": record["seat"],
            "shops": recovered[ep]["shops"],
            "dev_median_own": entry.get("dev_median_own"),
            "why": entry["why"],
        })
    strengths = [float(entry.get("dev_median_own") or 0.0) for entry in SELECTION]
    default_route = max(range(len(strengths)), key=lambda i: strengths[i])
    return {
        "routes": routes,
        "meta": meta,
        "shop_map": build_shop_map(meta, strengths),
        "default_route": default_route,
        "decide_step": 144,
        "liquidate_from": 708,
    }


def encode_payload(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.b85encode(zlib.compress(raw, 9)).decode("ascii")


def write_payload_into_source(blob: str) -> None:
    text = SOURCE.read_text(encoding="utf-8")
    pattern = re.compile(r'^_PAYLOAD_B85 = ".*"$', re.MULTILINE)
    if not pattern.search(text):
        raise SystemExit("could not find the _PAYLOAD_B85 assignment in candidates/candidate_i.py")
    SOURCE.write_text(pattern.sub(f'_PAYLOAD_B85 = "{blob}"', text, count=1), encoding="utf-8")


# --------------------------------------------------------------------------- packaging
HEADER = '''# Candidate I -- Kaggriculture route-replay clone. Built by
# tools/packaging/prepare_candidate_i_submission.py; do not edit by hand.
#
# The route portfolio is action data recorded from public Kaggriculture
# episodes played by other teams (see manifest.json for the episode ids, the
# teams and their leaderboard ranks at capture time). The play is theirs; the
# replay chassis below is this project's.
'''


def package() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")) and (
                "rl." in stripped or stripped.startswith("from rl")
                or "stack." in stripped or "candidates." in stripped
                or "tools." in stripped):
            raise SystemExit(f"candidates/candidate_i.py is not standalone: {stripped!r}")
    main = OUT / "main.py"
    main.write_text(HEADER + "\n" + source, encoding="utf-8")
    (OUT / "NOTICE").write_text(NOTICE, encoding="utf-8")
    return main


def load_packaged(path: Path):
    """Import the packaged file with this repository off sys.path."""
    saved = list(sys.path)
    try:
        sys.path = [str(path.parent)] + [p for p in saved
                                         if Path(p or ".").resolve() != ROOT.resolve()]
        spec = importlib.util.spec_from_file_location("candidate_i_main", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["candidate_i_main"] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path = saved


def verify(path: Path) -> dict:
    """The packaged file must make the same decisions as the source, all game.

    A full game is played with the source agent against a fixed opponent while
    every observation it sees is recorded; the packaged agent is then fed those
    observations in the same order and its actions compared step by step. Both
    agents carry state (the route they committed to at day 6), so replaying the
    observation sequence exercises the routing as well as the tape lookup.
    """
    from kaggle_environments import make

    sys.path.insert(0, str(ROOT))
    import candidates.candidate_i as source  # noqa: E402

    seen = []
    source_impl = source.build_agent(source._decode_payload(source._PAYLOAD_B85))

    def recorder(observation, configuration=None):
        action = source_impl(observation, configuration)
        seen.append((copy.deepcopy(dict(observation)), copy.deepcopy(action)))
        return action

    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": 4242,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run([recorder, "random"])
    final = env.steps[-1]

    packaged = load_packaged(path)
    if not callable(getattr(packaged, "agent", None)):
        raise SystemExit("packaged main.py does not expose agent()")
    replay = packaged.build_agent(packaged._decode_payload(packaged._PAYLOAD_B85))
    mismatches = []
    for observation, expected in seen:
        got = replay(observation, None)
        if got != expected:
            mismatches.append({"step": observation.get("step"),
                               "expected": expected, "got": got})
            if len(mismatches) >= 3:
                break
    if mismatches:
        raise SystemExit("packaged agent diverges from the source:\n"
                         + json.dumps(mismatches, indent=1)[:2000])
    # The check that actually matters, and the one whose absence put a dead
    # agent on the ladder: play the packaged FILE the way Kaggle plays it.
    # kaggle_environments loads a submission with `get_last_callable`, which
    # takes the last callable in the module rather than the one named `agent`,
    # so a stray helper defined after agent() silently becomes the agent. The
    # symptom is not an error: every action is rejected as malformed and both
    # farms finish on their starting money.
    from kaggle_environments.agent import get_last_callable
    loaded = get_last_callable(path.read_text(encoding="utf-8"), path=str(path))
    if getattr(loaded, "__name__", "") != "agent":
        raise SystemExit(
            "Kaggle would run %r as the agent, not agent(). Move it above "
            "agent() so agent() is the last callable in the file."
            % getattr(loaded, "__name__", loaded))
    live = make("kaggriculture",
                configuration={"episodeSteps": 720, "seed": 77,
                               "runTimeout": 36000, "actTimeout": 60},
                debug=False)
    live.run([str(path), "random"])
    reward = float(live.state[0].reward or 0)
    status = str(live.state[0].status)
    if status != "DONE" or reward <= 3000:
        raise SystemExit(
            "packaged file played by path scored %s (status %s): it is not "
            "acting. 3000 is the starting purse." % (f"{reward:,.0f}", status))
    return {
        "steps_compared": len(seen),
        "played_by_path_reward": reward,
        "identical": True,
        "source_payload_sha256": sha256_bytes(source._PAYLOAD_B85.encode("ascii")),
        "packaged_payload_sha256": sha256_bytes(packaged._PAYLOAD_B85.encode("ascii")),
        "smoke_game": {"seed": 4242, "reward": final[0].get("reward"),
                       "status": str(final[0].get("status"))},
        "routes": len(packaged.ROUTE_META),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--refresh-shops", action="store_true",
                        help="ignore the cached shop signatures and replay every episode")
    parser.add_argument("--report", action="store_true",
                        help="print the portfolio and the routing table and stop")
    args = parser.parse_args(argv)

    payload = build_payload(args.jobs, use_cache=not args.refresh_shops)
    if args.report:
        for index, entry in enumerate(payload["meta"]):
            cells = sum(1 for v in payload["shop_map"].values() if v == index)
            print(f"[{index:>2}] ep{entry['ep']} {entry['team'][:22]:<22} "
                  f"rk{entry['team_rank']:>3} recorded={entry['recorded_own']:>8.0f} "
                  f"dev={entry['dev_median_own'] or 0:>8.0f} cells={cells:>2} "
                  f"opening={entry['shops'][:2]}")
        return 0

    blob = encode_payload(payload)
    write_payload_into_source(blob)
    main_py = package()
    checks = verify(main_py)

    manifest = {
        "candidate": "I",
        "kind": "route replay of recorded top-200 leaderboard episodes",
        "source_corpus": "kaggle_cache/top200_tapes (public Kaggriculture episode API)",
        "routes": [{k: entry[k] for k in ("ep", "team", "team_rank", "team_score",
                                          "recorded_own", "recorded_opponent",
                                          "dev_median_own", "shops", "why")}
                   for entry in payload["meta"]],
        "default_route": payload["default_route"],
        "decide_step": payload["decide_step"],
        "liquidate_from": payload["liquidate_from"],
        "shop_map_cells": len(payload["shop_map"]),
        "main_sha256": sha256_bytes(main_py.read_bytes()),
        "main_bytes": main_py.stat().st_size,
        "checks": checks,
        "built": time.strftime("%Y-%m-%d %H:%M"),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {main_py} ({main_py.stat().st_size} bytes, "
          f"{len(payload['routes'])} routes)")
    print(f"verified identical over {checks['steps_compared']} steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
