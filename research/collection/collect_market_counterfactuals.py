"""Collect one-step hold-versus-sell counterfactuals by forking the game state."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from benchmark import load_simulator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
Agent = Callable[[dict[str, Any]], dict[str, Any]]


def force_wheat_choice(
    action: dict[str, Any],
    shed_wheat: int,
    choice: str,
) -> dict[str, Any]:
    if choice not in {"HOLD", "SELL"}:
        raise ValueError(f"Unsupported market choice: {choice}")
    forced = copy.deepcopy(action)
    orders = forced.get("market", [])
    orders = orders if isinstance(orders, list) else []
    retained = [order for order in orders if not _is_wheat_sale(order)]
    forced["market"] = (
        [["SELL", "WHEAT", shed_wheat], *retained]
        if choice == "SELL" and shed_wheat > 0
        else retained
    )
    return forced


def evaluate_choices(
    environment: Any,
    agent_player: int,
    controlled_agent: Agent,
    opponent_agent: Agent,
) -> dict[str, Any]:
    observation = environment.state[agent_player].observation
    shed_wheat = int(observation.private.get("shed", {}).get("WHEAT", 0))
    if shed_wheat <= 0:
        raise ValueError("Counterfactual state has no shed wheat")

    joint_actions = _joint_actions(
        environment,
        agent_player,
        controlled_agent,
        opponent_agent,
    )
    baseline_action = joint_actions[agent_player]
    baseline_choice = (
        "SELL"
        if any(_is_wheat_sale(order) for order in baseline_action["market"])
        else "HOLD"
    )
    outcomes = {}
    for choice in ("HOLD", "SELL"):
        branch = clone_for_counterfactual(environment)
        branch_actions = copy.deepcopy(joint_actions)
        branch_actions[agent_player] = force_wheat_choice(
            baseline_action,
            shed_wheat,
            choice,
        )
        branch.step(branch_actions)
        _run_to_completion(
            branch,
            agent_player,
            controlled_agent,
            opponent_agent,
        )
        outcomes[choice.lower()] = _terminal_outcome(branch, agent_player)

    coin_delta = round(
        outcomes["sell"]["terminal_money"]
        - outcomes["hold"]["terminal_money"],
        6,
    )
    preferred = "SELL" if coin_delta > 0 else "HOLD"
    if coin_delta == 0:
        preferred = "TIE"
    return {
        "baseline_choice": baseline_choice,
        "hold": outcomes["hold"],
        "sell": outcomes["sell"],
        "sell_minus_hold_terminal_coins": coin_delta,
        "preferred_choice": preferred,
    }


def clone_for_counterfactual(environment: Any) -> Any:
    branch = environment.clone()
    branch.info = copy.deepcopy(environment.info)
    return branch


def collect_episode(
    make: Any,
    controlled_agent: Agent,
    agent_path: Path,
    opponent: str,
    episode_steps: int,
    seed: int,
    agent_player: int,
    max_branches: int,
    sample_prices: set[int] | None = None,
) -> dict[str, Any]:
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": episode_steps, "seed": seed},
        debug=False,
    )
    opponent_agent = environment.agents[opponent]
    sampled_keys: set[tuple[int, str, str]] = set()
    rows = []

    while not environment.done:
        observation = environment.state[agent_player].observation
        features = _features(observation, agent_player)
        base_action = controlled_agent(observation)
        baseline_choice = (
            "SELL"
            if any(
                _is_wheat_sale(order)
                for order in base_action.get("market", [])
            )
            else "HOLD"
        )
        phase = (
            "pre_liquidation" if features["day"] < 25 else "liquidation"
        )
        sample_key = (
            features["wheat_market_price"],
            phase,
            baseline_choice,
        )
        if (
            features["shed_wheat"] > 0
            and (
                sample_prices is None
                or features["wheat_market_price"] in sample_prices
            )
            and sample_key not in sampled_keys
            and len(rows) < max_branches
        ):
            source_state = json.dumps(
                environment.toJSON()["steps"][-1],
                sort_keys=True,
            )
            outcomes = evaluate_choices(
                environment,
                agent_player,
                controlled_agent,
                opponent_agent,
            )
            if json.dumps(
                environment.toJSON()["steps"][-1],
                sort_keys=True,
            ) != source_state:
                raise RuntimeError("Counterfactual branch mutated source state")
            rows.append(
                {
                    "episode_id": (
                        f"{opponent}-seed-{seed}-player-{agent_player}"
                    ),
                    "seed": seed,
                    "agent_player": agent_player,
                    "features": features,
                    "intervention": {
                        "definition": (
                            "force one HOLD or SELL WHEAT order, preserve all "
                            "other actions, then return to frozen policy"
                        ),
                        "baseline_choice": outcomes["baseline_choice"],
                    },
                    "outcomes": {
                        "hold": outcomes["hold"],
                        "sell": outcomes["sell"],
                        "sell_minus_hold_terminal_coins": outcomes[
                            "sell_minus_hold_terminal_coins"
                        ],
                        "preferred_choice": outcomes["preferred_choice"],
                    },
                }
            )
            sampled_keys.add(sample_key)

        environment.step(
            _joint_actions(
                environment,
                agent_player,
                controlled_agent,
                opponent_agent,
            )
        )

    return {
        "episode_id": f"{opponent}-seed-{seed}-player-{agent_player}",
        "seed": seed,
        "agent_player": agent_player,
        "baseline": _terminal_outcome(environment, agent_player),
        "rows": rows,
        "agent_sha256": hashlib.sha256(agent_path.read_bytes()).hexdigest(),
    }


def _joint_actions(
    environment: Any,
    agent_player: int,
    controlled_agent: Agent,
    opponent_agent: Agent,
) -> list[dict[str, Any]]:
    actions = []
    for player, state in enumerate(environment.state):
        policy = controlled_agent if player == agent_player else opponent_agent
        actions.append(policy(state.observation))
    return actions


def _run_to_completion(
    environment: Any,
    agent_player: int,
    controlled_agent: Agent,
    opponent_agent: Agent,
) -> None:
    while not environment.done:
        environment.step(
            _joint_actions(
                environment,
                agent_player,
                controlled_agent,
                opponent_agent,
            )
        )


def _terminal_outcome(environment: Any, agent_player: int) -> dict[str, Any]:
    state = environment.state[agent_player]
    opponent = environment.state[1 - agent_player]
    money = float(state.observation.farms[agent_player].money)
    opponent_money = float(opponent.observation.farms[1 - agent_player].money)
    return {
        "terminal_money": money,
        "opponent_terminal_money": opponent_money,
        "terminal_margin": round(money - opponent_money, 6),
        "status": str(state.status),
        "result": "win" if money > opponent_money else (
            "loss" if money < opponent_money else "tie"
        ),
    }


def _features(observation: Any, player: int) -> dict[str, Any]:
    farm = observation.farms[player]
    private = observation.private
    return {
        "decision_observation_step": int(observation.step),
        "day": int(observation.day),
        "hour": int(observation.hour),
        "money": float(farm.money),
        "wheat_seeds": int(private.get("seeds", {}).get("WHEAT", 0)),
        "shed_wheat": int(private.get("shed", {}).get("WHEAT", 0)),
        "carried_wheat": sum(
            int(inventory.get("WHEAT", 0))
            for inventory in private.get("inventories", [])
        ),
        "planted_wheat": sum(
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile.get("crop") == "WHEAT"
            for row in farm.tiles
            for tile in row
        ),
        "wheat_market_price": int(
            observation.market.get("prices", {}).get("WHEAT", 0)
        ),
        "wheat_market_inventory": int(
            observation.market.get("inventory", {}).get("WHEAT", 0)
        ),
    }


def _is_wheat_sale(order: Any) -> bool:
    return (
        isinstance(order, list)
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] == "WHEAT"
    )


def load_agent(agent_path: Path) -> Agent:
    module_name = f"counterfactual_agent_{hashlib.sha256(agent_path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, agent_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load agent module: {agent_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    agent = getattr(module, "agent", None)
    if not callable(agent):
        raise ValueError(f"Agent file has no callable agent: {agent_path}")
    return agent


def summarize(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for episode in episodes for row in episode["rows"]]
    choices = {"HOLD": 0, "SELL": 0, "TIE": 0}
    for row in rows:
        choices[row["outcomes"]["preferred_choice"]] += 1
    return {
        "episodes": len(episodes),
        "counterfactual_states": len(rows),
        "preferred_choices": choices,
        "mean_sell_minus_hold_terminal_coins": (
            round(
                sum(
                    row["outcomes"]["sell_minus_hold_terminal_coins"]
                    for row in rows
                )
                / len(rows),
                4,
            )
            if rows
            else None
        ),
    }


def load_or_create_report(
    output_path: Path,
    collection: dict[str, Any],
) -> dict[str, Any]:
    if not output_path.exists():
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            **collection,
            "episodes": [],
            "summary": summarize([]),
            "complete": False,
        }

    report = json.loads(output_path.read_text(encoding="utf-8"))
    for field, expected in collection.items():
        if report.get(field) != expected:
            raise ValueError(f"checkpoint collection field differs: {field}")
    return report


def write_checkpoint(
    output_path: Path,
    report: dict[str, Any],
    expected_episodes: int,
) -> None:
    report["summary"] = summarize(report["episodes"])
    report["complete"] = len(report["episodes"]) == expected_episodes
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent", type=Path, default=PROJECT_ROOT / "main.py"
    )
    parser.add_argument(
        "--opponent", choices=("pass", "starter"), default="starter"
    )
    parser.add_argument("--seed-start", type=int, default=30)
    parser.add_argument("--seed-count", type=int, default=1)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--max-branches-per-episode", type=int, default=12)
    parser.add_argument("--sample-price", action="append", type=int, default=[])
    parser.add_argument("--both-positions", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed_count < 1:
        raise SystemExit("--seed-count must be at least 1")
    if args.max_branches_per_episode < 1:
        raise SystemExit("--max-branches-per-episode must be at least 1")
    agent_path = args.agent.resolve()
    controlled_agent = load_agent(agent_path)
    make, simulator_version = load_simulator()
    positions = (0, 1) if args.both_positions else (0,)
    collection = {
        "simulator_version": simulator_version,
        "agent_file": str(agent_path),
        "agent_sha256": hashlib.sha256(agent_path.read_bytes()).hexdigest(),
        "opponent": args.opponent,
        "episode_steps": args.steps,
        "seed_start": args.seed_start,
        "seed_count": args.seed_count,
        "positions": list(positions),
        "max_branches_per_episode": args.max_branches_per_episode,
        "sampling": (
            "first state per requested (price, pre/liquidation phase, "
            "baseline choice), up to max branches per episode"
        ),
        "sample_prices": sorted(set(args.sample_price)),
        "intervention": (
            "force one HOLD or SELL WHEAT order, preserve all other actions, "
            "then return to frozen policy"
        ),
    }
    expected_episodes = args.seed_count * len(positions)
    try:
        report = load_or_create_report(args.output, collection)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    completed = {
        (int(episode["seed"]), int(episode["agent_player"]))
        for episode in report["episodes"]
    }
    for seed in range(args.seed_start, args.seed_start + args.seed_count):
        for player in positions:
            if (seed, player) in completed:
                continue
            episode = collect_episode(
                make,
                controlled_agent,
                agent_path,
                args.opponent,
                args.steps,
                seed,
                player,
                args.max_branches_per_episode,
                set(args.sample_price) or None,
            )
            report["episodes"].append(episode)
            write_checkpoint(args.output, report, expected_episodes)
            print(
                f"seed={seed} player={player} "
                f"baseline={episode['baseline']['terminal_money']} "
                f"branches={len(episode['rows'])}"
            )

    write_checkpoint(args.output, report, expected_episodes)
    print(f"Summary: {report['summary']}")
    print(f"Complete: {report['complete']}")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()