"""Deadline capacity with a public-replay-inspired melon season."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


MELON_LAST_PLANT_DAY = 18


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Rotate cleared slots into melons through their safe final cohort."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="MELON",
        rotation_last_plant_day=MELON_LAST_PLANT_DAY,
        land_reserves=(300, 300),
        late_rotation_crop="MELON",
        late_rotation_last_plant_day=MELON_LAST_PLANT_DAY,
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run melon-season deadline capacity."""
    return decide(observation)
