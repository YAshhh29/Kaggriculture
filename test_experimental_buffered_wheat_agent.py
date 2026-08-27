import unittest
from unittest.mock import patch

from agents.experimental_buffered_wheat_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalBufferedWheatAgentTests(unittest.TestCase):
    def test_uses_two_cycle_seed_buffer(self) -> None:
        with patch(
            "agents.experimental_buffered_wheat_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=9))

        self.assertEqual(
            premium.call_args.kwargs["seed_buffer_multiplier"],
            2,
        )


if __name__ == "__main__":
    unittest.main()
