import unittest
from unittest.mock import patch

from agents.experimental_melon_capacity_agent import (
    MELON_LAST_PLANT_DAY,
    decide,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalMelonCapacityAgentTests(unittest.TestCase):
    def test_uses_day_eighteen_melon_rotation(self) -> None:
        with patch(
            "agents.experimental_melon_capacity_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertEqual(premium.call_args.kwargs["rotation_crop"], "MELON")
        self.assertEqual(
            premium.call_args.kwargs["rotation_last_plant_day"],
            MELON_LAST_PLANT_DAY,
        )
        self.assertEqual(
            premium.call_args.kwargs["late_rotation_last_plant_day"],
            MELON_LAST_PLANT_DAY,
        )


if __name__ == "__main__":
    unittest.main()
