"""Diagnostic Candidate B variant with land-priority disabled."""

from __future__ import annotations

from typing import Any

from candidates.candidate_b import build_candidate_b_agent


_DECIDE = build_candidate_b_agent(enable_land_priority=False)


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    return _DECIDE(observation)


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    return decide(observation)