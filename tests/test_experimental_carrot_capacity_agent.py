import unittest
from unittest.mock import patch

from agents.experimental_carrot_capacity_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalCarrotCapacityAgentTests(unittest.TestCase):
    def test_uses_carrot_rotation_for_cleared_slots(self) -> None:
        with patch(
            "agents.experimental_carrot_capacity_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertEqual(premium.call_args.kwargs["rotation_crop"], "CARROT")
        self.assertEqual(
            premium.call_args.kwargs["late_rotation_crop"],
            "CARROT",
        )


if __name__ == "__main__":
    unittest.main()
