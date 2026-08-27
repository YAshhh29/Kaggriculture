import unittest
from unittest.mock import patch

from policies.demand_animal_policy import (
    ARM_BALANCED,
    ARM_COW,
    ARM_GOOSE,
    decide_demand_animal_arm,
    extract_demand_animal_features,
)
from tests.test_experimental_scale_agent import scale_observation


class DemandAnimalPolicyTests(unittest.TestCase):
    def test_extracts_demand_specific_features_without_changing_macro_schema(self) -> None:
        state = scale_observation(day=6)
        state["town"]["unlocked_shops"] = ["BAKERY", "PET_CAFE"]

        features = extract_demand_animal_features(state)

        self.assertEqual(features["shops_egg"], 1.0)
        self.assertEqual(features["shops_carrot"], 1.0)
        self.assertIn("opportunity_cow", features)

    def test_each_arm_changes_only_two_expansion_slots(self) -> None:
        expected = {
            ARM_BALANCED: (0, 6, 6),
            ARM_COW: (0, 8, 4),
            ARM_GOOSE: (2, 6, 4),
        }
        for arm, counts in expected.items():
            with (
                self.subTest(arm=arm),
                patch(
                    "policies.demand_animal_policy._selected_arm",
                    return_value=ARM_BALANCED,
                ),
                patch(
                    "policies.demand_animal_policy.decide_premium"
                ) as premium,
            ):
                decide_demand_animal_arm(scale_observation(day=6), arm)
                plans = premium.call_args.kwargs["animal_plans"]
                actual = (
                    sum(plan["animal"] == "GOOSE" for plan in plans),
                    sum(plan["animal"] == "COW" for plan in plans),
                    sum(plan["animal"] == "SHEEP" for plan in plans),
                )
                self.assertEqual(actual, counts)


if __name__ == "__main__":
    unittest.main()
