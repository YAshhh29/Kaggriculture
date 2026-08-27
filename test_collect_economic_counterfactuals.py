import unittest
from unittest.mock import patch

from collect_economic_counterfactuals import _arm_decision
from policies.economic_policy import ARM_MELON_BALANCED, ARM_WHEAT_BALANCED
from test_experimental_scale_agent import scale_observation


class EconomicCounterfactualTests(unittest.TestCase):
    def test_all_arms_share_the_pre_day_four_opening(self) -> None:
        with patch(
            "collect_economic_counterfactuals.decide_economic_arm"
        ) as decide:
            _arm_decision(
                scale_observation(day=3),
                ARM_MELON_BALANCED,
            )

        self.assertEqual(decide.call_args.args[1], ARM_WHEAT_BALANCED)

    def test_selected_arm_starts_on_day_four(self) -> None:
        with patch(
            "collect_economic_counterfactuals.decide_economic_arm"
        ) as decide:
            _arm_decision(
                scale_observation(day=4),
                ARM_MELON_BALANCED,
            )

        self.assertEqual(decide.call_args.args[1], ARM_MELON_BALANCED)


if __name__ == "__main__":
    unittest.main()
