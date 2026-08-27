import unittest
from unittest.mock import patch

from agents.experimental_carried_fertilizer_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalCarriedFertilizerAgentTests(unittest.TestCase):
    def test_uses_only_carried_fertilizer(self) -> None:
        with patch(
            "agents.experimental_carried_fertilizer_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["carried_fertilizer_only"]
        )
        self.assertNotIn(
            "fertilizer_reserve_per_strawberry",
            premium.call_args.kwargs,
        )


if __name__ == "__main__":
    unittest.main()
