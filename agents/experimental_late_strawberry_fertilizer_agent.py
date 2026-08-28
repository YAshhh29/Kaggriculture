"""Isolate late workload-aware strawberry fertilization."""

from __future__ import annotations

from typing import Any

from agents.experimental_late_value_fertilizer_agent import (
    decide_value_fertilizer,
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Run only the late strawberry fertilizer arm."""
    return decide_value_fertilizer(
        observation,
        economic_feed=False,
        enabled_crops=("STRAWBERRY",),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run isolated late strawberry fertilization."""
    return decide(observation)
