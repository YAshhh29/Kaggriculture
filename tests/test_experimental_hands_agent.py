import ast
import unittest
from pathlib import Path

from agents.experimental_hands_agent import agent, decide
from tests.test_experimental_goose_agent import goose_tile
from tests.test_main import observation, wheat_tile


def staffed_observation(**kwargs):
    state = observation(**kwargs)
    state["farms"][0]["hands"] = [[1, 0], [2, 0]]
    state["private"]["inventories"] = [{}, {}, {}]
    return state


class ExperimentalHandsAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).resolve().parents[1] / "agents" / "experimental_hands_agent.py"
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(functions[-1], "agent")

    def test_hires_two_hands_and_buys_twelve_seeds_at_hour_zero(self) -> None:
        decision = agent(observation(money=3_000))

        self.assertEqual(decision["market"].count(["HIRE"]), 2)
        self.assertIn(["BUY_SEED", "WHEAT", 12], decision["market"])

    def test_can_evaluate_a_different_wheat_workload(self) -> None:
        decision = decide(
            observation(money=3_000),
            target_wheat_tiles=16,
        )

        self.assertIn(["BUY_SEED", "WHEAT", 16], decision["market"])

    def test_does_not_rehire_after_hour_zero(self) -> None:
        decision = agent(observation(hour=1, money=3_000))

        self.assertNotIn(["HIRE"], decision["market"])

    def test_assigns_distinct_water_actions_to_all_workers(self) -> None:
        tiles = [[None for _ in range(3)] for _ in range(3)]
        for x in range(3):
            tiles[0][x] = wheat_tile()
        tiles[2][2] = goose_tile(fed_today=True)
        state = staffed_observation(tiles=tiles)

        decision = agent(state)

        self.assertEqual(decision["farmer"], ["WATER"])
        self.assertEqual(decision["hands"], [["WATER"], ["WATER"]])

    def test_farmer_services_goose_while_hands_water(self) -> None:
        tiles = [[None for _ in range(3)] for _ in range(3)]
        tiles[0][0] = goose_tile(consecutive_unfed=1)
        tiles[0][1] = wheat_tile()
        tiles[0][2] = wheat_tile()
        state = staffed_observation(tiles=tiles)
        state["private"]["inventories"][0]["WHEAT"] = 1

        decision = agent(state)

        self.assertEqual(decision["farmer"], ["FEED"])
        self.assertEqual(decision["hands"], [["WATER"], ["WATER"]])

    def test_hand_wheat_does_not_suppress_farmer_feed_purchase(self) -> None:
        tiles = [[None for _ in range(3)] for _ in range(3)]
        tiles[0][0] = goose_tile(consecutive_unfed=1)
        state = staffed_observation(tiles=tiles)
        state["private"]["inventories"][1]["WHEAT"] = 1

        decision = agent(state)

        self.assertIn(["BUY_PRODUCT", "WHEAT", 1], decision["market"])

    def test_limits_same_turn_planting_to_available_seeds(self) -> None:
        tiles = [[None for _ in range(3)] for _ in range(3)]
        tiles[2][2] = goose_tile(fed_today=True)
        state = staffed_observation(tiles=tiles, seeds=2)

        decision = agent(state)
        plant_actions = [
            action
            for action in [decision["farmer"], *decision["hands"]]
            if action == ["PLANT", "WHEAT"]
        ]

        self.assertEqual(len(plant_actions), 2)

if __name__ == "__main__":
    unittest.main()