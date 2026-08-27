import inspect
import unittest

from research.evaluation.screen_fertilizer_value import threshold_agent


class ScreenFertilizerValueTests(unittest.TestCase):
    def test_threshold_agent_exposes_only_observation_parameter(self) -> None:
        parameters = inspect.signature(threshold_agent(60)).parameters

        self.assertEqual(tuple(parameters), ("observation",))


if __name__ == "__main__":
    unittest.main()