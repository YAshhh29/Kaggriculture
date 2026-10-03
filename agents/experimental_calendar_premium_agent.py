"""Candidate B research entrypoint: Candidate A plus premium order safety."""

from __future__ import annotations

from typing import Any

from candidates.candidate_b import agent as candidate_b


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    return candidate_b(observation)


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    return decide(observation)