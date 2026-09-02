import unittest
from unittest.mock import patch

from agents.experimental_high_utilization_agent import (
    HIGH_UTILIZATION_CROP_RESERVES,
    HIGH_UTILIZATION_HAND_TARGETS,
    decide,
)
from agents.experimental_throughput_agent import _purchase_cost
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalHighUtilizationAgentTests(unittest.TestCase):
    def test_fourteenth_hand_uses_simulator_fibonacci_cost(self) -> None:
        state = scale_observation()

        self.assertEqual(_purchase_cost(["HIRE"], state, 13), 377)

    def test_forwards_replay_grounded_capacity_controls(self) -> None:
        state = scale_observation(day=12)
        with (
            patch(
                "agents.experimental_high_utilization_agent._choices",
                return_value=("COW", "WHEAT"),
            ),
            patch(
                "agents.experimental_high_utilization_agent._selected_arm",
                return_value=0,
            ),
            patch(
                "agents.experimental_high_utilization_agent.decide_premium",
                return_value={"farmer": ["PASS"], "hands": [], "market": []},
            ) as premium,
        ):
            decide(state)

        kwargs = premium.call_args.kwargs
        self.assertEqual(kwargs["late_rotation_last_plant_day"], 27)
        self.assertEqual(kwargs["hand_targets"], HIGH_UTILIZATION_HAND_TARGETS)
        self.assertEqual(
            kwargs["crop_worker_reserves_by_day"],
            HIGH_UTILIZATION_CROP_RESERVES,
        )
        self.assertTrue(kwargs["opening_fill_nw"])
        self.assertEqual(kwargs["opening_melon_slots"], 5)
        self.assertTrue(kwargs["final_crop_liquidation"])


if __name__ == "__main__":
    unittest.main()
