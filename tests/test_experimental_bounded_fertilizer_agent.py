import unittest
from unittest.mock import patch

from agents.experimental_bounded_fertilizer_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalBoundedFertilizerAgentTests(unittest.TestCase):
    def test_caps_fertilization_and_reserve(self) -> None:
        with patch(
            "agents.experimental_bounded_fertilizer_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=11))

        self.assertEqual(
            premium.call_args.kwargs[
                "fertilized_strawberries_per_quadrant"
            ],
            1,
        )
        self.assertEqual(
            premium.call_args.kwargs["fertilizer_reserve_limit"],
            6,
        )


if __name__ == "__main__":
    unittest.main()
