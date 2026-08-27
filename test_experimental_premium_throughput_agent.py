import unittest
from collections import Counter

from agents.experimental_center_out_agent import ANIMAL_PLANS, CROP_DATA
from agents.experimental_premium_throughput_agent import (
    DENSE_CROP_PLANS,
    LAST_PLANT_DAYS,
    _dense_crop_plans,
    _crop_priority,
    _hand_target,
    _land_orders,
    _pair_quadrants,
    _assign_paired_planting,
    _assign_limited_animal_services,
    _assign_crop_tasks,
    _assign_crop_fertilization,
    _effective_crop_worker_reserve,
    _worker_actions,
    _sales_orders,
    _seed_orders,
    _wheat_trade_orders,
    _assign_colocated_feed_care,
)
from test_experimental_scale_agent import scale_observation


class ExperimentalPremiumThroughputAgentTests(unittest.TestCase):
    def test_dense_plan_fills_three_quadrants_around_animal_cores(
        self,
    ) -> None:
        counts = Counter(str(plan["crop"]) for plan in DENSE_CROP_PLANS)
        crop_positions = {tuple(plan["position"]) for plan in DENSE_CROP_PLANS}
        animal_positions = {tuple(plan["position"]) for plan in ANIMAL_PLANS}

        self.assertEqual(len(DENSE_CROP_PLANS), 63)
        self.assertEqual(
            counts,
            {"MELON": 10, "STRAWBERRY": 35, "WHEAT": 18},
        )
        self.assertTrue(crop_positions.isdisjoint(animal_positions))

    def test_each_unlocked_quadrant_exposes_twenty_one_crop_slots(
        self,
    ) -> None:
        state = scale_observation()
        farm = state["farms"][0]
        self.assertEqual(len(_dense_crop_plans(farm)), 21)
        farm["unlocked_quadrants"].extend(["NE", "SW"])
        self.assertEqual(len(_dense_crop_plans(farm)), 63)

    def test_nw_wheat_rotates_only_after_its_opening_crop_is_harvested(
        self,
    ) -> None:
        state = scale_observation(day=4)
        farm = state["farms"][0]
        rotation_plans = [
            plan
            for plan in DENSE_CROP_PLANS
            if plan.get("rotation_crop") == "STRAWBERRY"
        ]
        first = rotation_plans[0]
        x, y = first["position"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
        }

        active = {
            str(plan["id"]): str(plan["crop"])
            for plan in _dense_crop_plans(farm, 4)
        }

        self.assertEqual(len(rotation_plans), 8)
        self.assertEqual(active[str(first["id"])], "WHEAT")
        self.assertTrue(
            all(
                active[str(plan["id"])] == "STRAWBERRY"
                for plan in rotation_plans[1:]
            )
        )

    def test_rotation_slots_never_reopen_as_late_wheat(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        rotation_plans = [
            plan
            for plan in _dense_crop_plans(farm, 12)
            if plan.get("rotation_crop") == "STRAWBERRY"
        ]

        self.assertTrue(rotation_plans)
        self.assertTrue(
            all(plan["crop"] == "WHEAT" for plan in rotation_plans)
        )
        self.assertTrue(
            all(plan["last_plant_day"] == 1 for plan in rotation_plans)
        )

    def test_capacity_mode_backfills_empty_slots_with_safe_wheat(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        farm["unlocked_quadrants"].extend(["NE", "SW"])

        plans = _dense_crop_plans(
            farm,
            12,
            late_rotation_crop="WHEAT",
        )

        self.assertEqual(len(plans), 63)
        self.assertTrue(all(plan["crop"] == "WHEAT" for plan in plans))
        self.assertTrue(all(plan["first_plant_day"] <= 12 for plan in plans))
        self.assertTrue(all(plan["last_plant_day"] == 22 for plan in plans))

    def test_capacity_mode_keeps_the_premium_opening(self) -> None:
        state = scale_observation(day=0)
        farm = state["farms"][0]

        plans = _dense_crop_plans(
            farm,
            0,
            late_rotation_crop="WHEAT",
        )

        self.assertEqual(
            Counter(str(plan["crop"]) for plan in plans),
            {"MELON": 5, "STRAWBERRY": 8, "WHEAT": 8},
        )

    def test_capacity_mode_preserves_active_backfill_wheat(self) -> None:
        state = scale_observation(day=13)
        farm = state["farms"][0]
        plan = next(
            plan for plan in DENSE_CROP_PLANS
            if plan["crop"] == "STRAWBERRY"
        )
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 12,
        }

        active = {
            str(candidate["id"]): str(candidate["crop"])
            for candidate in _dense_crop_plans(
                farm,
                13,
                late_rotation_crop="WHEAT",
            )
        }

        self.assertEqual(active[str(plan["id"])], "WHEAT")

    def test_capacity_mode_preserves_active_premium_crop(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        plan = next(
            plan for plan in DENSE_CROP_PLANS
            if plan["crop"] == "STRAWBERRY"
        )
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "STRAWBERRY",
            "planted_day": 2,
        }

        active = {
            str(candidate["id"]): str(candidate["crop"])
            for candidate in _dense_crop_plans(
                farm,
                12,
                late_rotation_crop="WHEAT",
            )
        }

        self.assertEqual(active[str(plan["id"])], "STRAWBERRY")

    def test_capacity_mode_releases_reserve_as_crop_work_ends(self) -> None:
        state = scale_observation(day=22)
        farm = state["farms"][0]
        plans = _dense_crop_plans(
            farm,
            22,
            late_rotation_crop="WHEAT",
        )
        self.assertEqual(
            _effective_crop_worker_reserve(
                22,
                farm,
                state["private"],
                plans,
                2,
            ),
            2,
        )

        plan = plans[0]
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 22,
        }
        self.assertEqual(
            _effective_crop_worker_reserve(
                23,
                farm,
                state["private"],
                plans,
                2,
            ),
            1,
        )

        farm["tiles"][y][x] = None
        self.assertEqual(
            _effective_crop_worker_reserve(
                23,
                farm,
                state["private"],
                plans,
                2,
            ),
            0,
        )

    def test_capacity_mode_releases_workers_for_inert_crop(self) -> None:
        state = scale_observation(day=2)
        farm = state["farms"][0]
        plan = next(
            plan for plan in _dense_crop_plans(farm, 2)
            if plan["crop"] == "WHEAT"
        )
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 1,
            "watered_today": True,
            "consecutive_unwatered": 0,
            "yield_units": 1,
        }

        self.assertEqual(
            _effective_crop_worker_reserve(
                2,
                farm,
                state["private"],
                (plan,),
                2,
                actionable_only=True,
            ),
            0,
        )

    def test_capacity_mode_reserves_pair_only_with_seed(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        plan = next(
            plan for plan in _dense_crop_plans(
                farm,
                12,
                late_rotation_crop="WHEAT",
            )
            if plan["crop"] == "WHEAT"
        )

        self.assertEqual(
            _effective_crop_worker_reserve(
                12,
                farm,
                state["private"],
                (plan,),
                2,
                actionable_only=True,
            ),
            0,
        )
        state["private"]["seeds"]["WHEAT"] = 1
        self.assertEqual(
            _effective_crop_worker_reserve(
                12,
                farm,
                state["private"],
                (plan,),
                2,
                actionable_only=True,
            ),
            2,
        )

    def test_last_plant_days_leave_time_for_cleanup(self) -> None:
        self.assertEqual(
            LAST_PLANT_DAYS,
            {
                "MELON": 7,
                "STRAWBERRY": 11,
                "WHEAT": 22,
                "CARROT": 22,
            },
        )

    def test_lifecycle_windows_are_derived_from_cashable_horizon(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        farm["unlocked_quadrants"].extend(["NE", "SW"])

        plans = _dense_crop_plans(
            farm,
            12,
            rotation_crop="WHEAT",
            late_rotation_crop="WHEAT",
            lifecycle_windows=True,
        )

        self.assertTrue(all(plan["first_plant_day"] == 0 for plan in plans))
        self.assertTrue(
            all(
                plan["last_plant_day"]
                == 28 - CROP_DATA[str(plan["crop"])]["harvest_age"]
                for plan in plans
            )
        )

    def test_lifecycle_deadlines_can_preserve_opening_windows(self) -> None:
        state = scale_observation(day=0)
        plans = _dense_crop_plans(
            state["farms"][0],
            0,
            rotation_crop="WHEAT",
            late_rotation_crop="WHEAT",
            lifecycle_deadlines_only=True,
        )

        self.assertTrue(any(plan["first_plant_day"] == 4 for plan in plans))
        self.assertTrue(
            all(
                plan["last_plant_day"]
                == 28 - CROP_DATA[str(plan["crop"])]["harvest_age"]
                for plan in plans
            )
        )

    def test_carrot_rotation_reopens_expired_slots_safely(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        plans = _dense_crop_plans(
            farm,
            12,
            rotation_crop="CARROT",
            late_rotation_crop="CARROT",
        )

        self.assertTrue(any(plan["crop"] == "CARROT" for plan in plans))
        self.assertTrue(
            all(
                plan["last_plant_day"] == 22
                for plan in plans
                if plan["crop"] == "CARROT"
            )
        )

    def test_melon_rotation_accepts_a_later_safe_deadline(self) -> None:
        state = scale_observation(day=12)
        plans = _dense_crop_plans(
            state["farms"][0],
            12,
            rotation_crop="MELON",
            late_rotation_crop="MELON",
            rotation_last_plant_day=18,
            late_rotation_last_plant_day=18,
        )

        self.assertTrue(any(plan["crop"] == "MELON" for plan in plans))
        self.assertTrue(
            all(
                plan["last_plant_day"] == 18
                for plan in plans
                if plan["crop"] == "MELON"
            )
        )

    def test_unsafe_wheat_cohorts_are_not_admitted(self) -> None:
        sw_wheat = [
            plan
            for plan in DENSE_CROP_PLANS
            if plan["quadrant"] == "SW" and plan["crop"] == "WHEAT"
        ]
        delayed_nw = [
            plan
            for plan in DENSE_CROP_PLANS
            if plan["quadrant"] == "NW"
            and plan["crop"] == "WHEAT"
            and plan["first_plant_day"] == 4
        ]
        ne_wheat = [
            plan
            for plan in DENSE_CROP_PLANS
            if plan["quadrant"] == "NE" and plan["crop"] == "WHEAT"
        ]

        self.assertTrue(sw_wheat)
        self.assertTrue(
            all(plan["first_plant_day"] == 23 for plan in sw_wheat)
        )
        self.assertEqual({plan["block"] for plan in delayed_nw}, {1, 3, 4, 11})
        self.assertEqual({plan["block"] for plan in ne_wheat}, {40, 50})
        self.assertTrue(
            all(plan["first_plant_day"] == 23 for plan in ne_wheat)
        )

    def test_opening_assigns_two_pairs_to_nw(self) -> None:
        state = scale_observation(day=0)
        farm = state["farms"][0]

        self.assertEqual(_hand_target(0), 5)
        self.assertEqual(_pair_quadrants(0, farm), ("NW", "NW", "NW"))
        farm["unlocked_quadrants"].append("NE")
        self.assertEqual(_pair_quadrants(6, farm), ("NW", "NW", "NE"))
        self.assertEqual(_pair_quadrants(8, farm), ("NW", "NE", "NE"))

    def test_opening_prioritizes_cash_flow_before_strawberries(self) -> None:
        self.assertLess(_crop_priority(0, "MELON"), _crop_priority(0, "WHEAT"))
        self.assertLess(
            _crop_priority(0, "WHEAT"),
            _crop_priority(0, "STRAWBERRY"),
        )
        self.assertLess(
            _crop_priority(2, "STRAWBERRY"),
            _crop_priority(2, "WHEAT"),
        )

    def test_opening_buffers_one_seed_per_active_pair_and_crop(self) -> None:
        state = scale_observation(day=0)
        farm = state["farms"][0]
        farm["hands"] = [[4, 4] for _ in range(6)]

        self.assertEqual(
            _seed_orders(
                0,
                farm,
                state["private"],
                _dense_crop_plans(farm),
                3,
                ("NW", "NW", "NW"),
            ),
            [
                ["BUY_SEED", "MELON", 2],
                ["BUY_SEED", "WHEAT", 2],
            ],
        )

    def test_buffered_opening_buys_two_cycles_per_pair(self) -> None:
        state = scale_observation(day=0)
        farm = state["farms"][0]
        farm["hands"] = [[4, 4] for _ in range(6)]

        self.assertEqual(
            _seed_orders(
                0,
                farm,
                state["private"],
                _dense_crop_plans(farm),
                3,
                ("NW", "NW", "NW"),
                2,
            ),
            [
                ["BUY_SEED", "MELON", 4],
                ["BUY_SEED", "WHEAT", 4],
            ],
        )

    def test_wheat_only_buffer_leaves_premium_orders_unchanged(self) -> None:
        state = scale_observation(day=0)
        farm = state["farms"][0]
        farm["hands"] = [[4, 4] for _ in range(6)]

        self.assertEqual(
            _seed_orders(
                0,
                farm,
                state["private"],
                _dense_crop_plans(farm),
                3,
                ("NW", "NW", "NW"),
                1,
                2,
            ),
            [
                ["BUY_SEED", "MELON", 2],
                ["BUY_SEED", "WHEAT", 4],
            ],
        )

    def test_incremental_buffer_adds_one_global_wheat_seed(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        farm["hands"] = [[4, 4] for _ in range(12)]
        farm["unlocked_quadrants"].extend(["NE", "SW"])

        baseline = _seed_orders(
            12,
            farm,
            state["private"],
            _dense_crop_plans(
                farm,
                12,
                late_rotation_crop="WHEAT",
            ),
            6,
            ("NW", "NE", "SW"),
        )
        incremental = _seed_orders(
            12,
            farm,
            state["private"],
            _dense_crop_plans(
                farm,
                12,
                late_rotation_crop="WHEAT",
            ),
            6,
            ("NW", "NE", "SW"),
            1,
            None,
            1,
        )

        self.assertEqual(
            sum(
                order[2] for order in incremental
                if order[1] == "WHEAT"
            ),
            sum(
                order[2] for order in baseline
                if order[1] == "WHEAT"
            ) + 1,
        )

    def test_seed_reservation_funds_each_active_quadrant_pair(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        farm["hands"] = [[4, 4] for _ in range(12)]
        farm["unlocked_quadrants"].extend(["NE", "SW"])
        plans = tuple(
            {
                "id": f"{quadrant.lower()}_wheat_test",
                "quadrant": quadrant,
                "position": position,
                "crop": "WHEAT",
                "first_plant_day": 0,
                "last_plant_day": 22,
            }
            for quadrant, position in (
                ("NW", (0, 0)),
                ("NE", (5, 0)),
                ("SW", (0, 5)),
            )
        )

        self.assertEqual(
            _seed_orders(
                12,
                farm,
                state["private"],
                plans,
                6,
                ("NW", "NE", "SW"),
                reserve_seeds_per_quadrant=True,
            ),
            [["BUY_SEED", "WHEAT", 3]],
        )

    def test_paired_planting_uses_same_transition(self) -> None:
        state = scale_observation(day=0)
        farm = state["farms"][0]
        plan = _dense_crop_plans(farm)[0]
        target = tuple(plan["position"])
        positions = [target, target]
        actions = [None, None]
        state["private"]["seeds"]["MELON"] = 1

        _assign_paired_planting(
            0,
            farm,
            state["private"],
            (plan,),
            positions,
            actions,
        )

        self.assertEqual(actions, [["PLANT", "MELON"], ["WATER"]])

    def test_animal_service_preserves_one_crop_pair(self) -> None:
        state = scale_observation(day=2)
        farm = state["farms"][0]
        plans = tuple(
            plan for plan in ANIMAL_PLANS if plan["quadrant"] == "NW"
        )
        for plan in plans:
            x, y = plan["position"]
            farm["tiles"][y][x] = {
                "kind": "PASTURE",
                "animal": plan["animal"],
                "fed_today": True,
                "cared_today": False,
                "fertilizer_available": False,
                "yield_units": 0,
                "consecutive_unfed": 0,
            }
        positions = [tuple(plan["position"]) for plan in plans]
        positions.append((2, 2))
        actions = [None for _ in positions]

        _assign_limited_animal_services(
            plans,
            2,
            farm,
            positions,
            actions,
        )

        self.assertEqual(actions.count(["CARE"]), 3)
        self.assertEqual(actions.count(None), 2)

    def test_animal_service_can_care_before_daily_feed_completes(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        plan = ANIMAL_PLANS[0]
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PASTURE",
            "animal": "COW",
            "fed_today": False,
            "cared_today": False,
            "fertilizer_available": False,
            "yield_units": 0,
        }
        actions = [None]

        _assign_limited_animal_services(
            (plan,),
            12,
            farm,
            [tuple(plan["position"])],
            actions,
            crop_worker_reserve=0,
            anticipate_daily_feed=True,
        )

        self.assertEqual(actions, [["CARE"]])

    def test_final_strawberry_cleanup_precedes_decay(self) -> None:
        state = scale_observation(day=16)
        farm = state["farms"][0]
        plan = next(
            plan
            for plan in _dense_crop_plans(farm, 16)
            if plan["crop"] == "STRAWBERRY"
        )
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "STRAWBERRY",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 0,
            "yield_units": 0,
            "fertilized_until_day": -1,
        }
        positions = [tuple(plan["position"])]
        actions = [None]

        _assign_crop_tasks(
            16,
            farm,
            (plan,),
            positions,
            actions,
            critical=True,
        )

        self.assertEqual(actions, [["DIG"]])

    def test_capacity_mode_prioritizes_mature_wheat_harvest(self) -> None:
        state = scale_observation(day=16)
        farm = state["farms"][0]
        plan = next(
            plan for plan in _dense_crop_plans(
                farm,
                16,
                late_rotation_crop="WHEAT",
            )
            if plan["crop"] == "WHEAT"
        )
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 12,
            "watered_today": True,
            "consecutive_unwatered": 0,
            "yield_units": 4,
        }
        positions = [tuple(plan["position"])]
        actions = [None]

        _assign_crop_tasks(
            16,
            farm,
            (plan,),
            positions,
            actions,
            critical=True,
            prioritize_mature_harvest=True,
        )

        self.assertEqual(actions, [["HARVEST"]])

    def test_cross_quadrant_rescue_uses_otherwise_idle_worker(self) -> None:
        state = scale_observation(day=16)
        farm = state["farms"][0]
        farm["hands"] = [[4, 4], [4, 4]]
        farm["unlocked_quadrants"].append("NE")
        plans = tuple(
            plan for plan in _dense_crop_plans(
                farm,
                16,
                late_rotation_crop="WHEAT",
            )
            if plan["quadrant"] == "NE" and plan["crop"] == "WHEAT"
        )[:2]
        self.assertEqual(len(plans), 2)
        for plan in plans:
            x, y = plan["position"]
            farm["tiles"][y][x] = {
                "kind": "PLANT",
                "crop": "WHEAT",
                "planted_day": 12,
                "watered_today": True,
                "consecutive_unwatered": 0,
                "yield_units": 4,
            }

        farmer, hands = _worker_actions(
            (),
            16,
            farm,
            state["private"],
            plans,
            2,
            True,
            False,
            True,
            False,
            None,
            True,
        )

        self.assertEqual(
            sum(
                action[0] != "PASS"
                for action in [farmer, *hands]
            ),
            2,
        )

    def test_crop_first_mode_precedes_routine_animal_care(self) -> None:
        state = scale_observation(day=2)
        farm = state["farms"][0]
        animal_plan = ANIMAL_PLANS[0]
        ax, ay = animal_plan["position"]
        farm["tiles"][ay][ax] = {
            "kind": "PASTURE",
            "animal": animal_plan["animal"],
            "fed_today": True,
            "cared_today": False,
            "fertilizer_available": False,
            "yield_units": 0,
            "consecutive_unfed": 0,
        }
        crop_plan = next(
            plan for plan in _dense_crop_plans(farm, 2)
            if plan["crop"] == "WHEAT"
        )
        cx, cy = crop_plan["position"]
        farm["farmer"] = [cx, cy]
        farm["tiles"][cy][cx] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 0,
            "yield_units": 1,
        }

        farmer, _ = _worker_actions(
            (animal_plan,),
            2,
            farm,
            state["private"],
            (crop_plan,),
            0,
            False,
            False,
            False,
            False,
            None,
            False,
            True,
        )

        self.assertEqual(farmer, ["WATER"])

    def test_colocated_workers_pair_feed_and_care(self) -> None:
        state = scale_observation(day=12)
        farm = state["farms"][0]
        plan = ANIMAL_PLANS[0]
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PASTURE",
            "animal": "COW",
            "fed_today": False,
            "cared_today": False,
            "consecutive_unfed": 0,
        }
        actions = [None, None]

        paired = _assign_colocated_feed_care(
            (plan,),
            12,
            farm,
            [tuple(plan["position"]), tuple(plan["position"])],
            [{"WHEAT": 1}, {}],
            actions,
        )

        self.assertEqual(paired, {str(plan["id"])})
        self.assertEqual(actions, [["FEED"], ["CARE"]])

    def test_fertilized_capacity_pairs_fertilizer_and_water(self) -> None:
        state = scale_observation(day=11)
        farm = state["farms"][0]
        plan = next(
            plan for plan in _dense_crop_plans(farm, 11)
            if plan["crop"] == "STRAWBERRY"
        )
        target = tuple(plan["position"])
        x, y = target
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "STRAWBERRY",
            "planted_day": 2,
            "watered_today": False,
            "consecutive_unwatered": 0,
            "yield_units": 0,
            "fertilized_until_day": -1,
        }
        state["private"]["inventories"] = [
            {"FERTILIZER": 1},
            {},
        ]
        positions = [target, target]
        actions = [None, None]

        _assign_crop_fertilization(
            11,
            farm,
            state["private"],
            (plan,),
            positions,
            state["private"]["inventories"],
            actions,
        )

        self.assertEqual(actions, [["FERTILIZE"], ["WATER"]])

    def test_fertilization_limit_caps_selected_strawberries(self) -> None:
        state = scale_observation(day=11)
        farm = state["farms"][0]
        plans = tuple(
            plan for plan in _dense_crop_plans(farm, 11)
            if plan["crop"] == "STRAWBERRY"
        )[:2]
        positions = []
        inventories = []
        for plan in plans:
            x, y = plan["position"]
            farm["tiles"][y][x] = {
                "kind": "PLANT",
                "crop": "STRAWBERRY",
                "planted_day": 2,
                "watered_today": False,
                "consecutive_unwatered": 0,
                "yield_units": 0,
                "fertilized_until_day": -1,
            }
            positions.extend([tuple(plan["position"])] * 2)
            inventories.extend([{"FERTILIZER": 1}, {}])
        actions = [None for _ in positions]

        _assign_crop_fertilization(
            11,
            farm,
            state["private"],
            plans,
            positions,
            inventories,
            actions,
            1,
        )

        self.assertEqual(actions.count(["FERTILIZE"]), 1)
        self.assertEqual(actions.count(["WATER"]), 1)

    def test_fertilized_capacity_protects_active_crop_reserve(self) -> None:
        state = scale_observation(day=11)
        farm = state["farms"][0]
        plan = next(
            plan for plan in _dense_crop_plans(farm, 11)
            if plan["crop"] == "STRAWBERRY"
        )
        x, y = plan["position"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "STRAWBERRY",
            "planted_day": 2,
        }
        state["private"]["shed"]["FERTILIZER"] = 3

        orders = _sales_orders(
            11,
            farm,
            state["private"],
            (),
            set(),
            (plan,),
            2,
        )

        self.assertIn(["SELL", "FERTILIZER", 1], orders)

    def test_land_gate_uses_projected_sales_but_keeps_reserve(self) -> None:
        state = scale_observation(day=5, money=100)
        farm = state["farms"][0]
        market = {"prices": {"MILK": 160}}

        self.assertEqual(
            _land_orders(5, farm, market, [["SELL", "MILK", 10]]),
            [["BUY_LAND"]],
        )
        self.assertEqual(
            _land_orders(5, farm, market, [["SELL", "MILK", 7]]),
            [],
        )
        self.assertEqual(
            _land_orders(
                5,
                farm,
                market,
                [["SELL", "MILK", 8]],
                reserves=(0, 700),
            ),
            [["BUY_LAND"]],
        )
        farm["unlocked_quadrants"].append("NE")
        self.assertEqual(
            _land_orders(
                11,
                farm,
                market,
                [["SELL", "MILK", 20]],
                target_extra_land=1,
            ),
            [],
        )

    def test_wheat_trade_buys_only_inside_price_and_cash_guard(self) -> None:
        state = scale_observation(day=12, money=4000)
        farm = state["farms"][0]
        farm["unlocked_quadrants"].extend(["NE", "SW"])
        state["private"]["shed"]["WHEAT"] = 30

        self.assertEqual(
            _wheat_trade_orders(
                12,
                farm,
                state["private"],
                {"prices": {"WHEAT": 34}},
                [],
                48,
                34,
                3000,
            ),
            [["BUY_PRODUCT", "WHEAT", 18]],
        )
        self.assertEqual(
            _wheat_trade_orders(
                12,
                farm,
                state["private"],
                {"prices": {"WHEAT": 35}},
                [],
                48,
                34,
                3000,
            ),
            [],
        )
    def test_dynamic_land_gate_uses_occupancy_instead_of_day(self) -> None:
        state = scale_observation(day=2, money=1300)
        farm = state["farms"][0]
        for y in range(5):
            for x in range(5):
                if y * 5 + x >= 16:
                    break
                farm["tiles"][y][x] = {
                    "kind": "PLANT",
                    "crop": "WHEAT",
                    "planted_day": 0,
                    "watered_today": True,
                    "consecutive_unwatered": 0,
                }

        self.assertEqual(
            _land_orders(
                2,
                farm,
                {},
                [],
                dynamic_expansion=True,
            ),
            [["BUY_LAND"]],
        )

    def test_dynamic_land_gate_blocks_expansion_during_emergency(self) -> None:
        state = scale_observation(day=2, money=1300)
        farm = state["farms"][0]
        for index in range(16):
            x, y = index % 5, index // 5
            farm["tiles"][y][x] = (
                {"kind": "WEED"}
                if index == 0
                else {
                    "kind": "PLANT",
                    "crop": "WHEAT",
                    "planted_day": 0,
                    "watered_today": True,
                    "consecutive_unwatered": 0,
                }
            )

        self.assertEqual(
            _land_orders(
                2,
                farm,
                {},
                [],
                dynamic_expansion=True,
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
