import unittest
from unittest.mock import patch

from agents.experimental_dynamic_expansion_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalDynamicExpansionAgentTests(unittest.TestCase):
    def test_enables_dynamic_land_expansion(self) -> None:
        with patch(
            "agents.experimental_dynamic_expansion_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=4))

        self.assertTrue(
            premium.call_args.kwargs["dynamic_land_expansion"]
        )


if __name__ == "__main__":
    unittest.main()
