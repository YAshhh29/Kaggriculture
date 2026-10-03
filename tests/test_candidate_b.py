import unittest

from candidates.candidate_b import (
    _land_priority_ordering,
    _sequential_affordability_ordering,
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
    def test_premium_only_batch_preserves_quantities_and_routes(self) -> None:
        state = scale_observation(day=20, hour=0)
        state["step"] = 480
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

    def test_without_market_state_preserves_baseline_order(self) -> None:
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

        ordered = _sequential_affordability_ordering(state, orders)

        self.assertEqual(
            sorted((order[1], order[2]) for order in ordered),
            sorted((order[1], order[2]) for order in orders),
        )

    def test_moves_premium_sell_before_a_purchase_it_can_fund(self) -> None:
        state = scale_observation(day=20, hour=0, money=50)
        state["step"] = 480
        state["market"]["inventory"] = {"MELON": 9_000, "WHEAT": 9_999}
        state["private"]["shed"] = {"MELON": 2}
        orders = [
            ["BUY_PRODUCT", "WHEAT", 3],
            ["SELL", "MELON", 2],
        ]

        ordered = _sequential_affordability_ordering(state, orders)

        self.assertEqual(
            ordered,
            [["SELL", "MELON", 2], ["BUY_PRODUCT", "WHEAT", 3]],
        )
        self.assertEqual(
            sorted((order[1], order[2]) for order in ordered),
            sorted((order[1], order[2]) for order in orders),
        )

    def test_moves_wheat_sell_before_a_hire_it_can_fund(self) -> None:
        # This is the pattern actually observed in Candidate A's real games:
        # a WHEAT sell trailing an unrelated spend (HIRE here), 858 times
        # across 33 captured episodes -- not a premium sell (0 times).
        state = scale_observation(day=20, hour=0, money=50)
        state["step"] = 480
        state["farms"][0]["hires_today"] = 10  # hire #10 costs fib(10)=89
        state["market"]["inventory"] = {"WHEAT": 9_997}
        state["private"]["shed"] = {"WHEAT": 3}
        orders = [
            ["HIRE"],
            ["SELL", "WHEAT", 3],
        ]

        ordered = _sequential_affordability_ordering(state, orders)

        self.assertEqual(ordered, [["SELL", "WHEAT", 3], ["HIRE"]])

    def test_never_moves_a_sell_across_a_buy_seed_barrier(self) -> None:
        # A live paired-game gate (not just captured replay) found that
        # rescuing a BUY_SEED purchase this same way -- moving a WHEAT sell
        # ahead of it, at a turn also containing a walled-off BUY_ANIMAL --
        # still cost -15302 and flipped a win into a loss against a live
        # mirror-match opponent (seed 300 vs distilled-calendar), because
        # reordering our own trades shifts the price a *live* opponent's
        # own concurrent trades land on -- an effect the isolated
        # single-player safety simulation cannot see. So BUY_SEED is walled
        # off too, alongside BUY_ANIMAL; only HIRE and BUY_PRODUCT remain
        # rescue-eligible.
        state = scale_observation(day=20, hour=0, money=50)
        state["step"] = 480
        state["market"]["inventory"] = {"WHEAT": 9_997}
        state["private"]["shed"] = {"WHEAT": 3}
        orders = [
            ["BUY_SEED", "STRAWBERRY", 1],
            ["SELL", "WHEAT", 3],
        ]

        ordered = _sequential_affordability_ordering(state, orders)

        self.assertEqual(ordered, orders)

    def test_never_moves_a_sell_across_a_buy_animal_barrier(self) -> None:
        # A rescued HIRE is fine (Candidate A already re-aligns to the live
        # hand count), but a rescued BUY_ANIMAL is not: the fixed calendar
        # never schedules care for an animal it didn't plan for, and it can
        # block the calendar's own later, already-planned animal purchase.
        # The sell must still be free to jump the (non-barrier) HIRE.
        state = scale_observation(day=20, hour=0, money=20)
        state["step"] = 480
        state["farms"][0]["hires_today"] = 10  # hire #10 costs fib(10)=89
        state["market"]["inventory"] = {"WHEAT": 9_997}
        state["private"]["shed"] = {"WHEAT": 3}
        orders = [
            ["BUY_ANIMAL", "SHEEP", 1],
            ["HIRE"],
            ["SELL", "WHEAT", 3],
        ]

        ordered = _sequential_affordability_ordering(state, orders)

        self.assertEqual(
            ordered,
            [["BUY_ANIMAL", "SHEEP", 1], ["SELL", "WHEAT", 3], ["HIRE"]],
        )

    def test_keeps_baseline_when_reorder_would_starve_a_later_purchase(
        self,
    ) -> None:
        # BUY_LAND(1000) then BUY_ANIMAL SHEEP(500) with money=900 and a
        # premium sell worth ~541 in between: moving the sell first lets
        # BUY_LAND succeed (900+541=1441 >= 1000), but then only 441 is left
        # for the SHEEP, which succeeded in the original order (1441 >=
        # 500). That is a real purchase-fulfilment regression, so the
        # reorder must be rejected outright.
        state = scale_observation(day=20, hour=0, money=900)
        state["farms"][0]["unlocked_quadrants"] = ["NW"]
        state["market"]["inventory"] = {"MELON": 9_990}
        state["private"]["shed"] = {"MELON": 2}
        orders = [
            ["BUY_LAND"],
            ["SELL", "MELON", 2],
            ["BUY_ANIMAL", "SHEEP", 1],
        ]

        ordered = _sequential_affordability_ordering(state, orders)

        self.assertEqual(ordered, orders)

    def test_does_not_reorder_past_terminal_market_step(self) -> None:
        state = scale_observation(day=30, hour=0, money=50)
        state["step"] = 717
        state["market"]["inventory"] = {"MELON": 9_000, "WHEAT": 9_999}
        state["private"]["shed"] = {"MELON": 2}
        orders = [
            ["BUY_PRODUCT", "WHEAT", 3],
            ["SELL", "MELON", 2],
        ]

        ordered = _sequential_affordability_ordering(state, orders)

        self.assertEqual(ordered, orders)

    def test_can_disable_land_priority_for_ablation(self) -> None:
        state = scale_observation(day=8, hour=9, money=2192)
        state["step"] = 200
        baseline_market = [["BUY_PRODUCT", "WHEAT", 16], ["BUY_LAND"]]
        decision = build_candidate_b_agent(
            baseline=fixed_baseline(
                {
                    "farmer": ["PASS"],
                    "hands": [],
                    "market": baseline_market,
                }
            ),
            enable_land_priority=False,
        )(
            {
                **state,
                "market": {
                    **state["market"],
                    "inventory": {"WHEAT": 9_945},
                },
            }
        )

        self.assertEqual(decision["market"], baseline_market)

    def test_default_agent_keeps_land_priority_disabled(self) -> None:
        state = scale_observation(day=8, hour=9, money=2192)
        state["step"] = 200
        baseline_market = [["BUY_PRODUCT", "WHEAT", 16], ["BUY_LAND"]]
        decision = build_candidate_b_agent(
            baseline=fixed_baseline(
                {
                    "farmer": ["PASS"],
                    "hands": [],
                    "market": baseline_market,
                }
            ),
        )(
            {
                **state,
                "market": {
                    **state["market"],
                    "inventory": {"WHEAT": 9_945},
                },
            }
        )

        self.assertEqual(decision["market"], baseline_market)

    def test_moves_land_purchase_before_a_product_buy_that_starves_it(
        self,
    ) -> None:
        # Live episodes 105061000/105062726: the calendar's *only* scripted
        # BUY_LAND for the third quadrant (record 200, both games, both
        # seats) sat behind a BUY_PRODUCT WHEAT 16 that drained the money
        # it needed. The purchase failed silently, was never retried, and
        # the quadrant stayed locked for the rest of the episode. These are
        # the exact real numbers from episode 105061000 at that turn.
        state = scale_observation(day=8, hour=9, money=2192)
        state["farms"][0]["unlocked_quadrants"] = ["NW", "NE"]
        state["farms"][0]["hires_today"] = 8
        state["market"]["inventory"] = {"WHEAT": 9_945}
        state["private"]["shed"] = {"WHEAT": 2}
        orders = [["BUY_PRODUCT", "WHEAT", 16], ["BUY_LAND"]]

        ordered = _land_priority_ordering(state, orders)

        self.assertEqual(ordered, [["BUY_LAND"], ["BUY_PRODUCT", "WHEAT", 16]])

    def test_keeps_baseline_when_land_purchase_already_affordable(
        self,
    ) -> None:
        state = scale_observation(day=8, hour=9, money=100_000)
        state["farms"][0]["unlocked_quadrants"] = ["NW", "NE"]
        state["market"]["inventory"] = {"WHEAT": 9_945}
        orders = [["BUY_PRODUCT", "WHEAT", 16], ["BUY_LAND"]]

        ordered = _land_priority_ordering(state, orders)

        self.assertEqual(ordered, orders)

    def test_land_priority_never_moves_a_sell(self) -> None:
        state = scale_observation(day=8, hour=9, money=1_500)
        state["farms"][0]["unlocked_quadrants"] = ["NW", "NE"]
        state["market"]["inventory"] = {"WHEAT": 9_945, "MELON": 9_990}
        state["private"]["shed"] = {"MELON": 2}
        orders = [
            ["SELL", "MELON", 2],
            ["BUY_PRODUCT", "WHEAT", 16],
            ["BUY_LAND"],
        ]

        ordered = _land_priority_ordering(state, orders)

        self.assertEqual(
            ordered,
            [["SELL", "MELON", 2], ["BUY_LAND"], ["BUY_PRODUCT", "WHEAT", 16]],
        )

    def test_does_not_reorder_land_past_terminal_market_step(self) -> None:
        state = scale_observation(day=30, hour=0, money=2192)
        state["step"] = 717
        state["farms"][0]["unlocked_quadrants"] = ["NW", "NE"]
        state["market"]["inventory"] = {"WHEAT": 9_945}
        orders = [["BUY_PRODUCT", "WHEAT", 16], ["BUY_LAND"]]

        ordered = _land_priority_ordering(state, orders)

        self.assertEqual(ordered, orders)

    def test_full_agent_rescues_the_real_failing_turn(self) -> None:
        state = scale_observation(day=8, hour=9, money=2192)
        state["step"] = 199
        state["farms"][0]["unlocked_quadrants"] = ["NW", "NE"]
        state["farms"][0]["hires_today"] = 8
        state["market"]["inventory"] = {"WHEAT": 9_945}
        state["private"]["shed"] = {"WHEAT": 2}
        baseline_action = {
            "farmer": ["NORTH"],
            "hands": [],
            "market": [["BUY_PRODUCT", "WHEAT", 16], ["BUY_LAND"]],
        }

        decision = build_candidate_b_agent(
            baseline=fixed_baseline(baseline_action),
            enable_land_priority=True,
        )(state)

        self.assertEqual(
            decision["market"],
            [["BUY_LAND"], ["BUY_PRODUCT", "WHEAT", 16]],
        )


if __name__ == "__main__":
    unittest.main()
