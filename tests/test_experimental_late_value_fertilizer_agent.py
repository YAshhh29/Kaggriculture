import unittest
from unittest.mock import patch

from agents.experimental_late_value_fertilizer_agent import (
    _FERTILIZER_CHOICES,
    _selected_value_crops,
    decide_value_fertilizer,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalLateValueFertilizerAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _FERTILIZER_CHOICES.clear()

    def test_locks_melon_then_strawberry_from_late_features(self) -> None:
        melon = scale_observation(day=10, hour=12)
        strawberry = scale_observation(day=12, hour=12)
        with (
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "extract_live_macro_features",
                return_value={"features": 1.0},
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "fertilizer_service_supported",
                side_effect=lambda features, crop: crop == "MELON",
            ),
        ):
            self.assertEqual(_selected_value_crops(melon), ("MELON",))
            self.assertEqual(_selected_value_crops(strawberry), ("MELON",))

    def test_episode_reset_clears_stale_crop_choices(self) -> None:
        _FERTILIZER_CHOICES[0] = {"MELON": True, "STRAWBERRY": True}

        self.assertEqual(
            _selected_value_crops(scale_observation(day=0, hour=0)),
            (),
        )

    def test_forwards_value_crops_and_economic_feed(self) -> None:
        state = scale_observation(day=12, hour=12)
        with (
            patch(
                "agents.experimental_late_value_fertilizer_agent._choices",
                return_value=("COW", "WHEAT"),
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "_crop_service_selected",
                return_value=True,
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "_selected_value_crops",
                return_value=("MELON", "STRAWBERRY"),
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "_selected_hand_targets",
                return_value=tuple([12] * 30),
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "decide_demand",
                return_value={"farmer": ["PASS"], "hands": [], "market": []},
            ) as demand,
        ):
            decide_value_fertilizer(state, economic_feed=True)

        self.assertEqual(
            demand.call_args.kwargs["value_fertilization_crops"],
            ("MELON", "STRAWBERRY"),
        )
        self.assertTrue(
            demand.call_args.kwargs["economic_wheat_feed_reserve"]
        )

    def test_enabled_crops_isolates_one_service_arm(self) -> None:
        state = scale_observation(day=12, hour=12)
        with (
            patch(
                "agents.experimental_late_value_fertilizer_agent._choices",
                return_value=("COW", "WHEAT"),
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "_crop_service_selected",
                return_value=False,
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "_selected_value_crops",
                return_value=("MELON", "STRAWBERRY"),
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "_selected_hand_targets",
                return_value=tuple([12] * 30),
            ),
            patch(
                "agents.experimental_late_value_fertilizer_agent."
                "decide_demand",
                return_value={"farmer": ["PASS"], "hands": [], "market": []},
            ) as demand,
        ):
            decide_value_fertilizer(
                state,
                economic_feed=False,
                enabled_crops=("MELON",),
            )

        self.assertEqual(
            demand.call_args.kwargs["value_fertilization_crops"],
            ("MELON",),
        )


if __name__ == "__main__":
    unittest.main()
