from __future__ import annotations

from typing import Any

from agents.experimental_distilled_elite_try_agent import (
    agent as elite_try_route,
)
from rl.candidate_a import build_candidate_a_agent
from rl.candidate_b import build_candidate_b_agent
from rl.demand_sales import paced_orders
from rl.idle_rescue import build_idle_rescue_agent
from rl.runtime import AgentAction, Baseline, clone_action


# 0.0 disables pacing entirely; see the module docstring.
SELL_PACE = 0.0
IDLE_RESCUE = False
RESCUE_OPS = (
    "COLLECT_FERTILIZER", "HARVEST", "CARE", "FEED", "WATER", "DIG",
)
CASH_FLOOR = 15000.0
SHED_PRESSURE = 80
CLOSING_DAY = 29


def build_candidate_f_agent(
    baseline: Baseline = elite_try_route,
    *,
    pace: float = SELL_PACE,
    cash_floor: float = CASH_FLOOR,
    shed_pressure: int = SHED_PRESSURE,
    closing_day: int = CLOSING_DAY,
) -> Baseline:
    """The live-ladder route under A+B guards, with optional pacing."""
    inner = build_candidate_b_agent(
        baseline=build_candidate_a_agent(baseline=baseline)
    )
    if IDLE_RESCUE:
        # raw route to decide when the farm has drifted far enough to need
        # recovery; feeding it a already-repaired action changes what it
        # sees and it stops placing animals. Wrapping the finished action
        # instead leaves every guard reading exactly what it expects.
        inner = build_idle_rescue_agent(inner, frozenset(RESCUE_OPS))
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
