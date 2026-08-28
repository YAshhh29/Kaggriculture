import unittest

from core.economics import (
    animal_opportunity,
    crop_opportunity,
    daily_product_demand,
    fertilizer_marginal_units,
    fertilizer_net_value,
    profitable_feed_reserve_days,
    rank_crop_opportunities,
)
from tests.test_experimental_cow_agent import cow_tile
from tests.test_experimental_scale_agent import scale_observation


class EconomicsTests(unittest.TestCase):
    def test_melon_fertilizer_accelerates_two_units_within_cap(self) -> None:
        tile = {
            "kind": "PLANT",
            "crop": "MELON",
            "planted_day": 4,
            "watered_today": False,
            "yield_units": 1,
            "fertilized_until_day": -1,
        }

        self.assertEqual(fertilizer_marginal_units(10, tile), 2)

    def test_strawberry_fertilizer_values_two_scheduled_yields(self) -> None:
        state = scale_observation(day=9)
        state["market"]["prices"].update(
            {"STRAWBERRY": 140, "FERTILIZER": 100}
        )
        tile = {
            "kind": "PLANT",
            "crop": "STRAWBERRY",
            "planted_day": 0,
            "watered_today": False,
            "yield_units": 0,
            "fertilized_until_day": -1,
        }

        self.assertEqual(fertilizer_marginal_units(9, tile), 2)
        self.assertEqual(fertilizer_net_value(state, tile), 135.0)
        tile["fertilized_until_day"] = 10
        self.assertEqual(fertilizer_marginal_units(9, tile), 0)

    def test_feed_reserve_expands_only_when_animal_value_beats_wheat(
        self,
    ) -> None:
        profitable = scale_observation(day=12)
        expensive_wheat = scale_observation(day=12)
        for state in (profitable, expensive_wheat):
            state["farms"][0]["tiles"][0][0] = cow_tile()
            state["market"]["prices"]["MILK"] = 160
        profitable["market"]["prices"]["WHEAT"] = 25
        expensive_wheat["market"]["prices"]["WHEAT"] = 200

        self.assertEqual(profitable_feed_reserve_days(profitable), 3)
        self.assertEqual(profitable_feed_reserve_days(expensive_wheat), 1)

    def test_duplicate_single_product_shops_compound_demand(self) -> None:
        demand = daily_product_demand(["PET_CAFE", "PET_CAFE"])

        self.assertEqual(demand["CARROT"], 25)
        self.assertEqual(demand["MELON"], 1)

    def test_lifecycle_deadline_is_derived_from_cashable_day(self) -> None:
        state = scale_observation(day=24)

        wheat = crop_opportunity(state, "WHEAT")
        strawberry = crop_opportunity(state, "STRAWBERRY")

        self.assertEqual(wheat.last_plant_day, 24)
        self.assertTrue(wheat.feasible)
        self.assertEqual(strawberry.last_plant_day, 12)
        self.assertFalse(strawberry.feasible)

    def test_specialist_carrot_demand_changes_crop_ranking(self) -> None:
        state = scale_observation(day=10)
        state["town"]["unlocked_shops"] = ["PET_CAFE", "PET_CAFE"]

        ranking = rank_crop_opportunities(
            state,
            ("WHEAT", "CARROT"),
        )

        self.assertEqual(ranking[0].crop, "CARROT")
        self.assertGreater(ranking[0].score, ranking[1].score)

    def test_unserved_melon_is_discounted_despite_high_base_price(
        self,
    ) -> None:
        state = scale_observation(day=10)

        ranking = rank_crop_opportunities(
            state,
            ("WHEAT", "MELON"),
        )

        self.assertEqual(ranking[0].crop, "WHEAT")

    def test_yarn_store_improves_sheep_opportunity(self) -> None:
        baseline = scale_observation(day=10)
        demanded = scale_observation(day=10)
        demanded["town"]["unlocked_shops"] = ["YARN_STORE"]

        self.assertGreater(
            animal_opportunity(demanded, "SHEEP").score,
            animal_opportunity(baseline, "SHEEP").score,
        )


if __name__ == "__main__":
    unittest.main()
