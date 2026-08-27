import unittest
from unittest.mock import patch

from policies.capacity_policy import ARM_STRAWBERRY, ARM_WHEAT_RESERVE3
from research.collection.collect_capacity_counterfactuals import _arm_decision, _utility
from test_experimental_scale_agent import scale_observation


class CapacityCounterfactualTests(unittest.TestCase):
    def test_all_arms_share_the_opening_before_day_four(self) -> None:
        state = scale_observation(day=3)

        with patch(
            "research.collection.collect_capacity_counterfactuals.decide_capacity_arm"
        ) as decide:
            _arm_decision(state, ARM_WHEAT_RESERVE3)

        self.assertEqual(decide.call_args.args[1], ARM_STRAWBERRY)

    def test_selected_arm_starts_on_day_four(self) -> None:
        state = scale_observation(day=4)

        with patch(
            "research.collection.collect_capacity_counterfactuals.decide_capacity_arm"
        ) as decide:
            _arm_decision(state, ARM_WHEAT_RESERVE3)

        self.assertEqual(decide.call_args.args[1], ARM_WHEAT_RESERVE3)

    def test_terminal_win_dominates_bounded_margin(self) -> None:
        self.assertGreater(_utility(1, 0), _utility(100_000, 100_001))


if __name__ == "__main__":
    unittest.main()
