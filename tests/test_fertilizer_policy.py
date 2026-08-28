import unittest

from policies.fertilizer_policy import (
    fertilizer_service_supported,
    selection_point_reached,
)
from tests.test_experimental_scale_agent import scale_observation


def supported_features() -> dict[str, float]:
    return {
        "own_due_melons": 2.0,
        "own_due_strawberries": 3.0,
        "own_unfertilized_due_melons": 2.0,
        "own_unfertilized_due_strawberries": 3.0,
        "own_unfertilized_due_premium": 3.0,
        "own_fertilizer_carriers": 2.0,
        "own_min_carrier_distance_to_due_melons": 2.0,
        "own_min_carrier_distance_to_due_strawberries": 2.0,
        "own_min_carrier_distance_to_due_premium": 2.0,
        "own_pending_animal_service_per_worker": 1.5,
        "own_hands": 12.0,
        "own_harvestable_crop_units": 20.0,
    }


class FertilizerPolicyTests(unittest.TestCase):
    def test_melon_and_strawberry_have_separate_late_points(self) -> None:
        self.assertTrue(
            selection_point_reached(
                scale_observation(day=10, hour=12),
                "MELON",
            )
        )
        self.assertFalse(
            selection_point_reached(
                scale_observation(day=10, hour=12),
                "STRAWBERRY",
            )
        )

    def test_requires_nearby_carrier_and_spare_animal_capacity(self) -> None:
        features = supported_features()
        self.assertTrue(fertilizer_service_supported(features, "MELON"))

        features["own_min_carrier_distance_to_due_melons"] = 4.0
        self.assertFalse(fertilizer_service_supported(features, "MELON"))
        features["own_min_carrier_distance_to_due_melons"] = 2.0
        features["own_pending_animal_service_per_worker"] = 2.0
        self.assertFalse(fertilizer_service_supported(features, "MELON"))

    def test_strawberry_rejects_large_harvest_backlog(self) -> None:
        features = supported_features()
        self.assertTrue(
            fertilizer_service_supported(features, "STRAWBERRY")
        )

        features["own_harvestable_crop_units"] = 24.0
        self.assertFalse(
            fertilizer_service_supported(features, "STRAWBERRY")
        )

    def test_strawberry_does_not_borrow_melon_service_evidence(self) -> None:
        features = supported_features()
        features["own_unfertilized_due_strawberries"] = 0.0
        features["own_min_carrier_distance_to_due_strawberries"] = 8.0
        features["own_unfertilized_due_melons"] = 2.0
        features["own_min_carrier_distance_to_due_melons"] = 1.0

        self.assertFalse(
            fertilizer_service_supported(features, "STRAWBERRY")
        )


if __name__ == "__main__":
    unittest.main()
