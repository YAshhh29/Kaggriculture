"""Isolate late workload-aware melon fertilization."""

from __future__ import annotations

from typing import Any

from agents.experimental_late_value_fertilizer_agent import (
    decide_value_fertilizer,
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Run only the late melon fertilizer arm."""
    return decide_value_fertilizer(
        observation,
        economic_feed=False,
        enabled_crops=("MELON",),
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run isolated late melon fertilization."""
    return decide(observation)
