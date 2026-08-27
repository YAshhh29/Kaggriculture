import unittest
from collections import Counter
from unittest.mock import patch

from agents.experimental_cow_heavy_deadline_agent import (
    COW_HEAVY_ANIMAL_PLANS,
    decide,
)
from test_experimental_scale_agent import scale_observation


class ExperimentalCowHeavyDeadlineAgentTests(unittest.TestCase):
    def test_uses_ten_cows_and_two_sheep_on_same_twelve_tiles(self) -> None:
        self.assertEqual(
            Counter(
                str(plan["animal"])
                for plan in COW_HEAVY_ANIMAL_PLANS
            ),
            {"COW": 10, "SHEEP": 2},
        )
        self.assertEqual(
            len({tuple(plan["position"]) for plan in COW_HEAVY_ANIMAL_PLANS}),
            12,
        )

    def test_passes_cow_heavy_plan_to_safe_scheduler(self) -> None:
        with patch(
            "agents.experimental_cow_heavy_deadline_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=9))

        self.assertIs(
            premium.call_args.kwargs["animal_plans"],
            COW_HEAVY_ANIMAL_PLANS,
        )


if __name__ == "__main__":
    unittest.main()
