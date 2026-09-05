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
with this exact guard stack on our own final reward. The leaders were then
re-screened against *real top-500 opponents*, because that first screen
used three seeds against a single mid-field clone and is far too noisy to
pick a route on (section 9p).

Episode 105520725 (Andrey Tikhomirov, LB 2920.0, rank 4) led all three
independent evaluations:

    evaluation                              Andrey   Giulio 105531280      C1
    191-tape search (mean coins)           113,550            110,077   102,072
    60-game stratified top-500 panel          70.0%              61.7%     48.3%
    184-game full top-500 panel               64.1%              58.7%     56.0%

**This is a best-estimate choice, not a proven one.** On the 184-game
panel no pair reaches p < 0.05 (Andrey vs Giulio p = 0.19, Andrey vs C1
p = 0.079). What supports it is consistency across three evaluations
rather than any single significant result, plus the band that matters at
our current rating: Andrey wins **+16 games against ranks 51-500**, the
range actually faced around rank 677, while giving back 6 against the top
50, where the Giulio tape is stronger (50/74 against 44/74).

Tape quality belongs to the individual *game*, not the player: two Andrey
tapes recorded the same day score 70.0% and 40.0% on the same panel, and
three tapes from different teams (Jesse Bullard, Bohannn Wang x2) score
byte-identically, which is what a widely-copied public agent looks like
from the outside.

The wrapping is deliberately identical to Candidate C's, so the comparison
isolates the route: Candidate A's guarded recovery and live terminal
liquidation, then Candidate B's market-timing residuals with land priority
off by default.
"""

from __future__ import annotations

from typing import Any

from agents.experimental_distilled_elite_andrey_agent import (
    agent as elite_andrey_route,
)
from rl.candidate_a import build_candidate_a_agent
from rl.candidate_b import build_candidate_b_agent
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
