import unittest
from unittest.mock import patch

from agents.experimental_dynamic_horizon_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalDynamicHorizonAgentTests(unittest.TestCase):
    def test_enables_state_and_lifecycle_driven_capacity(self) -> None:
        with patch(
            "agents.experimental_dynamic_horizon_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["dynamic_land_expansion"]
        )
        self.assertTrue(
            premium.call_args.kwargs["dynamic_lifecycle_windows"]
        )


if __name__ == "__main__":
    unittest.main()
