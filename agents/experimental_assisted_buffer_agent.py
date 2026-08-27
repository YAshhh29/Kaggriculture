"""Funded midgame wheat buffering with cross-quadrant crop rescue."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_midgame_buffer_agent import _wheat_buffer_multiplier
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Use idle workers to rescue deadlines outside their home quadrant."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        cross_quadrant_crop_rescue=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        wheat_seed_buffer_multiplier=_wheat_buffer_multiplier(observation),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run assisted midgame wheat capacity."""
    return decide(observation)
