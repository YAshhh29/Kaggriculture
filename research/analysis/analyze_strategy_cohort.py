"""Analyze a stratified cohort of public Kaggriculture strategies."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import fmean
from typing import Any

from research.analysis.analyze_public_replay import analyze_replay
from research.collection.collect_live_replay_league import (
    _fetch_replay,
    _resolve_player,
)


def _daily_target_counts(
    player: dict[str, Any],
    operation: str,
) -> dict[str, int]:
    return {
        str(entry["day"]): int(entry["counts"].get(operation, 0))
        for entry in player["actions_by_day"]
    }


def _compact_player(player: dict[str, Any]) -> dict[str, Any]:
    utilization = player["board_utilization"]
    transitions = player["successful_board_transitions"]
    actions = player["action_counts"]["all_workers"]
    market = player["market_units_requested"]
    return {
        "reward": float(player["reward"]),
        "hires": player["workforce"]["hires"],
        "maximum_hands": player["workforce"]["maximum_simultaneous_hands"],
        "hires_by_day": player["workforce"]["hires_by_day"],
        "land_purchases": player["land_purchases"],
        "plants": transitions["plants"],
        "plants_by_day": transitions["plants_by_day"],
        "animal_placements": transitions["animal_placements"],
        "animal_losses": transitions["animal_losses"],
        "plant_actions_by_day": _daily_target_counts(player, "PLANT"),
        "water_actions_by_day": _daily_target_counts(player, "WATER"),
        "harvest_actions_by_day": _daily_target_counts(player, "HARVEST"),
        "pass_actions_by_day": _daily_target_counts(player, "PASS"),
        "actions": {
            key: int(actions.get(key, 0))
            for key in (
                "PLANT",
                "WATER",
                "HARVEST",
                "DIG",
                "FEED",
                "CARE",
                "COLLECT_FERTILIZER",
                "FERTILIZE",
                "PICKUP",
                "DROP",
                "PASS",
                "NORTH",
                "SOUTH",
                "EAST",
                "WEST",
            )
        },
        "sales": {
            key.removeprefix("SELL:"): int(value)
            for key, value in market.items()
            if key.startswith("SELL:")
        },
        "purchases": {
            key: int(value)
            for key, value in market.items()
            if key.startswith(("BUY_", "HIRE"))
        },
        "maximum_board_counts": player["maximum_board_counts"],
        "maximum_concurrent": utilization["maximum_concurrent_counts"],
        "peak_utilization": utilization["peak_productive_utilization"],
        "daily_peak_productive": utilization[
            "daily_peak_productive_tiles"
        ],
        "season_productive_utilization": utilization[
            "season_productive_capacity_utilization"
        ],
        "bank_by_day": player["bank_at_day_start"],
        "terminal": player["terminal"],
    }


def analyze_spec(spec: dict[str, Any]) -> dict[str, Any]:
    episode_id = int(spec["episode_id"])
    team_name = str(spec["team_name"])
    replay = _fetch_replay(episode_id)
    player = _resolve_player(replay, "auto", team_name)
    analysis = analyze_replay(replay)
    opponent = 1 - player
    own_reward = float(replay["rewards"][player])
    opponent_reward = float(replay["rewards"][opponent])
    return {
        "band": str(spec["band"]),
        "score": float(spec["score"]),
        "submission_id": int(spec["submission_id"]),
        "episode_id": episode_id,
        "seed": int(replay["info"]["seed"]),
        "team_name": team_name,
        "own_player": player,
        "result": (
            "win"
            if own_reward > opponent_reward
            else "loss"
            if own_reward < opponent_reward
            else "tie"
        ),
        "margin": own_reward - opponent_reward,
        "own": _compact_player(analysis["players"][player]),
        "opponent": _compact_player(analysis["players"][opponent]),
    }


def _mean(records: list[dict[str, Any]], path: tuple[str, ...]) -> float:
    values: list[float] = []
    for record in records:
        value: Any = record
        for key in path:
            value = value.get(key, 0) if isinstance(value, dict) else 0
        values.append(float(value or 0))
    return round(fmean(values), 2) if values else 0.0


def _sum_mapping(
    records: list[dict[str, Any]],
    path: tuple[str, ...],
) -> dict[str, int]:
    total: Counter[str] = Counter()
    for record in records:
        value: Any = record
        for key in path:
            value = value.get(key, {}) if isinstance(value, dict) else {}
        if isinstance(value, dict):
            total.update({str(key): int(item) for key, item in value.items()})
    return dict(sorted(total.items()))


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for band in sorted({str(record["band"]) for record in records}):
        selected = [record for record in records if record["band"] == band]
        result[band] = {
            "games": len(selected),
            "wins": sum(record["result"] == "win" for record in selected),
            "mean_reward": _mean(selected, ("own", "reward")),
            "mean_margin": _mean(selected, ("margin",)),
            "mean_hires": _mean(selected, ("own", "hires")),
            "mean_maximum_hands": _mean(
                selected,
                ("own", "maximum_hands"),
            ),
            "mean_maximum_productive_tiles": _mean(
                selected,
                ("own", "maximum_concurrent", "productive_tiles"),
            ),
            "mean_season_productive_utilization": _mean(
                selected,
                ("own", "season_productive_utilization"),
            ),
            "total_plants": _sum_mapping(selected, ("own", "plants")),
            "total_animals": _sum_mapping(
                selected,
                ("own", "animal_placements"),
            ),
            "total_losses": _sum_mapping(
                selected,
                ("own", "animal_losses"),
            ),
            "total_sales": _sum_mapping(selected, ("own", "sales")),
            "mean_plant_actions": _mean(
                selected,
                ("own", "actions", "PLANT"),
            ),
            "mean_pass_actions": _mean(
                selected,
                ("own", "actions", "PASS"),
            ),
            "mean_late_plant_actions": round(
                fmean(
                    sum(
                        int(quantity)
                        for day, quantity in record["own"][
                            "plant_actions_by_day"
                        ].items()
                        if int(day) >= 20
                    )
                    for record in selected
                ),
                2,
            ),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specification", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--episode", action="append", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    specs = json.loads(args.specification.read_text(encoding="utf-8"))[
        "episodes"
    ]
    if args.episode:
        requested = set(args.episode)
        specs = [
            spec
            for spec in specs
            if int(spec["episode_id"]) in requested
        ]
        found = {int(spec["episode_id"]) for spec in specs}
        if missing := sorted(requested - found):
            raise SystemExit(f"Unknown episode: {missing[0]}")
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        records = list(executor.map(analyze_spec, specs))
    records.sort(key=lambda record: (record["band"], record["episode_id"]))
    report = {
        "specification": str(args.specification),
        "summary": summarize(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
