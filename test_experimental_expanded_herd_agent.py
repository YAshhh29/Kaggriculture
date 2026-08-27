import unittest
from collections import Counter
from unittest.mock import patch

from agents.experimental_expanded_herd_agent import (
    EXPANDED_HERD_PLANS,
    EXTRA_COW_PLANS,
    decide,
)
from test_experimental_scale_agent import scale_observation


class ExperimentalExpandedHerdAgentTests(unittest.TestCase):
    def test_adds_two_day_eleven_cows(self) -> None:
        self.assertEqual(
            Counter(str(plan["animal"]) for plan in EXPANDED_HERD_PLANS),
            {"COW": 8, "SHEEP": 6},
        )
        self.assertTrue(
            all(plan["activation_day"] == 11 for plan in EXTRA_COW_PLANS)
        )

    def test_passes_expanded_herd_to_safe_scheduler(self) -> None:
        with patch(
            "agents.experimental_expanded_herd_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=11))

        self.assertIs(
            premium.call_args.kwargs["animal_plans"],
            EXPANDED_HERD_PLANS,
        )


if __name__ == "__main__":
    unittest.main()
