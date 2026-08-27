import unittest
from unittest.mock import patch

from agents.experimental_routine_rescue_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalRoutineRescueAgentTests(unittest.TestCase):
    def test_enables_only_routine_cross_quadrant_rescue(self) -> None:
        with patch(
            "agents.experimental_routine_rescue_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["cross_quadrant_routine_rescue"]
        )
        self.assertNotIn(
            "reserve_seeds_per_quadrant",
            premium.call_args.kwargs,
        )


if __name__ == "__main__":
    unittest.main()
