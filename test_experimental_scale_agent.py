import ast
import unittest
from pathlib import Path

from experimental_scale_agent import (
    ANIMAL_PLANS,
    LIVESTOCK_TILES,
    _selected_animal_plans,
    _staged_animal_plans,
    _land_orders,
    _hire_orders,
    _quadrant,
    _unlocked_animal_plans,
    agent,
    decide,
)
from test_experimental_cow_agent import cow_tile
from test_main import observation, wheat_tile


def sheep_tile(**kwargs):
    tile = cow_tile(**kwargs)
    tile["animal"] = "SHEEP"
    return tile


def scale_observation(*, day=0, hour=0, money=3_000):
    tiles = [[None for _ in range(10)] for _ in range(10)]
    state = observation(
        day=day,
        hour=hour,
        farmer=(4, 4),
        tiles=tiles,
        money=money,
    )
    return state


def place_animals(state, *, due=False, fed=False, fertilizer=False, yields=0):
    for plan in ANIMAL_PLANS:
        x, y = plan["position"]
        factory = cow_tile if plan["animal"] == "COW" else sheep_tile
        state["farms"][0]["tiles"][y][x] = factory(
            consecutive_unfed=1 if due else 0,
            fed_today=fed,
            fertilizer_available=fertilizer,
            yield_units=yields,
        )


class ExperimentalScaleAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).with_name("experimental_scale_agent.py")
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(functions[-1], "agent")

    def test_opens_with_eight_hands_two_cows_and_two_sheep(self) -> None:
        decision = agent(scale_observation())

        self.assertEqual(decision["farmer"], ["BUILD_PASTURE"])
        self.assertEqual(decision["market"].count(["HIRE"]), 8)
        self.assertIn(["BUY_ANIMAL", "COW", 2], decision["market"])
        self.assertIn(["BUY_ANIMAL", "SHEEP", 2], decision["market"])
        self.assertNotIn(["BUY_SEED", "WHEAT", 16], decision["market"])
        self.assertEqual(len(decision["market"]), 10)

    def test_all_workers_can_feed_distinct_animals(self) -> None:
        state = scale_observation(day=1)
        place_animals(state, due=True)
        state["farms"][0]["hands"] = [[3, 4], [4, 3], [3, 3], [5, 4]]
        state["private"]["inventories"] = [
            {"WHEAT": 1},
            {"WHEAT": 1},
            {"WHEAT": 1},
            {"WHEAT": 1},
            {},
        ]

        decision = agent(state)

        self.assertEqual(decision["farmer"], ["FEED"])
        self.assertEqual(decision["hands"][:3], [["FEED"], ["FEED"], ["FEED"]])

    def test_workers_build_distinct_missing_pastures(self) -> None:
        state = scale_observation()
        state["farms"][0]["hands"] = [[3, 4], [4, 3], [3, 3]]
        state["private"]["inventories"] = [{}, {}, {}, {}]

        decision = agent(state)
        builds = [
            action
            for action in [decision["farmer"], *decision["hands"]]
            if action == ["BUILD_PASTURE"]
        ]

        self.assertEqual(len(builds), 4)

    def test_crop_tasks_exclude_all_livestock_tiles(self) -> None:
        state = scale_observation()
        state["private"]["seeds"]["WHEAT"] = 20
        place_animals(state, fed=True)

        decision = agent(state)

        self.assertTrue(LIVESTOCK_TILES)
        self.assertNotEqual(decision["farmer"], ["PLANT", "WHEAT"])

    def test_care_is_off_by_default_and_available_as_isolated_axis(self) -> None:
        state = scale_observation(day=2)
        place_animals(state, fed=True)
        state["farms"][0]["hands"] = [[3, 4], [4, 3], [3, 3]]
        state["private"]["inventories"] = [{}, {}, {}, {}]

        uncared = decide(state, care_enabled=False)
        default_actions = [uncared["farmer"], *uncared["hands"]]
        cared = agent(state)
        cared_actions = [cared["farmer"], *cared["hands"]]

        self.assertNotIn(["CARE"], default_actions)
        self.assertEqual(cared_actions.count(["CARE"]), 4)

    def test_market_never_exceeds_ten_entries(self) -> None:
        state = scale_observation(day=10, hour=0)
        place_animals(state, due=True)
        state["private"]["shed"].update(
            {"MILK": 6, "WOOL": 6, "FERTILIZER": 4, "WHEAT": 12}
        )
        state["market"]["prices"]["WHEAT"] = 35
        state["farms"][0]["tiles"][0][0] = wheat_tile()

        decision = agent(state)

        self.assertLessEqual(len(decision["market"]), 10)
        self.assertIn(["SELL", "WHEAT", 8], decision["market"])
        self.assertNotIn(["BUY_PRODUCT", "WHEAT", 4], decision["market"])
        self.assertEqual(decision["market"].count(["HIRE"]), 6)

    def test_selects_first_quadrant_expansion_animals(self) -> None:
        plans = _selected_animal_plans(4, 4)

        self.assertEqual(len(plans), 8)
        self.assertEqual(
            sum(plan["animal"] == "COW" for plan in plans),
            4,
        )
        self.assertEqual(
            sum(plan["animal"] == "SHEEP" for plan in plans),
            4,
        )

    def test_stages_expansion_like_the_leader_opening(self) -> None:
        self.assertEqual(len(_staged_animal_plans(0, 4, 4)), 4)
        self.assertEqual(len(_staged_animal_plans(3, 4, 4)), 5)
        self.assertEqual(len(_staged_animal_plans(5, 4, 4)), 6)
        self.assertEqual(len(_staged_animal_plans(7, 4, 4)), 8)

    def test_stages_full_leader_animal_sequence(self) -> None:
        self.assertEqual(len(_staged_animal_plans(0, 6, 12)), 4)
        self.assertEqual(len(_staged_animal_plans(3, 6, 12)), 5)
        self.assertEqual(len(_staged_animal_plans(5, 6, 12)), 6)
        self.assertEqual(len(_staged_animal_plans(7, 6, 12)), 10)
        self.assertEqual(len(_staged_animal_plans(13, 6, 12)), 18)
        plans = _selected_animal_plans(6, 12)
        self.assertEqual(len({plan["position"] for plan in plans}), 18)

    def test_cow_heavy_layout_uses_all_eight_unique_tiles(self) -> None:
        plans = _selected_animal_plans(6, 2)

        self.assertEqual(len(plans), 8)
        self.assertEqual(len({plan["position"] for plan in plans}), 8)
        self.assertEqual(sum(plan["animal"] == "COW" for plan in plans), 6)
        self.assertEqual(sum(plan["animal"] == "SHEEP" for plan in plans), 2)

    def test_land_waits_for_day_and_cash_reserve(self) -> None:
        farm = scale_observation(day=7, money=1_999)["farms"][0]
        self.assertEqual(_land_orders(7, 0, farm, 1), [])

        farm["money"] = 2_000
        self.assertEqual(_land_orders(7, 0, farm, 1), [["BUY_LAND"]])
        self.assertEqual(_land_orders(6, 0, farm, 1), [["BUY_LAND"]])
        self.assertEqual(_land_orders(5, 0, farm, 1), [])

    def test_adaptive_hiring_matches_replay_targets(self) -> None:
        farm = scale_observation(day=0)["farms"][0]
        self.assertEqual(len(_hire_orders(0, 0, farm, 12, True)), 5)
        self.assertEqual(len(_hire_orders(8, 0, farm, 12, True)), 11)
        self.assertEqual(len(_hire_orders(29, 0, farm, 12, True)), 8)

    def test_locked_quadrant_animals_wait_for_land(self) -> None:
        state = scale_observation(day=13)
        plans = _staged_animal_plans(13, 6, 12)

        unlocked = _unlocked_animal_plans(plans, state["farms"][0])

        self.assertTrue(
            all(_quadrant(plan["position"], 10) == "NW" for plan in unlocked)
        )
        self.assertLess(len(unlocked), len(plans))

    def test_can_request_six_animals_without_changing_default(self) -> None:
        state = scale_observation(day=3)
        place_animals(state)

        default = decide(state, target_cows=2, target_sheep=2)
        expanded = agent(state)

        self.assertFalse(
            any(order[0] == "BUY_ANIMAL" for order in default["market"])
        )
        self.assertIn(["BUY_ANIMAL", "COW", 1], expanded["market"])

    def test_daily_feed_mode_buys_feed_before_escape_risk(self) -> None:
        state = scale_observation(day=1)
        place_animals(state, due=False)

        alternate_day = decide(state, feed_daily=False)
        daily = agent(state)

        self.assertNotIn(
            ["BUY_PRODUCT", "WHEAT", 4],
            alternate_day["market"],
        )
        self.assertIn(["BUY_PRODUCT", "WHEAT", 4], daily["market"])

    def test_daily_feed_reserve_is_not_sold_before_worker_pickup(self) -> None:
        state = scale_observation(day=25)
        place_animals(state, due=False)
        state["private"]["shed"]["WHEAT"] = 12

        decision = decide(state, feed_daily=True)

        self.assertIn(["SELL", "WHEAT", 8], decision["market"])
        self.assertNotIn(["SELL", "WHEAT", 12], decision["market"])

    def test_feed_is_purchased_before_hires_and_expansion_animals(self) -> None:
        state = scale_observation(day=3, hour=0)
        place_animals(state, due=False)

        decision = decide(
            state,
            target_daily_hands=8,
            target_cows=4,
            target_sheep=4,
            feed_daily=True,
        )

        feed_index = decision["market"].index(
            ["BUY_PRODUCT", "WHEAT", 4]
        )
        hire_index = decision["market"].index(["HIRE"])
        animal_index = decision["market"].index(
            ["BUY_ANIMAL", "COW", 1]
        )
        self.assertLess(feed_index, hire_index)
        self.assertLess(hire_index, animal_index)


if __name__ == "__main__":
    unittest.main()