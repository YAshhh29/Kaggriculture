import unittest

from agents.experimental_distilled_calendar_agent import decide as calendar
from candidates.candidate_a import build_candidate_a_agent
from tests.test_experimental_scale_agent import scale_observation


def fixed_baseline(action):
    def decide(observation):
        del observation
        return {
            "farmer": list(action.get("farmer", ["PASS"])),
            "hands": [list(item) for item in action.get("hands", [])],
            "market": [list(item) for item in action.get("market", [])],
        }

    return decide


def scheduled_baseline(actions):
    def decide(observation):
        step = int(observation.get("step", 0))
        action = actions.get(
            step,
            {"farmer": ["PASS"], "hands": [], "market": []},
        )
        return {
            "farmer": list(action.get("farmer", ["PASS"])),
            "hands": [list(item) for item in action.get("hands", [])],
            "market": [list(item) for item in action.get("market", [])],
        }

    return decide


class ExperimentalCalendarRecoveryAgentTests(unittest.TestCase):
    def test_no_guard_preserves_calendar_action(self) -> None:
        state = scale_observation(day=0, hour=0)
        state["step"] = 0
        candidate = build_candidate_a_agent(baseline=calendar)

        self.assertEqual(candidate(state), calendar(state))

    def test_weed_blocked_plant_digs_retries_and_waters(self) -> None:
        state = scale_observation(day=1, hour=10)
        state["step"] = 34
        x, y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][y][x] = {"kind": "WEED"}
        state["private"]["seeds"]["WHEAT"] = 1
        candidate = build_candidate_a_agent(
            baseline=scheduled_baseline(
                {
                    34: {
                        "farmer": ["PLANT", "WHEAT"],
                        "hands": [],
                        "market": [],
                    },
                    35: {
                        "farmer": ["WATER"],
                        "hands": [],
                        "market": [],
                    },
                    36: {
                        "farmer": ["PASS"],
                        "hands": [],
                        "market": [],
                    },
                }
            )
        )

        first = candidate(state)
        state["step"] = 35
        state["hour"] = 11
        state["farms"][0]["tiles"][y][x] = None
        second = candidate(state)
        state["step"] = 36
        state["hour"] = 12
        state["private"]["seeds"]["WHEAT"] = 0
        state["farms"][0]["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 1,
            "yield_units": 1,
            "watered_today": False,
        }
        third = candidate(state)

        self.assertEqual(first["farmer"], ["DIG"])
        self.assertEqual(second["farmer"], ["PLANT", "WHEAT"])
        self.assertEqual(third["farmer"], ["WATER"])

    def test_weed_repair_does_not_displace_scheduled_movement(self) -> None:
        state = scale_observation(day=1, hour=10)
        state["step"] = 34
        x, y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][y][x] = {"kind": "WEED"}
        state["private"]["seeds"]["WHEAT"] = 1
        candidate = build_candidate_a_agent(
            baseline=scheduled_baseline(
                {
                    34: {
                        "farmer": ["PLANT", "WHEAT"],
                        "hands": [],
                        "market": [],
                    },
                    35: {
                        "farmer": ["WATER"],
                        "hands": [],
                        "market": [],
                    },
                    36: {
                        "farmer": ["WEST"],
                        "hands": [],
                        "market": [],
                    },
                }
            )
        )

        first = candidate(state)
        state["step"] = 35
        state["hour"] = 11
        state["farms"][0]["tiles"][y][x] = None
        second = candidate(state)
        state["step"] = 36
        state["hour"] = 12
        third = candidate(state)

        # The multi-step repair (DIG -> PLANT -> WATER) must still be
        # declined here: step 36 is scheduled movement, and consuming it is
        # exactly what desynchronized the route for -32690 in section 6.
        # A bare 1:1 DIG is allowed because it costs the same single turn the
        # doomed PLANT would have cost and leaves the worker in place, so the
        # assertions that matter are that no retry is queued and that the
        # calendar's own next two actions -- including the WEST movement --
        # still execute on schedule.
        self.assertEqual(first["farmer"], ["DIG"])
        self.assertEqual(second["farmer"], ["WATER"])
        self.assertEqual(third["farmer"], ["WEST"])

    def test_live_hand_count_truncates_stale_calendar_actions(self) -> None:
        state = scale_observation(day=5, hour=0)
        state["step"] = 120
        state["farms"][0]["hands"] = [[4, 5]]
        state["private"]["inventories"] = [{}, {}]
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {
                    "farmer": ["PASS"],
                    "hands": [["NORTH"], ["SOUTH"]],
                    "market": [],
                }
            )
        )

        decision = candidate(state)

        self.assertEqual(decision["hands"], [["NORTH"]])

    def test_terminal_routes_carried_inventory_to_shed(self) -> None:
        state = scale_observation(day=29, hour=20)
        state["step"] = 716
        state["farms"][0]["farmer"] = [3, 4]
        state["private"]["inventories"] = [{"MILK": 2}]
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["PASS"], "hands": [], "market": []}
            )
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["EAST"])
        self.assertEqual(decision["market"], [])

    def test_terminal_commitment_advances_stranded_harvest(self) -> None:
        state = scale_observation(day=29, hour=7)
        state["step"] = 703
        state["farms"][0]["farmer"] = [3, 5]
        state["farms"][0]["tiles"][1][1] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 25,
            "yield_units": 5,
            "watered_today": False,
        }
        state["private"]["inventories"] = [{"WHEAT": 4}]
        schedule = {
            703: ["EAST"],
            704: ["DROP"],
            705: ["NORTH"],
            706: ["WEST"],
            707: ["NORTH"],
            708: ["WEST"],
            709: ["NORTH"],
            710: ["WEST"],
            711: ["NORTH"],
            712: ["WATER"],
            713: ["HARVEST"],
        }
        candidate = build_candidate_a_agent(
            baseline=scheduled_baseline(
                {
                    step: {
                        "farmer": operation,
                        "hands": [],
                        "market": [],
                    }
                    for step, operation in schedule.items()
                }
            ),
            enable_recovery=False,
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["WEST"])

    def test_terminal_commitment_keeps_returnable_harvest(self) -> None:
        state = scale_observation(day=29, hour=7)
        state["step"] = 703
        state["farms"][0]["farmer"] = [3, 5]
        state["farms"][0]["tiles"][4][4] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 25,
            "yield_units": 5,
            "watered_today": True,
        }
        candidate = build_candidate_a_agent(
            baseline=scheduled_baseline(
                {
                    703: {
                        "farmer": ["EAST"],
                        "hands": [],
                        "market": [],
                    },
                    704: {
                        "farmer": ["NORTH"],
                        "hands": [],
                        "market": [],
                    },
                    705: {
                        "farmer": ["HARVEST"],
                        "hands": [],
                        "market": [],
                    },
                }
            ),
            enable_recovery=False,
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["EAST"])

    def test_terminal_sells_actual_shed_and_same_turn_drop(self) -> None:
        state = scale_observation(day=29, hour=22)
        state["step"] = 718
        state["private"]["shed"] = {"WOOL": 3}
        state["private"]["inventories"] = [{"MILK": 2}]
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
            )
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["DROP"])
        self.assertEqual(
            decision["market"],
            [["SELL", "MILK", 2], ["SELL", "WOOL", 3]],
        )

    def test_recovery_only_preserves_terminal_calendar(self) -> None:
        state = scale_observation(day=29, hour=22)
        state["step"] = 718
        state["private"]["shed"] = {"WOOL": 3}
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
            ),
            enable_liquidation=False,
        )

        decision = candidate(state)

        self.assertEqual(decision["market"], [["HIRE"]])

    def test_liquidation_only_does_not_repair_weed(self) -> None:
        state = scale_observation(day=1, hour=10)
        state["step"] = 34
        x, y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][y][x] = {"kind": "WEED"}
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
            ),
            enable_recovery=False,
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["PLANT", "WHEAT"])

    def test_locked_quadrant_blocks_scheduled_tile_tasks(self) -> None:
        # Live episodes 105061000/105062726: the calendar's only scripted
        # BUY_LAND for the third quadrant was starved of funds by an
        # earlier same-turn BUY_PRODUCT, so the quadrant never unlocked.
        # Every later scheduled PLANT/WATER/etc. the calendar sent there
        # reported the tile as the literal string "LOCKED" and executed as
        # a no-op for the rest of the episode (471 times, in each replay).
        state = scale_observation(day=8, hour=17)
        state["step"] = 210
        farmer_x, farmer_y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][farmer_y][farmer_x] = "LOCKED"
        state["farms"][0]["hands"] = [(2, 8)]
        state["farms"][0]["tiles"][8][2] = "LOCKED"
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {
                    "farmer": ["PLANT", "WHEAT"],
                    "hands": [["WATER"]],
                    "market": [],
                }
            )
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["PASS"])
        self.assertEqual(decision["hands"][0], ["PASS"])

    def test_locked_quadrant_guard_leaves_normal_tiles_alone(self) -> None:
        state = scale_observation(day=8, hour=17)
        state["step"] = 210
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
            )
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["PLANT", "WHEAT"])

    def test_recovery_disabled_leaves_locked_tile_task_untouched(self) -> None:
        state = scale_observation(day=8, hour=17)
        state["step"] = 210
        x, y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][y][x] = "LOCKED"
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
            ),
            enable_recovery=False,
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["PLANT", "WHEAT"])

    def test_weed_blocked_water_is_cleared_in_place(self) -> None:
        # A real-game audit found WATER/HARVEST/FERTILIZE actions landing on
        # WEED tiles as guaranteed no-ops, because the schedule-safe repair
        # above only covers RECOVERABLE_SETUP work. The turn is already lost,
        # so clear the weed instead of spending it on nothing.
        state = scale_observation(day=8, hour=10)
        state["step"] = 200
        x, y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][y][x] = {"kind": "WEED"}
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["WATER"], "hands": [], "market": []}
            )
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["DIG"])

    def test_weed_clear_queues_no_retry_and_keeps_next_calendar_action(
        self,
    ) -> None:
        # The 1:1 substitution must not become an inserted step: the next
        # turn has to follow the calendar exactly, or this reintroduces the
        # route desync that cost -32690 in the rejected broad recovery.
        state = scale_observation(day=8, hour=10)
        state["step"] = 200
        x, y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][y][x] = {"kind": "WEED"}
        candidate = build_candidate_a_agent(
            baseline=scheduled_baseline(
                {
                    200: {"farmer": ["WATER"], "hands": [], "market": []},
                    201: {"farmer": ["EAST"], "hands": [], "market": []},
                }
            )
        )

        first = candidate(state)
        state["step"] = 201
        state["hour"] = 11
        state["farms"][0]["tiles"][y][x] = None
        second = candidate(state)

        self.assertEqual(first["farmer"], ["DIG"])
        self.assertEqual(second["farmer"], ["EAST"])

    def test_dig_on_a_weed_is_left_alone(self) -> None:
        state = scale_observation(day=8, hour=10)
        state["step"] = 200
        x, y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][y][x] = {"kind": "WEED"}
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["DIG"], "hands": [], "market": []}
            )
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["DIG"])

    def test_weed_clear_does_not_touch_a_healthy_plant(self) -> None:
        state = scale_observation(day=8, hour=10)
        state["step"] = 200
        x, y = state["farms"][0]["farmer"]
        state["farms"][0]["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 6,
            "yield_units": 0,
            "watered_today": False,
        }
        candidate = build_candidate_a_agent(
            baseline=fixed_baseline(
                {"farmer": ["WATER"], "hands": [], "market": []}
            )
        )

        decision = candidate(state)

        self.assertEqual(decision["farmer"], ["WATER"])


if __name__ == "__main__":
    unittest.main()