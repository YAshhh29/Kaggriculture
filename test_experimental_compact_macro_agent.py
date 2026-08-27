import unittest
from unittest.mock import patch

from agents.experimental_adaptive_counter_agent import ONE_LAND_ANIMAL_PLANS
from agents.experimental_compact_macro_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalCompactMacroAgentTests(unittest.TestCase):
    def test_uses_shared_opening_before_selection_day(self) -> None:
        state = scale_observation(day=8)
        expected = {"farmer": ["PASS"], "hands": [], "market": []}

        with patch(
            "agents.experimental_compact_macro_agent.decide_premium",
            return_value=expected,
        ) as premium:
            self.assertEqual(decide(state), expected)

        self.assertEqual(premium.call_args.kwargs, {})

    def test_commits_to_one_land_animal_plan_on_selection_day(self) -> None:
        state = scale_observation(day=9)
        expected = {"farmer": ["PASS"], "hands": [], "market": []}

        with patch(
            "agents.experimental_compact_macro_agent.decide_premium",
            return_value=expected,
        ) as premium:
            self.assertEqual(decide(state), expected)

        self.assertEqual(premium.call_args.kwargs["target_extra_land"], 1)
        self.assertIs(
            premium.call_args.kwargs["animal_plans"],
            ONE_LAND_ANIMAL_PLANS,
        )


if __name__ == "__main__":
    unittest.main()