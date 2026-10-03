import unittest

from candidates.demand import (
    CENTRE_INTERVAL,
    EPISODE_STEPS,
    SHOP_INTERVAL,
    demand_rate,
    preferred_animal,
    remaining_demand,
    shop_demand_per_event,
    unlocked_shops,
)


def obs(shops=None, prices=None, step=0):
    return {
        "step": step,
        "town": {"unlocked_shops": list(shops or [])},
        "market": {"prices": prices or {}, "inventory": {}},
    }


class ShopDemandTests(unittest.TestCase):
    def test_single_product_shops_count_double(self) -> None:
        # YARN_STORE sells only WOOL, so it removes two per event.
        self.assertEqual(shop_demand_per_event(["YARN_STORE"])["WOOL"], 2)
        self.assertEqual(shop_demand_per_event(["PET_CAFE"])["CARROT"], 2)

    def test_multi_product_shops_count_single(self) -> None:
        d = shop_demand_per_event(["PIZZA_SHOP"])
        self.assertEqual(d["MILK"], 1)
        self.assertEqual(d["TOMATO"], 1)
        self.assertEqual(d["WHEAT"], 1)

    def test_repeated_shops_stack(self) -> None:
        d = shop_demand_per_event(["YARN_STORE", "YARN_STORE"])
        self.assertEqual(d["WOOL"], 4)

    def test_melon_is_in_no_shop(self) -> None:
        every_shop = [
            "BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "YARN_STORE",
            "ICE_CREAM_SHOP", "PET_CAFE", "SMOOTHIE_SHOP", "FARMERS_MARKET",
        ]
        self.assertEqual(shop_demand_per_event(every_shop)["MELON"], 0)

    def test_unknown_shop_names_are_ignored(self) -> None:
        self.assertEqual(unlocked_shops(obs(["NOT_A_SHOP"])), [])


class RateTests(unittest.TestCase):
    def test_town_centre_floor_applies_without_shops(self) -> None:
        rate = demand_rate(obs([]))
        self.assertAlmostEqual(rate["MELON"], 1.0 / CENTRE_INTERVAL)

    def test_fertilizer_has_no_natural_demand(self) -> None:
        # Not sold by any shop and not a town-centre product.
        self.assertEqual(demand_rate(obs([]))["FERTILIZER"], 0.0)

    def test_shop_demand_adds_to_the_centre_floor(self) -> None:
        rate = demand_rate(obs(["YARN_STORE"]))
        expected = 2 / SHOP_INTERVAL + 1 / CENTRE_INTERVAL
        self.assertAlmostEqual(rate["WOOL"], expected)

    def test_remaining_demand_shrinks_as_the_game_runs_out(self) -> None:
        early = remaining_demand(obs(["YARN_STORE"], step=0))["WOOL"]
        late = remaining_demand(obs(["YARN_STORE"], step=700))["WOOL"]
        self.assertGreater(early, late)

    def test_remaining_demand_is_zero_at_the_end(self) -> None:
        end = remaining_demand(obs(["YARN_STORE"], step=EPISODE_STEPS))
        self.assertEqual(end["WOOL"], 0.0)


class PreferredAnimalTests(unittest.TestCase):
    def test_wool_town_prefers_sheep(self) -> None:
        state = obs(
            ["YARN_STORE", "YARN_STORE"],
            prices={"WOOL": 200, "MILK": 100},
        )
        self.assertEqual(preferred_animal(state), "SHEEP")

    def test_milk_town_prefers_cows(self) -> None:
        state = obs(
            ["PIZZA_SHOP", "SMOOTHIE_SHOP", "ICE_CREAM_SHOP"],
            prices={"WOOL": 50, "MILK": 160},
        )
        self.assertEqual(preferred_animal(state), "COW")

    def test_a_near_tie_names_no_winner(self) -> None:
        # Equal demand and equal price -- not worth disturbing a route.
        state = obs([], prices={"WOOL": 100, "MILK": 100})
        self.assertIsNone(preferred_animal(state))

    def test_margin_is_respected(self) -> None:
        state = obs(["YARN_STORE"], prices={"WOOL": 100, "MILK": 100})
        self.assertIsNone(preferred_animal(state, margin=99.0))
        self.assertIsNotNone(preferred_animal(state, margin=1.01))

    def test_price_of_zero_does_not_crash(self) -> None:
        state = obs([], prices={})
        self.assertIsNone(preferred_animal(state))


if __name__ == "__main__":
    unittest.main()
