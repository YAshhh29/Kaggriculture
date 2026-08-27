import unittest

from agents.experimental_incremental_buffer_agent import _extra_wheat_seed
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalIncrementalBufferAgentTests(unittest.TestCase):
    def test_requires_sw_cash_and_midgame_window(self) -> None:
        state = scale_observation(day=10, money=2_000)
        self.assertEqual(_extra_wheat_seed(state), 0)

        state["farms"][0]["unlocked_quadrants"].extend(["NE", "SW"])
        self.assertEqual(_extra_wheat_seed(state), 1)

        state["farms"][0]["money"] = 1_999
        self.assertEqual(_extra_wheat_seed(state), 0)

        state["farms"][0]["money"] = 2_000
        state["day"] = 19
        self.assertEqual(_extra_wheat_seed(state), 0)


if __name__ == "__main__":
    unittest.main()
