import unittest

from rl.candidate_b import (
    _premium_ordering,
    build_candidate_b_agent,
)
from tests.test_experimental_scale_agent import scale_observation


def fixed_baseline(action):
    def decide(observation):
        del observation
        return {
            "farmer": list(action.get("farmer", ["PASS"])),
            "hands": [list(item) for item in action.get("hands", [])],
            "market": [list(item) for item in action.get("market", [])],
        }

    return decide


class CandidateBTests(unittest.TestCase):
    def test_premium_ordering_preserves_quantities_and_routes(self) -> None:
        state = scale_observation(day=20, hour=0)
        state["step"] = 480
        state["market"]["prices"] = {
            "MELON": 250,
            "MILK": 160,
            "WOOL": 200,
            "STRAWBERRY": 120,
        }
        baseline = fixed_baseline(
            {
                "farmer": ["PASS"],
                "hands": [],
                "market": [
                    ["SELL", "MILK", 2],
                    ["SELL", "MELON", 2],
                ],
            }
        )

        decision = build_candidate_b_agent(baseline=baseline)(state)

        self.assertEqual(decision["farmer"], ["PASS"])
        self.assertEqual(decision["hands"], [])
        self.assertEqual(
            sorted((order[1], order[2]) for order in decision["market"]),
            [("MELON", 2), ("MILK", 2)],
        )

    def test_no_premium_signal_preserves_baseline_market(self) -> None:
        state = scale_observation(day=5, hour=0)
        state["step"] = 120
        baseline_action = {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["SELL", "WHEAT", 4]],
        }

        decision = build_candidate_b_agent(
            baseline=fixed_baseline(baseline_action),
        )(state)

        self.assertEqual(decision["market"], baseline_action["market"])

    def test_mixed_market_orders_preserve_financing_sequence(self) -> None:
        state = scale_observation(day=20, hour=0)
        state["step"] = 480
        baseline_market = [
            ["SELL", "WHEAT", 4],
            ["BUY_PRODUCT", "WHEAT", 2],
            ["SELL", "MELON", 2],
        ]
        decision = build_candidate_b_agent(
            baseline=fixed_baseline(
                {
                    "farmer": ["PASS"],
                    "hands": [],
                    "market": baseline_market,
                }
            ),
        )(state)

        self.assertEqual(decision["market"], baseline_market)

    def test_market_ordering_never_changes_total_sale_quantity(self) -> None:
        state = scale_observation(day=20, hour=0)
        state["step"] = 480
        state["market"]["inventory"] = {
            "MELON": 10_000,
            "MILK": 10_000,
        }
        orders = [
            ["SELL", "MILK", 3],
            ["SELL", "MELON", 2],
        ]

        ordered = _premium_ordering(state, orders)

        self.assertEqual(
            sorted((order[1], order[2]) for order in ordered),
            sorted((order[1], order[2]) for order in orders),
        )


if __name__ == "__main__":
    unittest.main()