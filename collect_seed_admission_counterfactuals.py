"""Collect daily baseline-versus-one-extra-wheat counterfactuals."""

from __future__ import annotations

import argparse
import copy
import importlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from benchmark import load_agent_callable
from collect_market_counterfactuals import (
    _joint_actions,
    _run_to_completion,
    _terminal_outcome,
    clone_for_counterfactual,
)
from agents.experimental_deadline_tapered_wheat_agent import agent as baseline_agent
from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium
from policies.macro_policy import extract_macro_features


ROOT = Path(__file__).resolve().parent
Agent = Callable[[dict[str, Any]], dict[str, Any]]
SAMPLE_DAYS = (10, 12, 14, 16, 18)
BUILTIN_OPPONENTS = {"pass", "random", "starter"}


def extra_seed_agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the frozen deadline policy with one extra wheat seed requested."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        extra_wheat_seed_buffer=1,
    )


def add_extra_wheat_seed(
    action: dict[str, Any],
) -> dict[str, Any] | None:
    """Increase an existing wheat order or append one without exceeding cap."""
    forced = copy.deepcopy(action)
    orders = forced.get("market", [])
    orders = orders if isinstance(orders, list) else []
    for order in orders:
        if (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "BUY_SEED"
            and order[1] == "WHEAT"
        ):
            order[2] = int(order[2]) + 1
            forced["market"] = orders
            return forced
    if len(orders) >= 10:
        return None
    forced["market"] = [*orders, ["BUY_SEED", "WHEAT", 1]]
    return forced


def _outcome_utility(outcome: dict[str, Any]) -> float:
    result = str(outcome["result"])
    win_value = 1 if result == "win" else -1 if result == "loss" else 0
    margin = max(
        -200.0,
        min(200.0, float(outcome["terminal_margin"]) / 1000.0),
    )
    return 1000.0 * win_value + margin


def evaluate_admission(
    environment: Any,
    agent_player: int,
    controlled_agent: Agent,
    opponent_agent: Agent,
) -> dict[str, Any] | None:
    decision_day = int(environment.state[agent_player].observation.day)
    outcomes = {}
    for choice in ("baseline", "extra"):
        branch = clone_for_counterfactual(environment)
        day_policy = (
            extra_seed_agent if choice == "extra" else controlled_agent
        )
        while (
            not branch.done
            and int(branch.state[agent_player].observation.day)
            == decision_day
        ):
            branch.step(
                _joint_actions(
                    branch,
                    agent_player,
                    day_policy,
                    opponent_agent,
                )
            )
        _run_to_completion(
            branch,
            agent_player,
            controlled_agent,
            opponent_agent,
        )
        outcomes[choice] = _terminal_outcome(branch, agent_player)
        outcomes[choice]["utility"] = _outcome_utility(outcomes[choice])
    delta = round(
        outcomes["extra"]["utility"]
        - outcomes["baseline"]["utility"],
        6,
    )
    return {
        "baseline": outcomes["baseline"],
        "extra": outcomes["extra"],
        "extra_minus_baseline_utility": delta,
        "preferred": (
            "EXTRA" if delta > 0 else "BASELINE" if delta < 0 else "TIE"
        ),
    }


def _features(observation: Any, player: int) -> dict[str, float]:
    public = extract_macro_features(observation)
    farm = observation.farms[player]
    private = observation.private
    own = Counter()
    own_animals = Counter()
    empty_owned = 0
    unlocked = set(farm.get("unlocked_quadrants", []))
    for y, row in enumerate(farm.tiles):
        for x, tile in enumerate(row):
            quadrant = "NW" if x < 5 and y < 5 else (
                "NE" if x >= 5 and y < 5 else "SW" if x < 5 else "SE"
            )
            if quadrant not in unlocked:
                continue
            if tile is None:
                empty_owned += 1
            elif isinstance(tile, dict) and tile.get("kind") == "PLANT":
                own[str(tile.get("crop", "UNKNOWN"))] += 1
            if isinstance(tile, dict) and tile.get("animal"):
                own_animals[str(tile["animal"])] += 1
    return {
        **public,
        "decision_day": float(observation.day),
        "own_hands": float(len(farm.get("hands", []))),
        "own_land": float(len(unlocked)),
        "own_wheat": float(own["WHEAT"]),
        "own_strawberry": float(own["STRAWBERRY"]),
        "own_melon": float(own["MELON"]),
        "own_animals": float(sum(own_animals.values())),
        "own_empty_tiles": float(empty_owned),
        "wheat_seeds": float(private.get("seeds", {}).get("WHEAT", 0)),
        "wheat_market_inventory": float(
            observation.market.get("inventory", {}).get("WHEAT", 0)
        ),
    }


