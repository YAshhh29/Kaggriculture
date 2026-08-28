"""Late premium fertilizer service capped across the full episode."""

from __future__ import annotations

from typing import Any

from agents.experimental_late_value_fertilizer_agent import (
    decide_value_fertilizer,
)


MAX_FERTILIZER_APPLICATIONS = 4
_APPLICATION_COUNTS: dict[int, int] = {}


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Use at most four total fertilizer actions in one episode."""
    player = int(observation["player"])
    if (
        int(observation.get("day", 0)) == 0
        and int(observation.get("hour", 0)) == 0
    ):
        _APPLICATION_COUNTS.pop(player, None)
    used = _APPLICATION_COUNTS.get(player, 0)
    remaining = max(0, MAX_FERTILIZER_APPLICATIONS - used)
    decision = decide_value_fertilizer(
        observation,
        economic_feed=False,
        enabled_crops=("STRAWBERRY",),
        application_limit=remaining,
    )
    actions = [decision.get("farmer", ["PASS"])]
    actions.extend(decision.get("hands", []))
    applied = sum(action == ["FERTILIZE"] for action in actions)
    _APPLICATION_COUNTS[player] = used + applied
    return decision


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run budgeted late strawberry fertilization."""
    return decide(observation)
