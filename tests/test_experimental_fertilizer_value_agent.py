import unittest
from unittest.mock import patch

from agents.experimental_fertilizer_value_agent import decide_with_threshold
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalFertilizerValueAgentTests(unittest.TestCase):
    def test_forwards_bounded_fertilizer_hold(self) -> None:
        state = scale_observation(day=12)
        with (
            patch(
                "agents.experimental_fertilizer_value_agent._choices",
                return_value=("SHEEP", "WHEAT"),
            ),
            patch(
                "agents.experimental_fertilizer_value_agent.decide_demand"
            ) as demand,
        ):
            decide_with_threshold(state, 70)

        self.assertEqual(
            demand.call_args.kwargs["minimum_fertilizer_sale_price"],
            70,
        )
        self.assertEqual(
            demand.call_args.kwargs["maximum_fertilizer_holdings"],
            72,
        )
        self.assertEqual(
            demand.call_args.kwargs["fertilizer_liquidation_day"],
            28,
        )


if __name__ == "__main__":
    unittest.main()