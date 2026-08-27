import unittest
from unittest.mock import patch

from agents.experimental_dynamic_replacement_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalDynamicReplacementAgentTests(unittest.TestCase):
    def test_bounds_lifecycle_driven_replacement(self) -> None:
        with patch(
            "agents.experimental_dynamic_replacement_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["dynamic_lifecycle_deadlines_only"]
        )
        self.assertEqual(
            premium.call_args.kwargs["max_active_crops_per_quadrant"],
            13,
        )


if __name__ == "__main__":
    unittest.main()
