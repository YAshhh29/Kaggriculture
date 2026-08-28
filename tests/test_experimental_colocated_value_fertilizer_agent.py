import unittest
from unittest.mock import patch

from agents.experimental_colocated_value_fertilizer_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalColocatedValueFertilizerAgentTests(unittest.TestCase):
    def test_forwards_zero_staging_distance(self) -> None:
        with patch(
            "agents.experimental_colocated_value_fertilizer_agent.decide_idle",
            return_value={"farmer": ["PASS"], "hands": [], "market": []},
        ) as idle:
            decide(scale_observation(day=12, hour=12))

        self.assertEqual(idle.call_args.kwargs["maximum_distance"], 0)


if __name__ == "__main__":
    unittest.main()
