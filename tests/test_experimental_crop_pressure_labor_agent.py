import unittest
from copy import deepcopy

from agents.experimental_crop_pressure_labor_agent import (
    _PRESSURE_CHOICES,
    _selected_hand_targets,
)
from agents.experimental_deadline_tapered_wheat_agent import (
    DEADLINE_HAND_TARGETS,
)
from agents.experimental_future_labor_agent import FUTURE_HAND_TARGETS
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalCropPressureLaborAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _PRESSURE_CHOICES.clear()

    @staticmethod
    def _independent_opponent(state: dict) -> None:
        state["farms"][1] = deepcopy(state["farms"][1])
        state["farms"][1]["tiles"] = [
            [None for _ in range(10)] for _ in range(10)
        ]

    def test_sheep_context_funds_labor_when_opponent_leads_crops(self) -> None:
        state = scale_observation(day=6)
        self._independent_opponent(state)
        for x in range(4):
            state["farms"][1]["tiles"][0][x] = {
                "kind": "PLANT",
                "crop": "WHEAT",
            }

        self.assertEqual(
            _selected_hand_targets(state, "SHEEP"),
            FUTURE_HAND_TARGETS,
        )

    def test_small_crop_gap_keeps_submitted_labor(self) -> None:
        state = scale_observation(day=6)
        self._independent_opponent(state)
        for x in range(3):
            state["farms"][1]["tiles"][0][x] = {
                "kind": "PLANT",
                "crop": "WHEAT",
            }

        self.assertEqual(
            _selected_hand_targets(state, "SHEEP"),
            DEADLINE_HAND_TARGETS,
        )

    def test_pressure_choice_locks_for_episode(self) -> None:
        state = scale_observation(day=6)
        self._independent_opponent(state)
        for x in range(4):
            state["farms"][1]["tiles"][0][x] = {
                "kind": "PLANT",
                "crop": "WHEAT",
            }
        selected = _selected_hand_targets(state, "SHEEP")
        state["day"] = 7
        state["farms"][1]["tiles"] = [
            [None for _ in range(10)] for _ in range(10)
        ]

        self.assertEqual(selected, FUTURE_HAND_TARGETS)
        self.assertEqual(
            _selected_hand_targets(state, "SHEEP"),
            FUTURE_HAND_TARGETS,
        )


if __name__ == "__main__":
    unittest.main()