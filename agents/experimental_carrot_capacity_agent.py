"""Deadline capacity using fast carrot rotation after the opening."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Rotate cleared premium slots into three-day carrots."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="CARROT",
        land_reserves=(300, 300),
        late_rotation_crop="CARROT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run carrot-rotation deadline capacity."""
    return decide(observation)
