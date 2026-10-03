"""Play an opening route until a switch day, then hand control to a closed-loop policy.

A recorded route assumes the farm its own earlier actions built, so it
cannot take over a farm built by something else; a policy that reads the
live board can. The handover therefore only runs route to policy, never the
reverse.

`switch_day` (default 15) is a measured parameter: too early wastes the
route's opening, too late leaves the policy too little of the season.
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
