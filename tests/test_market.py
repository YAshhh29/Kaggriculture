import unittest

from candidates.market import (
    MARKET_I0,
    headroom,
    inventory_of,
    marginal_price,
    price_at,
    sale_revenue,
)


def obs(inventory=None):
    return {"market": {"inventory": inventory or {}}}


class PriceCurveTests(unittest.TestCase):
    def test_equilibrium_is_base_price(self) -> None:
        self.assertEqual(price_at("WHEAT", MARKET_I0), 25.0)
        self.assertEqual(price_at("EGG", MARKET_I0), 50.0)

    def test_selling_pushes_the_price_down(self) -> None:
        self.assertLess(
            price_at("MILK", MARKET_I0 + 40), price_at("MILK", MARKET_I0)
        )

    def test_scarcity_pushes_the_price_above_base(self) -> None:
        # This is the state every real game ends in for egg: the town keeps
        # eating them and nobody keeps geese.
        self.assertGreater(price_at("EGG", MARKET_I0 - 300), 50.0)

    def test_price_never_falls_below_the_floor(self) -> None:
        self.assertEqual(price_at("WOOL", MARKET_I0 + 5000), 1.0)

    def test_unknown_item_is_worthless(self) -> None:
        self.assertEqual(price_at("GOLD", MARKET_I0), 0.0)


class CollapseTests(unittest.TestCase):
    """The result Agent E's herd and crop choices are built on."""

    def test_wool_and_milk_collapse_inside_a_hundred_units(self) -> None:
        self.assertEqual(price_at("WOOL", MARKET_I0 + 100), 1.0)
        self.assertEqual(price_at("MILK", MARKET_I0 + 100), 1.0)

    def test_egg_survives_four_hundred_units(self) -> None:
        self.assertGreater(price_at("EGG", MARKET_I0 + 400), 35.0)

    def test_wheat_survives_four_hundred_units(self) -> None:
        self.assertGreater(price_at("WHEAT", MARKET_I0 + 400), 15.0)

    def test_egg_out_earns_wool_over_a_herds_output(self) -> None:
        # 400 units is roughly what a full herd produces in a season.
        self.assertGreater(
            sale_revenue(obs(), "EGG", 400), sale_revenue(obs(), "WOOL", 400)
        )


class RevenueTests(unittest.TestCase):
    def test_a_batch_is_worth_less_than_spot_times_count(self) -> None:
        spot = price_at("MELON", MARKET_I0)
        self.assertLess(sale_revenue(obs(), "MELON", 100), spot * 100)

    def test_zero_units_earn_nothing(self) -> None:
        self.assertEqual(sale_revenue(obs(), "MELON", 0), 0.0)

    def test_sold_already_shifts_the_starting_point(self) -> None:
        first = sale_revenue(obs(), "MILK", 30)
        later = sale_revenue(obs(), "MILK", 30, sold_already=120)
        self.assertGreater(first, later)

    def test_negative_sold_already_models_town_demand(self) -> None:
        # The town lifts inventory back out, so the same units fetch more.
        with_demand = sale_revenue(obs(), "WOOL", 30, sold_already=-200)
        self.assertGreater(with_demand, sale_revenue(obs(), "WOOL", 30))


class MarginalTests(unittest.TestCase):
    def test_marginal_price_reads_live_inventory(self) -> None:
        cheap = marginal_price(obs({"MILK": MARKET_I0 + 200}), "MILK")
        self.assertEqual(cheap, 1.0)

    def test_inventory_defaults_to_equilibrium(self) -> None:
        self.assertEqual(inventory_of(obs(), "WHEAT"), float(MARKET_I0))


class HeadroomTests(unittest.TestCase):
    def test_headroom_is_small_for_the_products_that_collapse(self) -> None:
        self.assertLess(headroom(obs(), "WOOL", 30.0), 100)
        self.assertLess(headroom(obs(), "MILK", 30.0), 100)

    def test_headroom_is_large_for_egg(self) -> None:
        self.assertGreater(headroom(obs(), "EGG", 30.0), 500)

    def test_no_headroom_below_a_price_already_unreachable(self) -> None:
        self.assertEqual(headroom(obs(), "WHEAT", 999.0), 0)


if __name__ == "__main__":
    unittest.main()
