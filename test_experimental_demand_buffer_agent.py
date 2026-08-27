import unittest

from agents.experimental_demand_buffer_agent import _wheat_buffer_multiplier
from test_experimental_scale_agent import scale_observation
from test_main import wheat_tile


class ExperimentalDemandBufferAgentTests(unittest.TestCase):
    def test_requires_funded_sw_and_diversified_opponent(self) -> None:
        state = scale_observation(day=12, money=2_000)
        state["farms"][0]["unlocked_quadrants"].extend(["NE", "SW"])
        state["farms"][1]["tiles"][0][0] = wheat_tile()
        self.assertIsNone(_wheat_buffer_multiplier(state))

        state["farms"][1]["tiles"][0][1] = {
            "kind": "PLANT",
            "crop": "MELON",
        }
        self.assertEqual(_wheat_buffer_multiplier(state), 2)

        state["farms"][0]["money"] = 1_999
        self.assertIsNone(_wheat_buffer_multiplier(state))

    def test_stops_buffering_after_safe_window(self) -> None:
        state = scale_observation(day=19, money=10_000)
        state["farms"][0]["unlocked_quadrants"].extend(["NE", "SW"])
        state["farms"][1]["tiles"][0][0] = {
            "kind": "PLANT",
            "crop": "MELON",
        }

        self.assertIsNone(_wheat_buffer_multiplier(state))


if __name__ == "__main__":
    unittest.main()
