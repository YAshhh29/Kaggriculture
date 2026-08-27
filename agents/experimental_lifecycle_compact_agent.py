"""Compact lifecycle candidate matching the submitted NE labor footprint."""

from __future__ import annotations

from typing import Any

from agents.experimental_lifecycle_agent import _demand_capacity, decide


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run six animal workers, two crop pairs, and one floater."""
    return decide(
        observation,
        max_wheat_per_pair=_demand_capacity(observation),
        target_daily_hands=10,
        animal_crew_size=6,
    )