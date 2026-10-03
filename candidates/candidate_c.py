"""Candidate C: public-state route portfolio over complete route experts.

Status: two validated routes. `elite_pasture` is the new default -- see
`docs/research/GOAL.md` section 9c for the full account. Four candidates were
rejected before it by direct measurement: two hand-built strategies
(`experimental_center_out_agent.py`; the best homegrown lineage,
`gated-late-strawberry`/`tiered-fertilizer`), and two real-replay clones
sourced from this project's own Kaggle match history
(`experimental_distilled_pasture_agent.py`, kept rejected). The pattern
that broke the streak: Kaggle's ladder pairs similarly-rated opponents, so
this project's own match history never contained a genuinely elite
replay to clone -- a real Kaggle API token unblocked pulling one directly
from the leaderboard instead of from this project's own games.

`elite_pasture` (`experimental_distilled_elite_pasture_agent.py`) clones
episode 105144807, player "fog flower" (public leaderboard score 2882.6),
who beat the leaderboard's #2 team (2965.4) in that game. Wrapped in the
same guard and market-timing layers as Candidate A/B
(`build_candidate_b_agent(baseline=build_candidate_a_agent(baseline=...))`),
it beat Candidate B 10-0 and Candidate A 4-0 across fresh seeds neither
was recorded on, both seats -- the first candidate tested this way to
win convincingly instead of losing decisively. `calendar` (Candidate B)
is kept as the second route, both as a documented fallback and because
nothing yet justifies discarding a submission with its own extensive
validation history.

This module still cannot legally choose between them: both are
step-indexed scripted replays with no live-opponent signal available at
episode start (see the non-reentrant rule below), so `_select_route_name`
remains a placeholder returning whichever route is listed first --
currently `elite_pasture`, because it is the better-measured of the two,
not because a real per-opponent selection rule exists yet. Hard
invariants, per `docs/research/GOAL.md` section 9 ("Selector"):

  - Only public/legal state is ever read by `_select_route_name` -- it
    receives nothing but the live `observation` dict, which never contains
    team name, rank, submission ID, replay ID, or seed (those live only in
    a replay file's `info` block, never in what an agent is called with).
    There is no field for those to leak in through even by accident.
  - A scripted, step-indexed route -- both routes here are, since each
    wraps a frozen 720-step replay with no awareness of a board state it
    did not itself create -- can only be entered at episode start. This
    module enforces that as a hard, checked, one-way transition
    (`RouteExpert.reentrant = False`), not just a convention a future edit
    could quietly break.
  - Hysteresis: once committed, a route is never reconsidered for the rest
    of the episode. This is the strictest possible reading of "latch with
    hysteresis; do not oscillate," and is the correct starting point before
    any evidence exists that switching mid-episode is safe for a given
    route pair -- switching a *reactive* route out mid-game may be safe
    (it just looks at the current board), but nothing here has been
    measured yet, so nothing here claims otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from agents.experimental_distilled_elite_pasture_agent import (
    agent as elite_pasture_route,
)
from candidates.candidate_a import build_candidate_a_agent
from candidates.candidate_b import agent as calendar_route, build_candidate_b_agent
from rl.runtime import AgentAction


RouteFn = Callable[[dict[str, Any]], AgentAction]
SelectRouteName = Callable[[dict[str, Any], "tuple[RouteExpert, ...]"], str]


@dataclass(frozen=True)
class RouteExpert:
    """One complete, standalone agent callable and its safety metadata."""

    name: str
    decide: RouteFn
    reentrant: bool


ELITE_PASTURE = RouteExpert(
    name="elite_pasture",
    decide=build_candidate_b_agent(
        baseline=build_candidate_a_agent(baseline=elite_pasture_route)
    ),
    reentrant=False,
)
CALENDAR = RouteExpert(name="calendar", decide=calendar_route, reentrant=False)
ROUTES: tuple[RouteExpert, ...] = (ELITE_PASTURE, CALENDAR)


def _select_route_name(
    observation: dict[str, Any],
    routes: tuple[RouteExpert, ...],
) -> str:
    """Pick a route name using only the live observation's public state.

    Placeholder: always the first configured route. There is currently
    only one validated route, so there is nothing to select between yet --
    this function exists so the selection *point* and its signature are
    fixed now, and a real rule can replace this body later without
    touching the executor.
    """
    del observation
    return routes[0].name


@dataclass
class CandidateCState:
    committed_route: str | None = None
    last_step: int = -1


class CandidateCExecutor:
    """Commits once, per episode, to exactly one complete route expert."""

    def __init__(
        self,
        routes: tuple[RouteExpert, ...] = ROUTES,
        *,
        select_route_name: SelectRouteName = _select_route_name,
    ) -> None:
        if not routes:
            raise ValueError("Candidate C needs at least one route")
        self._routes: dict[str, RouteExpert] = {
            route.name: route for route in routes
        }
        self._order = routes
        self._select = select_route_name
        self._states: dict[int, CandidateCState] = {}

    def _state(self, player: int, step: int) -> CandidateCState:
        state = self._states.setdefault(player, CandidateCState())
        if step == 0 or step <= state.last_step:
            state = CandidateCState()
            self._states[player] = state
        state.last_step = step
        return state

    def decide(self, observation: dict[str, Any]) -> AgentAction:
        player = int(observation["player"])
        step = int(observation.get("step", 0))
        state = self._state(player, step)
        if state.committed_route is None:
            name = self._select(observation, self._order)
            if name not in self._routes:
                raise ValueError(f"Unknown route selected: {name!r}")
            route = self._routes[name]
            if step > 0 and not route.reentrant:
                raise ValueError(
                    f"Route {name!r} is not reentrant and cannot be "
                    f"selected after episode start (step={step})"
                )
            state.committed_route = name
        return self._routes[state.committed_route].decide(observation)


def build_candidate_c_agent(
    routes: tuple[RouteExpert, ...] = ROUTES,
) -> RouteFn:
    """Create the Candidate C route-portfolio agent."""
    executor = CandidateCExecutor(routes=routes)

    def decide(observation: dict[str, Any]) -> AgentAction:
        return executor.decide(observation)

    return decide


agent = build_candidate_c_agent()
