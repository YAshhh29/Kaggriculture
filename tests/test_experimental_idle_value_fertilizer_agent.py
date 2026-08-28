import unittest
from unittest.mock import patch

from agents.experimental_idle_value_fertilizer_agent import (
    _APPLICATION_COUNTS,
    decide,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalIdleValueFertilizerAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _APPLICATION_COUNTS.clear()

    def test_forwards_idle_only_service_and_budget(self) -> None:
        state = scale_observation(day=12, hour=12)
        with patch(
            "agents.experimental_idle_value_fertilizer_agent."
            "decide_value_fertilizer",
            return_value={
                "farmer": ["FERTILIZE"],
                "hands": [],
                "market": [],
            },
        ) as value_agent:
            decide(state)

        self.assertEqual(value_agent.call_args.kwargs["enabled_crops"], ())
        self.assertEqual(
            value_agent.call_args.kwargs["idle_enabled_crops"],
            ("STRAWBERRY",),
        )
        self.assertEqual(value_agent.call_args.kwargs["application_limit"], 4)
        self.assertEqual(
            value_agent.call_args.kwargs["idle_maximum_distance"],
            2,
        )
        self.assertEqual(_APPLICATION_COUNTS[0], 1)

    def test_custom_application_budget_is_forwarded(self) -> None:
        state = scale_observation(day=12, hour=12)
        with patch(
            "agents.experimental_idle_value_fertilizer_agent."
            "decide_value_fertilizer",
            return_value={"farmer": ["PASS"], "hands": [], "market": []},
        ) as value_agent:
            decide(state, maximum_applications=5)

        self.assertEqual(value_agent.call_args.kwargs["application_limit"], 5)

    def test_staging_movement_does_not_consume_application_budget(
        self,
    ) -> None:
        state = scale_observation(day=12, hour=12)
        with patch(
            "agents.experimental_idle_value_fertilizer_agent."
            "decide_value_fertilizer",
            side_effect=[
                {"farmer": ["WEST"], "hands": [], "market": []},
                {"farmer": ["PASS"], "hands": [], "market": []},
            ],
        ) as value_agent:
            decide(state)
            decide(state)

        self.assertEqual(
            [
                call.kwargs["application_limit"]
                for call in value_agent.call_args_list
            ],
            [4, 4],
        )
        self.assertEqual(_APPLICATION_COUNTS[0], 0)


if __name__ == "__main__":
    unittest.main()
