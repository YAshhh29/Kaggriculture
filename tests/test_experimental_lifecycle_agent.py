import ast
import unittest
from pathlib import Path

from agents.experimental_lifecycle_agent import (
    ANIMAL_CREW_SIZE,
    MAX_WHEAT_PER_PAIR,
    _assign_idle_current_animal_services,
    _crop_task_groups,
    _demand_capacity,
    _daily_hand_target,
    _effective_pair_count,
    _pair_owner,
    agent,
    decide,
)
from agents.experimental_scale_agent import _staged_animal_plans
from tests.test_experimental_scale_agent import scale_observation
from tests.test_main import wheat_tile


class ExperimentalLifecycleAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).resolve().parents[1] / "agents" / "experimental_lifecycle_agent.py"
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(functions[-1], "agent")

    def test_skips_non_productive_age_one_watering(self) -> None:
        state = scale_observation(day=1)
        state["farms"][0]["tiles"][4][1] = wheat_tile(
            planted_day=0,
            watered_today=False,
            consecutive_unwatered=0,
        )

        groups = _crop_task_groups(
            1,
            state["farms"][0],
            set(),
            pair=0,
            pair_count=3,
        )

        self.assertNotIn((1, 4), groups["urgent_water"])
        self.assertNotIn((1, 4), groups["yield_water"])

    def test_waters_wheat_during_yield_window(self) -> None:
        state = scale_observation(day=2)
        state["farms"][0]["tiles"][4][1] = wheat_tile(
            planted_day=0,
            watered_today=False,
            consecutive_unwatered=1,
        )

        groups = _crop_task_groups(
            2,
            state["farms"][0],
            set(),
            pair=0,
            pair_count=3,
        )

        self.assertIn((1, 4), groups["urgent_water"])

    def test_pair_ownership_is_stable_by_tile(self) -> None:
        positions = [(1, 2), (4, 2), (7, 2), (9, 4)]

        first = [_pair_owner(position, 3) for position in positions]
        second = [_pair_owner(position, 3) for position in positions]

        self.assertEqual(first, second)
        self.assertEqual(first, [0, 1, 2, 2])

    def test_effective_pair_count_uses_actual_crew_capacity(self) -> None:
        self.assertEqual(_effective_pair_count(12, 7), 3)
        self.assertEqual(_effective_pair_count(10, 6), 2)

    def test_pair_never_admits_more_than_its_capacity(self) -> None:
        state = scale_observation(day=2)
        state["farms"][0]["unlocked_quadrants"].append("NE")
        owned = [
            (x, y)
            for y in range(5)
            for x in range(10)
            if _pair_owner((x, y), 3) == 1
        ][:MAX_WHEAT_PER_PAIR]
        for x, y in owned:
            state["farms"][0]["tiles"][y][x] = wheat_tile(
                planted_day=0,
                watered_today=True,
            )

        groups = _crop_task_groups(
            2,
            state["farms"][0],
            set(),
            pair=1,
            pair_count=3,
        )

        self.assertEqual(groups["plant"], [])

    def test_future_animal_tiles_are_reserved_from_day_zero(self) -> None:
        state = scale_observation(day=0)
        final_plans = _staged_animal_plans(29, 6, 8)
        livestock_tiles = {plan["position"] for plan in final_plans}

        groups = _crop_task_groups(
            0,
            state["farms"][0],
            livestock_tiles,
            pair=1,
            pair_count=3,
        )

        self.assertTrue(livestock_tiles)
        self.assertTrue(
            all(position not in groups["plant"] for position in livestock_tiles)
        )


    def test_uses_seven_animal_workers_and_three_crop_pairs(self) -> None:
        state = scale_observation(day=7)
        state["farms"][0]["hands"] = [[4, 4] for _ in range(12)]
        state["private"]["inventories"] = [{} for _ in range(13)]

        decision = agent(state)

        self.assertEqual(ANIMAL_CREW_SIZE, 7)
        self.assertEqual(len(decision["hands"]), 12)

    def test_idle_crop_worker_services_animal_only_on_current_tile(self) -> None:
        state = scale_observation(day=7)
        plan = {
            "id": "cow_test",
            "animal": "COW",
            "structure": "PASTURE",
            "position": (5, 4),
            "product": "MILK",
            "max_held": 6,
        }
        state["farms"][0]["tiles"][4][5] = {
            "kind": "PASTURE",
            "animal": "COW",
            "fed_today": True,
            "cared_today": False,
            "fertilizer_available": False,
            "yield_units": 0,
            "consecutive_unfed": 0,
        }
        positions = [(4, 4), (5, 4), (9, 0)]
        actions = [["PASS"], None, None]

        _assign_idle_current_animal_services(
            (plan,),
            7,
            state["farms"][0],
            positions,
            actions,
            first_assistant=1,
        )

        self.assertEqual(actions[1], ["CARE"])
        self.assertIsNone(actions[2])

    def test_idle_assistant_helps_nearby_but_not_far_animal(self) -> None:
        state = scale_observation(day=7)
        plan = {
            "id": "cow_test",
            "animal": "COW",
            "structure": "PASTURE",
            "position": (5, 4),
            "product": "MILK",
            "max_held": 6,
        }
        state["farms"][0]["tiles"][4][5] = {
            "kind": "PASTURE",
            "animal": "COW",
            "fed_today": True,
            "cared_today": False,
            "fertilizer_available": False,
            "yield_units": 0,
            "consecutive_unfed": 0,
        }
        positions = [(4, 4), (3, 4), (1, 4)]
        actions = [["PASS"], None, None]

        _assign_idle_current_animal_services(
            (plan,),
            7,
            state["farms"][0],
            positions,
            actions,
            first_assistant=1,
        )

        self.assertEqual(actions[1], ["EAST"])
        self.assertIsNone(actions[2])

    def test_compact_wrapper_uses_ten_hands(self) -> None:
        state = scale_observation(day=7)
        decision = __import__(
            "agents.experimental_lifecycle_compact_agent",
            fromlist=["agent"],
        ).agent(state)

        self.assertEqual(decision["market"].count(["HIRE"]), 7)

    def test_compact_seed_target_matches_two_crop_pairs(self) -> None:
        state = scale_observation(day=7, hour=1)
        state["farms"][0]["hands"] = [[4, 4] for _ in range(10)]
        state["private"]["inventories"] = [{} for _ in range(11)]
        state["private"]["shed"].update({"COW": 6, "SHEEP": 8})

        decision = __import__(
            "agents.experimental_lifecycle_compact_agent",
            fromlist=["agent"],
        ).agent(state)

        self.assertIn(["BUY_SEED", "WHEAT", 10], decision["market"])


    def test_shed_animals_suppress_duplicate_purchase_orders(self) -> None:
        state = scale_observation(day=7, hour=1)
        state["private"]["shed"].update({"COW": 6, "SHEEP": 8})

        decision = decide(state)

        animal_orders = [
            order
            for order in decision["market"]
            if order[0] == "BUY_ANIMAL"
        ]
        self.assertEqual(animal_orders, [])

    def test_demand_capacity_stays_five_without_wheat_demand(self) -> None:
        state = scale_observation(day=9)
        state["town"]["unlocked_shops"] = ["YARN_STORE", "PET_CAFE"]
        state["market"]["prices"]["WHEAT"] = 25

        self.assertEqual(_demand_capacity(state), 5)

    def test_demand_capacity_expands_for_two_wheat_shops(self) -> None:
        state = scale_observation(day=9)
        state["town"]["unlocked_shops"] = ["BAKERY", "PIZZA_SHOP"]

        self.assertEqual(_demand_capacity(state), 6)

    def test_demand_capacity_expands_for_wheat_scarcity(self) -> None:
        state = scale_observation(day=9)
        state["market"]["prices"]["WHEAT"] = 35

        self.assertEqual(_demand_capacity(state), 6)

    def test_daily_hands_taper_after_crop_and_service_deadlines(self) -> None:
        self.assertEqual(_daily_hand_target(24, 12), 12)
        self.assertEqual(_daily_hand_target(25, 12), 10)
        self.assertEqual(_daily_hand_target(26, 12), 8)
        self.assertEqual(_daily_hand_target(27, 12), 8)
        self.assertEqual(_daily_hand_target(28, 12), 5)
        self.assertEqual(_daily_hand_target(29, 12), 2)

    def test_final_day_farmer_returns_and_sells_carried_value(self) -> None:
        state = scale_observation(day=29, hour=21)
        state["farms"][0]["farmer"] = [4, 3]
        state["private"]["inventories"] = [{"FERTILIZER": 2}]

        returning = decide(state)

        self.assertEqual(returning["farmer"], ["SOUTH"])

        state["hour"] = 22
        state["farms"][0]["farmer"] = [4, 4]
        dropping = decide(state)

        self.assertEqual(dropping["farmer"], ["DROP"])
        self.assertIn(["SELL", "FERTILIZER", 2], dropping["market"])

    def test_final_day_crew_drops_and_sells_all_worker_inventory(self) -> None:
        state = scale_observation(day=29, hour=22)
        state["farms"][0]["hands"] = [[5, 4], [4, 5]]
        state["private"]["inventories"] = [
            {"FERTILIZER": 1},
            {"MILK": 2},
            {"WOOL": 3},
        ]

        decision = decide(state)

        self.assertEqual(decision["farmer"], ["DROP"])
        self.assertEqual(decision["hands"], [["DROP"], ["DROP"]])
        self.assertIn(["SELL", "FERTILIZER", 1], decision["market"])
        self.assertIn(["SELL", "MILK", 2], decision["market"])
        self.assertIn(["SELL", "WOOL", 3], decision["market"])

    def test_final_day_farmer_prioritizes_more_valuable_product(self) -> None:
        state = scale_observation(day=29, hour=0)
        state["farms"][0]["unlocked_quadrants"].append("NE")
        state["market"]["prices"].update(
            {"MILK": 160, "WOOL": 200, "FERTILIZER": 100}
        )
        plans = _staged_animal_plans(29, 6, 8)
        cow = plans[0]
        sheep = next(plan for plan in plans if plan["animal"] == "SHEEP")
        for plan, units in ((cow, 1), (sheep, 2)):
            x, y = plan["position"]
            state["farms"][0]["tiles"][y][x] = {
                "kind": "PASTURE",
                "animal": plan["animal"],
                "yield_units": units,
                "fertilizer_available": True,
                "fed_today": False,
                "cared_today": False,
                "consecutive_unfed": 0,
            }

        decision = decide(state)

        self.assertEqual(decision["farmer"], ["NORTH"])

    def test_final_day_farmer_rejects_task_without_return_budget(self) -> None:
        state = scale_observation(day=29, hour=22)
        state["farms"][0]["farmer"] = [4, 4]
        state["farms"][0]["tiles"][4][4] = {
            "kind": "PASTURE",
            "animal": "COW",
            "yield_units": 1,
            "fertilizer_available": True,
            "fed_today": False,
            "cared_today": False,
            "consecutive_unfed": 0,
        }
        state["private"]["inventories"] = [{"FERTILIZER": 1}]

        decision = decide(state)

        self.assertEqual(decision["farmer"], ["DROP"])


if __name__ == "__main__":
    unittest.main()