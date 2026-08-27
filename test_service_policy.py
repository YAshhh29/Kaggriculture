import unittest
from unittest.mock import patch

from policies.service_policy import ARM_BASELINE, ARM_PAIRED, decide_service_arm
from test_experimental_scale_agent import scale_observation


class ServicePolicyTests(unittest.TestCase):
    def test_paired_arm_enables_only_pairing_axis(self) -> None:
        with patch("policies.service_policy.decide_premium") as premium:
            decide_service_arm(scale_observation(day=1), ARM_PAIRED)

        self.assertTrue(
            premium.call_args.kwargs["pair_colocated_feed_care"]
        )

    def test_baseline_arm_disables_pairing(self) -> None:
        with patch("policies.service_policy.decide_premium") as premium:
            decide_service_arm(scale_observation(day=1), ARM_BASELINE)

        self.assertFalse(
            premium.call_args.kwargs["pair_colocated_feed_care"]
        )


if __name__ == "__main__":
    unittest.main()
