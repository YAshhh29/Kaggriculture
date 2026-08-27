import unittest
from unittest.mock import patch

from agents.experimental_anticipatory_care_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalAnticipatoryCareAgentTests(unittest.TestCase):
    def test_enables_anticipatory_care(self) -> None:
        with patch(
            "agents.experimental_anticipatory_care_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["anticipate_daily_feed_for_care"]
        )


if __name__ == "__main__":
    unittest.main()
