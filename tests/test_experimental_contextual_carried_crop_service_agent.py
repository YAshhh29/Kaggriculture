import unittest
from unittest.mock import patch

from agents.experimental_contextual_carried_crop_service_agent import (
    _CARRIED_SERVICE_CHOICES,
    _carried_service_selected,
    decide,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalContextualCarriedCropServiceAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _CARRIED_SERVICE_CHOICES.clear()

    def test_selects_only_supported_high_wheat_no_wool_context(self) -> None:
        state = scale_observation(day=6)
        supported = {
            "price_wheat": 1.32,
            "shops_wool": 0.0,
            "opponent_wheat": 2.0,
        }
        with patch(
            "agents.experimental_contextual_carried_crop_service_agent."
            "extract_macro_features",
            return_value=supported,
        ):
            self.assertTrue(_carried_service_selected(state))

        _CARRIED_SERVICE_CHOICES.clear()
        for feature, value in (
            ("price_wheat", 1.28),
            ("shops_wool", 1.0),
            ("opponent_wheat", 4.0),
        ):
            unsupported = {**supported, feature: value}
            with patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "extract_macro_features",
                return_value=unsupported,
            ):
                self.assertFalse(_carried_service_selected(state))
            _CARRIED_SERVICE_CHOICES.clear()

    def test_forwards_routed_service_only_when_both_guards_pass(self) -> None:
        state = scale_observation(day=6)
        with (
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "_choices",
                return_value=("COW", "WHEAT"),
            ),
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "_crop_service_selected",
                return_value=True,
            ),
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "_carried_service_selected",
                return_value=True,
            ),
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "_selected_hand_targets",
                return_value=tuple([12] * 30),
            ),
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "decide_demand",
                return_value={"farmer": ["PASS"], "hands": [], "market": []},
            ) as demand,
        ):
            decide(state)

        self.assertTrue(demand.call_args.kwargs["fertilize_strawberries"])
        self.assertTrue(
            demand.call_args.kwargs["pair_colocated_strawberry_service"]
        )
        self.assertTrue(demand.call_args.kwargs["carried_fertilizer_only"])

    def test_decide_clears_stale_choice_before_service_selection(self) -> None:
        state = scale_observation(day=0)
        _CARRIED_SERVICE_CHOICES[0] = True
        with (
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "_choices",
                return_value=("SHEEP", "WHEAT"),
            ),
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "_crop_service_selected",
                return_value=False,
            ),
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "_selected_hand_targets",
                return_value=tuple([12] * 30),
            ),
            patch(
                "agents.experimental_contextual_carried_crop_service_agent."
                "decide_demand",
                return_value={"farmer": ["PASS"], "hands": [], "market": []},
            ),
        ):
            decide(state)

        self.assertNotIn(0, _CARRIED_SERVICE_CHOICES)


if __name__ == "__main__":
    unittest.main()