"""Trace differing wheat sale decisions between two file-loaded agents."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

from benchmark import load_simulator


Agent = Callable[[dict[str, Any]], dict[str, Any]]


def load_agent(path: Path, module_name: str) -> Agent:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load agent: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    agent = getattr(module, "agent", None)
    if not callable(agent):
        raise ValueError(f"Agent file has no callable agent: {path}")
    return agent


def trace_seed(
    make: Any,
    control: Agent,
    candidate: Agent,
    seed: int,
    opponent: str,
    episode_steps: int,
    advantage: Callable[[dict[str, Any]], float] | None = None,
) -> dict[str, Any]:
    control_replay = _run(make, control, opponent, seed, episode_steps)
    candidate_replay = _run(make, candidate, opponent, seed, episode_steps)
    differences = []
    for index in range(1, len(control_replay["steps"])):
        control_state = control_replay["steps"][index][0]
        candidate_state = candidate_replay["steps"][index][0]
        control_sales = _wheat_sales(control_state.get("action", {}))
        candidate_sales = _wheat_sales(candidate_state.get("action", {}))
        if control_sales == candidate_sales:
            continue
        observation = candidate_replay["steps"][index - 1][0]["observation"]
        differences.append(
            {
                "record_index": index,
                "day": int(observation.get("day", 0)),
                "hour": int(observation.get("hour", 0)),
                "wheat_price": int(
                    observation["market"]["prices"].get("WHEAT", 0)
                ),
                "shed_wheat": int(
                    observation["private"]["shed"].get("WHEAT", 0)
                ),
                "money": float(observation["farms"][0]["money"]),
                "control_sales": control_sales,
                "candidate_sales": candidate_sales,
                "predicted_sell_advantage": (
                    round(float(advantage(observation)), 6)
                    if advantage is not None
                    else None
                ),
            }
        )
    return {
        "seed": seed,
        "control_score": control_replay["steps"][-1][0]["reward"],
        "candidate_score": candidate_replay["steps"][-1][0]["reward"],
        "coin_delta": (
            candidate_replay["steps"][-1][0]["reward"]
            - control_replay["steps"][-1][0]["reward"]
        ),
        "differences": differences,
    }


def _run(
    make: Any,
    agent: Agent,
    opponent: str,
    seed: int,
    episode_steps: int,
) -> dict[str, Any]:
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": episode_steps, "seed": seed},
        debug=False,
    )
    environment.run([agent, opponent])
    return environment.toJSON()


def _wheat_sales(action: Any) -> list[list[Any]]:
    if not isinstance(action, dict):
        return []
    return [
        order
        for order in action.get("market", [])
        if (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "SELL"
            and order[1] == "WHEAT"
        )
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--seed-start", type=int, default=30)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--opponent", default="starter")
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    make, simulator_version = load_simulator()
    control = load_agent(args.control, "trace_control")
    candidate = load_agent(args.candidate, "trace_candidate")
    candidate_module = importlib.util.module_from_spec(
        importlib.util.spec_from_file_location(
            "trace_candidate_advantage", args.candidate
        )
    )
    candidate_spec = candidate_module.__spec__
    if candidate_spec is None or candidate_spec.loader is None:
        raise ValueError(f"Could not inspect candidate: {args.candidate}")
    candidate_spec.loader.exec_module(candidate_module)
    advantage = getattr(candidate_module, "_predicted_sell_advantage", None)
    traces = [
        trace_seed(
            make,
            control,
            candidate,
            seed,
            args.opponent,
            args.steps,
            advantage if callable(advantage) else None,
        )
        for seed in range(args.seed_start, args.seed_start + args.seed_count)
    ]
    report = {
        "simulator_version": simulator_version,
        "control": str(args.control),
        "candidate": str(args.candidate),
        "traces": traces,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    for trace in traces:
        print(
            f"seed={trace['seed']} delta={trace['coin_delta']} "
            f"differences={len(trace['differences'])}"
        )
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()