"""Safe animal-service templates for contextual policy selection."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


ARM_BASELINE = 0
ARM_PAIRED = 1
SERVICE_ARMS = (ARM_BASELINE, ARM_PAIRED)
ARM_NAMES = {
    ARM_BASELINE: "deadline-baseline",
    ARM_PAIRED: "colocated-feed-care",
}


def decide_service_arm(
    observation: dict[str, Any],
    arm: int,
) -> dict[str, Any]:
    """Execute one service template through deterministic safety."""
    if arm not in SERVICE_ARMS:
        raise ValueError(f"Unknown service arm: {arm}")
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        pair_colocated_feed_care=arm == ARM_PAIRED,
    )
