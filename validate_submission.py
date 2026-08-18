"""Run Kaggle's full self-play validation for a prepared agent file."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from kaggle_environments import make


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", type=Path)
    parser.add_argument("--seed", type=int, default=50)
    args = parser.parse_args()

    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    agent_path = str(args.agent.resolve())
    environment.run([agent_path, agent_path])
    final = environment.steps[-1]
    statuses = [str(state.status) for state in final]
    rewards = [state.reward for state in final]
    digest = hashlib.sha256(args.agent.read_bytes()).hexdigest()

    print(f"Agent: {args.agent}")
    print(f"Statuses: {statuses}")
    print(f"Rewards: {rewards}")
    print(f"SHA-256: {digest}")
    if statuses != ["DONE", "DONE"]:
        raise SystemExit("Submission self-play did not finish successfully")


if __name__ == "__main__":
    main()
