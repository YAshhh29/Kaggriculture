import unittest
from unittest.mock import patch

from agents.experimental_paired_incremental_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalPairedIncrementalAgentTests(unittest.TestCase):
    def test_combines_pairing_with_one_funded_extra_seed(self) -> None:
        state = scale_observation(day=12, money=3000)
        state["farms"][0]["unlocked_quadrants"].extend(["NE", "SW"])
        with patch(
            "agents.experimental_paired_incremental_agent.decide_premium"
        ) as premium:
            decide(state)

        self.assertTrue(
            premium.call_args.kwargs["pair_colocated_feed_care"]
        )
        self.assertEqual(
            premium.call_args.kwargs["extra_wheat_seed_buffer"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
