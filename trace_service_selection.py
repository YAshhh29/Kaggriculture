"""Trace the learned service arm selected in direct simulator matches."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from benchmark import load_agent_callable
from agents.experimental_learned_service_agent import (
    _SELECTED_ARMS,
    _selected_arm,
    decide,
)
from policies.macro_policy import extract_macro_features


ROOT = Path(__file__).resolve().parent


def trace_match(
    make: Any,
    opponent: str,
    seed: int,
    player: int,
) -> dict[str, Any]:
    snapshot: dict[str, Any] | None = None
    _SELECTED_ARMS.clear()

    def traced_agent(observation: dict[str, Any]) -> dict[str, Any]:
        nonlocal snapshot
        if snapshot is None and int(observation.get("day", 0)) >= 1:
            snapshot = {
                "features": extract_macro_features(observation),
                "arm": _selected_arm(observation),
            }
        return decide(observation)

    opponent_agent = load_agent_callable((ROOT / opponent).resolve())
    agents: list[Any] = [traced_agent, opponent_agent]
    if player == 1:
        agents.reverse()
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    environment.run(agents)
    final = environment.steps[-1]
    return {
        "player": player,
        "snapshot": snapshot,
        "reward": float(final[player].reward),
        "opponent_reward": float(final[1 - player].reward),
        "status": str(final[player].status),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("opponent")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    make = importlib.import_module("kaggle_environments").make
    report = {
        "opponent": args.opponent,
        "seed": args.seed,
        "games": [
            trace_match(make, args.opponent, args.seed, player)
            for player in (0, 1)
        ],
    }
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Service selection trace written to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
