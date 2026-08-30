import unittest
from unittest.mock import patch

from agents.experimental_tiered_late_strawberry_agent import (
    _LATE_STRAWBERRY_CHOICES,
    _late_strawberry_selected,
    decide,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalTieredLateStrawberryAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _LATE_STRAWBERRY_CHOICES.clear()

    def test_forwards_eight_late_strawberry_slots(self) -> None:
        state = scale_observation(day=12, hour=12)
        with (
            patch(
                "agents.experimental_tiered_late_strawberry_agent."
                "_late_strawberry_selected",
                return_value=True,
            ),
            patch(
                "agents.experimental_tiered_late_strawberry_agent."
                "decide_tiered",
                return_value={
                    "farmer": ["PASS"],
                    "hands": [],
                    "market": [],
                },
            ) as tiered,
        ):
            decide(state)

        self.assertEqual(
            tiered.call_args.kwargs["late_strawberry_slots"],
            8,
        )

    def test_locks_day_six_strawberry_value_gate(self) -> None:
        state = scale_observation(day=6, hour=0)
        with patch(
            "agents.experimental_tiered_late_strawberry_agent."
            "extract_macro_features",
            return_value={"price_strawberry": 1.30},
        ):
            self.assertTrue(_late_strawberry_selected(state))

        with patch(
            "agents.experimental_tiered_late_strawberry_agent."
            "extract_macro_features",
            return_value={"price_strawberry": 1.10},
        ):
            self.assertTrue(_late_strawberry_selected(state))

    def test_rejects_below_threshold_and_resets_next_episode(self) -> None:
        state = scale_observation(day=6, hour=0)
        with patch(
            "agents.experimental_tiered_late_strawberry_agent."
            "extract_macro_features",
            return_value={"price_strawberry": 1.299},
        ):
            self.assertFalse(_late_strawberry_selected(state))

        self.assertFalse(
            _late_strawberry_selected(scale_observation(day=0, hour=0))
        )
        self.assertNotIn(0, _LATE_STRAWBERRY_CHOICES)


if __name__ == "__main__":
    unittest.main()
