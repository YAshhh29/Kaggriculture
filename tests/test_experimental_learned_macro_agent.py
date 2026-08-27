import copy
import unittest
from unittest.mock import patch

from agents.experimental_learned_macro_agent import (
    _SELECTED_ARMS,
    _selected_arm,
    decide,
)
from policies.macro_policy import ARM_COMPACT, ARM_COMPACT_CROP, ARM_EXPANDED
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalLearnedMacroAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _SELECTED_ARMS.clear()

    def test_expands_above_the_high_milk_price_split(self) -> None:
        state = scale_observation(day=9)
        state["market"]["prices"]["MILK"] = 224

        self.assertEqual(_selected_arm(state), ARM_EXPANDED)

    def test_compacts_against_funded_opponent_and_locks_choice(self) -> None:
        state = scale_observation(day=9)
        state["market"]["prices"]["MILK"] = 210
        state["town"]["unlocked_shops"] = ["BRUNCH_SPOT"]
        self.assertEqual(_selected_arm(state), ARM_COMPACT)

        later = copy.deepcopy(state)
        later["day"] = 10
        later["farms"][1]["money"] = 0
        self.assertEqual(_selected_arm(later), ARM_COMPACT)

    def test_new_episode_resets_the_locked_arm(self) -> None:
        state = scale_observation(day=9)
        state["market"]["prices"]["MILK"] = 210
        state["town"]["unlocked_shops"] = ["BRUNCH_SPOT"]
        self.assertEqual(_selected_arm(state), ARM_COMPACT)

        opening = scale_observation(day=0)
        self.assertEqual(_selected_arm(opening), ARM_EXPANDED)
        self.assertNotIn(0, _SELECTED_ARMS)

    def test_compact_decision_calls_safe_one_land_template(self) -> None:
        state = scale_observation(day=9)
        state["market"]["prices"]["MILK"] = 210
        state["town"]["unlocked_shops"] = ["BRUNCH_SPOT"]
        expected = {"farmer": ["PASS"], "hands": [], "market": []}

        with patch(
            "agents.experimental_learned_macro_agent.decide_premium",
            return_value=expected,
        ) as premium:
            self.assertEqual(decide(state), expected)

        self.assertEqual(premium.call_args.kwargs["target_extra_land"], 1)

    def test_no_strawberry_demand_selects_crop_protected_arm(self) -> None:
        state = scale_observation(day=9)
        state["farms"][0]["money"] = 1000
        state["farms"][1]["money"] = 100
        state["town"]["unlocked_shops"] = ["PET_CAFE"]

        self.assertEqual(_selected_arm(state), ARM_COMPACT_CROP)


if __name__ == "__main__":
    unittest.main()
