"""Execute the rejected demand-animal tree for shadow comparison only."""

from __future__ import annotations

from typing import Any

from policies.demand_animal_policy import decide_demand_animal_arm
from policies.shadow_controller import select_shadow_arm


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the shadow recommendation through deterministic safe templates."""
    return decide_demand_animal_arm(
        observation,
        select_shadow_arm(observation),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the research-only shadow policy."""
    return decide(observation)
