import unittest
from unittest.mock import patch

from agents.experimental_paired_service_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalPairedServiceAgentTests(unittest.TestCase):
    def test_enables_colocated_feed_care_pairing(self) -> None:
        with patch(
            "agents.experimental_paired_service_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["pair_colocated_feed_care"]
        )


if __name__ == "__main__":
    unittest.main()
