import unittest
from unittest.mock import patch

from research.collection.collect_service_counterfactuals import _arm_decision, _utility
from policies.service_policy import ARM_BASELINE, ARM_PAIRED
from tests.test_experimental_scale_agent import scale_observation


class ServiceCounterfactualTests(unittest.TestCase):
    def test_arms_share_day_zero_opening(self) -> None:
        with patch(
            "research.collection.collect_service_counterfactuals.decide_service_arm"
        ) as decide:
            _arm_decision(scale_observation(day=0), ARM_PAIRED)

        self.assertEqual(decide.call_args.args[1], ARM_BASELINE)

    def test_paired_arm_starts_after_shop_unlocks(self) -> None:
        with patch(
            "research.collection.collect_service_counterfactuals.decide_service_arm"
        ) as decide:
            _arm_decision(scale_observation(day=1), ARM_PAIRED)

        self.assertEqual(decide.call_args.args[1], ARM_PAIRED)

    def test_terminal_win_dominates_bounded_margin(self) -> None:
        self.assertGreater(
            _utility({"result": "win", "terminal_margin": 1}),
            _utility({"result": "loss", "terminal_margin": 100_000}),
        )


if __name__ == "__main__":
    unittest.main()