def _opponent_agent(environment: Any, opponent: str) -> Agent:
    if opponent in BUILTIN_OPPONENTS:
        return environment.agents[opponent]
    return load_agent_callable((ROOT / opponent).resolve())


def collect_episode(
    make: Any,
    opponent: str,
    seed: int,
    player: int,
) -> dict[str, Any]:
    environment = make(
        "kaggriculture",
        configuration={
            "episodeSteps": 720,
            "seed": seed,
            "runTimeout": 10_000,
        },
        debug=False,
    )
    opponent_agent = _opponent_agent(environment, opponent)
    rows = []
    sampled_days: set[int] = set()
    while not environment.done:
        observation = environment.state[player].observation
        day = int(observation.day)
        hour = int(observation.hour)
        if day in SAMPLE_DAYS and hour == 0 and day not in sampled_days:
            source = json.dumps(
                environment.toJSON()["steps"][-1],
                sort_keys=True,
            )
            outcomes = evaluate_admission(
                environment,
                player,
                baseline_agent,
                opponent_agent,
            )
            if outcomes is not None:
                rows.append(
                    {
                        "opponent": opponent,
                        "seed": seed,
                        "player": player,
                        "features": _features(observation, player),
                        "outcomes": outcomes,
                    }
                )
                sampled_days.add(day)
            if json.dumps(
                environment.toJSON()["steps"][-1],
                sort_keys=True,
            ) != source:
                raise RuntimeError("Admission branch mutated source state")
        environment.step(
            _joint_actions(
                environment,
                player,
                baseline_agent,
                opponent_agent,
            )
        )
    return {
        "opponent": opponent,
        "seed": seed,
        "player": player,
        "rows": rows,
        "baseline": _terminal_outcome(environment, player),
    }


def _write(
    output: Path,
    metadata: dict[str, Any],
    episodes: list[dict[str, Any]],
    expected: int,
) -> None:
    rows = [row for episode in episodes for row in episode["rows"]]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                **metadata,
                "complete": len(episodes) == expected,
                "episodes": episodes,
                "rows": rows,
                "summary": {
                    "episodes": len(episodes),
                    "states": len(rows),
                    "preferred": dict(
                        Counter(row["outcomes"]["preferred"] for row in rows)
                    ),
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=159)
    parser.add_argument("--seed-count", type=int, default=1)
    parser.add_argument("--opponent", action="append", dest="opponents")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    opponents = tuple(
        args.opponents
        or (
            "agents/experimental_compact_macro_agent.py",
            "agents/experimental_scale_agent.py",
        )
    )
    contexts = [
        (opponent, seed, player)
        for opponent in opponents
        for seed in range(args.seed_start, args.seed_start + args.seed_count)
        for player in (0, 1)
    ]
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "simulator_version": "1.32.7",
        "seed_start": args.seed_start,
        "seed_count": args.seed_count,
        "opponents": list(opponents),
        "sample_days": list(SAMPLE_DAYS),
    }
    episodes: list[dict[str, Any]] = []
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        keys = ("simulator_version", "seed_start", "seed_count", "opponents")
        if all(existing.get(key) == metadata[key] for key in keys):
            episodes = list(existing.get("episodes", []))
    completed = {
        (episode["opponent"], episode["seed"], episode["player"])
        for episode in episodes
    }
    make = importlib.import_module("kaggle_environments").make
    for opponent, seed, player in contexts:
        if (opponent, seed, player) in completed:
            continue
        episode = collect_episode(make, opponent, seed, player)
        episodes.append(episode)
        _write(args.output, metadata, episodes, len(contexts))
        print(
            f"opponent={opponent} seed={seed} player={player} "
            f"states={len(episode['rows'])}"
        )
    _write(args.output, metadata, episodes, len(contexts))
    print(f"Episodes: {len(episodes)}/{len(contexts)}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
