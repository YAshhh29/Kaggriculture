"""Late workload-aware premium fertilizer service over future labor."""

from __future__ import annotations

from typing import Any

from agents.experimental_demand_aware_agent import _choices, decide_demand
from agents.experimental_future_labor_agent import _selected_hand_targets
from agents.experimental_guarded_colocated_crop_service_agent import (
    _crop_service_selected,
)
from policies.fertilizer_policy import (
    SELECTION_POINTS,
    fertilizer_service_supported,
    selection_point_reached,
)
from policies.live_macro_features import extract_live_macro_features


MIN_FERTILIZER_NET_VALUE = 50.0
_FERTILIZER_CHOICES: dict[int, dict[str, bool]] = {}


def _selected_value_crops(
    observation: dict[str, Any],
) -> tuple[str, ...]:
    """Lock independent melon and strawberry decisions after setup."""
    player = int(observation["player"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day == 0 and hour == 0:
        _FERTILIZER_CHOICES.pop(player, None)
    choices = _FERTILIZER_CHOICES.setdefault(player, {})
    pending = [
        crop
        for crop in SELECTION_POINTS
        if crop not in choices
        and selection_point_reached(observation, crop)
    ]
    if pending:
        features = extract_live_macro_features(observation)
        for crop in pending:
            choices[crop] = fertilizer_service_supported(features, crop)
    return tuple(
        crop
        for crop in SELECTION_POINTS
        if choices.get(crop, False)
    )


def decide_value_fertilizer(
    observation: dict[str, Any],
    *,
    economic_feed: bool,
    enabled_crops: tuple[str, ...] = tuple(SELECTION_POINTS),
    application_limit: int | None = None,
    idle_enabled_crops: tuple[str, ...] = (),
    idle_maximum_distance: int = 2,
    late_strawberry_slots: int = 0,
) -> dict[str, Any]:
    """Execute late value service through the deterministic scheduler."""
    animal, crop = _choices(observation)
    paired = _crop_service_selected(observation)
    selected = _selected_value_crops(observation)
    value_crops = tuple(crop for crop in selected if crop in enabled_crops)
    idle_value_crops = tuple(
        crop for crop in selected if crop in idle_enabled_crops
    )
    return decide_demand(
        observation,
        use_crop_demand=False,
        use_animal_demand=True,
        hand_targets=_selected_hand_targets(observation, animal),
        pair_colocated_strawberry_service=paired,
        value_fertilization_crops=value_crops,
        minimum_fertilizer_net_value=MIN_FERTILIZER_NET_VALUE,
        economic_wheat_feed_reserve=economic_feed,
        value_fertilization_limit=application_limit,
        idle_value_fertilization_crops=idle_value_crops,
        idle_fertilization_max_distance=idle_maximum_distance,
        selective_late_rotation_crop=(
            "STRAWBERRY"
            if crop == "STRAWBERRY" and late_strawberry_slots > 0
            else None
        ),
        selective_late_rotation_slots=(
            late_strawberry_slots if crop == "STRAWBERRY" else 0
        ),
    )


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Run late value fertilizer service without changing feed reserves."""
    return decide_value_fertilizer(observation, economic_feed=False)


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the late value fertilizer research agent."""
    return decide(observation)
