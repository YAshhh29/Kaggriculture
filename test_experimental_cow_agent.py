import ast
import unittest
from pathlib import Path

from agents.experimental_cow_agent import (
    LIVESTOCK_TILES,
    _collection_action,
    agent,
    decide,
)
from agents.experimental_hands_agent import _task_groups
from test_experimental_goose_agent import goose_tile
from test_main import observation, wheat_tile


def cow_tile(
    *,
    consecutive_unfed: int = 0,
    fed_today: bool = False,
    fertilizer_available: bool = False,
    yield_units: int = 0,
) -> dict:
    return {
        "kind": "PASTURE",
        "animal": "COW",
        "placed_day": 0,
        "yield_units": yield_units,
        "consecutive_unfed": consecutive_unfed,
        "fed_today": fed_today,
        "cared_today": False,
        "fertilizer_available": fertilizer_available,
        "pending_care_bonus": 0,
    }


def livestock_observation(*, day=0, hour=0, farmer=(4, 4), money=3_000):
    tiles = [[None for _ in range(10)] for _ in range(10)]
    state = observation(
        day=day,
        hour=hour,
        farmer=farmer,
        tiles=tiles,
        money=money,
    )
    state["farms"][0]["hands"] = [[4, 4], [5, 4]]
    state["private"]["inventories"] = [{}, {}, {}]
    return state


class ExperimentalCowAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).parent / "agents" / "experimental_cow_agent.py"
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(functions[-1], "agent")

    def test_opens_with_two_hands_both_animals_and_twelve_seeds(self) -> None:
        state = livestock_observation()
        state["farms"][0]["hands"] = []
        state["private"]["inventories"] = [{}]

        decision = agent(state)

        self.assertEqual(decision["farmer"], ["BUILD_COOP"])
        self.assertEqual(decision["market"].count(["HIRE"]), 2)
        self.assertIn(["BUY_ANIMAL", "GOOSE", 1], decision["market"])
        self.assertIn(["BUY_ANIMAL", "COW", 1], decision["market"])
        self.assertIn(["BUY_SEED", "WHEAT", 12], decision["market"])
        self.assertLessEqual(len(decision["market"]), 10)

    def test_can_evaluate_five_daily_hands_without_changing_default(self) -> None:
        state = livestock_observation()
        state["farms"][0]["hands"] = []
        state["private"]["inventories"] = [{}]

        default = agent(state)
        scaled = decide(state, target_daily_hands=5)

        self.assertEqual(default["market"].count(["HIRE"]), 2)
        self.assertEqual(scaled["market"].count(["HIRE"]), 5)

    def test_crop_scheduler_never_targets_livestock_tiles(self) -> None:
        state = livestock_observation()
        state["private"]["seeds"]["WHEAT"] = 12

        task_groups = _task_groups(
            0,
            state["farms"][0],
            state["private"],
            LIVESTOCK_TILES,
        )
        targets = {
            position
            for tasks in task_groups
            for position, _ in tasks
        }

        self.assertTrue(LIVESTOCK_TILES.isdisjoint(targets))

    def test_builds_pasture_after_goose_setup(self) -> None:
        state = livestock_observation(farmer=(3, 4))
        state["farms"][0]["tiles"][4][4] = goose_tile(fed_today=True)
        state["private"]["shed"]["COW"] = 1

        decision = agent(state)

        self.assertEqual(decision["farmer"], ["BUILD_PASTURE"])

    def test_feeds_each_due_animal_from_farmer_inventory(self) -> None:
        state = livestock_observation(farmer=(4, 4), day=1)
        state["farms"][0]["tiles"][4][4] = goose_tile(
            consecutive_unfed=1
        )
        state["farms"][0]["tiles"][4][3] = cow_tile(
            consecutive_unfed=1
        )
        state["private"]["inventories"][0]["WHEAT"] = 2

        self.assertEqual(agent(state)["farmer"], ["FEED"])

        state["farms"][0]["farmer"] = [3, 4]
        state["farms"][0]["tiles"][4][4]["fed_today"] = True
        self.assertEqual(agent(state)["farmer"], ["FEED"])

    def test_hand_feed_does_not_suppress_two_unit_feed_purchase(self) -> None:
        state = livestock_observation(day=1)
        state["farms"][0]["tiles"][4][4] = goose_tile(
            consecutive_unfed=1
        )
        state["farms"][0]["tiles"][4][3] = cow_tile(
            consecutive_unfed=1
        )
        state["private"]["inventories"][1]["WHEAT"] = 2

        self.assertIn(
            ["BUY_PRODUCT", "WHEAT", 2],
            agent(state)["market"],
        )

    def test_does_not_replace_lost_animals_after_opening_day(self) -> None:
        state = livestock_observation(day=2)
        state["farms"][0]["tiles"][4][4] = {"kind": "COOP"}
        state["farms"][0]["tiles"][4][3] = {"kind": "PASTURE"}

        market = agent(state)["market"]

        self.assertNotIn(["BUY_ANIMAL", "GOOSE", 1], market)
        self.assertNotIn(["BUY_ANIMAL", "COW", 1], market)

    def test_collects_fertilizer_before_partial_day_28_milk(self) -> None:
        state = livestock_observation(day=28, farmer=(3, 4))
        state["farms"][0]["tiles"][4][4] = goose_tile(
            fed_today=True,
            fertilizer_available=True,
            yield_units=2,
        )
        state["farms"][0]["tiles"][4][3] = cow_tile(
            fed_today=True,
            fertilizer_available=True,
            yield_units=3,
        )

        self.assertEqual(
            _collection_action(28, state["farms"][0]),
            ["COLLECT_FERTILIZER"],
        )

        state["farms"][0]["tiles"][4][4]["fertilizer_available"] = False
        state["farms"][0]["tiles"][4][3]["fertilizer_available"] = False
        self.assertEqual(
            _collection_action(28, state["farms"][0]),
            ["HARVEST"],
        )
        self.assertIsNone(_collection_action(29, state["farms"][0]))

    def test_stops_buying_feed_after_day_27(self) -> None:
        state = livestock_observation(day=28)
        state["farms"][0]["tiles"][4][4] = goose_tile(
            consecutive_unfed=1
        )
        state["farms"][0]["tiles"][4][3] = cow_tile(
            consecutive_unfed=1
        )

        self.assertNotIn(
            ["BUY_PRODUCT", "WHEAT", 2],
            agent(state)["market"],
        )

    def test_sells_all_livestock_products_from_shed(self) -> None:
        state = livestock_observation(day=10)
        state["farms"][0]["tiles"][4][4] = goose_tile(fed_today=True)
        state["farms"][0]["tiles"][4][3] = cow_tile(fed_today=True)
        state["private"]["shed"].update(
            {"EGG": 4, "MILK": 3, "FERTILIZER": 2}
        )

        market = agent(state)["market"]

        self.assertIn(["SELL", "EGG", 4], market)
        self.assertIn(["SELL", "MILK", 3], market)
        self.assertIn(["SELL", "FERTILIZER", 2], market)
        self.assertLessEqual(len(market), 10)

    def test_hands_water_while_farmer_feeds(self) -> None:
        state = livestock_observation(day=1)
        state["farms"][0]["hands"] = [[0, 0], [1, 0]]
        state["farms"][0]["tiles"][4][4] = goose_tile(
            consecutive_unfed=1
        )
        state["farms"][0]["tiles"][4][3] = cow_tile(fed_today=True)
        state["farms"][0]["tiles"][0][0] = wheat_tile()
        state["farms"][0]["tiles"][0][1] = wheat_tile()
        state["private"]["inventories"][0]["WHEAT"] = 1

        decision = agent(state)

        self.assertEqual(decision["farmer"], ["FEED"])
        self.assertEqual(decision["hands"], [["WATER"], ["WATER"]])


if __name__ == "__main__":
    unittest.main()