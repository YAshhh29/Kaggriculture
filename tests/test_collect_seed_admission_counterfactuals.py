import unittest
from unittest.mock import patch

from research.collection.collect_seed_admission_counterfactuals import (
    _outcome_utility,
    add_extra_wheat_seed,
    extra_seed_agent,
)
from tests.test_experimental_scale_agent import scale_observation


class SeedAdmissionCounterfactualTests(unittest.TestCase):
    def test_increments_existing_wheat_order(self) -> None:
        action = {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", 2], ["HIRE"]],
        }

        extra = add_extra_wheat_seed(action)

        self.assertEqual(extra["market"][0], ["BUY_SEED", "WHEAT", 3])
        self.assertEqual(action["market"][0], ["BUY_SEED", "WHEAT", 2])

    def test_appends_without_exceeding_market_cap(self) -> None:
        action = {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
        full = {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["HIRE"] for _ in range(10)],
        }

        self.assertEqual(
            add_extra_wheat_seed(action)["market"][-1],
            ["BUY_SEED", "WHEAT", 1],
        )
        self.assertIsNone(add_extra_wheat_seed(full))

    def test_win_first_utility_dominates_margin(self) -> None:
        win = {"result": "win", "terminal_margin": 1}
        loss = {"result": "loss", "terminal_margin": 100_000}

        self.assertGreater(_outcome_utility(win), _outcome_utility(loss))

    def test_extra_policy_requests_one_incremental_wheat_seed(self) -> None:
        with patch(
            "research.collection.collect_seed_admission_counterfactuals.decide_premium"
        ) as premium:
            extra_seed_agent(scale_observation(day=12))

        self.assertEqual(
            premium.call_args.kwargs["extra_wheat_seed_buffer"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
