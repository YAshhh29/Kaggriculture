import unittest

from agents.experimental_center_out_agent import (
    ANIMAL_PLANS,
    CENTER_OUT_BLOCKS,
    CORE_ANIMAL_BLOCKS,
    CROP_PLANS,
    LAND_SEQUENCE,
    MAX_MELONS,
    MAX_STRAWBERRIES,
    MAX_CROP_SLOTS_PER_QUADRANT,
    _crop_operations,
    _crop_task_groups,
    _crop_seed_orders,
    _crop_task_groups,
    _assign_global_crop_deadlines,
    _daily_hand_target,
    _fertilizer_reserve,
    _land_orders,
    _managed_crop_plans,
    _worker_actions,
    agent,
    block_to_position,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalCenterOutAgentTests(unittest.TestCase):
    def test_block_numbers_map_left_to_right_then_top_to_bottom(self) -> None:
        self.assertEqual(block_to_position(1), (0, 0))
        self.assertEqual(block_to_position(34), (3, 3))
        self.assertEqual(block_to_position(45), (4, 4))
        self.assertEqual(block_to_position(100), (9, 9))

    def test_nw_core_and_first_crop_shell_match_the_spatial_plan(self) -> None:
        self.assertEqual(CORE_ANIMAL_BLOCKS["NW"], (34, 35, 44, 45))
        self.assertEqual(
            CENTER_OUT_BLOCKS["NW"][:5],
            (25, 24, 23, 33, 43),
        )

    def test_land_expands_from_starting_nw_to_ne_then_sw(self) -> None:
        self.assertEqual(LAND_SEQUENCE, ("NW", "NE", "SW"))

    def test_premium_crop_exposure_is_bounded(self) -> None:
        self.assertGreaterEqual(MAX_STRAWBERRIES, 1)
        self.assertLessEqual(MAX_STRAWBERRIES, 4)
        self.assertEqual(MAX_MELONS, 2)

    def test_each_unlocked_core_balances_milk_and_wool(self) -> None:
        for quadrant in LAND_SEQUENCE:
            plans = [
                plan for plan in ANIMAL_PLANS
                if plan["quadrant"] == quadrant
            ]
            self.assertEqual(len(plans), 4)
            self.assertEqual(
                [plan["animal"] for plan in plans].count("COW"),
                2,
            )
            self.assertEqual(
                [plan["animal"] for plan in plans].count("SHEEP"),
                2,
            )
            self.assertEqual(
                {plan["block"] for plan in plans},
                set(CORE_ANIMAL_BLOCKS[quadrant]),
            )

    def test_crop_plan_uses_only_center_out_blocks(self) -> None:
        for quadrant in LAND_SEQUENCE:
            planned_blocks = {
                plan["block"]
                for plan in CROP_PLANS
                if plan["quadrant"] == quadrant
            }
            self.assertTrue(planned_blocks)
            self.assertTrue(
                planned_blocks.issubset(set(CENTER_OUT_BLOCKS[quadrant]))
            )

    def test_crop_mix_has_four_strawberries_and_two_melons(self) -> None:
        crops = [plan["crop"] for plan in CROP_PLANS]
        self.assertEqual(crops.count("STRAWBERRY"), MAX_STRAWBERRIES)
        self.assertEqual(crops.count("MELON"), MAX_MELONS)
        self.assertIn("CARROT", crops)
        self.assertIn("TOMATO", crops)
        self.assertIn("WHEAT", crops)

    def test_each_pair_manages_six_center_out_slots(self) -> None:
        state = scale_observation()
        plans = _managed_crop_plans(state["farms"][0])

        self.assertEqual(MAX_CROP_SLOTS_PER_QUADRANT, 6)
        self.assertEqual(len(plans), 6)
        self.assertEqual(
            tuple(plan["block"] for plan in plans),
            tuple(
                block
                for block, _ in (
                    (25, "WHEAT"), (24, "WHEAT"),
                    (43, "CARROT"), (15, "TOMATO"),
                    (14, "STRAWBERRY"), (13, "MELON"),
                )
            ),
        )

    def test_strawberry_production_day_requires_fertilizer_and_water(self) -> None:
        tile = {
            "kind": "PLANT",
            "crop": "STRAWBERRY",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 0,
            "yield_units": 0,
            "fertilized_until_day": -1,
        }

        self.assertEqual(
            _crop_operations(9, tile),
            {"FERTILIZE", "WATER"},
        )

    def test_urgent_strawberry_waits_for_paired_fertilizer_and_water(self) -> None:
        state = scale_observation(day=13)
        plan = next(
            plan
            for plan in CROP_PLANS
            if plan["quadrant"] == "NW"
            and plan["crop"] == "STRAWBERRY"
        )
        x, y = plan["position"]
        state["farms"][0]["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "STRAWBERRY",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 0,
            "fertilized_until_day": 11,
        }
        actions = [None]

        _assign_global_crop_deadlines(
            13,
            state["farms"][0],
            [(4, 4)],
            actions,
        )

        self.assertEqual(actions, [None])

    def test_sw_strawberries_are_first_after_land_unlock(self) -> None:
        state = scale_observation(day=11)
        state["farms"][0]["unlocked_quadrants"].extend(["NE", "SW"])

        sw_plans = [
            plan
            for plan in _managed_crop_plans(state["farms"][0])
            if plan["quadrant"] == "SW"
        ]

        self.assertEqual(
            [(plan["block"], plan["crop"]) for plan in sw_plans[:2]],
            [(53, "STRAWBERRY"), (63, "STRAWBERRY")],
        )

    def test_one_time_crop_waters_peak_day_before_harvest(self) -> None:
        tile = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 0,
            "yield_units": 3,
            "fertilized_until_day": -1,
        }

        self.assertEqual(_crop_operations(4, tile), {"WATER"})
        tile["watered_today"] = True
        self.assertEqual(_crop_operations(4, tile), {"HARVEST"})

    def test_overdue_one_time_crop_harvests_without_wasted_water(self) -> None:
        tile = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 2,
            "fertilized_until_day": -1,
        }

        self.assertEqual(_crop_operations(5, tile), {"HARVEST"})

    def test_spent_ongoing_crop_is_dug_instead_of_watered(self) -> None:
        tile = {
            "kind": "PLANT",
            "crop": "TOMATO",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 0,
            "fertilized_until_day": -1,
        }

        self.assertEqual(_crop_operations(12, tile), {"DIG"})

    def test_tomato_production_day_waters_then_harvests(self) -> None:
        tile = {
            "kind": "PLANT",
            "crop": "TOMATO",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 1,
            "fertilized_until_day": -1,
        }

        self.assertEqual(_crop_operations(8, tile), {"WATER", "HARVEST"})

    def test_opening_buys_balanced_animals_within_order_cap(self) -> None:
        decision = agent(scale_observation())

        self.assertEqual(len(decision["market"]), 10)
        self.assertNotIn(["BUY_ANIMAL", "GOOSE", 1], decision["market"])
        self.assertIn(["BUY_ANIMAL", "COW", 2], decision["market"])
        self.assertIn(["BUY_ANIMAL", "SHEEP", 2], decision["market"])
        self.assertEqual(decision["market"].count(["HIRE"]), 8)

    def test_first_center_out_crop_is_planted_and_watered_together(self) -> None:
        state = scale_observation(day=0, hour=1)
        target = list(block_to_position(25))
        state["farms"][0]["hands"] = [
            [4, 4], [4, 4], [4, 4], [4, 4], [4, 4],
            target, target, [4, 4],
        ]
        state["private"]["inventories"] = [{} for _ in range(9)]
        state["private"]["seeds"].update(
            {
                "WHEAT": 1,
                "CARROT": 0,
                "TOMATO": 0,
                "STRAWBERRY": 0,
                "MELON": 0,
            }
        )

        decision = agent(state)

        self.assertEqual(decision["hands"][5], ["PLANT", "WHEAT"])
        self.assertEqual(decision["hands"][6], ["WATER"])

    def test_fertilizer_reserve_scales_with_owned_strawberries(self) -> None:
        state = scale_observation(day=8)
        farm = state["farms"][0]
        self.assertEqual(_fertilizer_reserve(8, farm), 2)

        farm["unlocked_quadrants"].append("NE")
        self.assertEqual(_fertilizer_reserve(8, farm), 4)

        farm["unlocked_quadrants"].append("SW")
        self.assertEqual(_fertilizer_reserve(8, farm), 8)

    def test_seed_orders_buy_only_each_pairs_next_admissible_seed(self) -> None:
        state = scale_observation(day=0)
        state["private"]["seeds"].update(
            {
                "WHEAT": 0,
                "CARROT": 0,
                "TOMATO": 0,
                "STRAWBERRY": 0,
                "MELON": 0,
            }
        )

        self.assertEqual(
            _crop_seed_orders(
                0,
                state["farms"][0],
                state["private"],
            ),
            [["BUY_SEED", "WHEAT", 1]],
        )

    def test_seed_orders_skip_capacity_blocked_nw_staples(self) -> None:
        state = scale_observation(day=4)
        farm = state["farms"][0]
        plans = tuple(
            plan
            for plan in _managed_crop_plans(farm)
            if plan["quadrant"] == "NW"
        )
        for block in (25, 13):
            plan = next(plan for plan in plans if plan["block"] == block)
            x, y = plan["position"]
            farm["tiles"][y][x] = {
                "kind": "PLANT",
                "crop": plan["crop"],
                "planted_day": 2,
                "watered_today": True,
                "consecutive_unwatered": 0,
                "yield_units": 1,
                "fertilized_until_day": -1,
            }
        state["private"]["seeds"].update(
            {
                "WHEAT": 0,
                "CARROT": 0,
                "TOMATO": 0,
                "STRAWBERRY": 0,
                "MELON": 0,
            }
        )

        self.assertEqual(
            _crop_seed_orders(4, farm, state["private"]),
            [["BUY_SEED", "TOMATO", 1]],
        )

    def test_land_gates_ne_then_sw_with_cash_reserves(self) -> None:
        farm = scale_observation(day=6, money=2_199)["farms"][0]
        self.assertEqual(_land_orders(6, farm, 2), [])
        farm["money"] = 2_200
        self.assertEqual(_land_orders(6, farm, 2), [["BUY_LAND"]])

        farm["unlocked_quadrants"].append("NE")
        farm["money"] = 4_199
        self.assertEqual(_land_orders(11, farm, 2), [])
        farm["money"] = 4_200
        self.assertEqual(_land_orders(11, farm, 2), [["BUY_LAND"]])

    def test_any_idle_worker_can_harvest_overdue_crop(self) -> None:
        state = scale_observation(day=5)
        position = block_to_position(25)
        state["farms"][0]["tiles"][position[1]][position[0]] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 3,
            "fertilized_until_day": -1,
        }
        positions = [(4, 4)]
        actions = [None]

        _assign_global_crop_deadlines(
            5,
            state["farms"][0],
            positions,
            actions,
        )

        self.assertEqual(actions[0], ["NORTH"])

    def test_one_time_admission_closes_before_endgame_taper(self) -> None:
        from agents.experimental_center_out_agent import CROP_DATA

        self.assertEqual(CROP_DATA["WHEAT"]["last_plant_day"], 22)
        self.assertEqual(CROP_DATA["CARROT"]["last_plant_day"], 22)

    def test_nw_defers_wheat_or_carrot_at_two_active_one_time_crops(self) -> None:
        state = scale_observation(day=4)
        plans = tuple(
            plan
            for plan in _managed_crop_plans(state["farms"][0])
            if plan["quadrant"] == "NW"
        )
        for block in (25, 13):
            plan = next(plan for plan in plans if plan["block"] == block)
            x, y = plan["position"]
            state["farms"][0]["tiles"][y][x] = {
                "kind": "PLANT",
                "crop": plan["crop"],
                "planted_day": 2,
                "watered_today": True,
                "consecutive_unwatered": 0,
                "yield_units": 1,
                "fertilized_until_day": -1,
            }

        groups = _crop_task_groups(4, state["farms"][0], plans)

        self.assertFalse(
            any(
                plan["crop"] in {"WHEAT", "CARROT"}
                for plan in groups["plant"]
            )
        )

    def test_ne_defers_carrot_at_three_active_one_time_crops(self) -> None:
        state = scale_observation(day=16)
        state["farms"][0]["unlocked_quadrants"].append("NE")
        plans = tuple(
            plan
            for plan in _managed_crop_plans(state["farms"][0])
            if plan["quadrant"] == "NE"
        )
        for block in (26, 27, 18):
            plan = next(plan for plan in plans if plan["block"] == block)
            x, y = plan["position"]
            state["farms"][0]["tiles"][y][x] = {
                "kind": "PLANT",
                "crop": plan["crop"],
                "planted_day": 14,
                "watered_today": True,
                "consecutive_unwatered": 0,
                "yield_units": 1,
                "fertilized_until_day": -1,
            }

        groups = _crop_task_groups(16, state["farms"][0], plans)

        self.assertNotIn(
            next(plan for plan in plans if plan["block"] == 48),
            groups["plant"],
        )

    def test_three_crop_pairs_remain_staffed_through_day_28(self) -> None:
        farm = scale_observation()["farms"][0]

        self.assertEqual(_daily_hand_target(0, farm, 12), 11)
        self.assertEqual(_daily_hand_target(25, farm, 12), 11)
        self.assertEqual(_daily_hand_target(28, farm, 12), 11)
        self.assertEqual(_daily_hand_target(29, farm, 12), 4)

    def test_animal_service_precedes_cross_quadrant_crop_rescue(self) -> None:
        state = scale_observation(day=5)
        animal = ANIMAL_PLANS[0]
        animal_x, animal_y = animal["position"]
        state["farms"][0]["tiles"][animal_y][animal_x] = {
            "kind": animal["structure"],
            "animal": animal["animal"],
            "placed_day": 0,
            "yield_units": 0,
            "fed_today": False,
            "consecutive_unfed": 0,
            "cared_today": False,
            "fertilizer_available": True,
            "pending_care_bonus": 0,
        }
        crop_x, crop_y = block_to_position(25)
        state["farms"][0]["tiles"][crop_y][crop_x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 3,
            "fertilized_until_day": -1,
        }

        farmer, _ = _worker_actions(
            (animal,),
            5,
            state["farms"][0],
            state["private"],
        )

        self.assertEqual(farmer, ["COLLECT_FERTILIZER"])


if __name__ == "__main__":
    unittest.main()