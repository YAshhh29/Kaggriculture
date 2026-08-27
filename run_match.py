"""Run a local Kaggriculture match and optionally save its replay."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from benchmark import load_agent_callable


PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent",
        type=Path,
        default=PROJECT_ROOT / "main.py",
        help="agent file to run (default: main.py)",
    )
    parser.add_argument(
        "--opponent",
        default="pass",
        help="built-in opponent or agent file (default: pass)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=48,
        help="episode length; use 720 for a full season (default: 48)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="environment seed for a repeatable match (default: 7)",
    )
    parser.add_argument(
        "--replay",
        type=Path,
        help="optional path for the replay JSON",
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="optional path for a self-contained visual replay",
    )
    return parser.parse_args()


def load_make() -> Any:
    try:
        package = importlib.import_module("kaggle_environments")
    except ModuleNotFoundError as error:
        raise SystemExit(
            "kaggle-environments is not installed. See README.md under "
            "'Optional simulator setup'."
        ) from error
    return package.make


def main() -> None:
    args = parse_args()
    agent_path = args.agent.resolve()
    if not agent_path.is_file():
        raise SystemExit(f"Agent file does not exist: {agent_path}")
    make = load_make()
    configuration = {"episodeSteps": args.steps, "seed": args.seed}
    opponent_input: Any = args.opponent
    if args.opponent not in ("pass", "random", "starter"):
        opponent_path = Path(args.opponent).resolve()
        if not opponent_path.is_file():
            raise SystemExit(
                f"Opponent file does not exist: {opponent_path}"
            )
        opponent_input = load_agent_callable(opponent_path)
    environment = make(
        "kaggriculture",
        configuration=configuration,
        debug=True,
    )
    environment.run([str(agent_path), opponent_input])

    final_states = environment.steps[-1]
    failed = False
    for player, state in enumerate(final_states):
        print(f"Player {player}: reward={state.reward}, status={state.status}")
        failed = failed or state.status != "DONE"

    if args.replay:
        args.replay.parent.mkdir(parents=True, exist_ok=True)
        args.replay.write_text(
            json.dumps(environment.toJSON()),
            encoding="utf-8",
        )
        print(f"Replay written to {args.replay}")

    if args.html:
        rendered = environment.render(
            mode="html",
            width=1200,
            height=800,
        )
        if not isinstance(rendered, str):
            raise SystemExit("The Kaggle renderer did not return HTML.")
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(rendered, encoding="utf-8")
        print(f"HTML replay written to {args.html}")

    if failed:
        raise SystemExit("At least one agent did not finish successfully.")


if __name__ == "__main__":
    main()
