"""Candidate C2: Candidate C's portfolio over a second recorded elite route.

It reuses `RouteExpert` and `build_candidate_c_agent` from
`candidates/candidate_c.py` unchanged; only the default route differs, a won
game recorded from a top-ranked team. Two different elite routes diverge in
most games, so comparing them on the ladder carries information that a
residual-flag variant would not. Measured before packaging it went 8-0 against
Candidate B and 2-6 against C1, so it ships as a comparison arm, not as an
improvement.
"""

from __future__ import annotations

from agents.experimental_distilled_elite_giulio_agent import (
    agent as giulio_route,
)
from candidates.candidate_a import build_candidate_a_agent
from candidates.candidate_b import agent as calendar_route, build_candidate_b_agent
from candidates.candidate_c import RouteExpert, RouteFn, build_candidate_c_agent


ELITE_GIULIO = RouteExpert(
    name="elite_giulio",
    decide=build_candidate_b_agent(
        baseline=build_candidate_a_agent(baseline=giulio_route)
    ),
    reentrant=False,
)
CALENDAR = RouteExpert(name="calendar", decide=calendar_route, reentrant=False)
ROUTES: tuple[RouteExpert, ...] = (ELITE_GIULIO, CALENDAR)


def build_candidate_c2_agent(
    routes: tuple[RouteExpert, ...] = ROUTES,
) -> RouteFn:
    """Create the Candidate C2 route-portfolio agent."""
    return build_candidate_c_agent(routes=routes)


agent = build_candidate_c2_agent()
