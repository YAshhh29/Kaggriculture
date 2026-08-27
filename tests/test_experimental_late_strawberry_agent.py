import unittest
from unittest.mock import patch

from agents.experimental_late_strawberry_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalLateStrawberryAgentTests(unittest.TestCase):
    def test_strawberry_demand_enables_four_late_slots(self) -> None:
        state = scale_observation(day=9)
        with (
            patch(
                "agents.experimental_late_strawberry_agent._choices",
                return_value=("SHEEP", "STRAWBERRY"),
            ),
            patch(
                "agents.experimental_late_strawberry_agent.decide_premium"
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
            premium.call_args.kwargs["hand_targets"][9],
            12,
        )


if __name__ == "__main__":
    unittest.main()