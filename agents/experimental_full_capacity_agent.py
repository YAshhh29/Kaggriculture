"""Three-quadrant challenger that keeps paid workers productive late."""

from __future__ import annotations

from typing import Any

from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Expand through SW and backfill cleared crop slots with safe wheat."""
    return decide_premium(
        observation,
        target_extra_land=2,
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the full-capacity policy."""
    return decide(observation)
