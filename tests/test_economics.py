import unittest

from rl.economics import (
    BASE_PRICE,
    LAST_DAY,
    care_value,
    collect_fertilizer_value,
    crop_can_mature,
    days_left,
    feed_value,
    fertilize_value,
    harvest_value,
    live_price,
    plant_value,
    water_value,
)


def obs(prices=None):
    return {"market": {"prices": prices or {}}}


def plant(crop, planted_day, **kw):
    tile = {
        "kind": "PLANT",
        "crop": crop,
        "planted_day": planted_day,
        "watered_today": False,
        "fertilized_until_day": -1,
        "yield_units": 0,
        "consecutive_unwatered": 0,
    }
    tile.update(kw)
    return tile


def animal(kind, **kw):
    tile = {
        "kind": "PASTURE",
        "animal": kind,
        "fed_today": False,
        "cared_today": False,
        "yield_units": 0,
        "consecutive_unfed": 0,
        "fertilizer_available": False,
    }
    tile.update(kw)
    return tile


class PriceTests(unittest.TestCase):
    def test_live_price_prefers_the_market(self) -> None:
        self.assertEqual(live_price(obs({"WHEAT": 41}), "WHEAT"), 41.0)

    def test_live_price_falls_back_to_base(self) -> None:
        self.assertEqual(live_price(obs(), "WHEAT"), float(BASE_PRICE["WHEAT"]))

    def test_days_left_never_negative(self) -> None:
        self.assertEqual(days_left(LAST_DAY + 5), 0)


class MaturityTests(unittest.TestCase):
    def test_late_strawberry_cannot_mature(self) -> None:
        # STRAWBERRY first yields 10 days after planting.
        self.assertFalse(
            crop_can_mature("STRAWBERRY", LAST_DAY - 5, LAST_DAY - 5)
        )

    def test_early_strawberry_can_mature(self) -> None:
        self.assertTrue(crop_can_mature("STRAWBERRY", 2, 2))

    def test_wheat_planted_late_still_matures(self) -> None:
        self.assertTrue(
            crop_can_mature("WHEAT", LAST_DAY - 2, LAST_DAY - 2)
        )


class WaterTests(unittest.TestCase):
    def test_watering_in_window_is_worth_one_unit(self) -> None:
        # WHEAT window is age 2..4; at age 3 an unfertilized water adds 1.
        value = water_value(obs({"WHEAT": 40}), plant("WHEAT", 0), day=3)
        self.assertEqual(value, 40.0)

    def test_fertilized_watering_is_worth_double(self) -> None:
        tile = plant("WHEAT", 0, fertilized_until_day=5)
        self.assertEqual(water_value(obs({"WHEAT": 40}), tile, day=3), 80.0)

    def test_watering_a_doomed_crop_is_worthless(self) -> None:
        tile = plant("STRAWBERRY", LAST_DAY - 3)
        self.assertEqual(water_value(obs(), tile, day=LAST_DAY - 3), 0.0)

    def test_full_tile_gains_nothing_from_water(self) -> None:
        tile = plant("WHEAT", 0, yield_units=6)
        self.assertEqual(water_value(obs({"WHEAT": 40}), tile, day=3), 0.0)

    def test_outside_window_only_rescues_from_weeds(self) -> None:
        safe = plant("WHEAT", 0)
        at_risk = plant("WHEAT", 0, consecutive_unwatered=1)
        self.assertEqual(water_value(obs({"WHEAT": 40}), safe, day=1), 0.0)
        self.assertGreater(water_value(obs({"WHEAT": 40}), at_risk, day=1), 0.0)


class FertilizeTests(unittest.TestCase):
    def test_fertilizing_in_window_beats_selling_it(self) -> None:
        tile = plant("WHEAT", 0)
        value = fertilize_value(
            obs({"WHEAT": 40, "FERTILIZER": 45}), tile, day=2
        )
        self.assertGreater(value, 0.0)

    def test_already_fertilized_is_worthless(self) -> None:
        tile = plant("WHEAT", 0, fertilized_until_day=9)
        self.assertEqual(fertilize_value(obs(), tile, day=3), 0.0)

    def test_doomed_crop_is_not_worth_fertilizer(self) -> None:
        tile = plant("STRAWBERRY", LAST_DAY - 2)
        self.assertEqual(
            fertilize_value(obs(), tile, day=LAST_DAY - 2), 0.0
        )

    def test_full_tile_is_not_worth_fertilizer(self) -> None:
        tile = plant("WHEAT", 0, yield_units=6)
        self.assertEqual(fertilize_value(obs(), tile, day=3), 0.0)


class HarvestTests(unittest.TestCase):
    def test_crop_harvest_is_units_times_price(self) -> None:
        tile = plant("MELON", 0, yield_units=4)
        self.assertEqual(harvest_value(obs({"MELON": 200}), tile), 800.0)

    def test_animal_harvest_uses_its_product_price(self) -> None:
        tile = animal("COW", yield_units=3)
        self.assertEqual(harvest_value(obs({"MILK": 150}), tile), 450.0)

    def test_empty_tile_harvest_is_zero(self) -> None:
        self.assertEqual(harvest_value(obs(), plant("WHEAT", 0)), 0.0)


class LivestockTests(unittest.TestCase):
    def test_starving_animal_is_worth_more_than_a_fed_one(self) -> None:
        starving = animal("COW", consecutive_unfed=1)
        calm = animal("COW")
        self.assertGreater(
            feed_value(obs({"MILK": 160}), starving, day=10),
            feed_value(obs({"MILK": 160}), calm, day=10),
        )

    def test_feeding_is_worthless_after_the_season(self) -> None:
        self.assertEqual(feed_value(obs(), animal("COW"), day=LAST_DAY), 0.0)

    def test_already_fed_animal_needs_nothing(self) -> None:
        self.assertEqual(
            feed_value(obs(), animal("COW", fed_today=True), day=10), 0.0
        )

    def test_care_is_worth_one_product_unit(self) -> None:
        self.assertEqual(
            care_value(obs({"WOOL": 190}), animal("SHEEP"), day=10), 190.0
        )

    def test_care_on_a_full_animal_is_worthless(self) -> None:
        full = animal("SHEEP", yield_units=6)
        self.assertEqual(care_value(obs({"WOOL": 190}), full, day=10), 0.0)

    def test_collect_needs_available_fertilizer(self) -> None:
        self.assertEqual(collect_fertilizer_value(obs(), animal("COW")), 0.0)
        ready = animal("COW", fertilizer_available=True)
        self.assertGreater(collect_fertilizer_value(obs(), ready), 0.0)


class PlantTests(unittest.TestCase):
    def test_planting_late_strawberry_is_worthless(self) -> None:
        self.assertEqual(
            plant_value(obs(), "STRAWBERRY", day=LAST_DAY - 3), 0.0
        )

    def test_planting_wheat_late_still_pays(self) -> None:
        self.assertGreater(
            plant_value(obs({"WHEAT": 40}), "WHEAT", day=LAST_DAY - 3), 0.0
        )

    def test_seed_cost_is_subtracted(self) -> None:
        cheap = plant_value(obs({"WHEAT": 1}), "WHEAT", day=2)
        self.assertLess(cheap, 0.0)


if __name__ == "__main__":
    unittest.main()
