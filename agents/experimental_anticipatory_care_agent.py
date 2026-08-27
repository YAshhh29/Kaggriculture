"""Deadline capacity using reserve-respecting same-day anticipatory CARE."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """CARE before FEED completes when service capacity permits."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        anticipate_daily_feed_for_care=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run anticipatory CARE capacity."""
    return decide(observation)
