"""Summarize late crop cycles and inventory from a goose benchmark report."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    for game in report["games"]:
        cycles = game["route_analysis"]["crop_cycles"]
        planted = Counter(int(cycle["planted_day"]) for cycle in cycles)
        harvested = Counter(
            int(cycle["harvest_day"])
            for cycle in cycles
            if cycle.get("status") == "harvested"
        )
        late_cycles = [
            {
                "planted_day": cycle["planted_day"],
                "planted_hour": cycle["planted_hour"],
                "status": cycle["status"],
                "harvest_day": cycle.get("harvest_day"),
                "harvest_units": cycle.get("harvest_units"),
            }
            for cycle in cycles
            if int(cycle["planted_day"]) >= 19
        ]
        print(
            f"seed={game['seed']} player={game['agent_player']} "
            f"score={game['agent_reward']} final={game['final_inventory']}"
        )
        print("  late plant counts:", dict(sorted(planted.items())))
        print("  late harvest counts:", dict(sorted(harvested.items())))
        print("  late cycles:", late_cycles)


if __name__ == "__main__":
    main()
