"""Paired animal service funding one bounded incremental wheat cohort."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_incremental_buffer_agent import _extra_wheat_seed
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Spend paired-service slack on one funded midgame wheat seed."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        pair_colocated_feed_care=True,
        extra_wheat_seed_buffer=_extra_wheat_seed(observation),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run paired incremental capacity."""
    return decide(observation)
