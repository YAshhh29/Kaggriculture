"""Gate future labor against the live package across opponent families."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from benchmark import load_agent_callable, load_simulator, run_game, summarize


ROOT = Path(__file__).resolve().parents[2]
VARIANTS = {
    "submitted_control": "submissions/demand-animal/main.py",
    "future_labor": "agents/experimental_future_labor_agent.py",
}
DEFAULT_OPPONENTS = (
    "submissions/demand-animal/main.py",
    "agents/experimental_compact_macro_agent.py",
    "agents/experimental_adaptive_counter_agent.py",
    "agents/experimental_lifecycle_agent.py",
    "agents/experimental_scale_agent.py",
    "submissions/learned-service/main.py",
    "agents/current_top_replay_agent.py",
    "agents/current_rank2_replay_agent.py",
)
Agent = Callable[[dict[str, Any]], dict[str, Any]]


def compact_game(record: dict[str, Any]) -> dict[str, Any]:
    route = record["route_analysis"]
    livestock = record["livestock_analysis"]
    return {
        key: record[key]
        for key in (
            "seed",
            "agent_player",
            "agent_reward",
            "opponent_reward",
            "result",
        )
    } | {
        "movement_turns": route.get("all_worker_movement_turns", 0),
        "cycles_planted": route.get("cycles_planted", 0),
        "cycles_harvested": route.get("cycles_harvested", 0),
        "cycles_weeded": route.get("cycles_weeded", 0),
        "cycles_unfinished": route.get("cycles_unfinished", 0),
        "livestock_losses": livestock.get("losses", {}),
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def totals(results: dict[str, Any]) -> dict[str, Any]:
    summaries = [entry["summary"] for entry in results.values()]
    games = sum(int(summary["games"]) for summary in summaries)
    return {
        "games": games,
        "wins": sum(int(summary["wins"]) for summary in summaries),
        "losses": sum(int(summary["losses"]) for summary in summaries),
        "errors": sum(int(summary["errors"]) for summary in summaries),
        "mean_margin": round(
            sum(
                float(summary["mean_margin"]) * int(summary["games"])
                for summary in summaries
            )
            / games,
            2,
        ),
    }


def promotion(report: dict[str, Any]) -> dict[str, Any]:
    variants = report["variants"]
    control = totals(variants["submitted_control"])
    candidate = totals(variants["future_labor"])
    checks = {
        "zero_errors": candidate["errors"] == 0,
        "more_total_wins": candidate["wins"] > control["wins"],
        "positive_margin_delta": (
            candidate["mean_margin"] > control["mean_margin"]
        ),
        "no_opponent_win_regression": all(
            int(entry["summary"]["wins"])
            >= int(
                variants["submitted_control"][opponent]["summary"]["wins"]
            )
            for opponent, entry in variants["future_labor"].items()
        ),
    }
    return {
        "decision": "PROMOTE" if all(checks.values()) else "REJECT",
        "checks": checks,
        "candidate": candidate,
        "control": control,
    }


def run_gate(
    *,
    seed_start: int,
    seed_count: int,
    opponents: tuple[str, ...],
    output: Path,
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
    for variant, agent_path in VARIANTS.items():
        agent: Agent = load_agent_callable((ROOT / agent_path).resolve())
        report["variants"][variant] = {}
        for opponent_path in opponents:
            opponent = load_agent_callable((ROOT / opponent_path).resolve())
            records = []
            for seed in range(seed_start, seed_start + seed_count):
                for player in (0, 1):
                    record = run_game(
                        make,
                        agent,
                        opponent,
                        720,
                        seed,
                        player,
                    )
                    records.append(record)
                    report["variants"][variant][opponent_path] = {
                        "summary": summarize(records),
                        "games": [compact_game(item) for item in records],
                    }
                    write_report(output, report)
                    print(
                        f"{variant} vs {Path(opponent_path).stem} "
                        f"seed={seed} player={player} {record['result']} "
                        f"{record['agent_reward']}-{record['opponent_reward']}"
                    )
    report["totals"] = {
        name: totals(results)
        for name, results in report["variants"].items()
    }
    report["promotion"] = promotion(report)
    write_report(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=209)
    parser.add_argument("--seed-count", type=int, default=1)
    parser.add_argument("--opponent", action="append", dest="opponents")
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "benchmarks"
            / "future-labor-gate.json"
        ),
    )
    args = parser.parse_args()
    report = run_gate(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        opponents=tuple(args.opponents or DEFAULT_OPPONENTS),
        output=args.output,
    )
    print(json.dumps(report["totals"], indent=2))
    print(json.dumps(report["promotion"], indent=2))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()