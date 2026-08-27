import unittest
from unittest.mock import patch

from agents.experimental_future_labor_agent import FUTURE_HAND_TARGETS
from agents.experimental_pressure_late_strawberry_agent import decide
from policies.service_policy import ARM_PAIRED
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalPressureLateStrawberryAgentTests(unittest.TestCase):
    def test_supported_pressure_enables_four_late_strawberries(self) -> None:
        state = scale_observation(day=9)
        with (
            patch(
                "agents.experimental_pressure_late_strawberry_agent._choices",
                return_value=("SHEEP", "STRAWBERRY"),
            ),
            patch(
                "agents.experimental_pressure_late_strawberry_agent._selected_hand_targets",
                return_value=FUTURE_HAND_TARGETS,
            ),
            patch(
                "agents.experimental_pressure_late_strawberry_agent._selected_arm",
                return_value=ARM_PAIRED,
            ),
            patch(
                "agents.experimental_pressure_late_strawberry_agent.decide_premium"
            ) as premium,
        ):
            decide(state)

        self.assertEqual(
            premium.call_args.kwargs["selective_late_rotation_crop"],
            "STRAWBERRY",
        )
        self.assertEqual(
            premium.call_args.kwargs["selective_late_rotation_slots"],
            4,
        )
        self.assertEqual(
            premium.call_args.kwargs["late_rotation_crop"],
            "WHEAT",
        )

    def test_unsupported_crop_keeps_wheat_only_backfill(self) -> None:
        state = scale_observation(day=9)
        with (
            patch(
                "agents.experimental_pressure_late_strawberry_agent._choices",
                return_value=("SHEEP", "WHEAT"),
            ),
            patch(
                "agents.experimental_pressure_late_strawberry_agent._selected_hand_targets",
                return_value=FUTURE_HAND_TARGETS,
            ),
            patch(
                "agents.experimental_pressure_late_strawberry_agent.decide_premium"
            ) as premium,
        ):
            decide(state)

        self.assertIsNone(
            premium.call_args.kwargs["selective_late_rotation_crop"]
        )
        self.assertEqual(
            premium.call_args.kwargs["selective_late_rotation_slots"],
            0,
        )


if __name__ == "__main__":
    unittest.main()