"""Collect checkpointed market-decision trajectories from local matches."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.analysis.audit_episode import build_audit
from benchmark import load_simulator
from research.collection.export_market_dataset import build_dataset, summarize_rows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
V9_MARKET_POLICY = [
    "sell shed wheat when its market price is at least 35",
    "sell shed wheat when holdings reach 72 units",
    "liquidate all remaining shed wheat from day 25 onward",
    "buy seeds needed to maintain six concurrent wheat crops",
    "stop seed buying and planting after day 24",
]


def collect_episode(
    make: Any,
    agent_path: Path,
    opponent: str,
    episode_steps: int,
    seed: int,
    agent_player: int,
) -> dict[str, Any]:
    agents: list[Any] = [str(agent_path), opponent]
    if agent_player == 1:
        agents.reverse()
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": episode_steps, "seed": seed},
        debug=False,
    )
    environment.run(agents)
    replay = environment.toJSON()
    episode_id = f"{opponent}-seed-{seed}-player-{agent_player}"
    audit = build_audit(
        replay,
        player=agent_player,
        source_replay=None,
        agent_path=agent_path,
        market_policy=V9_MARKET_POLICY,
    )
    audit["metadata"]["collection"] = {
        "episode_id": episode_id,
        "seed": seed,
        "agent_player": agent_player,
        "opponent": opponent,
        "raw_replay_persisted": False,
    }
    return audit


def write_checkpoint(
    output_path: Path,
    report: dict[str, Any],
    expected_episodes: int,
) -> None:
    report["complete"] = len(report["episodes"]) == expected_episodes
    report["summary"] = summarize_rows(report["rows"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )


def load_or_create_report(
    output_path: Path,
    collection: dict[str, Any],
) -> dict[str, Any]:
    if not output_path.exists():
        report = build_dataset([])
        report["created_at"] = datetime.now(timezone.utc).isoformat()
        report["collection"] = collection
        report["complete"] = False
        return report

    report = json.loads(output_path.read_text(encoding="utf-8"))
    existing = report.get("collection", {})
    for field in (
        "agent_sha256",
        "opponent",
        "episode_steps",
        "seed_start",
        "seed_count",
        "positions",
        "simulator_version",
    ):
        if existing.get(field) != collection.get(field):
            raise ValueError(f"checkpoint collection field differs: {field}")
    for episode in report.get("episodes", []):
        source_replay = str(episode.get("source_replay", ""))
        if source_replay.startswith("collected/"):
            episode["source_replay"] = ""
            episode["raw_replay_persisted"] = False
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent", type=Path, default=PROJECT_ROOT / "main.py"
    )
    parser.add_argument(
        "--opponent", choices=("pass", "random", "starter"), default="starter"
    )
    parser.add_argument("--seed-start", type=int, default=30)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--one-position", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed_count < 1:
        raise SystemExit("--seed-count must be at least 1")
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")
    agent_path = args.agent.resolve()
    if not agent_path.is_file():
        raise SystemExit(f"Agent file does not exist: {agent_path}")

    make, simulator_version = load_simulator()
    positions = [0] if args.one_position else [0, 1]
    collection = {
        "agent_file": str(agent_path),
        "agent_sha256": hashlib.sha256(agent_path.read_bytes()).hexdigest(),
        "opponent": args.opponent,
        "episode_steps": args.steps,
        "seed_start": args.seed_start,
        "seed_count": args.seed_count,
        "positions": positions,
        "simulator_version": simulator_version,
    }
    expected_episodes = args.seed_count * len(positions)
    try:
        report = load_or_create_report(args.output, collection)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    completed = {
        (episode.get("seed"), episode.get("agent_player"))
        for episode in report["episodes"]
    }

    for seed in range(args.seed_start, args.seed_start + args.seed_count):
        for agent_player in positions:
            if (seed, agent_player) in completed:
                continue
            audit = collect_episode(
                make,
                agent_path,
                args.opponent,
                args.steps,
                seed,
                agent_player,
            )
            episode_dataset = build_dataset([audit])
            report["episodes"].extend(episode_dataset["episodes"])
            report["rows"].extend(episode_dataset["rows"])
            write_checkpoint(args.output, report, expected_episodes)
            episode = episode_dataset["episodes"][0]
            print(
                f"seed={seed:3d} player={agent_player} "
                f"result={episode['result']:<5} "
                f"coins={episode['terminal_money']} rows={episode['rows']}"
            )

    write_checkpoint(args.output, report, expected_episodes)
    print(f"Episodes: {len(report['episodes'])}/{expected_episodes}")
    print(f"Market decisions: {len(report['rows'])}")
    print(f"Complete: {report['complete']}")
    print(f"Dataset written to {args.output}")


if __name__ == "__main__":
    main()