"""Candidate D: the best elite route found by search, under A and B's guards.

D adds no new mechanism; the residuals tried before it all measured neutral or
negative, so it changes only the recorded route. 191 tapes from games won by
teams rated 2400+ were scored under this exact wrapper, and the leaders were
re-screened against real top-500 opponents; the chosen route won 64.1% of a
184-game top-500 panel. It is a best estimate, consistent across three
evaluations, not a significant result (no pair reaches p < 0.05).

The wrapping matches Candidate C's: Candidate A's guarded recovery and terminal
liquidation, then Candidate B's market-timing residuals with land priority off.
"""

from __future__ import annotations

from typing import Any

from agents.experimental_distilled_elite_andrey_agent import (
    agent as elite_andrey_route,
)
from candidates.candidate_a import build_candidate_a_agent
from candidates.candidate_b import build_candidate_b_agent
from rl.runtime import AgentAction, Baseline


def build_candidate_d_agent(
    baseline: Baseline = elite_andrey_route,
) -> Baseline:
    """Wrap a route in Candidate A's guards and Candidate B's residuals."""
    return build_candidate_b_agent(
        baseline=build_candidate_a_agent(baseline=baseline)
    )


_DECIDE = build_candidate_d_agent()


def decide(observation: dict[str, Any]) -> AgentAction:
    return _DECIDE(observation)


agent = build_candidate_d_agent()
