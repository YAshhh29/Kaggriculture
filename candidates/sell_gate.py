"""Hold back glut-sensitive sales while the shared market is saturated.

The measured basis (docs/research/GOAL.md sections 9r and 9s):

* Winners and losers sell the *same* volume; winners are simply paid more
  per unit, concentrated in milk (p=0.0005 over 90 paired games).
* The mechanism is market saturation at the moment of sale, not timing:
  winners sell milk at inventory 10,047.6 against losers' 10,050.2
  (p=0.0004), and milk moves 2.098 coins per unit of deviation, so that
  2.6-unit gap is worth ~5.5 coins/unit against an observed 5.8.
* Across rank bands the same skill is the largest single behavioural gap:
  teams at 2850+ realise 73.1 per wool unit against 26.5 for the
  2300-2600 band, and 53.5 against 41.9 for milk, selling at wool
  inventory 10,041.5 against 10,053.9 -- for the same volume sold.

Only WOOL and MILK are gated. Those are the two products whose glut
response is steep enough for a few units of inventory to matter: wool is
quadratic (`above_func "sq"`, target 3.20) and milk linear with a large
coefficient (target 1.60, T 122). Strawberry and melon showed no
significant effect and are left alone.

**Why the first attempt at this failed.** An earlier version (section 9j)
used a glut threshold of 10,500. Real inventory only moves in a band of
roughly 10,040-10,060, so the rule never once fired across 80 games. A
second version gated on *price* with a hard floor and cost 12-16k coins,
because withholding sales starved the two things the sales were really
funding: clearing the 100-unit shed so harvests can be deposited, and
buying the wheat that feeds the animals. Both failures are guarded here --
the thresholds are calibrated to the measured band, and cash, shed and
terminal guards always override the gate.
"""

from __future__ import annotations

from typing import Any

from rl.runtime import AgentAction, Baseline, clone_action


# Products whose price is steep enough in glut for this to pay.
GATED: dict[str, float] = {
    "WOOL": 10_046.0,
    "MILK": 10_052.0,
}
SHED_CAPACITY = 100
SHED_HEADROOM = 25
CASH_FLOOR = 3_000.0
TERMINAL_STEP = 690
MAX_HOLD_STEPS = 48


def _market(observation: dict[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    market = observation.get("market") or {}
    inventory = {
        str(k): float(v) for k, v in (market.get("inventory") or {}).items()
    }
    prices = {str(k): float(v) for k, v in (market.get("prices") or {}).items()}
    return inventory, prices


def _shed_total(observation: dict[str, Any]) -> int:
    private = observation.get("private") or {}
    shed = private.get("shed") or {}
    return sum(int(v) for v in shed.values())


def _money(observation: dict[str, Any]) -> float:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    if player >= len(farms) or not isinstance(farms[player], dict):
        return 0.0
    return float(farms[player].get("money", 0.0))


class SellGateState:
    """Per-episode memory of how long each product has been held back."""

    def __init__(self) -> None:
        self.last_step = -1
        self.held_since: dict[str, int] = {}

    def reset_if_new_episode(self, step: int) -> None:
        if step == 0 or step <= self.last_step:
            self.held_since.clear()
        self.last_step = step


def gate_orders(
    observation: dict[str, Any],
    action: AgentAction,
    state: SellGateState,
    thresholds: dict[str, float] | None = None,
) -> AgentAction:
    """Drop SELL orders for gated products while the market is saturated."""
    thresholds = GATED if thresholds is None else thresholds
    step = int(observation.get("step", 0))
    state.reset_if_new_episode(step)
    orders = action["market"]
    if not orders:
        return action

    # Guards that always win: never strand goods, never starve logistics.
    if step >= TERMINAL_STEP:
        state.held_since.clear()
        return action
    if _money(observation) < CASH_FLOOR:
        return action
    if _shed_total(observation) > SHED_CAPACITY - SHED_HEADROOM:
        return action

    inventory, _prices = _market(observation)
    kept: list[list[Any]] = []
    for order in orders:
        if not (len(order) >= 3 and order[0] == "SELL"):
            kept.append(order)
            continue
        item = str(order[1])
        limit = thresholds.get(item)
        if limit is None or item not in inventory:
            kept.append(order)
            continue
        if inventory[item] <= limit:
            state.held_since.pop(item, None)
            kept.append(order)
            continue
        since = state.held_since.setdefault(item, step)
        if step - since >= MAX_HOLD_STEPS:
            # Patience exhausted -- take the price rather than strand it.
            state.held_since.pop(item, None)
            kept.append(order)
            continue
        # Held: the order is dropped and the goods stay in the shed.
    if len(kept) == len(orders):
        return action
    return {**action, "market": kept}


def build_sell_gated_agent(
    baseline: Baseline,
    *,
    thresholds: dict[str, float] | None = None,
) -> Baseline:
    state = SellGateState()

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        return gate_orders(observation, action, state, thresholds)

    return decide
