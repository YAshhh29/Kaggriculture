import ast
import unittest
from pathlib import Path

from main import agent, decide


def wheat_tile(
    *,
    planted_day: int = 0,
    watered_today: bool = False,
    consecutive_unwatered: int = 0,
    yield_units: int = 0,
) -> dict:
    return {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": planted_day,
        "watered_today": watered_today,
        "consecutive_unwatered": consecutive_unwatered,
        "yield_units": yield_units,
    }


def observation(
    *,
    day: int = 0,
    hour: int = 0,
    farmer: tuple[int, int] = (0, 0),
    tiles: list[list[object]] | None = None,
    money: int = 3_000,
    seeds: int = 0,
    shed_wheat: int = 0,
    wheat_price: int = 25,
) -> dict:
    board = tiles or [[None for _ in range(3)] for _ in range(3)]
    farm = {
        "money": money,
        "tiles": board,
        "farmer": list(farmer),
        "hands": [],
        "unlocked_quadrants": ["NW"],
        "hires_today": 0,
    }
    return {
        "player": 0,
        "day": day,
        "hour": hour,
        "farms": [farm, farm],
        "market": {"inventory": {}, "prices": {"WHEAT": wheat_price}},
        "town": {"unlocked_shops": []},
        "private": {
            "shed": {"WHEAT": shed_wheat},
            "seeds": {"WHEAT": seeds},
            "inventories": [{}],
        },
    }


class AgentDecisionTests(unittest.TestCase):
    def test_agent_is_last_function_for_kaggle_file_loader(self) -> None:
        source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        functions = [
            node.name
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        self.assertEqual(functions[-1], "agent")

    def test_buys_six_seeds_on_first_turn(self) -> None:
        decision = agent(observation())

        self.assertEqual(decision["farmer"], ["PASS"])
        self.assertEqual(decision["market"], [["BUY_SEED", "WHEAT", 6]])

    def test_can_evaluate_an_eight_plot_experiment(self) -> None:
        decision = decide(observation(), target_wheat_tiles=8)

        self.assertEqual(decision["market"], [["BUY_SEED", "WHEAT", 8]])

    def test_last_planting_day_is_inclusive(self) -> None:
        decision = agent(observation(day=24, seeds=1))

        self.assertEqual(decision["farmer"], ["PLANT", "WHEAT"])

    def test_stops_buying_and_planting_after_cutoff(self) -> None:
        purchase_decision = agent(observation(day=25))
        planting_decision = agent(observation(day=25, seeds=1))

        self.assertEqual(purchase_decision["market"], [])
        self.assertEqual(planting_decision["farmer"], ["PASS"])

    def test_plants_when_standing_on_an_empty_tile(self) -> None:
        decision = agent(observation(seeds=1))

        self.assertEqual(decision["farmer"], ["PLANT", "WHEAT"])

    def test_moves_toward_nearest_unwatered_wheat(self) -> None:
        tiles = [[None for _ in range(3)] for _ in range(3)]
        tiles[1][2] = wheat_tile()

        decision = agent(observation(tiles=tiles, seeds=3))

        self.assertEqual(decision["farmer"], ["EAST"])

    def test_waters_before_harvesting_mature_wheat(self) -> None:
        tiles = [[wheat_tile(yield_units=6)]]

        decision = agent(observation(day=4, tiles=tiles, seeds=3))

        self.assertEqual(decision["farmer"], ["WATER"])

    def test_harvests_mature_watered_wheat(self) -> None:
        tiles = [[wheat_tile(watered_today=True, yield_units=6)]]

        decision = agent(observation(day=4, tiles=tiles, seeds=3))

        self.assertEqual(decision["farmer"], ["HARVEST"])

    def test_candidate_finishes_current_mature_tile_before_moving(self) -> None:
        tiles = [[None for _ in range(3)] for _ in range(3)]
        tiles[0][0] = wheat_tile(watered_today=True, yield_units=4)
        tiles[0][1] = wheat_tile()

        decision = decide(
            observation(day=4, tiles=tiles, seeds=4),
            harvest_watered_current_first=True,
        )

        self.assertEqual(decision["farmer"], ["HARVEST"])

    def test_sells_shed_wheat_and_replenishes_seeds(self) -> None:
        decision = agent(observation(shed_wheat=6, wheat_price=35))

        self.assertEqual(
            decision["market"],
            [["SELL", "WHEAT", 6], ["BUY_SEED", "WHEAT", 6]],
        )

    def test_candidate_holds_wheat_below_price_threshold(self) -> None:
        decision = decide(
            observation(shed_wheat=24, wheat_price=30),
            minimum_wheat_sale_price=35,
            maximum_wheat_holdings=72,
            wheat_liquidation_day=25,
        )

        self.assertNotIn(["SELL", "WHEAT", 24], decision["market"])

    def test_candidate_sells_when_price_reaches_threshold(self) -> None:
        decision = decide(
            observation(shed_wheat=24, wheat_price=35),
            minimum_wheat_sale_price=35,
            maximum_wheat_holdings=72,
            wheat_liquidation_day=25,
        )

        self.assertIn(["SELL", "WHEAT", 24], decision["market"])

    def test_candidate_sells_at_inventory_safety_cap(self) -> None:
        decision = decide(
            observation(shed_wheat=72, wheat_price=30),
            minimum_wheat_sale_price=35,
            maximum_wheat_holdings=72,
            wheat_liquidation_day=25,
        )

        self.assertIn(["SELL", "WHEAT", 72], decision["market"])

    def test_candidate_liquidates_after_deadline(self) -> None:
        decision = decide(
            observation(day=25, shed_wheat=4, wheat_price=30),
            minimum_wheat_sale_price=35,
            maximum_wheat_holdings=72,
            wheat_liquidation_day=25,
        )

        self.assertIn(["SELL", "WHEAT", 4], decision["market"])


if __name__ == "__main__":
    unittest.main()
