import unittest
from unittest.mock import patch

from agents.experimental_rescue_deadline_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalRescueDeadlineAgentTests(unittest.TestCase):
    def test_enables_only_cross_quadrant_rescue(self) -> None:
        with patch(
            "agents.experimental_rescue_deadline_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["cross_quadrant_crop_rescue"]
        )
        self.assertNotIn(
            "reserve_seeds_per_quadrant",
            premium.call_args.kwargs,
        )
        self.assertNotIn(
            "crop_before_routine_animals",
            premium.call_args.kwargs,
        )


if __name__ == "__main__":
    unittest.main()
