"""Candidate F: a route taken from the live ladder, plus the demand engine.

**The route now comes from the current ladder, and that is the whole
change.** Until 2026-09-08, F ran RB25det from `kaggle_cache/`, captured
on 2026-09-04 and chosen by screening 245 routes against opponents drawn
from that same cache. Profiling the live corpus by what each agent *buys*
showed why that could not work: fourteen of the twenty-four teams we are
actually drawn against post an identical fingerprint -- 5 carrot seeds,
198 wheat, no geese -- which is the public getting-started notebook run
unmodified. RB25det's fingerprint is 6 carrot, 185 wheat, no geese. F was
a clone of the field it was trying to beat, and it landed at the field's
rating. None of the nine teams above 2765 runs that opening.

Screened under an identical guard stack against 32 live ladder opponents
the route was **not** selected against, both seats, 64 games:

    route                            mean coins   win rate   median margin
    D's (Andrey, ep105520725)            64,501     40.6%          -1,085
    RB25det (F until now)                67,514     37.5%          -3,786
    **Matthew Huang, ep106610780**       78,554   **92.2%**      **+18,030**

That is not a trade of coins against wins, which is what the previous
route change was. It is more of both.

**A demand-paced market layer.** `rl.demand_sales` holds a sale back while
the town has not yet eaten the last one, because price is a function of a
shared market inventory and the town's consumption is the only thing
pushing it back up. Whether that pays depends on volume: on a high-volume
clone it measured negative five separate times (10.8c, 10.8l), and it
costs Candidate D three thousand coins, because D sells 2,138 units
against the roughly 3,800 the town absorbs across both players. It stays
wired in and defaults to **off** for that reason.

The held-out screen above also settled what the layer is really worth:
Agent E, which sells around a thousand units a game and realises the best
price per unit of anything here, earns the most coins of any agent in this
project (89,278) and wins **zero** games out of sixty-four. The same
frozen opponent tapes score about 67,000 against D and about 141,000
against E. Selling less does not only forgo revenue; it leaves the shared
market intact for the opponent to sell into. Pacing is not a small
positive that got lost in the noise -- on this ladder it is the mechanism
by which an agent hands its opponent the game.

Everything else is D's proven wrapping: Candidate A's guarded recovery and
terminal liquidation, then Candidate B's market-timing residuals.
"""

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
        # Outside the guard stack, not inside it. Candidate A watches the
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
