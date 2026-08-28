"""Late workload gates for value-ranked premium-crop fertilization."""

from __future__ import annotations

from typing import Any


SELECTION_POINTS = {
    "MELON": (10, 12),
    "STRAWBERRY": (12, 12),
}
MAX_CARRIER_DISTANCE = 3.0
MAX_ANIMAL_SERVICE_PER_WORKER = 2.0
MIN_HANDS = 10.0
MAX_STRAWBERRY_HARVESTABLE_UNITS = 23.0


def fertilizer_service_supported(
    features: dict[str, float],
    crop: str,
) -> bool:
    """Admit premium service only with nearby stock and spare labor."""
    due_feature = {
        "MELON": "own_due_melons",
        "STRAWBERRY": "own_due_strawberries",
    }[crop]
    unfertilized_feature = {
        "MELON": "own_unfertilized_due_melons",
        "STRAWBERRY": "own_unfertilized_due_strawberries",
    }[crop]
    distance_feature = {
        "MELON": "own_min_carrier_distance_to_due_melons",
        "STRAWBERRY": "own_min_carrier_distance_to_due_strawberries",
    }[crop]
    return (
        features[due_feature] > 0
        and features[unfertilized_feature] > 0
        and features["own_fertilizer_carriers"] > 0
        and features[distance_feature] <= MAX_CARRIER_DISTANCE
        and features["own_pending_animal_service_per_worker"]
        < MAX_ANIMAL_SERVICE_PER_WORKER
        and features["own_hands"] >= MIN_HANDS
        and (
            crop != "STRAWBERRY"
            or features["own_harvestable_crop_units"]
            <= MAX_STRAWBERRY_HARVESTABLE_UNITS
        )
    )


def selection_point_reached(
    observation: dict[str, Any],
    crop: str,
) -> bool:
    """Return whether the crop's one-time decision point has arrived."""
    point = SELECTION_POINTS[crop]
    current = (
        int(observation.get("day", 0)),
        int(observation.get("hour", 0)),
    )
    return current >= point
