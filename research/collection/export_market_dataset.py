"""Export auditable hold-versus-sell examples from episode audits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


def build_dataset(audits: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []

    for audit_index, audit in enumerate(audits):
        metadata = audit.get("metadata", {})
        collection = metadata.get("collection", {})
        collection = collection if isinstance(collection, dict) else {}
        source_replay = str(metadata.get("source_replay", ""))
        episode_id = str(
            collection.get("episode_id")
            or Path(source_replay).stem
            or f"episode-{audit_index}"
        )
        behavior_policy = {
            "agent_sha256": metadata.get("agent_sha256"),
            "market_policy": audit.get("policy_under_audit", {}).get(
                "market_policy", []
            ),
        }
        score = audit.get("score", {})
        summary = audit.get("summary", {})
        terminal_money = float(summary.get("final_money", 0))
        opponent_reward = score.get("opponent_reward")
        final_reward = score.get("final_reward")
        terminal_margin = (
            float(final_reward) - float(opponent_reward)
            if final_reward is not None and opponent_reward is not None
            else None
        )

        episode_rows = 0
        for record in audit.get("records", []):
            if record.get("record_type") != "executed_transition":
                continue
            state = record.get("state_before", {})
            shed_wheat = int(state.get("shed_wheat", 0))
            if shed_wheat <= 0:
                continue

            sale_units_ordered = _sale_units(record.get("market_orders", []))
            cash_flow = record.get("cash_flow", {})
            money_before = float(state.get("money", 0))
            rows.append(
                {
                    "episode_id": episode_id,
                    "seed": collection.get("seed"),
                    "agent_player": collection.get(
                        "agent_player", metadata.get("player")
                    ),
                    "opponent": collection.get("opponent"),
                    "behavior_policy_sha256": behavior_policy[
                        "agent_sha256"
                    ],
                    "record_index": int(record.get("record_index", 0)),
                    "features": {
                        "decision_observation_step": int(
                            record.get("decision_observation_step", 0)
                        ),
                        "day": int(record.get("day", 0)),
                        "hour": int(record.get("hour", 0)),
                        "money": money_before,
                        "wheat_seeds": int(state.get("wheat_seeds", 0)),
                        "shed_wheat": shed_wheat,
                        "carried_wheat": int(state.get("carried_wheat", 0)),
                        "planted_wheat": int(state.get("planted_wheat", 0)),
                        "weeds": int(state.get("weeds", 0)),
                        "wheat_market_price": int(
                            state.get("wheat_market_price", 0)
                        ),
                        "wheat_market_inventory": int(
                            state.get("wheat_market_inventory", 0)
                        ),
                    },
                    "decision": {
                        "action": "SELL" if sale_units_ordered else "HOLD",
                        "sale_units_ordered": sale_units_ordered,
                    },
                    "outcomes": {
                        "immediate_money_delta": float(
                            cash_flow.get("net_money_delta", 0)
                        ),
                        "wheat_units_sold": int(
                            cash_flow.get("wheat_units_sold", 0)
                        ),
                        "realized_sale_revenue": cash_flow.get(
                            "realized_sale_revenue"
                        ),
                        "terminal_money": terminal_money,
                        "observed_terminal_money_delta": round(
                            terminal_money - money_before,
                            6,
                        ),
                        "terminal_result": score.get("result"),
                        "terminal_margin": terminal_margin,
                    },
                }
            )
            episode_rows += 1

        episodes.append(
            {
                "episode_id": episode_id,
                "source_replay": source_replay,
                "simulator_version": metadata.get("simulator_version"),
                "seed": collection.get("seed"),
                "agent_player": collection.get(
                    "agent_player", metadata.get("player")
                ),
                "opponent": collection.get("opponent"),
                "raw_replay_persisted": collection.get(
                    "raw_replay_persisted",
                    bool(source_replay),
                ),
                "behavior_policy": behavior_policy,
                "rows": episode_rows,
                "terminal_money": terminal_money,
                "result": score.get("result"),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "purpose": "offline analysis of observed wheat hold/sell decisions",
        "feature_boundary": (
            "features contains decision-time observations only; decision is "
            "the recorded behavior; outcomes contains post-decision values "
            "and must not be used as model input"
        ),
        "limitations": [
            "outcomes describe the chosen action, not a counterfactual action",
            "rows from one episode share the same terminal result",
        ],
        "episodes": episodes,
        "rows": rows,
        "summary": summarize_rows(rows),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    action_counts = {"HOLD": 0, "SELL": 0}
    for row in rows:
        action = row.get("decision", {}).get("action")
        if action in action_counts:
            action_counts[action] += 1
    return {
        "episodes": len({row.get("episode_id") for row in rows}),
        "market_decisions": len(rows),
        "action_counts": action_counts,
    }


def _sale_units(orders: Any) -> int:
    if not isinstance(orders, list):
        return 0
    return sum(
        max(0, int(order[2]))
        for order in orders
        if (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "SELL"
            and order[1] == "WHEAT"
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audits", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audits = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.audits
    ]
    dataset = build_dataset(audits)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(dataset, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Episodes: {len(dataset['episodes'])}")
    print(f"Market decisions: {len(dataset['rows'])}")
    print(f"Dataset written to {args.output}")


if __name__ == "__main__":
    main()