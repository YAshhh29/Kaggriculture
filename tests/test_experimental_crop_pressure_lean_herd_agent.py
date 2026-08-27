import unittest
from copy import deepcopy

from agents.experimental_crop_pressure_lean_herd_agent import (
    _LEAN_CHOICES,
    _lean_selected,
    lean_expansion_animal_plans,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalCropPressureLeanHerdAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _LEAN_CHOICES.clear()

    def test_removes_one_expansion_sheep_per_new_quadrant(self) -> None:
        plans = lean_expansion_animal_plans("SHEEP")

        self.assertEqual(len(plans), 10)
        self.assertEqual(
            sum(plan["animal"] == "COW" for plan in plans),
            6,
        )
        self.assertEqual(
            sum(plan["animal"] == "SHEEP" for plan in plans),
            4,
        )

    def test_pressure_choice_locks_for_episode(self) -> None:
        state = scale_observation(day=6)
        state["farms"][1] = deepcopy(state["farms"][1])
        state["farms"][1]["tiles"] = [
            [None for _ in range(10)] for _ in range(10)
        ]
        for x in range(4):
            state["farms"][1]["tiles"][0][x] = {
                "kind": "PLANT",
                "crop": "WHEAT",
            }

        self.assertTrue(_lean_selected(state))
        state["day"] = 7
        state["farms"][1]["tiles"] = [
            [None for _ in range(10)] for _ in range(10)
        ]
        self.assertTrue(_lean_selected(state))

    def test_small_crop_gap_keeps_full_herd(self) -> None:
        state = scale_observation(day=6)
        state["farms"][1] = deepcopy(state["farms"][1])
        state["farms"][1]["tiles"] = [
            [None for _ in range(10)] for _ in range(10)
        ]
        for x in range(3):
            state["farms"][1]["tiles"][0][x] = {
                "kind": "PLANT",
                "crop": "WHEAT",
            }

        self.assertFalse(_lean_selected(state))


if __name__ == "__main__":
    unittest.main()