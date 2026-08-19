import ast
import unittest
from pathlib import Path

from experimental_zoned_agent import (
    _assign_zoned_crops,
    _zoned_task_groups,
    agent,
)
from test_experimental_scale_agent import scale_observation


class ExperimentalZonedAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).with_name("experimental_zoned_agent.py")
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]
        self.assertEqual(functions[-1], "agent")

    def test_default_keeps_safe_scale_capital_policy(self) -> None:
        decision = agent(scale_observation())

        self.assertEqual(decision["market"].count(["HIRE"]), 8)
        self.assertIn(["BUY_ANIMAL", "COW", 2], decision["market"])
        self.assertIn(["BUY_ANIMAL", "SHEEP", 2], decision["market"])
        self.assertNotIn(["BUY_LAND"], decision["market"])

    def test_can_reduce_near_animals_for_far_crop_crew(self) -> None:
        decision = __import__("experimental_zoned_agent").decide(
            scale_observation(),
            target_cows=2,
            target_sheep=2,
        )

        self.assertIn(["BUY_ANIMAL", "COW", 2], decision["market"])
        self.assertIn(["BUY_ANIMAL", "SHEEP", 2], decision["market"])

    def test_near_planting_starts_beside_center_not_top_left(self) -> None:
        state = scale_observation()
        state["private"]["seeds"]["WHEAT"] = 4
        plants = _zoned_task_groups(
            0,
            state["farms"][0],
            state["private"],
            set(),
            "near",
        )[-1]

        self.assertEqual(plants[0][0], (4, 4))
        self.assertNotIn((0, 0), [position for position, _ in plants])

    def test_far_crew_prefers_right_quadrant(self) -> None:
        state = scale_observation()
        state["farms"][0]["unlocked_quadrants"].append("NE")
        state["private"]["seeds"]["WHEAT"] = 8
        plants = _zoned_task_groups(
            0,
            state["farms"][0],
            state["private"],
            set(),
            "far",
        )[-1]

        self.assertTrue(all(position[0] >= 5 for position, _ in plants))

    def test_near_and_far_workers_choose_different_zones(self) -> None:
        state = scale_observation()
        state["farms"][0]["unlocked_quadrants"].append("NE")
        state["farms"][0]["hands"] = [
            [4, 4], [4, 4], [4, 4], [4, 4], [4, 4], [4, 4]
        ]
        state["private"]["inventories"] = [{} for _ in range(7)]
        state["private"]["seeds"]["WHEAT"] = 12
        positions = [
            tuple(state["farms"][0]["farmer"]),
            *(tuple(position) for position in state["farms"][0]["hands"]),
        ]
        actions = [None for _ in positions]

        _assign_zoned_crops(
            0,
            state["farms"][0],
            state["private"],
            positions,
            actions,
            set(),
        )

        self.assertEqual(actions[0], ["PLANT", "WHEAT"])
        self.assertEqual(actions[5], ["EAST"])

    def test_far_worker_can_rescue_near_urgent_crop(self) -> None:
        state = scale_observation(day=2)
        state["farms"][0]["unlocked_quadrants"].append("NE")
        state["farms"][0]["farmer"] = [9, 0]
        state["farms"][0]["hands"] = [[4, 4] for _ in range(5)]
        state["private"]["inventories"] = [{} for _ in range(6)]
        state["farms"][0]["tiles"][4][4] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 1,
        }
        positions = [
            tuple(state["farms"][0]["farmer"]),
            *(tuple(position) for position in state["farms"][0]["hands"]),
        ]
        actions = [None for _ in positions]

        _assign_zoned_crops(
            2,
            state["farms"][0],
            state["private"],
            positions,
            actions,
            set(),
        )

        self.assertEqual(actions[0], ["WEST"])


if __name__ == "__main__":
    unittest.main()