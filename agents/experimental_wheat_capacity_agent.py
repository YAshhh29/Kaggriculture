"""Three-quadrant capacity policy with continuous wheat rotation."""

from __future__ import annotations

from typing import Any

from policies.capacity_policy import ARM_WHEAT, decide_capacity_arm


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the fixed wheat-rotation capacity template."""
    return decide_capacity_arm(observation, ARM_WHEAT)


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the fixed wheat-capacity policy."""
    return decide(observation)
