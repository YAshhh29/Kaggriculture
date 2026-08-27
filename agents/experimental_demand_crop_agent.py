"""Demand-selected crop rotation with the frozen balanced animal plan."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import decide_demand


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Vary only crop rotation from public demand."""
    return decide_demand(
        observation,
        use_crop_demand=True,
        use_animal_demand=False,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run demand-selected crop rotation."""
    return decide(observation)
