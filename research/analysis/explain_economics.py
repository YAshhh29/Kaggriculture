"""Explain public crop and animal opportunities at one replay record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from core.economics import economic_snapshot


def replay_snapshot(
    replay: dict[str, Any],
    record: int,
    player: int,
) -> dict[str, Any]:
    observation = replay["steps"][record][player]["observation"]
    return {
        "record": record,
        "player": player,
        "day": int(observation.get("day", 0)),
        "hour": int(observation.get("hour", 0)),
        **economic_snapshot(observation),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--record", type=int, required=True)
    parser.add_argument("--player", type=int, choices=(0, 1), default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    replay = json.loads(args.replay.read_text(encoding="utf-8"))
    report = replay_snapshot(replay, args.record, args.player)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Economic snapshot written to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
