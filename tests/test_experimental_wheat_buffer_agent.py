import unittest
from unittest.mock import patch

from agents.experimental_wheat_buffer_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalWheatBufferAgentTests(unittest.TestCase):
    def test_buffers_only_wheat(self) -> None:
        with patch(
            "agents.experimental_wheat_buffer_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=9))

        self.assertEqual(
            premium.call_args.kwargs["wheat_seed_buffer_multiplier"],
            2,
        )
        self.assertNotIn("seed_buffer_multiplier", premium.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
