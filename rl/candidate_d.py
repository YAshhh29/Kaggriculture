"""Candidate D: the searched-best elite route under the proven guard stack.

Candidate D is not a new mechanism. Sections 9j and 9k spent a long time
looking for one -- glut-aware sell deferral, a price-floor throttle, eager
selling, a C1/C2 route selector, and twelve alternative tapes -- and every
one of them measured neutral or negative. Section 9m then found why the
search kept failing: the tape panel those experiments were scored on
overstates live strength by roughly forty points, because a frozen replay
is far weaker than the agent it was recorded from.

So Candidate D changes the one thing that measurement showed still moves:
the quality of the physical route, chosen by search rather than by
assuming a high leaderboard rank implies a good tape (section 9k measured
that it does not -- the world #1's tape wins 6 of 24).

**Selection.** 191 candidate tapes -- every side of every cached replay
whose team is rated 2400+, taken from a game that team won -- were scored
with this exact guard stack on our own final reward across fixed seeds.
The five best then ran 48 games each across six seeds, both seats and four
opponents (two mid-field clones, two elite tapes). Episode 105531280
(Giulio Ravasio, LB 2908.0) won on all three metrics at once:

    candidate                     wins    mean coins   floor
    Giulio ep105531280           38/48       108,472   51,094
    Mater Welon ep105545969      28/48       112,794   53,645
    peikopon ep105552428         32/48       107,097   49,999
    Candidate C1 (fog flower)    32/48        97,043   47,364
    Andrew Reed ep105554550      36/48        87,440   43,542

It is also balanced -- 6/12, 12/12, 8/12, 12/12 across the four opponents,
with no collapse against any one of them, and it is strongest exactly
where C1 is weakest (8/12 against the Jesse Bullard tape, against C1's
4/12). Mater Welon's tape earns more coins but loses 0/12 to one opponent,
which is the failure mode a single frozen route can least afford.

Note this is a *different game* from the one Candidate C2 clones. C2 uses
Giulio's episode 105144807; this is 105531280, captured a day later, and
the two are not interchangeable -- the search scored many Giulio games and
only this one came out on top.

The wrapping is deliberately identical to Candidate C's, so the comparison
isolates the route: Candidate A's guarded recovery and live terminal
liquidation, then Candidate B's market-timing residuals with land priority
off by default.
"""

from __future__ import annotations

from typing import Any

from agents.experimental_distilled_elite_giulio2_agent import (
    agent as elite_giulio2_route,
)
from rl.candidate_a import build_candidate_a_agent
from rl.candidate_b import build_candidate_b_agent
from rl.runtime import AgentAction, Baseline


def build_candidate_d_agent(
    baseline: Baseline = elite_giulio2_route,
) -> Baseline:
    """Wrap a route in Candidate A's guards and Candidate B's residuals."""
    return build_candidate_b_agent(
        baseline=build_candidate_a_agent(baseline=baseline)
    )


_DECIDE = build_candidate_d_agent()


def decide(observation: dict[str, Any]) -> AgentAction:
    return _DECIDE(observation)


agent = build_candidate_d_agent()
