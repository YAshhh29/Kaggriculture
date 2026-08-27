import unittest

from agents.experimental_deadline_tapered_wheat_agent import (
    DEADLINE_HAND_TARGETS,
)
from agents.experimental_future_labor_agent import (
    FUTURE_HAND_TARGETS,
    _LABOR_CHOICES,
    _selected_hand_targets,
    hand_targets_for_animal,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalFutureLaborAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _LABOR_CHOICES.clear()

    def test_cheaper_demand_animals_fund_peak_labor(self) -> None:
        self.assertEqual(
            hand_targets_for_animal("COW"),
            FUTURE_HAND_TARGETS,
        )
        self.assertEqual(
            hand_targets_for_animal("GOOSE"),
            FUTURE_HAND_TARGETS,
        )

    def test_balanced_sheep_herd_keeps_submitted_labor(self) -> None:
        self.assertEqual(
            hand_targets_for_animal("SHEEP"),
            DEADLINE_HAND_TARGETS,
        )

    def test_diversified_opponent_supports_and_locks_extra_labor(self) -> None:
        state = scale_observation(day=6)
        state["farms"][1]["tiles"][0][0] = {
            "kind": "PLANT",
            "crop": "STRAWBERRY",
        }

        selected = _selected_hand_targets(state, "GOOSE")
        state["day"] = 7
        state["farms"][1]["tiles"][0][0]["crop"] = "WHEAT"

        self.assertEqual(selected, FUTURE_HAND_TARGETS)
        self.assertEqual(
            _selected_hand_targets(state, "GOOSE"),
            FUTURE_HAND_TARGETS,
        )

    def test_wheat_heavy_opponent_keeps_submitted_labor(self) -> None:
        state = scale_observation(day=6)
        state["farms"][1]["tiles"][0][0] = {
            "kind": "PLANT",
            "crop": "WHEAT",
        }

        self.assertEqual(
            _selected_hand_targets(state, "GOOSE"),
            DEADLINE_HAND_TARGETS,
        )


if __name__ == "__main__":
    unittest.main()