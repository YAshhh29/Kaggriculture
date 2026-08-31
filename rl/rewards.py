"""Win-first reward contracts for Kaggriculture learning experiments."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, tanh


@dataclass(frozen=True)
class RewardBreakdown:
    outcome: float
    margin_bonus: float
    total: float


def win_first_reward(
    own_coins: float,
    opponent_coins: float,
    *,
    margin_scale: float = 100_000.0,
    margin_weight: float = 0.05,
) -> RewardBreakdown:
    """Prioritize match outcome while retaining a bounded margin signal."""
    values = (own_coins, opponent_coins, margin_scale, margin_weight)
    if not all(isfinite(float(value)) for value in values):
        raise ValueError("Reward inputs must be finite")
    if margin_scale <= 0:
        raise ValueError("margin_scale must be positive")
    if not 0 <= margin_weight < 1:
        raise ValueError("margin_weight must be in [0, 1)")
    margin = float(own_coins) - float(opponent_coins)
    outcome = 1.0 if margin > 0 else -1.0 if margin < 0 else 0.0
    margin_bonus = margin_weight * tanh(margin / margin_scale)
    return RewardBreakdown(
        outcome=outcome,
        margin_bonus=margin_bonus,
        total=outcome + margin_bonus,
    )