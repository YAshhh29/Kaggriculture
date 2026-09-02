"""Evaluate safe macro arms against captured live opponent schedules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from agents.experimental_crop_pressure_labor_agent import (
    agent as pressure_labor,
)
from agents.experimental_budgeted_value_fertilizer_agent import (
    agent as budgeted_value_fertilizer,
)
from agents.experimental_center_out_agent import agent as center_out
from agents.experimental_distilled_calendar_agent import decide as calendar
from rl.candidate_a import build_candidate_a_agent
from agents.experimental_colocated_crop_service_agent import (
    agent as colocated_crop_service,
)
from agents.experimental_colocated_value_fertilizer_agent import (
    agent as colocated_value_fertilizer,
)
from agents.experimental_contextual_carried_crop_service_agent import (
    agent as contextual_carried_crop_service,
)
from agents.experimental_crop_pressure_lean_herd_agent import (
    agent as lean_herd,
)
from agents.experimental_fertilizer_value_agent import decide_with_threshold
from agents.experimental_full_capacity_agent import agent as full_capacity
from agents.experimental_guarded_colocated_crop_service_agent import (
    agent as guarded_colocated_crop_service,
)
from agents.experimental_guarded_carried_crop_service_agent import (
    agent as guarded_carried_crop_service,
)
from agents.experimental_idle_value_fertilizer_agent import (
    agent as idle_value_fertilizer,
)
from agents.experimental_investment_agent import agent as investment
from agents.experimental_late_strawberry_agent import agent as late_strawberry
from agents.experimental_late_melon_fertilizer_agent import (
    agent as late_melon_fertilizer,
)
from agents.experimental_late_strawberry_fertilizer_agent import (
    agent as late_strawberry_fertilizer,
)
from agents.experimental_late_value_fertilizer_agent import (
    agent as late_value_fertilizer,
)
from agents.experimental_late_value_fertilizer_feed_agent import (
    agent as late_value_fertilizer_feed,
)
from agents.experimental_dynamic_replacement_agent import (
    agent as dynamic_replacement,
)
from agents.experimental_pressure_late_strawberry_agent import (
    agent as pressure_late_strawberry,
)
from agents.experimental_tiered_value_fertilizer_agent import (
    agent as tiered_value_fertilizer,
)
from agents.experimental_tiered_late_strawberry_agent import (
    agent as tiered_late_strawberry,
)
from benchmark import load_agent_callable, load_simulator
from rl.candidate_a import (
    CandidateATelemetry,
    build_candidate_a_agent,
)


ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "submissions" / "future-labor" / "main.py"
Agent = Callable[[dict[str, Any]], dict[str, Any]]
InstrumentedArm = Callable[[CandidateATelemetry | None], Agent]


def _calendar_recovery_arm(telemetry: CandidateATelemetry | None = None) -> Agent:
    return build_candidate_a_agent(baseline=calendar, telemetry=telemetry)


def _calendar_recovery_only_arm(
    telemetry: CandidateATelemetry | None = None,
) -> Agent:
    return build_candidate_a_agent(
        baseline=calendar,
        enable_liquidation=False,
        telemetry=telemetry,
    )


def _calendar_liquidation_only_arm(
    telemetry: CandidateATelemetry | None = None,
) -> Agent:
    return build_candidate_a_agent(
        baseline=calendar,
        enable_recovery=False,
        telemetry=telemetry,
    )


calendar_recovery = _calendar_recovery_arm()
calendar_recovery_only = _calendar_recovery_only_arm()
calendar_liquidation_only = _calendar_liquidation_only_arm()
INSTRUMENTED_ARMS: dict[str, InstrumentedArm] = {
    "calendar_recovery": _calendar_recovery_arm,
    "calendar_recovery_only": _calendar_recovery_only_arm,
    "calendar_liquidation_only": _calendar_liquidation_only_arm,
}


def replay_agent(actions: list[dict[str, Any]]) -> Agent:
    """Return a one-argument callable following a captured schedule."""
    def agent(observation: dict[str, Any]) -> dict[str, Any]:
        record = int(observation.get("step", 0)) + 1
        if record >= len(actions):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        return actions[record]

    return agent


def fertilizer_70(observation: dict[str, Any]) -> dict[str, Any]:
    return decide_with_threshold(observation, 70)


def run_episode(
    make: Any,
    agent: Agent,
    record: dict[str, Any],
) -> tuple[float, float]:
    agents = [agent, replay_agent(record["opponent_actions"])]
    own_player = int(record["own_player"])
    if own_player == 1:
        agents.reverse()
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": int(record["seed"])},
        debug=False,
    )
    environment.run(agents)
    final = environment.steps[-1]
    return float(final[own_player].reward), float(final[1 - own_player].reward)


def validate_control_reproduction(
    record: dict[str, Any],
    reward: float,
    opponent_reward: float,
) -> None:
    """Require both terminal rewards to match the captured live episode."""
    episode_id = int(record["episode_id"])
    own_player = int(record["own_player"])
    expected = (
        float(record["expected_rewards"][own_player]),
        float(record["expected_rewards"][1 - own_player]),
    )
    actual = (reward, opponent_reward)
    if actual != expected:
        raise ValueError(
            f"Control did not reproduce episode {episode_id}: "
            f"{actual} != {expected}"
        )


def _aggregate_telemetry(
    episodes: list[dict[str, Any]],
) -> dict[str, Any]:
    guard_types: dict[str, int] = {}
    guard_firings = 0
    prevented_invalid = 0
    recovered_units = 0
    sold_units = 0
    for episode in episodes:
        guard_firings += int(episode.get("guard_firings", 0))
        prevented_invalid += int(episode.get("prevented_invalid", 0))
        recovered_units += int(episode.get("recovered_units", 0))
        sold_units += int(episode.get("sold_units", 0))
        for guard_type, count in episode.get("guard_types", {}).items():
            guard_types[guard_type] = guard_types.get(guard_type, 0) + count
    return {
        "episodes": len(episodes),
        "guard_firings": guard_firings,
        "guard_types": guard_types,
        "prevented_invalid": prevented_invalid,
        "recovered_units": recovered_units,
        "sold_units": sold_units,
    }


def summarize(
    outcomes: list[dict[str, Any]],
    control: dict[int, float],
) -> dict[str, Any]:
    deltas = [
        outcome["reward"] - control[int(outcome["episode_id"])]
        for outcome in outcomes
    ]
    return {
        "games": len(outcomes),
        "wins": sum(
            outcome["reward"] > outcome["opponent_reward"]
            for outcome in outcomes
        ),
        "mean_reward": round(
            sum(outcome["reward"] for outcome in outcomes) / len(outcomes),
            2,
        ),
        "mean_reward_delta": round(sum(deltas) / len(deltas), 2),
        "improved_tied_worse": [
            sum(delta > 0 for delta in deltas),
            sum(delta == 0 for delta in deltas),
            sum(delta < 0 for delta in deltas),
        ],
        "minimum_reward_delta": min(deltas),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--arm", action="append")
    parser.add_argument("--control", type=Path, default=CONTROL)
    parser.add_argument("--episode", action="append", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.dataset.read_text(encoding="utf-8"))["records"]
    if args.episode:
        requested = set(args.episode)
        records = [
            record
            for record in records
            if int(record["episode_id"]) in requested
        ]
        found = {int(record["episode_id"]) for record in records}
        if missing := sorted(requested - found):
            raise SystemExit(f"Unknown episode: {missing[0]}")
    make, simulator_version = load_simulator()
    arms: dict[str, Agent] = {
        "control": load_agent_callable(args.control),
        "budgeted_value_fertilizer": budgeted_value_fertilizer,
        "full_capacity": full_capacity,
        "center_out": center_out,
        "calendar_recovery": calendar_recovery,
        "calendar_recovery_only": calendar_recovery_only,
        "calendar_liquidation_only": calendar_liquidation_only,
        "investment": investment,
        "dynamic_replacement": dynamic_replacement,
        "colocated_crop_service": colocated_crop_service,
        "colocated_value_fertilizer": colocated_value_fertilizer,
        "contextual_carried_crop_service": contextual_carried_crop_service,
        "guarded_colocated_crop_service": guarded_colocated_crop_service,
        "guarded_carried_crop_service": guarded_carried_crop_service,
        "idle_value_fertilizer": idle_value_fertilizer,
        "pressure_labor": pressure_labor,
        "lean_herd": lean_herd,
        "late_strawberry": late_strawberry,
        "late_melon_fertilizer": late_melon_fertilizer,
        "late_strawberry_fertilizer": late_strawberry_fertilizer,
        "late_value_fertilizer": late_value_fertilizer,
        "late_value_fertilizer_feed": late_value_fertilizer_feed,
        "pressure_late_strawberry": pressure_late_strawberry,
        "tiered_value_fertilizer": tiered_value_fertilizer,
        "tiered_late_strawberry": tiered_late_strawberry,
        "fertilizer_70": fertilizer_70,
    }
    if args.arm:
        unknown = [
            name for name in args.arm
            if name not in arms or name == "control"
        ]
        if unknown:
            raise SystemExit(f"Unknown candidate arm: {unknown[0]}")
        arms = {
            "control": arms["control"],
            **{name: arms[name] for name in dict.fromkeys(args.arm)},
        }
    results: dict[str, Any] = {}
    control_rewards: dict[int, float] = {}
    telemetry_reports: dict[str, Any] = {}
    for name, arm in arms.items():
        outcomes = []
        episode_telemetry: list[dict[str, Any]] = []
        for record in records:
            telemetry = (
                CandidateATelemetry()
                if name in INSTRUMENTED_ARMS
                else None
            )
            agent = (
                INSTRUMENTED_ARMS[name](telemetry)
                if name in INSTRUMENTED_ARMS
                else arm
            )
            reward, opponent_reward = run_episode(make, agent, record)
            episode_id = int(record["episode_id"])
            outcomes.append(
                {
                    "episode_id": episode_id,
                    "reward": reward,
                    "opponent_reward": opponent_reward,
                    "result": (
                        "win" if reward > opponent_reward else "loss"
                    ),
                }
            )
            if name == "control":
                control_rewards[episode_id] = reward
                validate_control_reproduction(
                    record,
                    reward,
                    opponent_reward,
                )
            if telemetry is not None:
                episode_telemetry.append(
                    {
                        "episode_id": episode_id,
                        **telemetry.summarize(),
                    }
                )
            print(
                f"{name} episode={episode_id} reward={reward} "
                f"opponent={opponent_reward}"
            )
        results[name] = {"outcomes": outcomes}
        if name != "control":
            results[name]["summary"] = summarize(outcomes, control_rewards)
            if episode_telemetry:
                telemetry_reports[name] = {
                    "episodes": episode_telemetry,
                    "aggregate": _aggregate_telemetry(episode_telemetry),
                }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        report_payload = {
            "simulator_version": simulator_version,
            "dataset": str(args.dataset),
            "control": str(args.control),
            "episodes": [
                int(record["episode_id"])
                for record in records
            ],
            "results": results,
        }
        if telemetry_reports:
            report_payload["residual_instrumentation"] = telemetry_reports
        args.output.write_text(
            json.dumps(
                report_payload,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
