import ast
import unittest
from pathlib import Path

from agents.experimental_ridge_agent import (
    MINIMUM_PREDICTED_SELL_ADVANTAGE,
    _predicted_sell_advantage,
    agent,
)
from test_main import observation, wheat_tile


class ExperimentalRidgeAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).parent / "agents" / "experimental_ridge_agent.py"
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(functions[-1], "agent")

    def test_model_can_choose_hold_and_sell(self) -> None:
        hold = self._observation(day=5, price=29, shed=24)
        sell = self._observation(day=23, price=40, shed=60, money=7_000)

        self.assertLess(_predicted_sell_advantage(hold), 0)
        self.assertGreater(
            _predicted_sell_advantage(sell),
            MINIMUM_PREDICTED_SELL_ADVANTAGE,
        )
        self.assertNotIn(["SELL", "WHEAT", 24], agent(hold)["market"])
        self.assertIn(["SELL", "WHEAT", 60], agent(sell)["market"])

    def test_inventory_cap_and_liquidation_override_model(self) -> None:
        cap = self._observation(day=5, price=29, shed=72)
        liquidation = self._observation(day=25, price=29, shed=4)

        self.assertIn(["SELL", "WHEAT", 72], agent(cap)["market"])
        self.assertIn(["SELL", "WHEAT", 4], agent(liquidation)["market"])

    def test_prices_outside_training_range_fall_back_to_v9(self) -> None:
        low = self._observation(day=5, price=27, shed=24)
        high = self._observation(day=5, price=41, shed=24)

        self.assertNotIn(["SELL", "WHEAT", 24], agent(low)["market"])
        self.assertIn(["SELL", "WHEAT", 24], agent(high)["market"])

    @staticmethod
    def _observation(
        *, day: int, price: int, shed: int, money: int = 3_000
    ) -> dict:
        tiles = [[None for _ in range(3)] for _ in range(3)]
        for index in range(6):
            tiles[index // 3][index % 3] = wheat_tile()
        result = observation(
            day=day,
            tiles=tiles,
            money=money,
            shed_wheat=shed,
            wheat_price=price,
        )
        result["market"]["inventory"]["WHEAT"] = 9_900
        return result


if __name__ == "__main__":
    unittest.main()