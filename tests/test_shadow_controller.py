import unittest
from unittest.mock import patch

from policies.demand_animal_policy import ARM_BALANCED, ARM_COW
from policies.shadow_controller import _SELECTED_ARMS, select_shadow_arm
from tests.test_experimental_scale_agent import scale_observation


class ShadowControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        _SELECTED_ARMS.clear()

    def test_uses_balanced_opening_before_day_six(self) -> None:
        self.assertEqual(select_shadow_arm(scale_observation(day=5)), ARM_BALANCED)

    def test_locks_model_recommendation_for_episode(self) -> None:
        state = scale_observation(day=6)
        with patch(
            "policies.shadow_controller.select_macro_arm",
            return_value=ARM_COW,
        ) as select:
            first = select_shadow_arm(state)
            state["day"] = 7
            second = select_shadow_arm(state)

        self.assertEqual((first, second), (ARM_COW, ARM_COW))
        select.assert_called_once()

    def test_unsupported_opening_falls_back_to_balanced(self) -> None:
        state = scale_observation(day=6)
        state["farms"][1]["money"] = 100

        self.assertEqual(select_shadow_arm(state), ARM_BALANCED)


if __name__ == "__main__":
    unittest.main()
