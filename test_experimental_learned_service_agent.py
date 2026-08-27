import unittest
from unittest.mock import patch

from agents.experimental_learned_service_agent import (
    _SELECTED_ARMS,
    _selected_arm,
    decide,
)
from policies.service_policy import ARM_BASELINE, ARM_PAIRED
from test_experimental_scale_agent import scale_observation


class ExperimentalLearnedServiceAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _SELECTED_ARMS.clear()

    def test_uses_baseline_during_shared_opening(self) -> None:
        self.assertEqual(_selected_arm(scale_observation(day=0)), ARM_BASELINE)

    def test_learned_choice_locks_for_episode(self) -> None:
        state = scale_observation(day=1)
        state["town"]["unlocked_shops"] = ["BAKERY"]
        with patch(
            "agents.experimental_learned_service_agent.select_macro_arm",
            return_value=ARM_PAIRED,
        ) as select:
            first = _selected_arm(state)
            state["day"] = 2
            second = _selected_arm(state)

        self.assertEqual((first, second), (ARM_PAIRED, ARM_PAIRED))
        select.assert_called_once()

    def test_new_episode_resets_locked_choice(self) -> None:
        _SELECTED_ARMS[0] = ARM_PAIRED
        _selected_arm(scale_observation(day=0, hour=0))

        self.assertNotIn(0, _SELECTED_ARMS)

    def test_out_of_distribution_bank_falls_back_to_baseline(self) -> None:
        state = scale_observation(day=1)
        state["farms"][1]["money"] = 1
        with patch(
            "agents.experimental_learned_service_agent.select_macro_arm"
        ) as select:
            arm = _selected_arm(state)

        self.assertEqual(arm, ARM_BASELINE)
        select.assert_not_called()

    def test_decide_executes_selected_service_arm(self) -> None:
        with (
            patch(
                "agents.experimental_learned_service_agent._selected_arm",
                return_value=ARM_PAIRED,
            ),
            patch(
                "agents.experimental_learned_service_agent.decide_service_arm"
            ) as service,
        ):
            decide(scale_observation(day=1))

        self.assertEqual(service.call_args.args[1], ARM_PAIRED)


if __name__ == "__main__":
    unittest.main()
