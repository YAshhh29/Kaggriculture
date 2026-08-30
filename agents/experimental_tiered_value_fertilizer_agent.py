"""Price-tiered idle strawberry fertilizer staging."""

from __future__ import annotations

from typing import Any

from agents.experimental_idle_value_fertilizer_agent import (
    decide as decide_idle,
)
from policies.live_macro_features import extract_live_macro_features


SELECTION_DAY = 12
SELECTION_HOUR = 12
MIN_STAGING_STRAWBERRY_PRICE_MULTIPLIER = 1.30
_STAGING_DISTANCES: dict[int, int] = {}


def _selected_staging_distance(observation: dict[str, Any]) -> int:
    """Lock distance two only when strawberry value supports movement."""
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _STAGING_DISTANCES.pop(player, None)
    if (day, hour) < (SELECTION_DAY, SELECTION_HOUR):
        return 0
    if player not in _STAGING_DISTANCES:
        features = extract_live_macro_features(observation)
        _STAGING_DISTANCES[player] = (
            2
            if features["price_strawberry"]
            > MIN_STAGING_STRAWBERRY_PRICE_MULTIPLIER
            else 0
        )
    return _STAGING_DISTANCES[player]


def decide(
    observation: dict[str, Any],
    *,
    maximum_applications: int = 4,
    late_strawberry_slots: int = 0,
) -> dict[str, Any]:
    """Run colocated service or value-supported two-step staging."""
    return decide_idle(
        observation,
        maximum_distance=_selected_staging_distance(observation),
        maximum_applications=maximum_applications,
        late_strawberry_slots=late_strawberry_slots,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the frozen tiered value fertilizer policy."""
    return decide(observation)
