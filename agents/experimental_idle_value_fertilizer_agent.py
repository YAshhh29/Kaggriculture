"""Budgeted strawberry service using only otherwise-idle carriers."""

from __future__ import annotations

from typing import Any

from agents.experimental_late_value_fertilizer_agent import (
    decide_value_fertilizer,
)


MAX_FERTILIZER_APPLICATIONS = 4
_APPLICATION_COUNTS: dict[int, int] = {}


def decide(
    observation: dict[str, Any],
    *,
    maximum_distance: int = 2,
    maximum_applications: int = MAX_FERTILIZER_APPLICATIONS,
) -> dict[str, Any]:
    """Stage idle carriers without replacing productive assignments."""
    player = int(observation["player"])
    if (
        int(observation.get("day", 0)) == 0
        and int(observation.get("hour", 0)) == 0
    ):
        _APPLICATION_COUNTS.pop(player, None)
    used = _APPLICATION_COUNTS.get(player, 0)
    decision = decide_value_fertilizer(
        observation,
        economic_feed=False,
        enabled_crops=(),
        idle_enabled_crops=("STRAWBERRY",),
        application_limit=max(0, maximum_applications - used),
        idle_maximum_distance=maximum_distance,
    )
    actions = [decision.get("farmer", ["PASS"]), *decision.get("hands", [])]
    _APPLICATION_COUNTS[player] = used + sum(
        action == ["FERTILIZE"] for action in actions
    )
    return decision


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run idle-only value fertilizer service."""
    return decide(observation)
