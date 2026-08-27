"""Summarize requested wheat trades against pre-transition market quotes."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _orders(action: Any) -> list[list[Any]]:
    if not isinstance(action, dict):
        return []
    market = action.get("market", [])
    return market if isinstance(market, list) else []


def analyze_wheat_trades(replay: dict[str, Any], player: int) -> dict[str, Any]:
    """Align each executed wheat order with its pre-decision observation."""
    events: list[dict[str, Any]] = []
    daily = Counter()
    steps = replay.get("steps", [])
    for record_index in range(1, len(steps)):
        before = steps[record_index - 1][player].get("observation", {})
        action = steps[record_index][player].get("action")
        market = before.get("market", {})
        price = int(market.get("prices", {}).get("WHEAT", 0))
        inventory = int(market.get("inventory", {}).get("WHEAT", 0))
        day = int(before.get("day", 0))
        hour = int(before.get("hour", 0))
        for order in _orders(action):
            if (
                len(order) < 3
                or order[0] not in {"BUY_PRODUCT", "SELL"}
                or order[1] != "WHEAT"
            ):
                continue
            quantity = int(order[2])
            operation = str(order[0])
            events.append(
                {
                    "day": day,
                    "hour": hour,
                    "operation": operation,
                    "quantity": quantity,
                    "quoted_price": price,
                    "market_inventory": inventory,
                }
            )
            daily[(day, operation)] += quantity

    def operation_summary(operation: str) -> dict[str, Any]:
        selected = [
            event for event in events if event["operation"] == operation
        ]
        units = sum(int(event["quantity"]) for event in selected)
        return {
            "orders": len(selected),
            "units": units,
            "minimum_quote": min(
                (int(event["quoted_price"]) for event in selected),
                default=None,
            ),
            "maximum_quote": max(
                (int(event["quoted_price"]) for event in selected),
                default=None,
            ),
            "weighted_mean_quote": (
                round(
                    sum(
                        int(event["quoted_price"])
                        * int(event["quantity"])
                        for event in selected
                    )
                    / units,
                    4,
                )
                if units
                else None
            ),
        }

    return {
        "player": player,
        "buy": operation_summary("BUY_PRODUCT"),
        "sell": operation_summary("SELL"),
        "daily_units": [
            {
                "day": day,
                "bought": daily[(day, "BUY_PRODUCT")],
                "sold": daily[(day, "SELL")],
            }
            for day in sorted({day for day, _ in daily})
        ],
        "events": events,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    replay = json.loads(args.replay.read_text(encoding="utf-8"))
    report = {
        "replay": str(args.replay),
        "players": [
            analyze_wheat_trades(replay, player)
            for player in range(len(replay.get("steps", [[None, None]])[0]))
        ],
    }
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wheat trade analysis written to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
