import unittest
from unittest.mock import patch

from policies.demand_animal_policy import ARM_BALANCED, ARM_COW
from research.collection.collect_demand_animal_counterfactuals import (
    _arm_decision,
    _utility,
)
from tests.test_experimental_scale_agent import scale_observation


class DemandAnimalCounterfactualTests(unittest.TestCase):
    def test_arms_share_opening_before_day_six(self) -> None:
        with patch(
            "research.collection.collect_demand_animal_counterfactuals.decide_demand_animal_arm"
        ) as decide:
            _arm_decision(scale_observation(day=5), ARM_COW)

        self.assertEqual(decide.call_args.args[1], ARM_BALANCED)

    def test_selected_arm_starts_on_day_six(self) -> None:
        with patch(
            "research.collection.collect_demand_animal_counterfactuals.decide_demand_animal_arm"
        ) as decide:
            _arm_decision(scale_observation(day=6), ARM_COW)

        self.assertEqual(decide.call_args.args[1], ARM_COW)

    def test_terminal_win_dominates_margin(self) -> None:
        self.assertGreater(
            _utility({"result": "win", "terminal_margin": 1}),
            _utility({"result": "loss", "terminal_margin": 100_000}),
        )


if __name__ == "__main__":
    unittest.main()
