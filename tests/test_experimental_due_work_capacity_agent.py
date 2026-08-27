import unittest
from unittest.mock import patch

from agents.experimental_due_work_capacity_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalDueWorkCapacityAgentTests(unittest.TestCase):
    def test_scales_crop_reserve_for_saturated_admission(self) -> None:
        with patch(
            "agents.experimental_due_work_capacity_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["scale_crop_reserve_to_due_work"]
        )
        self.assertTrue(
            premium.call_args.kwargs["reserve_seeds_per_quadrant"]
        )


if __name__ == "__main__":
    unittest.main()
