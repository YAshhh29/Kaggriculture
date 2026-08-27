import unittest

from agents.experimental_midgame_buffer_agent import _wheat_buffer_multiplier
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalMidgameBufferAgentTests(unittest.TestCase):
    def test_buffers_only_inside_funded_midgame_window(self) -> None:
        self.assertEqual(
            _wheat_buffer_multiplier(scale_observation(day=11, money=8_000)),
            1,
        )
        self.assertEqual(
            _wheat_buffer_multiplier(scale_observation(day=12, money=4_999)),
            1,
        )
        self.assertEqual(
            _wheat_buffer_multiplier(scale_observation(day=12, money=5_000)),
            2,
        )
        self.assertEqual(
            _wheat_buffer_multiplier(scale_observation(day=18, money=5_000)),
            2,
        )
        self.assertEqual(
            _wheat_buffer_multiplier(scale_observation(day=19, money=8_000)),
            1,
        )


if __name__ == "__main__":
    unittest.main()
