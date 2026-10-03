"""Candidate A: guarded recovery and liquidation over the elite calendar."""

from __future__ import annotations

from typing import Any

from agents.experimental_distilled_calendar_agent import decide as calendar
from candidates.candidate_a import build_candidate_a_agent


_DECIDE = build_candidate_a_agent(baseline=calendar)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    return _DECIDE(observation)


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Execute Candidate A's guarded calendar policy."""
    return decide(observation)
