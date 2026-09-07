import unittest

from rl.idle_rescue import (
    build_idle_rescue_agent,
    rescue_action,
    would_be_refused,
)


def plant(**kw):
    tile = {
        "kind": "PLANT", "crop": "WHEAT", "planted_day": 0,
        "watered_today": False, "yield_units": 0, "fertilized_until_day": -1,
    }
    tile.update(kw)
    return tile


def animal(**kw):
    tile = {
        "kind": "PASTURE", "animal": "COW", "yield_units": 0,
        "fed_today": False, "cared_today": False,
        "fertilizer_available": False,
    }
    tile.update(kw)
    return tile


def refused(action, tile, inventory=None, seeds=None, shed=None, day=5,
            x=0, y=0):
    return would_be_refused(action, tile, inventory or {}, seeds or {},
                            shed or {}, day, x, y)


class RefusalTests(unittest.TestCase):
    def test_movement_is_never_a_refusal(self) -> None:
        self.assertFalse(refused(["NORTH"], None))
        self.assertFalse(refused(["PASS"], None))

    def test_water_on_a_vanished_plant_is_refused(self) -> None:
        self.assertTrue(refused(["WATER"], None))
        self.assertTrue(refused(["WATER"], animal()))
        self.assertFalse(refused(["WATER"], plant()))

    def test_water_on_an_already_watered_plant_is_refused(self) -> None:
        self.assertTrue(refused(["WATER"], plant(watered_today=True)))

    def test_harvest_before_first_yield_day_is_refused(self) -> None:
        # WHEAT first yields on day 2; this one is a day old.
        self.assertTrue(
            refused(["HARVEST"], plant(yield_units=1, planted_day=4), day=5)
        )
        self.assertFalse(
            refused(["HARVEST"], plant(yield_units=1, planted_day=0), day=5)
        )

    def test_place_onto_an_occupied_pen_is_refused(self) -> None:
        self.assertTrue(
            refused(["PLACE", "COW"], animal(), inventory={"COW": 1})
        )

    def test_place_with_nothing_in_hand_is_refused(self) -> None:
        self.assertTrue(refused(["PLACE", "COW"], {"kind": "PASTURE"}))

    def test_place_onto_a_matching_empty_pen_is_allowed(self) -> None:
        self.assertFalse(
            refused(["PLACE", "COW"], {"kind": "PASTURE"},
                    inventory={"COW": 1})
        )

    def test_feed_without_wheat_is_refused(self) -> None:
        self.assertTrue(refused(["FEED"], animal()))
        self.assertFalse(refused(["FEED"], animal(), inventory={"WHEAT": 1}))

    def test_pickup_away_from_the_shed_is_refused(self) -> None:
        self.assertTrue(
            refused(["PICKUP", "WHEAT", 1], None, shed={"WHEAT": 9}, x=0, y=0)
        )
        self.assertFalse(
            refused(["PICKUP", "WHEAT", 1], None, shed={"WHEAT": 9}, x=4, y=3)
        )


class RescueChoiceTests(unittest.TestCase):
    def test_manure_is_collected_first(self) -> None:
        self.assertEqual(
            rescue_action(animal(fertilizer_available=True), {}, 5),
            ["COLLECT_FERTILIZER"],
        )

    def test_a_loaded_animal_is_harvested(self) -> None:
        self.assertEqual(
            rescue_action(animal(yield_units=3), {}, 5), ["HARVEST"]
        )

    def test_an_idle_animal_is_cared_for(self) -> None:
        self.assertEqual(rescue_action(animal(), {}, 5), ["CARE"])

    def test_a_dry_plant_is_watered(self) -> None:
        self.assertEqual(rescue_action(plant(), {}, 5), ["WATER"])

    def test_a_plant_is_never_harvested_by_the_rescue(self) -> None:
        # Harvesting destroys a non-ongoing crop, so the rescue must not
        # do it however many units are sitting there.
        self.assertEqual(
            rescue_action(plant(yield_units=5, watered_today=True), {}, 5),
            None,
        )

    def test_a_weed_is_dug(self) -> None:
        self.assertEqual(rescue_action({"kind": "WEED"}, {}, 5), ["DIG"])

    def test_empty_ground_offers_nothing(self) -> None:
        self.assertIsNone(rescue_action(None, {}, 5))


class WrapperTests(unittest.TestCase):
    def _observation(self, tiles, action):
        return {
            "player": 0,
            "day": 5,
            "farms": [{"tiles": tiles, "farmer": [0, 0], "hands": []}],
            "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
        }, action

    def test_a_refused_action_becomes_useful_work(self) -> None:
        tiles = [[animal(fertilizer_available=True)]]
        action = {"farmer": ["PLACE", "COW"], "hands": [], "market": []}
        observation, _ = self._observation(tiles, action)
        agent = build_idle_rescue_agent(lambda o: action)
        self.assertEqual(agent(observation)["farmer"], ["COLLECT_FERTILIZER"])

    def test_a_valid_action_is_left_alone(self) -> None:
        tiles = [[plant()]]
        action = {"farmer": ["WATER"], "hands": [], "market": []}
        observation, _ = self._observation(tiles, action)
        agent = build_idle_rescue_agent(lambda o: action)
        self.assertEqual(agent(observation)["farmer"], ["WATER"])

    def test_market_orders_are_untouched(self) -> None:
        tiles = [[None]]
        orders = [["SELL", "WHEAT", 5], ["HIRE"]]
        action = {"farmer": ["PASS"], "hands": [], "market": orders}
        observation, _ = self._observation(tiles, action)
        agent = build_idle_rescue_agent(lambda o: action)
        self.assertEqual(agent(observation)["market"], orders)

    def test_nothing_useful_leaves_the_action_as_it_was(self) -> None:
        tiles = [[None]]
        action = {"farmer": ["WATER"], "hands": [], "market": []}
        observation, _ = self._observation(tiles, action)
        agent = build_idle_rescue_agent(lambda o: action)
        self.assertEqual(agent(observation)["farmer"], ["WATER"])


if __name__ == "__main__":
    unittest.main()
