import unittest
from unittest.mock import patch

from agents.experimental_assisted_buffer_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalAssistedBufferAgentTests(unittest.TestCase):
    def test_enables_cross_quadrant_rescue(self) -> None:
        with patch(
            "agents.experimental_assisted_buffer_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12, money=5_000))

        self.assertTrue(
            premium.call_args.kwargs["cross_quadrant_crop_rescue"]
        )


if __name__ == "__main__":
    unittest.main()
