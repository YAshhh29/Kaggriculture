import unittest
from unittest.mock import patch

from agents.experimental_tiered_value_fertilizer_agent import (
    _STAGING_DISTANCES,
    _selected_staging_distance,
    decide,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalTieredValueFertilizerAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _STAGING_DISTANCES.clear()

    def test_locks_distance_from_day_twelve_strawberry_price(self) -> None:
        state = scale_observation(day=12, hour=12)
        with patch(
            "agents.experimental_tiered_value_fertilizer_agent."
            "extract_live_macro_features",
            return_value={"price_strawberry": 1.31},
        ):
            self.assertEqual(_selected_staging_distance(state), 2)

        _STAGING_DISTANCES.clear()
        with patch(
            "agents.experimental_tiered_value_fertilizer_agent."
            "extract_live_macro_features",
            return_value={"price_strawberry": 1.30},
        ):
            self.assertEqual(_selected_staging_distance(state), 0)

    def test_new_episode_clears_stale_distance(self) -> None:
        _STAGING_DISTANCES[0] = 2

        self.assertEqual(
            _selected_staging_distance(scale_observation(day=0, hour=0)),
            0,
        )
        self.assertNotIn(0, _STAGING_DISTANCES)

    def test_forwards_selected_distance(self) -> None:
        state = scale_observation(day=12, hour=12)
        with (
            patch(
                "agents.experimental_tiered_value_fertilizer_agent."
                "_selected_staging_distance",
                return_value=2,
            ),
            patch(
                "agents.experimental_tiered_value_fertilizer_agent."
                "decide_idle",
                return_value={"farmer": ["PASS"], "hands": [], "market": []},
            ) as idle,
        ):
            decide(state)

        self.assertEqual(idle.call_args.kwargs["maximum_distance"], 2)
        self.assertEqual(idle.call_args.kwargs["maximum_applications"], 4)


if __name__ == "__main__":
    unittest.main()
