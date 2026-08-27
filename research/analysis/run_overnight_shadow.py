"""Compare control, candidate, shadow, and fixed demand-animal policies."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from benchmark import load_agent_callable, load_simulator, run_game, summarize
from policies.demand_animal_policy import (
    ARM_COW,
    ARM_GOOSE,
    decide_demand_animal_arm,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPPONENTS = (
    "submissions/learned-service/main.py",
    "agents/experimental_compact_macro_agent.py",
    "agents/experimental_adaptive_counter_agent.py",
    "agents/experimental_lifecycle_agent.py",
    "agents/experimental_scale_agent.py",
)
VARIANTS = (
    "submitted_control",
    "demand_heuristic",
    "shadow_tree",
    "fixed_cows",
    "fixed_geese",
)
Agent = Callable[[dict[str, Any]], dict[str, Any]]


def compact_game(record: dict[str, Any]) -> dict[str, Any]:
    """Retain outcome and mechanism signals without embedding full routes."""
    route = record.get("route_analysis", {})
    livestock = record.get("livestock_analysis", {})
    return {
        key: record[key]
        for key in (
            "seed",
            "agent_player",
            "agent_reward",
            "opponent_reward",
            "agent_status",
            "opponent_status",
            "result",
        )
    } | {
        "movement_turns": int(route.get("all_worker_movement_turns", 0)),
        "cycles_planted": int(route.get("cycles_planted", 0)),
        "cycles_harvested": int(route.get("cycles_harvested", 0)),
        "cycles_weeded": int(route.get("cycles_weeded", 0)),
        "livestock_losses": livestock.get("losses", {}),
    }


def aggregate(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-opponent benchmark summaries for one variant."""
    summaries = [entry["summary"] for entry in results.values()]
    games = sum(int(summary["games"]) for summary in summaries)
    margins = [
        float(summary["mean_margin"]) * int(summary["games"])
        for summary in summaries
        if summary["mean_margin"] is not None
    ]
    return {
        "games": games,
        "wins": sum(int(summary["wins"]) for summary in summaries),
        "losses": sum(int(summary["losses"]) for summary in summaries),
        "ties": sum(int(summary["ties"]) for summary in summaries),
        "errors": sum(int(summary["errors"]) for summary in summaries),
        "mean_margin": round(sum(margins) / games, 2) if games else None,
    }


def classify_promotion(
    variants: dict[str, dict[str, Any]],
    *,
    candidate: str = "demand_heuristic",
    control: str = "submitted_control",
) -> dict[str, Any]:
    """Apply conservative direct-rollout promotion requirements."""
    candidate_total = aggregate(variants[candidate])
    control_total = aggregate(variants[control])
    no_opponent_win_regression = all(
        int(variants[candidate][opponent]["summary"]["wins"])
        >= int(control_entry["summary"]["wins"])
        for opponent, control_entry in variants[control].items()
    )
    checks = {
        "zero_errors": candidate_total["errors"] == 0,
        "more_total_wins": candidate_total["wins"] > control_total["wins"],
        "positive_margin_delta": (
            candidate_total["mean_margin"] is not None
            and control_total["mean_margin"] is not None
            and candidate_total["mean_margin"] > control_total["mean_margin"]
        ),
        "no_opponent_win_regression": no_opponent_win_regression,
    }
    return {
        "decision": "PROMOTE" if all(checks.values()) else "REJECT",
        "checks": checks,
        "candidate": candidate_total,
        "control": control_total,
    }


def _variant_agent(name: str) -> Agent:
    if name == "submitted_control":
        return load_agent_callable(
            ROOT / "submissions" / "learned-service" / "main.py"
        )
    if name == "demand_heuristic":
        return load_agent_callable(
            ROOT / "agents" / "experimental_demand_animal_agent.py"
        )
    if name == "shadow_tree":
        return load_agent_callable(
            ROOT / "agents" / "experimental_shadow_demand_agent.py"
        )
    arm = ARM_COW if name == "fixed_cows" else ARM_GOOSE
    return lambda observation: decide_demand_animal_arm(observation, arm)


def run_suite(
    *,
    seed_start: int,
    seed_count: int,
    opponents: tuple[str, ...],
) -> dict[str, Any]:
    make, simulator_version = load_simulator()
    report: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "simulator_version": simulator_version,
        "seed_start": seed_start,
        "seed_count": seed_count,
        "opponents": list(opponents),
        "variants": {},
    }
    for variant in VARIANTS:
        agent = _variant_agent(variant)
        report["variants"][variant] = {}
        for opponent in opponents:
            opponent_agent = load_agent_callable((ROOT / opponent).resolve())
            records = [
                run_game(make, agent, opponent_agent, 720, seed, player)
                for seed in range(seed_start, seed_start + seed_count)
                for player in (0, 1)
            ]
            report["variants"][variant][opponent] = {
                "summary": summarize(records),
                "games": [compact_game(record) for record in records],
            }
    report["promotion"] = classify_promotion(report["variants"])
    report["variant_totals"] = {
        variant: aggregate(results)
        for variant, results in report["variants"].items()
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=188)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--opponent", action="append", dest="opponents")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts" / "benchmarks" / "overnight-shadow.json",
    )
    args = parser.parse_args()
    opponents = tuple(args.opponents or DEFAULT_OPPONENTS)
    report = run_suite(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        opponents=opponents,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["variant_totals"], indent=2))
    print(json.dumps(report["promotion"], indent=2))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
