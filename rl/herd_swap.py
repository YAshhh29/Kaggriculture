"""Steer a frozen route's herd toward the product this town actually wants.

A tape cannot adapt: its purchases and placements were recorded in a game
whose shops were drawn differently from ours. Section 9v measured what
that costs -- adaptation to demand is the cleanest correlate of rank we
have (wool-demand-to-sheep +0.672 at 2850+, **+0.000 below 2400**), and a
frozen route scores structurally zero.

This layer buys the tape that ability with a surgical rewrite. COW and
SHEEP are interchangeable at the level of *actions*: both occupy a
PASTURE tile, both are placed with PLACE, both accept FEED and CARE, and
both are collected with HARVEST. Only the product and yield cadence
differ (milk every 2 days, wool every 3). So rewriting `BUY_ANIMAL COW`
to `BUY_ANIMAL SHEEP` -- and every matching `PLACE COW` to `PLACE SHEEP`
-- leaves the route's geometry, routing and service schedule completely
intact while changing what the farm produces.

The swap is deliberately conservative:

* it only ever swaps **between COW and SHEEP**, never touches geese,
  crops, seeds or land;
* it requires the preferred product to lead by a margin
  (`rl.demand.preferred_animal`), so a near-tie leaves the tape alone;
* it **latches** once placements begin, because a herd half-bought as
  cows and half as sheep would leave the tape's PLACE actions holding the
  wrong animal;
* it never rewrites a PLACE for an animal the farm actually holds, so it
  cannot strand a purchased animal in inventory.
"""

from __future__ import annotations

from typing import Any

from rl.demand import preferred_animal
from rl.runtime import AgentAction, Baseline, clone_action


SWAPPABLE = ("COW", "SHEEP")
DECISION_DEADLINE_STEP = 240  # ~day 10; after this the herd is committed
ANIMAL_COST = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
CASH_BUFFER = 1_200.0


class HerdSwapState:
    """Per-episode latch recording which animal this game settled on."""

    def __init__(self) -> None:
        self.last_step = -1
        self.target: str | None = None
        self.locked = False

    def reset_if_new_episode(self, step: int) -> None:
        if step == 0 or step <= self.last_step:
            self.target = None
            self.locked = False
        self.last_step = step


def _held_by(observation: dict[str, Any], worker: int, animal: str) -> int:
    """How many of `animal` this *specific* worker is carrying.

    Inventory is per worker, not shared. An earlier version summed across
    all workers and rewrote `PLACE COW` to `PLACE SHEEP` for a worker who
    was not the one holding the sheep; the placement then silently failed
    and the pasture stayed empty. That cost 7 of 17 animals and half the
    reward, so this must stay per-worker.
    """
    private = observation.get("private") or {}
    inventories = private.get("inventories") or []
    if worker >= len(inventories) or not isinstance(inventories[worker], dict):
        return 0
    return int(inventories[worker].get(animal, 0))


def apply_herd_swap(
    observation: dict[str, Any],
    action: AgentAction,
    state: HerdSwapState,
) -> AgentAction:
    step = int(observation.get("step", 0))
    state.reset_if_new_episode(step)

    if state.target is None and not state.locked:
        if step <= DECISION_DEADLINE_STEP:
            state.target = preferred_animal(observation, SWAPPABLE)
        else:
            state.locked = True
    target = state.target
    if target is None:
        return action

    other = "SHEEP" if target == "COW" else "COW"
    market = [list(o) for o in action["market"]]
    swapped_purchase = False

    # Cash coupling is what killed the first version: a tape's purchase
    # schedule is tuned to its own cash trajectory with no slack, so
    # substituting a dearer animal makes a later purchase fail outright and
    # strands the pasture empty for the rest of the game. Swapping toward
    # the cheaper animal frees cash and is always safe; swapping toward the
    # dearer one is only allowed with a real buffer behind it.
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    money = (
        float(farms[player].get("money", 0.0))
        if player < len(farms) and isinstance(farms[player], dict)
        else 0.0
    )
    for order in market:
        if not (
            len(order) >= 3
            and order[0] == "BUY_ANIMAL"
            and str(order[1]) == other
        ):
            continue
        quantity = int(order[2])
        extra = (ANIMAL_COST[target] - ANIMAL_COST[other]) * quantity
        if extra > 0 and money < ANIMAL_COST[target] * quantity + CASH_BUFFER:
            continue
        order[1] = target
        swapped_purchase = True

    # A bought animal lands in the SHED, not in a worker's hands, so the
    # tape's route is buy -> PICKUP -> PLACE. Rewriting only the purchase
    # leaves the PICKUP asking for an animal that is no longer there, the
    # worker arrives empty and the PLACE silently fails -- which cost 7 of
    # 17 pastures and half the reward before this was understood.
    shed = (observation.get("private") or {}).get("shed") or {}
    shed_other = int(shed.get(other, 0))
    shed_target = int(shed.get(target, 0))

    units = [action["farmer"], *action["hands"]]
    rewritten: list[list[Any]] = []
    for worker, unit_action in enumerate(units):
        act = list(unit_action)
        if len(act) >= 2 and str(act[1]) == other:
            if (
                act[0] == "PICKUP"
                and shed_other == 0
                and shed_target > 0
            ):
                act[1] = target
                state.locked = True
            elif (
                act[0] == "PLACE"
                and _held_by(observation, worker, other) == 0
                and _held_by(observation, worker, target) > 0
            ):
                # The tape wants the animal it recorded; place what we hold.
                act[1] = target
                state.locked = True
        rewritten.append(act)

    if swapped_purchase:
        state.locked = True

    return {
        "farmer": rewritten[0],
        "hands": rewritten[1:],
        "market": market,
    }


def build_herd_swap_agent(baseline: Baseline) -> Baseline:
    state = HerdSwapState()

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        return apply_herd_swap(observation, action, state)

    return decide
