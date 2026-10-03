"""Candidate C: a route portfolio that commits to one route per episode.

Each route is a recorded elite route wrapped in Candidate A's guards and
Candidate B's market-timing residuals. The default, `elite_pasture`, follows a
won game by a top-rated player and beat Candidate B 10-0 on seeds it was not
recorded on; `calendar` (Candidate B) is kept as the fallback.

`_select_route_name` reads only the public observation and is a placeholder
that returns the first listed route. Routes are step-indexed, so one can only
be entered at episode start (`RouteExpert.reentrant = False`), and a committed
route is never reconsidered.
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
