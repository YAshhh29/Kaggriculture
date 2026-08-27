import unittest
from unittest.mock import patch

from agents.experimental_full_capacity_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalFullCapacityAgentTests(unittest.TestCase):
    def test_enables_three_quadrant_capacity_controls(self) -> None:
        state = scale_observation(day=9)
        expected = {"farmer": ["PASS"], "hands": [], "market": []}

        with patch(
            "agents.experimental_full_capacity_agent.decide_premium",
            return_value=expected,
        ) as premium:
            self.assertEqual(decide(state), expected)

        self.assertEqual(premium.call_args.kwargs["target_extra_land"], 2)
        self.assertEqual(premium.call_args.kwargs["land_reserves"], (300, 300))
        self.assertEqual(
            premium.call_args.kwargs["late_rotation_crop"],
            "WHEAT",
        )
        self.assertTrue(
            premium.call_args.kwargs["release_idle_crop_reserve"]
        )
        self.assertTrue(
            premium.call_args.kwargs["prioritize_mature_harvest"]
        )


if __name__ == "__main__":
    unittest.main()
