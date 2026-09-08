"""Open with the route, finish with the economics.

Two facts measured today point at the same architecture.

**Candidate F wins early and caps late.** Its mean coin lead over the
opponent runs -501 at day 10, +7,019 at day 15, +13,215 at day 20 -- and
in the games it loses it finishes with fertilizer at +493, which is
exactly where that good reaches the price floor (10.8y, 10.8v). Its
revenue is one saturated commodity and it has no second act, so an
opponent that keeps building past that point wins: F takes the game when
the rival ends on 11.6 animals and loses when it ends on 15.4, with its
own herd fixed at 14.0 either way because a recording cannot respond.

**Agent E is the reverse.** It realises 102 coins a unit against F's 66 on
the same volume and prices every decision from live state (10.8ad), but
its opening is weak: four cows on day 10 where a competitive route has
six, and eighteen variants have failed to improve it.

The switch is only safe in one direction, and that is what makes this
buildable at all. A recording's action at turn t assumes the farm its own
past actions built, so handing a tape a farm it did not build lands its
plan on the wrong ground -- `rl/route_portfolio.py` measured that at 0/16.
A closed-loop agent has no such assumption: it reads the farm in front of
it and prices what it finds. **Route to policy is safe; policy to route is
not.** So the route opens and the policy finishes, never the other way
round.

`switch_day` is a measured parameter rather than a derived one. Too early
and the route's opening advantage is thrown away; too late and there is
not enough season left for the economics to matter.
"""

from __future__ import annotations

from typing import Any

from rl.runtime import AgentAction, Baseline

TURNS_PER_DAY = 24


def build_handover_agent(
    opening: Baseline,
    endgame: Baseline,
    *,
    switch_day: int = 15,
) -> Baseline:
    """Follow `opening` until `switch_day`, then `endgame` for the rest.

    Both are called every turn regardless of which one is driving. That is
    deliberate: an agent that keeps internal state across turns would
    otherwise wake up mid-game with no idea what has happened, and the
    cost of one extra evaluation per turn is nothing next to the risk of
    handing over to an agent that has not been watching.
    """

    def decide(observation: dict[str, Any]) -> AgentAction:
        day = int(observation.get("day", int(observation.get("step", 0))
                                  // TURNS_PER_DAY))
        early = opening(observation)
        late = endgame(observation)
        return early if day < switch_day else late

    return decide
