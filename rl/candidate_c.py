"""Candidate C: public-state route portfolio over complete route experts.

Status: selector machinery only. Exactly one validated, competitive route
exists in this repository today -- Candidate A+B, the calendar-clone
family (`rl.candidate_b.agent`). Two independent hand-built alternatives
were tried and both lost decisively in direct local testing before any
selector work started:

  - `experimental_center_out_agent.py` (the one genuinely diversified
    5-crop layout in the whole `agents/experimental_*.py` catalog): 0-10,
    0-4, 0-4 against agents that are themselves weaker than Candidate B.
  - The most evolved homegrown lineage (`gated-late-strawberry`,
    `tiered-fertilizer`): 0-8 against Candidate B directly (seeds 500-501,
    both seats), by roughly 2x margin each time.

Per `rl/GOAL.md` section 3 ("If measurements disagree with these bands,
trust measurements and update the plan"), a second route for this module
should come from behavior-cloning a genuinely different real elite replay
-- the same method that built the current parent -- not another hand-built
heuristic; two independent hand-built attempts have now failed against
this specific opponent. `ROUTES` below contains only the safe fallback
until one is validated.

This module implements the selector state machine and its safety
invariants now, so a validated second route can be added later as data
(one `RouteExpert` entry) rather than a redesign. Hard invariants, per
`rl/GOAL.md` section 9 ("Selector"):

  - Only public/legal state is ever read by `_select_route_name` -- it
    receives nothing but the live `observation` dict, which never contains
    team name, rank, submission ID, replay ID, or seed (those live only in
    a replay file's `info` block, never in what an agent is called with).
    There is no field for those to leak in through even by accident.
  - A scripted, step-indexed route -- the calendar (`rl.candidate_b`,
    which wraps `rl.candidate_a`, which wraps the frozen 720-step replay)
    -- has no awareness of a board state it did not itself create, because
    its baseline looks up `CALENDAR_ACTIONS[step + 1]` and nothing else.
    It can only be entered at episode start. This module enforces that as
    a hard, checked, one-way transition (`RouteExpert.reentrant = False`),
    not just a convention a future edit could quietly break.
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

from rl.candidate_b import agent as calendar_route
from rl.runtime import AgentAction


RouteFn = Callable[[dict[str, Any]], AgentAction]
SelectRouteName = Callable[[dict[str, Any], "tuple[RouteExpert, ...]"], str]


@dataclass(frozen=True)
class RouteExpert:
    """One complete, standalone agent callable and its safety metadata."""

    name: str
    decide: RouteFn
    reentrant: bool


FALLBACK = RouteExpert(name="calendar", decide=calendar_route, reentrant=False)
ROUTES: tuple[RouteExpert, ...] = (FALLBACK,)


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
