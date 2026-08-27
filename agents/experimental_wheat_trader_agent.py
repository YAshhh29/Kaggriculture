"""Deadline capacity with bounded intertemporal wheat trading."""

from __future__ import annotations

from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_premium_throughput_agent import decide as decide_premium


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Hold up to 48 wheat below 40 and accumulate it at 34 or less."""
    return decide_premium(
        observation,
        target_extra_land=2,
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        wheat_trade_target=48,
        wheat_trade_buy_price=34,
        wheat_trade_sell_price=40,
        wheat_trade_cash_reserve=3000,
    )


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run bounded wheat trading over deadline capacity."""
    return decide(observation)
