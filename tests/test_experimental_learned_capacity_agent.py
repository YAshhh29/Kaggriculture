import copy
import unittest
from unittest.mock import patch

from policies.capacity_policy import ARM_STRAWBERRY, ARM_WHEAT
from agents.experimental_learned_capacity_agent import (
    _SELECTED_ARMS,
    _selected_arm,
    decide,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalLearnedCapacityAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _SELECTED_ARMS.clear()

    def test_uses_shared_strawberry_opening_before_day_four(self) -> None:
        self.assertEqual(
            _selected_arm(scale_observation(day=3)),
            ARM_STRAWBERRY,
        )

    def test_learned_choice_locks_for_the_episode(self) -> None:
        state = scale_observation(day=4)
        with patch(
            "agents.experimental_learned_capacity_agent.select_macro_arm",
            return_value=ARM_WHEAT,
        ) as select:
            self.assertEqual(_selected_arm(state), ARM_WHEAT)
            later = copy.deepcopy(state)
            later["day"] = 10
            self.assertEqual(_selected_arm(later), ARM_WHEAT)

        select.assert_called_once()

    def test_new_episode_clears_the_locked_choice(self) -> None:
        _SELECTED_ARMS[0] = ARM_WHEAT

        self.assertEqual(
            _selected_arm(scale_observation(day=0)),
            ARM_STRAWBERRY,
        )
        self.assertNotIn(0, _SELECTED_ARMS)

    def test_decide_executes_selected_capacity_arm(self) -> None:
        state = scale_observation(day=4)
        expected = {"farmer": ["PASS"], "hands": [], "market": []}

        with (
            patch(
                "agents.experimental_learned_capacity_agent._selected_arm",
                return_value=ARM_WHEAT,
            ),
            patch(
                "agents.experimental_learned_capacity_agent.decide_capacity_arm",
                return_value=expected,
            ) as capacity,
        ):
            self.assertEqual(decide(state), expected)

        self.assertEqual(capacity.call_args.args[1], ARM_WHEAT)


if __name__ == "__main__":
    unittest.main()
