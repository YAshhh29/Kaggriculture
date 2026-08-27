"""Evidence-backed compact macro policy over deterministic safe execution."""

from __future__ import annotations

from typing import Any

from agents.experimental_adaptive_counter_agent import ONE_LAND_ANIMAL_PLANS
from agents.experimental_premium_throughput_agent import decide as decide_premium


SELECTION_DAY = 9


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Keep the shared opening, then commit capital to one extra quadrant."""
    if int(observation.get("day", 0)) < SELECTION_DAY:
        return decide_premium(observation)
    return decide_premium(
        observation,
        target_extra_land=1,
        animal_plans=ONE_LAND_ANIMAL_PLANS,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the fixed compact macro policy."""
    return decide(observation)