"""Candidate C2: the same portfolio machinery over a second elite baseline.

Identical in structure to `rl/candidate_c.py` -- same executor, same
one-commitment-per-episode hysteresis, same non-reentrant rule -- and it
reuses that module's `RouteExpert`/`build_candidate_c_agent` directly
rather than forking them, so there is exactly one implementation of the
selector state machine to reason about.

The only difference is the baseline: this variant clones "Giulio Ravasio"
(public leaderboard rank #2, 2965.4) instead of "fog flower" (2882.6).
That difference is deliberate. Two Candidate C variants differing only in
a residual flag would differ by roughly one decision per game, which is far
below the +/-35 point leaderboard noise measured on byte-identical uploads
in section 9c -- comparing them would burn a submission slot and settle
nothing. Two different elite strategies actually diverge (they disagree in
6 of 8 head-to-head games), so the live comparison can carry information.

Measured before packaging, wrapped in the same Candidate A guard and
Candidate B market-timing stack as C1:

- vs Candidate B: 8-0 (seeds 970-973, both seats)
- vs Candidate C1 (fog flower): 2-6 on the same seeds

So C2 is strong in absolute terms and clearly weaker than C1 head-to-head.
It is shipped as a comparison arm, not as a claimed improvement -- if only
one C slot is available, section 9's evidence favours C1.
"""

from __future__ import annotations

from agents.experimental_distilled_elite_giulio_agent import (
    agent as giulio_route,
)
from rl.candidate_a import build_candidate_a_agent
from rl.candidate_b import agent as calendar_route, build_candidate_b_agent
from rl.candidate_c import RouteExpert, RouteFn, build_candidate_c_agent


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
