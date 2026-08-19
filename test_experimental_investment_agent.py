import ast
import unittest
from pathlib import Path

from experimental_investment_agent import (
    _pressure_targets,
    _investment_market_orders,
    agent,
    decide,
)
from test_experimental_scale_agent import scale_observation


class ExperimentalInvestmentAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).with_name("experimental_investment_agent.py")
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]
        self.assertEqual(functions[-1], "agent")

    def test_opening_matches_leader_investment_shape(self) -> None:
        decision = agent(scale_observation())

        self.assertEqual(decision["market"].count(["HIRE"]), 5)
        self.assertIn(["BUY_ANIMAL", "COW", 2], decision["market"])
        self.assertIn(["BUY_ANIMAL", "SHEEP", 2], decision["market"])
        self.assertLessEqual(len(decision["market"]), 10)

    def test_can_screen_lower_workforce_and_crop_load(self) -> None:
        state = scale_observation(day=8)
        state["farms"][0]["hands"] = []
        state["private"]["inventories"] = [{}]

        default = agent(state)
        screened = decide(
            state,
            target_wheat_tiles=12,
            target_daily_hands=10,
        )

        self.assertGreaterEqual(default["market"].count(["HIRE"]), 1)
        self.assertLessEqual(
            screened["market"].count(["HIRE"]),
            default["market"].count(["HIRE"]),
        )
        self.assertNotIn(["BUY_SEED", "WHEAT", 24], screened["market"])

    def test_market_prioritizes_feed_land_animals_before_hires(self) -> None:
        orders = _investment_market_orders(
            [["SELL", "MILK", 2]],
            [
                ["BUY_ANIMAL", "SHEEP", 2],
                ["BUY_PRODUCT", "WHEAT", 4],
            ],
            [["BUY_LAND"]],
            [["HIRE"], ["HIRE"]],
            [["BUY_SEED", "WHEAT", 24]],
        )

        self.assertEqual(
            [order[0] for order in orders],
            [
                "SELL",
                "BUY_PRODUCT",
                "BUY_LAND",
                "BUY_ANIMAL",
                "HIRE",
                "HIRE",
                "BUY_SEED",
            ],
        )

    def test_opponent_animals_reduce_our_investment_target(self) -> None:
        state = scale_observation(day=8)
        opponent = state["farms"][1]
        for index in range(8):
            x = index % 4
            y = index // 4
            opponent["tiles"][y][x] = {
                "kind": "PASTURE",
                "animal": "COW",
            }

        cows, sheep, hands, land = _pressure_targets(state, 0, 10)

        self.assertEqual(cows + sheep, 10)
        self.assertLessEqual(hands, 10)
        self.assertLessEqual(land, 1)

        cows, sheep, _, _ = _pressure_targets(state, 0, 10, 17)
        self.assertEqual(cows + sheep, 9)

    def test_pressure_target_never_abandons_owned_animals(self) -> None:
        state = scale_observation(day=10)
        for farm in state["farms"]:
            for index in range(8):
                x = index % 4
                y = index // 4
                farm["tiles"][y][x] = {
                    "kind": "PASTURE",
                    "animal": "COW" if index < 6 else "SHEEP",
                }

        cows, sheep, _, _ = _pressure_targets(state, 0, 10)

        self.assertGreaterEqual(cows, 6)
        self.assertGreaterEqual(sheep, 2)


if __name__ == "__main__":
    unittest.main()