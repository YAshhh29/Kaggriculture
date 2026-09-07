"""Candidate F: the route that wins most often, plus the demand engine.

F differs from Candidate D in exactly two ways, and the first one is the
larger.

**A different route, chosen on the right objective.** Kaggle's simulation
ladder rates on match *outcomes*: a game won by one coin counts exactly as
much as a game won by fifty thousand. Every route this project has
selected -- D's included -- was ranked on mean reward instead. Screened
under an identical guard stack against 80 real opponents from the cached
corpus, both seats, 160 games each:

    route                       mean coins   win rate
    D's (Andrey, ep105520725)      100,815        85%   (136/160)
    **F's (RB25det, ep105419382)**  92,459    **95%**   (152/160)

F gives up about 8,000 coins a game to win sixteen more games in a hundred
and sixty, which is the trade the ladder actually pays for. Section 10.8j
records the full screen, including the six routes that lost.

**A demand-paced market layer.** `rl.demand_sales` holds a sale back while
the town has not yet eaten the last one, because price is a function of a
shared market inventory and the town's consumption is the only thing
pushing it back up. Whether that pays depends on volume: it is worth about
a thousand coins to Agent E, which sells around a thousand units a game
and is inside the town's appetite, and it *cost* Candidate D three
thousand, because D sells 2,138 units against the roughly 3,800 the town
absorbs across both players. So the pace is a measured parameter here, not
an assumption -- see 10.8l for where it settled on this route.

Everything else is D's proven wrapping: Candidate A's guarded recovery and
terminal liquidation, then Candidate B's market-timing residuals.
"""

from __future__ import annotations

from typing import Any

from agents.experimental_distilled_elite_rb25det_agent import (
    agent as elite_rb25det_route,
)
from rl.candidate_a import build_candidate_a_agent
from rl.candidate_b import build_candidate_b_agent
from rl.demand_sales import paced_orders
from rl.runtime import AgentAction, Baseline, clone_action


# 0.0 disables pacing entirely; see the module docstring.
SELL_PACE = 0.0
CASH_FLOOR = 15000.0
SHED_PRESSURE = 80
CLOSING_DAY = 29


def build_candidate_f_agent(
    baseline: Baseline = elite_rb25det_route,
    *,
    pace: float = SELL_PACE,
    cash_floor: float = CASH_FLOOR,
    shed_pressure: int = SHED_PRESSURE,
    closing_day: int = CLOSING_DAY,
) -> Baseline:
    """The RB25det route under A+B guards, with optional demand pacing."""
    inner = build_candidate_b_agent(
        baseline=build_candidate_a_agent(baseline=baseline)
    )
    if pace <= 0.0:
        return inner

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(inner(observation))
        action["market"] = paced_orders(
            observation,
            list(action["market"]),
            pace=pace,
            cash_floor=cash_floor,
            shed_pressure=shed_pressure,
            closing_day=closing_day,
        )
        return action

    return decide


def _rebuild() -> None:
    """Rebuild after a constant is overridden, for tuning harnesses."""
    global agent, _DECIDE
    _DECIDE = build_candidate_f_agent(
        pace=SELL_PACE, cash_floor=CASH_FLOOR,
        shed_pressure=SHED_PRESSURE, closing_day=CLOSING_DAY,
    )
    agent = _DECIDE


_DECIDE = build_candidate_f_agent()


def decide(observation: dict[str, Any]) -> AgentAction:
    return _DECIDE(observation)


agent = build_candidate_f_agent()
