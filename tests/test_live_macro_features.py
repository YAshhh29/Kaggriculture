import unittest

from policies.live_macro_features import extract_live_macro_features
from tests.test_experimental_cow_agent import cow_tile
from tests.test_experimental_scale_agent import scale_observation
from tests.test_main import wheat_tile


class LiveMacroFeaturesTests(unittest.TestCase):
    def test_extracts_own_service_load_and_fertilizer_stock(self) -> None:
        state = scale_observation(day=6)
        state["farms"][0]["hands"] = [[3, 4]]
        state["farms"][0]["unlocked_quadrants"] = ["NW", "NE"]
        state["farms"][0]["tiles"][0][0] = wheat_tile(
            consecutive_unwatered=1,
            yield_units=2,
        )
        state["farms"][0]["tiles"][0][1] = cow_tile(
            consecutive_unfed=1,
            yield_units=3,
        )
        state["private"]["shed"]["FERTILIZER"] = 2
        state["private"]["inventories"] = [
            {"FERTILIZER": 1},
            {},
        ]

        features = extract_live_macro_features(state)

        self.assertEqual(features["own_hands"], 1.0)
        self.assertEqual(features["own_land"], 2.0)
        self.assertEqual(features["own_wheat"], 1.0)
        self.assertEqual(features["own_unwatered_crops"], 1.0)
        self.assertEqual(features["own_stressed_crops"], 1.0)
        self.assertEqual(features["own_harvestable_crop_units"], 2.0)
        self.assertEqual(features["own_animals"], 1.0)
        self.assertEqual(features["own_cows"], 1.0)
        self.assertEqual(features["own_sheep"], 0.0)
        self.assertEqual(features["own_geese"], 0.0)
        self.assertEqual(features["own_due_feed"], 1.0)
        self.assertEqual(features["own_collectable_animal_units"], 3.0)
        self.assertEqual(features["own_fertilizer_stock"], 3.0)
        self.assertEqual(features["own_service_tasks_per_worker"], 2.0)


if __name__ == "__main__":
    unittest.main()