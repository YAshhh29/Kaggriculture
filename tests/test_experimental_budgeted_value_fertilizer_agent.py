import unittest
from unittest.mock import patch

from agents.experimental_budgeted_value_fertilizer_agent import (
    _APPLICATION_COUNTS,
    decide,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalBudgetedValueFertilizerAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _APPLICATION_COUNTS.clear()

    def test_decrements_and_stops_episode_application_budget(self) -> None:
        state = scale_observation(day=12, hour=12)
        fertilized = {
            "farmer": ["FERTILIZE"],
            "hands": [["PASS"]],
            "market": [],
        }
        with patch(
            "agents.experimental_budgeted_value_fertilizer_agent."
            "decide_value_fertilizer",
            side_effect=[fertilized, fertilized, fertilized, fertilized, {
                "farmer": ["PASS"], "hands": [], "market": []
            }],
        ) as value_agent:
            for _ in range(5):
                decide(state)

        limits = [
            call.kwargs["application_limit"]
            for call in value_agent.call_args_list
        ]
        self.assertEqual(limits, [4, 3, 2, 1, 0])
        self.assertEqual(_APPLICATION_COUNTS[0], 4)

    def test_new_episode_clears_stale_application_count(self) -> None:
        _APPLICATION_COUNTS[0] = 4
        state = scale_observation(day=0, hour=0)
        with patch(
            "agents.experimental_budgeted_value_fertilizer_agent."
            "decide_value_fertilizer",
            return_value={"farmer": ["PASS"], "hands": [], "market": []},
        ) as value_agent:
            decide(state)

        self.assertEqual(
            value_agent.call_args.kwargs["application_limit"],
            4,
        )


if __name__ == "__main__":
    unittest.main()
