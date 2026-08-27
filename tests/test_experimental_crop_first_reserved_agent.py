import unittest
from unittest.mock import patch

from agents.experimental_crop_first_reserved_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalCropFirstReservedAgentTests(unittest.TestCase):
    def test_enables_reservation_and_crop_first_service(self) -> None:
        with patch(
            "agents.experimental_crop_first_reserved_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["reserve_seeds_per_quadrant"]
        )
        self.assertTrue(
            premium.call_args.kwargs["crop_before_routine_animals"]
        )


if __name__ == "__main__":
    unittest.main()
