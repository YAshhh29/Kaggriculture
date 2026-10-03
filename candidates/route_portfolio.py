"""Play several recorded routes, re-choosing which one to follow every 72-turn block.

A route's action at turn t assumes the farm its own earlier actions built,
so switching mid-game only works between closely related routes (such as
several games of one submission) whose crews line up: `farm["hands"]` is
append-ordered and each hand instruction is addressed by position.
`roster_gap` scores how far a route's recorded crew, land and herd are from
the live farm.

Choosers: `fixed_route` (never switches; the control), `cycling_route`
(switches every block), `matching_route` (smallest `roster_gap`) and
`sticky` (wraps a chooser so it only switches past a margin).
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from rl.runtime import AgentAction

BLOCK_TURNS = 72
TOTAL_TURNS = 720
PASS: list[str] = ["PASS"]

Chooser = Callable[[int, dict[str, Any], int, Sequence["RouteStats"]], int]


class RouteStats:
    """What a tape had built by each turn, read off the tape alone.

    A recording carries no observations, so the only thing we can know
    about the farm a route expects is what its own orders bought. That is
    enough for the comparison that matters: crew size, land, and herd are
    exactly the quantities whose mismatch makes a switch land badly.
    """

    __slots__ = ("actions", "hands", "land", "animals", "money_spent")

    def __init__(self, actions: Sequence[dict[str, Any]]) -> None:
        self.actions = actions
        self.hands: list[int] = []
        self.land: list[int] = []
        self.animals: list[int] = []
        land = 0
        animals = 0
        for action in actions:
            if not isinstance(action, dict):
                self.hands.append(0)
                self.land.append(land)
                self.animals.append(animals)
                continue
            self.hands.append(len(action.get("hands") or []))
            for order in action.get("market") or []:
                if not isinstance(order, list) or not order:
                    continue
                if order[0] == "BUY_LAND":
                    land += 1
                elif order[0] == "BUY_ANIMAL" and len(order) > 2:
                    try:
                        animals += int(order[2])
                    except (TypeError, ValueError):
                        pass
            self.land.append(land)
            self.animals.append(animals)

    def at(self, turn: int) -> dict[str, Any]:
        index = min(max(turn, 0), len(self.actions) - 1)
        return self.actions[index]


def _farm(observation: dict[str, Any]) -> dict[str, Any]:
    seat = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    if seat < len(farms) and isinstance(farms[seat], dict):
        return farms[seat]
    return {}


def roster_gap(observation: dict[str, Any], stats: RouteStats,
               turn: int) -> float:
    """How badly this route's expectations miss the farm we actually have.

    Crew is weighted hardest because a crew mismatch misdirects *every*
    hand instruction in the block, not just one.
    """
    farm = _farm(observation)
    index = min(max(turn, 0), len(stats.hands) - 1)
    hands = len(farm.get("hands") or [])
    quadrants = len(farm.get("unlocked_quadrants") or [])
    herd = sum(
        1
        for row in (farm.get("tiles") or [])
        for tile in row
        if isinstance(tile, dict) and "animal" in tile
    )
    return (
        4.0 * abs(hands - stats.hands[index])
        + 2.0 * abs(max(0, quadrants - 1) - stats.land[index])
        + 0.5 * abs(herd - stats.animals[index])
    )


def fixed_route(block: int, observation: dict[str, Any], previous: int,
                stats: Sequence[RouteStats]) -> int:
    return previous if previous >= 0 else 0


def cycling_route(block: int, observation: dict[str, Any], previous: int,
                  stats: Sequence[RouteStats]) -> int:
    return block % len(stats)


def matching_route(block: int, observation: dict[str, Any], previous: int,
                   stats: Sequence[RouteStats]) -> int:
    turn = block * BLOCK_TURNS
    scored = [
        (roster_gap(observation, route, turn), index)
        for index, route in enumerate(stats)
    ]
    return min(scored)[1]


def sticky(chooser: Chooser, margin: float = 2.0) -> Chooser:
    """Abandon the running route only when a rival is clearly better.

    Without this a router flips on noise, and every flip pays the cost of
    landing a new plan on an unfamiliar farm.
    """

    def decide(block: int, observation: dict[str, Any], previous: int,
               stats: Sequence[RouteStats]) -> int:
        pick = chooser(block, observation, previous, stats)
        if previous < 0 or pick == previous:
            return pick
        turn = block * BLOCK_TURNS
        here = roster_gap(observation, stats[previous], turn)
        there = roster_gap(observation, stats[pick], turn)
        return pick if there + margin < here else previous

    return decide


def build_portfolio_agent(
    routes: Sequence[Sequence[dict[str, Any]]],
    *,
    chooser: Chooser = matching_route,
    block_turns: int = BLOCK_TURNS,
    start_route: int = 0,
):
    """Play one of `routes`, reconsidering every `block_turns` turns.

    State is kept per seat and reset when the step counter goes backwards,
    so one built agent can play several games in a process without
    carrying a stale route across the boundary.
    """
    stats = [RouteStats(route) for route in routes]
    sessions: dict[int, dict[str, int]] = {}

    def decide(observation: dict[str, Any]) -> AgentAction:
        turn = int(observation.get("step", 0))
        seat = int(observation.get("player", 0))
        state = sessions.get(seat)
        if state is None or turn < state["turn"]:
            state = {"turn": -1, "block": -1, "route": start_route}
            sessions[seat] = state
        block = turn // block_turns
        if block != state["block"]:
            state["route"] = chooser(block, observation, state["route"], stats)
            state["block"] = block
        state["turn"] = turn

        # Same off-by-one as rl/replay_agent: the action recorded at index
        # k was chosen while observing step k-1.
        planned = stats[state["route"]].at(turn + 1)
        if turn + 1 >= len(stats[state["route"]].actions):
            return {"farmer": PASS, "hands": [], "market": []}
        return {
            "farmer": list(planned.get("farmer", PASS)),
            "hands": [list(a) for a in planned.get("hands", [])],
            "market": [list(o) for o in planned.get("market", [])],
        }

    return decide
