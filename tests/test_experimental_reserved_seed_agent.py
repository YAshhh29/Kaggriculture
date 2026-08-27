import unittest
from unittest.mock import patch

from agents.experimental_reserved_seed_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalReservedSeedAgentTests(unittest.TestCase):
    def test_enables_per_quadrant_seed_reservation(self) -> None:
        with patch(
            "agents.experimental_reserved_seed_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["reserve_seeds_per_quadrant"]
        )


if __name__ == "__main__":
    unittest.main()
