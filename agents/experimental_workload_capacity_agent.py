"""Rejected workload-only reserve release experiment."""

from __future__ import annotations

from typing import Any

from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Release crop reserves whenever no crop action is due this turn."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        actionable_crop_reserve=True,
        prioritize_mature_harvest=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the workload-only reserve experiment."""
    return decide(observation)
