"""Budgeted value fertilizer using only already-colocated idle carriers."""

from __future__ import annotations

from typing import Any

from agents.experimental_idle_value_fertilizer_agent import (
    decide as decide_idle,
)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Forbid fertilizer staging movement to preserve future routes."""
    return decide_idle(observation, maximum_distance=0)


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run colocated-only value fertilizer service."""
    return decide(observation)
