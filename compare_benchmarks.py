"""Compare two benchmark reports game by game."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import fmean, median
from typing import Any


def compare_reports(
    candidate: dict[str, Any],
    control: dict[str, Any],
    excluded_seeds: set[int] | None = None,
) -> dict[str, Any]:
    _validate_compatible(candidate, control)
    candidate_games = _index_games(candidate.get("games", []))
    control_games = _index_games(control.get("games", []))
    if candidate_games.keys() != control_games.keys():
        raise ValueError("candidate and control must contain identical games")

    rows = []
    for seed, player in sorted(candidate_games):
        candidate_game = candidate_games[(seed, player)]
        control_game = control_games[(seed, player)]
        candidate_coins = float(candidate_game["agent_reward"])
        control_coins = float(control_game["agent_reward"])
        rows.append(
            {
                "seed": seed,
                "agent_player": player,
                "candidate_coins": candidate_coins,
                "control_coins": control_coins,
                "coin_delta": round(candidate_coins - control_coins, 6),
                "candidate_result": candidate_game.get("result"),
                "control_result": control_game.get("result"),
            }
        )

    excluded_seeds = excluded_seeds or set()
    strict_rows = [
        row for row in rows if row["seed"] not in excluded_seeds
    ]
    seed_rows = _aggregate_by_seed(rows)
    strict_seed_rows = [
        row for row in seed_rows if row["seed"] not in excluded_seeds
    ]
    candidate_route = candidate["summary"]["route_analysis"]
    control_route = control["summary"]["route_analysis"]
    return {
        "simulator_version": candidate.get("simulator_version"),
        "opponent": candidate.get("opponent"),
        "episode_steps": candidate.get("episode_steps"),
        "candidate_parameters": candidate.get("parameters", {}),
        "control_parameters": control.get("parameters", {}),
        "summary": {
            "all_games": _paired_summary(rows),
            "all_seeds": _paired_summary(seed_rows),
            "excluded_seed_check": {
                "excluded_seeds": sorted(excluded_seeds),
                "games": _paired_summary(strict_rows),
                "seeds": _paired_summary(strict_seed_rows),
            },
            "candidate": _report_summary(candidate),
            "control": _report_summary(control),
            "production": {
                "candidate_harvested_units": candidate_route.get(
                    "harvested_units", 0
                ),
                "control_harvested_units": control_route.get(
                    "harvested_units", 0
                ),
                "candidate_sold_units": candidate_route.get(
                    "matched_sold_units", 0
                ),
                "control_sold_units": control_route.get(
                    "matched_sold_units", 0
                ),
                "candidate_unsold_harvested_units": candidate_route.get(
                    "unmatched_harvested_units", 0
                ),
                "control_unsold_harvested_units": control_route.get(
                    "unmatched_harvested_units", 0
                ),
            },
        },
        "checks": {
            "identical_game_keys": True,
            "candidate_won_every_game": all(
                row["candidate_result"] == "win" for row in rows
            ),
            "candidate_improved_every_game": all(
                row["coin_delta"] > 0 for row in rows
            ),
            "identical_harvested_units": (
                candidate_route.get("harvested_units")
                == control_route.get("harvested_units")
            ),
            "candidate_sold_every_harvested_unit": (
                candidate_route.get("unmatched_harvested_units") == 0
            ),
        },
        "games": rows,
        "seeds": seed_rows,
    }


def _validate_compatible(
    candidate: dict[str, Any], control: dict[str, Any]
) -> None:
    for field in ("simulator_version", "opponent", "episode_steps"):
        if candidate.get(field) != control.get(field):
            raise ValueError(f"benchmark field differs: {field}")
    if not candidate.get("complete") or not control.get("complete"):
        raise ValueError("both benchmark reports must be complete")


def _index_games(games: list[dict[str, Any]]) -> dict[tuple[int, int], Any]:
    indexed = {}
    for game in games:
        key = (int(game["seed"]), int(game["agent_player"]))
        if key in indexed:
            raise ValueError(f"duplicate game: {key}")
        indexed[key] = game
    return indexed


def _paired_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    deltas = [float(row["coin_delta"]) for row in rows]
    improved = sum(delta > 0 for delta in deltas)
    tied = sum(delta == 0 for delta in deltas)
    worse = sum(delta < 0 for delta in deltas)
    return {
        "games": len(rows),
        "mean_coin_delta": round(fmean(deltas), 2) if deltas else None,
        "median_coin_delta": round(median(deltas), 2) if deltas else None,
        "minimum_coin_delta": min(deltas, default=None),
        "maximum_coin_delta": max(deltas, default=None),
        "improved_games": improved,
        "tied_games": tied,
        "worse_games": worse,
        "one_sided_sign_test_p_value": _sign_test_p_value(
            improved,
            worse,
        ),
    }


def _aggregate_by_seed(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(int(row["seed"]), []).append(row)
    return [
        {
            "seed": seed,
            "positions": len(seed_rows),
            "coin_delta": round(
                fmean(float(row["coin_delta"]) for row in seed_rows),
                6,
            ),
        }
        for seed, seed_rows in sorted(grouped.items())
    ]


def _sign_test_p_value(improved: int, worse: int) -> float | None:
    non_tied = improved + worse
    if non_tied == 0:
        return None
    tail = sum(
        math.comb(non_tied, successes)
        for successes in range(improved, non_tied + 1)
    )
    return tail / (2**non_tied)


def _report_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["summary"]
    return {
        "wins": summary.get("wins"),
        "losses": summary.get("losses"),
        "ties": summary.get("ties"),
        "errors": summary.get("errors"),
        "mean_coins": summary.get("mean_agent_coins"),
        "minimum_coins": summary.get("min_agent_coins"),
        "maximum_coins": summary.get("max_agent_coins"),
        "final_inventory_totals": summary.get("final_inventory_totals"),
        "mean_harvest_to_sale_turns": summary.get(
            "route_analysis", {}
        ).get("mean_harvest_to_sale_turns"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("control", type=Path)
    parser.add_argument("--exclude-seed", action="append", type=int, default=[])
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    control = json.loads(args.control.read_text(encoding="utf-8"))
    comparison = compare_reports(
        candidate,
        control,
        set(args.exclude_seed),
    )
    comparison["candidate_report"] = str(args.candidate)
    comparison["control_report"] = str(args.control)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(comparison, indent=2) + "\n",
        encoding="utf-8",
    )
    all_games = comparison["summary"]["all_games"]
    print(f"Games: {all_games['games']}")
    print(f"Mean coin delta: {all_games['mean_coin_delta']}")
    print(
        "Improved/tied/worse: "
        f"{all_games['improved_games']}/"
        f"{all_games['tied_games']}/"
        f"{all_games['worse_games']}"
    )
    print(f"Comparison written to {args.output}")


if __name__ == "__main__":
    main()