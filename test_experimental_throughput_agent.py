import unittest

from agents.experimental_throughput_agent import (
    HIRE_COSTS,
    MAX_WHEAT_PER_PAIR,
    _affordable_market_orders,
    _animal_crew_size,
    _hand_target,
)
from test_experimental_scale_agent import scale_observation


class ExperimentalThroughputAgentTests(unittest.TestCase):
    def test_replay_grounded_labor_and_crew_stages(self) -> None:
        self.assertEqual(_hand_target(0), 4)
        self.assertEqual(_hand_target(6), 8)
        self.assertEqual(_hand_target(11), 12)
        self.assertEqual(_hand_target(29), 8)
        self.assertEqual(_animal_crew_size(0), 3)
        self.assertEqual(_animal_crew_size(6), 4)
        self.assertEqual(_animal_crew_size(11), 6)
        self.assertEqual(MAX_WHEAT_PER_PAIR, 18)
        self.assertEqual(HIRE_COSTS[12], 233)

    def test_hiring_precedes_livestock_and_unaffordable_sheep_is_dropped(
        self,
    ) -> None:
        state = scale_observation(day=8, money=159)
        state["farms"][0]["hands"] = [[4, 4] for _ in range(7)]
        state["market"] = {"prices": {"WHEAT": 25}}

        orders = _affordable_market_orders(
            state,
            [
                ["BUY_ANIMAL", "SHEEP", 2],
                ["HIRE"],
                ["HIRE"],
                ["BUY_SEED", "WHEAT", 1],
            ],
        )

        self.assertEqual(orders[:2], [["HIRE"], ["HIRE"]])
        self.assertIn(["BUY_SEED", "WHEAT", 1], orders)
        self.assertFalse(any(order[0] == "BUY_ANIMAL" for order in orders))


if __name__ == "__main__":
    unittest.main()
