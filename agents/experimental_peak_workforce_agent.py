"""Deadline policy with replay-grounded 13-hand peak days."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


PEAK_HAND_DAYS = frozenset({19, 21, 26})
PEAK_HAND_TARGETS = tuple(
    13 if day in PEAK_HAND_DAYS else target
    for day, target in enumerate(DEADLINE_HAND_TARGETS)
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Add one worker on the winning elite replay's peak days."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=PEAK_HAND_TARGETS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the replay-grounded peak workforce policy."""
    return decide(observation)
