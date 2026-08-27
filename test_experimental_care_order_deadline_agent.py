import unittest
from unittest.mock import patch

from agents.experimental_care_order_deadline_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalCareOrderDeadlineAgentTests(unittest.TestCase):
    def test_changes_only_service_order(self) -> None:
        with patch(
            "agents.experimental_care_order_deadline_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["crops_before_care_only"]
        )
        self.assertTrue(
            premium.call_args.kwargs["plant_before_care"]
        )
        self.assertNotIn(
            "reserve_seeds_per_quadrant",
            premium.call_args.kwargs,
        )


if __name__ == "__main__":
    unittest.main()
