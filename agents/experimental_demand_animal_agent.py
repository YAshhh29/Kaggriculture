"""Demand-selected expansion animals with frozen wheat rotation."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import decide_demand


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Vary only expansion animal species from public demand."""
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run demand-selected expansion animals."""
    return decide(observation)
