import json
import tempfile
import unittest
from pathlib import Path

from benchmark import (
    analyze_livestock,
    analyze_route,
    classify_result,
    count_actions,
    inventory_snapshot,
    load_agent_callable,
    load_parameterized_agent,
    summarize,
    write_report,
)
from test_main import observation


class BenchmarkTests(unittest.TestCase):
    def test_tracks_animal_placements_losses_and_maximum_active(self) -> None:
        empty = [[{"kind": "PASTURE"}, {"kind": "PASTURE"}]]
        one_cow = [[
            {"kind": "PASTURE", "animal": "COW"},
            {"kind": "PASTURE"},
        ]]
        cow_and_sheep = [[
            {"kind": "PASTURE", "animal": "COW"},
            {"kind": "PASTURE", "animal": "SHEEP"},
        ]]
        escaped_cow = [[
            {"kind": "PASTURE"},
            {"kind": "PASTURE", "animal": "SHEEP"},
        ]]
        steps = [
            [self._state(0, 0, 0, (0, 0), empty, ["PASS"])],
            [self._state(1, 0, 1, (0, 0), one_cow, ["PLACE", "COW"])],
            [
                self._state(
                    2,
                    0,
                    2,
                    (1, 0),
                    cow_and_sheep,
                    ["PLACE", "SHEEP"],
                )
            ],
            [self._state(24, 1, 0, (0, 0), escaped_cow, ["PASS"])],
        ]

        self.assertEqual(
            analyze_livestock(steps, 0),
            {
                "placements": {"COW": 1, "SHEEP": 1},
                "losses": {"COW": 1},
                "maximum_active": {"COW": 1, "SHEEP": 1},
                "final_active": {"SHEEP": 1},
                "placement_events": [
                    {
                        "step": 1,
                        "day": 0,
                        "hour": 1,
                        "animal": "COW",
                        "tile": [0, 0],
                    },
                    {
                        "step": 2,
                        "day": 0,
                        "hour": 2,
                        "animal": "SHEEP",
                        "tile": [1, 0],
                    },
                ],
                "loss_events": [
                    {
                        "step": 24,
                        "day": 1,
                        "hour": 0,
                        "animal": "COW",
                        "tile": [0, 0],
                    }
                ],
            },
        )

    def test_analyzes_route_crop_cycle_and_sale_delay(self) -> None:
        empty_tiles = [[None for _ in range(5)] for _ in range(5)]
        planted_tiles = [[None for _ in range(5)] for _ in range(5)]
        planted_tiles[4][3] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "yield_units": 1,
        }
        mature_tiles = [[None for _ in range(5)] for _ in range(5)]
        mature_tiles[4][3] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "yield_units": 4,
        }
        steps = [
            [self._state(0, 0, 0, (4, 4), empty_tiles, ["PASS"])],
            [self._state(1, 0, 1, (3, 4), empty_tiles, ["WEST"])],
            [self._state(2, 0, 2, (3, 4), planted_tiles, ["PLANT", "WHEAT"])],
            [self._state(3, 0, 3, (3, 4), planted_tiles, ["WATER"])],
            [self._state(96, 4, 0, (3, 4), mature_tiles, ["PASS"])],
            [self._state(97, 4, 1, (3, 4), empty_tiles, ["HARVEST"])],
            [
                self._state(
                    120,
                    5,
                    0,
                    (4, 4),
                    empty_tiles,
                    ["PASS"],
                    shed_wheat=4,
                )
            ],
            [
                self._state(
                    121,
                    5,
                    1,
                    (4, 4),
                    empty_tiles,
                    ["PASS"],
                    market=[["SELL", "WHEAT", 4]],
                )
            ],
        ]

        analysis = analyze_route(steps, 0)

        self.assertEqual(analysis["movement_turns"], 1)
        self.assertEqual(analysis["task_visit_count"], 3)
        self.assertEqual(analysis["cycles_harvested"], 1)
        self.assertEqual(analysis["same_day_watered_cycles"], 1)
        self.assertEqual(analysis["cycles_weeded"], 0)
        self.assertEqual(analysis["harvested_units"], 4)
        self.assertEqual(analysis["matched_sold_units"], 4)
        self.assertEqual(analysis["mean_plant_to_harvest_turns"], 95.0)
        self.assertEqual(analysis["mean_harvest_to_shed_turns"], 24.0)
        self.assertEqual(analysis["mean_harvest_to_sale_turns"], 24.0)
        self.assertEqual(
            analysis["routes_by_day"]["0"],
            [
                {
                    "step": 1,
                    "day": 0,
                    "hour": 1,
                    "worker": "farmer",
                    "task": "PLANT",
                    "tile": [3, 4],
                    "travel_turns": 1,
                },
                {
                    "step": 2,
                    "day": 0,
                    "hour": 2,
                    "worker": "farmer",
                    "task": "WATER",
                    "tile": [3, 4],
                    "travel_turns": 0,
                },
            ],
        )

    def test_analyzes_a_hand_only_crop_cycle(self) -> None:
        empty = [[None]]
        planted = [[{
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "yield_units": 1,
        }]]
        mature = [[{
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "yield_units": 4,
        }]]
        steps = [
            [self._state_with_hand(0, 0, 0, empty, ["PASS"])],
            [self._state_with_hand(1, 0, 1, planted, ["PLANT", "WHEAT"])],
            [self._state_with_hand(2, 0, 2, planted, ["WATER"])],
            [self._state_with_hand(96, 4, 0, mature, ["PASS"])],
            [self._state_with_hand(97, 4, 1, empty, ["HARVEST"])],
        ]

        analysis = analyze_route(steps, 0)

        self.assertEqual(analysis["cycles_harvested"], 1)
        self.assertEqual(analysis["harvested_units"], 4)
        self.assertEqual(analysis["hand_movement_turns"], 0)
        self.assertEqual(analysis["all_worker_movement_turns"], 0)
        self.assertEqual(
            [visit["worker"] for visit in analysis["task_visits"]],
            ["hand_1", "hand_1", "hand_1"],
        )

    def test_checkpoints_an_incomplete_report(self) -> None:
        records = [self._record(0, "win", 100, 90, {"WATER": 2})]

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "report.json"
            report = write_report(output_path, {"opponent": "starter"}, records, 2)
            saved_report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertFalse(report["complete"])
        self.assertEqual(saved_report["games"], records)
        self.assertEqual(saved_report["summary"]["wins"], 1)

    def test_loads_a_parameterized_wheat_agent(self) -> None:
        agent_path = Path(__file__).with_name("main.py")
        experiment_agent = load_parameterized_agent(
            agent_path,
            {
                "target_wheat_tiles": 8,
                "last_planting_day": 24,
                "harvest_watered_current_first": True,
                "minimum_wheat_sale_price": 35,
                "maximum_wheat_holdings": 72,
                "wheat_liquidation_day": 25,
            },
        )

        decision = experiment_agent(observation())

        self.assertEqual(decision["market"], [["BUY_SEED", "WHEAT", 8]])

    def test_loads_a_file_opponent_callable(self) -> None:
        opponent_path = Path(__file__).with_name("leader_replay_agent.py")

        opponent = load_agent_callable(opponent_path)

        self.assertTrue(callable(opponent))

    def test_classifies_results_and_invalid_games(self) -> None:
        self.assertEqual(classify_result(10, 9, "DONE", "DONE"), "win")
        self.assertEqual(classify_result(9, 10, "DONE", "DONE"), "loss")
        self.assertEqual(classify_result(10, 10, "DONE", "DONE"), "tie")
        self.assertEqual(classify_result(None, 10, "ERROR", "DONE"), "error")

    def test_counts_farmer_hand_and_market_actions(self) -> None:
        steps = [
            [
                {
                    "action": {
                        "farmer": ["WATER"],
                        "hands": [["EAST"], ["HARVEST"]],
                        "market": [["SELL", "WHEAT", 2]],
                    }
                }
            ],
            [
                {
                    "action": {
                        "farmer": ["PASS"],
                        "hands": [["WATER"], ["PASS"]],
                        "market": [
                            ["BUY_SEED", "WHEAT", 1],
                            ["SELL", "WHEAT", 1],
                        ],
                    }
                }
            ],
        ]

        self.assertEqual(
            count_actions(steps, 0),
            {
                "farmer": {"PASS": 1, "WATER": 1},
                "hands": {
                    "EAST": 1,
                    "HARVEST": 1,
                    "PASS": 1,
                    "WATER": 1,
                },
                "market": {"BUY_SEED": 1, "SELL": 2},
                "market_units": {
                    "BUY_SEED:WHEAT": 1,
                    "SELL:WHEAT": 3,
                },
            },
        )

    def test_snapshots_only_positive_final_inventory(self) -> None:
        observation = {
            "private": {
                "shed": {"WHEAT": 0, "CARROT": 2},
                "seeds": {"WHEAT": 3, "CARROT": 0},
                "inventories": [
                    {"WHEAT": 4},
                    {"WHEAT": 1, "CARROT": 0},
                ],
            }
        }

        self.assertEqual(
            inventory_snapshot(observation),
            {
                "shed": {"CARROT": 2},
                "carried": {"WHEAT": 5},
                "seeds": {"WHEAT": 3},
            },
        )

    def test_summarizes_scores_positions_and_actions(self) -> None:
        records = [
            self._record(0, "win", 100, 90, {"WATER": 2}),
            self._record(1, "loss", 80, 100, {"PASS": 1}),
            self._record(0, "tie", 50, 50, {"WATER": 1}),
            self._record(1, "error", None, None, {}),
        ]

        summary = summarize(records)

        self.assertEqual(summary["completed"], 3)
        self.assertEqual(summary["wins"], 1)
        self.assertEqual(summary["losses"], 1)
        self.assertEqual(summary["ties"], 1)
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["win_rate"], 0.3333)
        self.assertEqual(summary["score_rate"], 0.5)
        self.assertEqual(summary["mean_agent_coins"], 76.67)
        self.assertEqual(summary["mean_margin"], -3.33)
        self.assertEqual(summary["by_player"]["0"]["wins"], 1)
        self.assertEqual(
            summary["agent_actions"]["farmer"],
            {"PASS": 1, "WATER": 3},
        )

    @staticmethod
    def _state(
        step: int,
        day: int,
        hour: int,
        position: tuple[int, int],
        tiles: list[list[object]],
        farmer_action: list[str],
        *,
        shed_wheat: int = 0,
        market: list[list[object]] | None = None,
    ) -> dict:
        return {
            "action": {
                "farmer": farmer_action,
                "hands": [],
                "market": market or [],
            },
            "observation": {
                "step": step,
                "day": day,
                "hour": hour,
                "farms": [
                    {
                        "farmer": list(position),
                        "tiles": tiles,
                    }
                ],
                "private": {
                    "shed": {"WHEAT": shed_wheat},
                    "seeds": {},
                    "inventories": [{}],
                },
            },
        }

    @staticmethod
    def _state_with_hand(
        step: int,
        day: int,
        hour: int,
        tiles: list[list[object]],
        hand_action: list[str],
    ) -> dict:
        return {
            "action": {
                "farmer": ["PASS"],
                "hands": [hand_action],
                "market": [],
            },
            "observation": {
                "step": step,
                "day": day,
                "hour": hour,
                "farms": [{
                    "farmer": [0, 0],
                    "hands": [[0, 0]],
                    "tiles": tiles,
                }],
                "private": {
                    "shed": {"WHEAT": 0},
                    "seeds": {},
                    "inventories": [{}, {}],
                },
            },
        }

    @staticmethod
    def _record(
        player: int,
        result: str,
        agent_reward: int | None,
        opponent_reward: int | None,
        farmer_actions: dict[str, int],
    ) -> dict:
        return {
            "agent_player": player,
            "result": result,
            "agent_reward": agent_reward,
            "opponent_reward": opponent_reward,
            "agent_actions": {
                "farmer": farmer_actions,
                "market": {},
                "market_units": {},
            },
            "route_analysis": {
                "movement_turns": 0,
                "task_visit_count": 0,
                "travel_turns_to_tasks": 0,
                "max_travel_turns_to_task": 0,
                "cycles_planted": 0,
                "cycles_harvested": 0,
                "cycles_weeded": 0,
                "cycles_unfinished": 0,
                "same_day_watered_cycles": 0,
                "missed_planting_day_water_cycles": 0,
                "harvested_units": 0,
                "matched_sold_units": 0,
                "mean_harvest_to_sale_turns": None,
                "tile_task_counts": {},
            },
            "final_inventory": {"shed": {}, "carried": {}, "seeds": {}},
        }


if __name__ == "__main__":
    unittest.main()
