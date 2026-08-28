"""Late value fertilizer service with economic wheat feed retention."""

from __future__ import annotations

from typing import Any

from agents.experimental_late_value_fertilizer_agent import (
    decide_value_fertilizer,
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Run late value fertilization and value-gated wheat retention."""
    return decide_value_fertilizer(observation, economic_feed=True)


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the fertilizer-plus-economic-feed research agent."""
    return decide(observation)
