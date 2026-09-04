"""Candidate D: a narrow, price-aware sell-timing residual over Candidate C.

Mechanism, verified against the installed simulator source
(`kaggle_environments/envs/kaggriculture/kaggriculture.py`), not guessed:
the market is a single pool shared by both players (`observation["market"]`
is not per-player), priced by `price(inv) = base +/- amp * f(|inv - I0|)`
with `I0 = MARKET_I0 = 10000`. The `above` (glut) response shape is item-
specific, and two products -- MELON and WOOL -- use `above_func = "sq"`
with the highest `above_target` (3.60 / 3.20) of any product: selling into
an already-oversupplied market is quadratically punishing for exactly
these two goods, while every other product is linear, sqrt, or log (mild).

Candidate C's elite-clone baseline blindly replays one real player's exact
historical sell schedule, with no reaction to the live shared market -- it
cannot know whether the current opponent happens to be dumping the same
goods at the same time, which this shared-pool mechanic makes newly
punishing in a way the source player's own game never tested. This module
adds one narrow, conservative correction: when Candidate C's own market
batch proposes selling MELON or WOOL while the market is well above
equilibrium, hold that specific order back a few steps rather than sell
into the glut, and flush the exact same quantity once the market has
cooled, a hard step deadline is reached, or the terminal window is close.
It never invents, drops, or resizes an order -- only retimes one.

Evidence: rl/GOAL.md section 9j. Diagnostic basis: 80 real-opponent local
games (kaggle_cache/candidate_c1_stranded_inventory_probe.json) showed
Candidate C1 already strands negligible terminal inventory (median 0,
mean 0.2 units) -- ruling out a terminal-liquidation gap -- while its 4
losses in that sample were all close, non-anomalous games against
competent real opponents with MELON/WOOL among the heaviest sell volumes,
consistent with (not proof of) this specific mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rl.candidate_c import agent as candidate_c
from rl.runtime import AgentAction, Baseline, clone_action


MARKET_I0 = 10000
GLUT_SENSITIVE_ITEMS = ("MELON", "WOOL")
GLUT_THRESHOLD = 10500
MAX_DEFER_STEPS = 6
DEFERRAL_CUTOFF_STEP = 700
FLUSH_BY_STEP = 690
MAX_MARKET_ORDERS = 10


@dataclass
class GlutDeferralState:
    last_step: int = -1
    pending: dict[str, int] = field(default_factory=dict)
    deferred_since: dict[str, int] = field(default_factory=dict)


def _market_inventory(observation: dict[str, Any]) -> dict[str, int]:
    market = observation.get("market", {})
    inventory = market.get("inventory", {}) if isinstance(market, dict) else {}
    return {str(item): int(quantity) for item, quantity in inventory.items()}


def _should_flush(
    item: str,
    step: int,
    state: GlutDeferralState,
    inventory: dict[str, int],
) -> bool:
    if step >= FLUSH_BY_STEP:
        return True
    if step - state.deferred_since.get(item, step) >= MAX_DEFER_STEPS:
        return True
    return inventory.get(item, MARKET_I0) <= MARKET_I0


def _apply_glut_deferral(
    observation: dict[str, Any],
    action: AgentAction,
    state: GlutDeferralState,
) -> AgentAction:
    step = int(observation.get("step", 0))
    market_orders = action["market"]
    inventory = _market_inventory(observation)

    if step >= DEFERRAL_CUTOFF_STEP:
        # Too close to Candidate A's own terminal liquidation window
        # (TERMINAL_PLANNING_STEP=700 / TERMINAL_SELL_STEP=717 in
        # rl/candidate_a.py) to safely hold anything back further --
        # flush every pending unit into this turn's batch untouched and
        # stop deferring anything new.
        for item, quantity in state.pending.items():
            market_orders = _merge_sell(market_orders, item, quantity)
        state.pending.clear()
        state.deferred_since.clear()
        return {**action, "market": market_orders[:MAX_MARKET_ORDERS]}

    just_flushed: set[str] = set()
    for item in list(state.pending):
        if _should_flush(item, step, state, inventory):
            market_orders = _merge_sell(market_orders, item, state.pending[item])
            del state.pending[item]
            state.deferred_since.pop(item, None)
            just_flushed.add(item)

    if len(market_orders) < MAX_MARKET_ORDERS:
        kept: list[list[Any]] = []
        for order in market_orders:
            item = order[1] if len(order) > 1 else None
            quantity = order[2] if len(order) > 2 else 0
            if (
                order
                and order[0] == "SELL"
                and item in GLUT_SENSITIVE_ITEMS
                and item not in just_flushed
                and inventory.get(item, MARKET_I0) > GLUT_THRESHOLD
                and int(quantity) > 0
            ):
                state.pending[item] = state.pending.get(item, 0) + int(quantity)
                state.deferred_since.setdefault(item, step)
                continue
            kept.append(order)
        market_orders = kept

    return {**action, "market": market_orders[:MAX_MARKET_ORDERS]}


def _merge_sell(
    market_orders: list[list[Any]],
    item: str,
    quantity: int,
) -> list[list[Any]]:
    if quantity <= 0:
        return market_orders
    for order in market_orders:
        if order and order[0] == "SELL" and len(order) > 1 and order[1] == item:
            order[2] = int(order[2]) + quantity
            return market_orders
    return [*market_orders, ["SELL", item, quantity]]


class CandidateDExecutor:
    """Defers glut-sensitive sells over any baseline route."""

    def __init__(self, baseline: Baseline) -> None:
        self._baseline = baseline
        self._states: dict[int, GlutDeferralState] = {}

    def _state(self, player: int, step: int) -> GlutDeferralState:
        state = self._states.setdefault(player, GlutDeferralState())
        if step == 0 or step <= state.last_step:
            state = GlutDeferralState()
            self._states[player] = state
        state.last_step = step
        return state

    def decide(self, observation: dict[str, Any]) -> AgentAction:
        action = clone_action(self._baseline(observation))
        player = int(observation.get("player", 0))
        step = int(observation.get("step", 0))
        state = self._state(player, step)
        return _apply_glut_deferral(observation, action, state)


def build_candidate_d_agent(baseline: Baseline = candidate_c) -> Baseline:
    executor = CandidateDExecutor(baseline)

    def decide(observation: dict[str, Any]) -> AgentAction:
        return executor.decide(observation)

    return decide


agent = build_candidate_d_agent()
