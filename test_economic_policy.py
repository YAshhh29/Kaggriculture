import unittest
from unittest.mock import patch

from policies.economic_policy import (
    ARM_MELON_BALANCED,
    ARM_WHEAT_BALANCED,
    ARM_WHEAT_COW_HEAVY,
    decide_economic_arm,
)
from agents.experimental_center_out_agent import ANIMAL_PLANS
from agents.experimental_cow_heavy_deadline_agent import COW_HEAVY_ANIMAL_PLANS
from test_experimental_scale_agent import scale_observation


class EconomicPolicyTests(unittest.TestCase):
    def test_balanced_arm_uses_standard_animal_plan(self) -> None:
        with patch("policies.economic_policy.decide_premium") as premium:
            decide_economic_arm(
                scale_observation(day=4),
                ARM_WHEAT_BALANCED,
            )

        self.assertIs(
            premium.call_args.kwargs["animal_plans"],
            ANIMAL_PLANS,
        )

    def test_cow_heavy_arm_uses_the_cow_heavy_herd(self) -> None:
        with patch("policies.economic_policy.decide_premium") as premium:
            decide_economic_arm(
                scale_observation(day=4),
                ARM_WHEAT_COW_HEAVY,
            )

        self.assertIs(
            premium.call_args.kwargs["animal_plans"],
            COW_HEAVY_ANIMAL_PLANS,
        )

    def test_melon_arm_uses_the_day_eighteen_deadline(self) -> None:
        with patch("policies.economic_policy.decide_premium") as premium:
            decide_economic_arm(
                scale_observation(day=4),
                ARM_MELON_BALANCED,
            )

        self.assertEqual(premium.call_args.kwargs["rotation_crop"], "MELON")
        self.assertEqual(
            premium.call_args.kwargs["rotation_last_plant_day"],
            18,
        )


if __name__ == "__main__":
    unittest.main()
