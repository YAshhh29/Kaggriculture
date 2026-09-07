"""Candidate F: a proven route, sold into the town's actual appetite.

F is deliberately the opposite of Agent E. E generates every action from
scratch; F takes the strongest physical route this project has measured --
Candidate D's, episode 105520725 under Candidate A's guards and B's
residuals -- and changes exactly one thing about it: **when it sells**.

The route is left alone because sections 9j, 9k, 10.8c and 10.8g all
measured the same thing from different directions: a recorded route's
farming cannot be improved by editing it. Swapping its herd gains 133
coins over 48 games, forcing a pure herd costs 16,000 to 25,000, and its
opening cannot be transplanted anywhere else. What that work never tested
is the part of a tape that is *not* coupled to its geometry.

Selling is that part. A tape's sell orders were recorded against a market
its own opponent shaped, and it dumps everything the moment it reaches the
shed -- 389 wool at 34 coins a unit, 347 milk at 92, 455 fertilizer at 36.
The market is a single shared pool whose price is a function of inventory,
and the only thing pushing that inventory back down is the town eating a
fixed number of units every four steps. Selling faster than the town
absorbs is a farm competing with its own earlier sales.

So F keeps every worker action, every purchase and every placement of the
route, and paces only the sales against `rl.demand`. Nothing about the
farm changes; only the price it gets for what the farm already grew.
"""

from __future__ import annotations

from typing import Any

from agents.experimental_distilled_elite_andrey_agent import (
    agent as elite_andrey_route,
)
from rl.candidate_a import build_candidate_a_agent
from rl.candidate_b import build_candidate_b_agent
from rl.demand_sales import paced_orders
from rl.runtime import AgentAction, Baseline, clone_action


SELL_PACE = 24.0
CASH_FLOOR = 15000.0
SHED_PRESSURE = 80
CLOSING_DAY = 29


def build_candidate_f_agent(
    baseline: Baseline = elite_andrey_route,
    *,
    pace: float = SELL_PACE,
    cash_floor: float = CASH_FLOOR,
    shed_pressure: int = SHED_PRESSURE,
    closing_day: int = CLOSING_DAY,
) -> Baseline:
    """Candidate D's stack, with sales paced against the town's demand."""
    inner = build_candidate_b_agent(
        baseline=build_candidate_a_agent(baseline=baseline)
    )

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


_DECIDE = build_candidate_f_agent()


def decide(observation: dict[str, Any]) -> AgentAction:
    return _DECIDE(observation)


def _rebuild() -> None:
    """Rebuild the module agent after a constant is overridden (tuning)."""
    global agent, _DECIDE
    _DECIDE = build_candidate_f_agent(
        pace=SELL_PACE, cash_floor=CASH_FLOOR,
        shed_pressure=SHED_PRESSURE, closing_day=CLOSING_DAY,
    )
    agent = _DECIDE


agent = build_candidate_f_agent()
