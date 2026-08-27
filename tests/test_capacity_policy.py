import unittest
from unittest.mock import patch

from policies.capacity_policy import (
    ARM_STRAWBERRY,
    ARM_WHEAT,
    ARM_WHEAT_RESERVE3,
    decide_capacity_arm,
)
from tests.test_experimental_scale_agent import scale_observation


class CapacityPolicyTests(unittest.TestCase):
    def test_wheat_arm_keeps_wheat_rotation_without_fertilizer(self) -> None:
        state = scale_observation(day=4)

        with patch("policies.capacity_policy.decide_premium") as premium:
            decide_capacity_arm(state, ARM_WHEAT)

        self.assertEqual(premium.call_args.kwargs["rotation_crop"], "WHEAT")
        self.assertFalse(
            premium.call_args.kwargs.get("fertilize_strawberries", False)
        )

    def test_reserve_three_arm_protects_an_extra_crop_worker(self) -> None:
        state = scale_observation(day=4)

        with patch("policies.capacity_policy.decide_premium") as premium:
            decide_capacity_arm(state, ARM_WHEAT_RESERVE3)

        self.assertEqual(premium.call_args.kwargs["crop_worker_reserve"], 3)

    def test_unknown_arm_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            decide_capacity_arm(scale_observation(), 99)

    def test_strawberry_arm_is_defined(self) -> None:
        self.assertEqual(ARM_STRAWBERRY, 0)


if __name__ == "__main__":
    unittest.main()
