"""Screen bounded fertilizer sale thresholds on the first live loss."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.experimental_fertilizer_value_agent import decide_with_threshold
from benchmark import load_agent_callable, load_simulator, run_game


ROOT = Path(__file__).resolve().parents[2]
OPPONENT = ROOT / "agents" / "future_labor_first_loss_replay_agent.py"
OUTPUT = (
    ROOT
    / "artifacts"
    / "benchmarks"
    / "v1327-fertilizer-value-first-live-loss-screen.json"
)
SEED = 1_426_717_232
THRESHOLDS = (50, 60, 70)


def threshold_agent(threshold: int) -> Any:
    """Return a one-argument callable with a closed-over threshold."""
    def agent(observation: dict[str, Any]) -> dict[str, Any]:
        return decide_with_threshold(observation, threshold)

    return agent


def main() -> None:
    make, simulator_version = load_simulator()
    opponent = load_agent_callable(OPPONENT)
    records: dict[str, Any] = {}
    for threshold in THRESHOLDS:
        record = run_game(
            make,
            threshold_agent(threshold),
            opponent,
            720,
            SEED,
            0,
        )
        records[str(threshold)] = {
            "reward": record["agent_reward"],
            "opponent_reward": record["opponent_reward"],
            "result": record["result"],
            "fertilizer_sold": record["agent_actions"]
            .get("market_units", {})
            .get("SELL:FERTILIZER", 0),
            "final_inventory": record["final_inventory"],
            "cycles": {
                key: record["route_analysis"].get(key, 0)
                for key in (
                    "cycles_planted",
                    "cycles_harvested",
                    "cycles_weeded",
                    "cycles_unfinished",
                )
            },
        }
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(
                {
                    "simulator_version": simulator_version,
                    "seed": SEED,
                    "records": records,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            f"threshold={threshold} reward={record['agent_reward']} "
            f"opponent={record['opponent_reward']} "
            f"result={record['result']}"
        )
    print(f"Report: {OUTPUT}")


if __name__ == "__main__":
    main()