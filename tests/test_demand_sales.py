import unittest

from rl.demand_sales import paced_orders, sell_allowance


def obs(step=100, money=5000, shed=None, shops=("BAKERY", "PIZZA_SHOP")):
    return {
        "step": step,
        "player": 0,
        "farms": [{"money": money}],
        "private": {"shed": shed or {}},
        "town": {"unlocked_shops": list(shops)},
    }


class AllowanceTests(unittest.TestCase):
    def test_allowance_tracks_town_demand(self) -> None:
        a = sell_allowance(obs(), pace=24.0, cash_floor=1200.0,
                           shed_pressure=80, closing_day=29)
        self.assertIsNotNone(a)
        # WHEAT is sold by both shops here, so it must out-rank TOMATO.
        self.assertGreater(a["WHEAT"], a["TOMATO"])

    def test_no_limit_on_the_closing_day(self) -> None:
        self.assertIsNone(sell_allowance(obs(step=29 * 24), pace=24.0,
                                         cash_floor=1200.0, shed_pressure=80,
                                         closing_day=29))

    def test_no_limit_when_cash_is_short(self) -> None:
        self.assertIsNone(sell_allowance(obs(money=10), pace=24.0,
                                         cash_floor=1200.0, shed_pressure=80,
                                         closing_day=29))

    def test_no_limit_when_the_shed_is_filling(self) -> None:
        self.assertIsNone(sell_allowance(obs(shed={"WHEAT": 90}), pace=24.0,
                                         cash_floor=1200.0, shed_pressure=80,
                                         closing_day=29))


class PacedOrderTests(unittest.TestCase):
    def test_a_big_sale_is_trimmed_to_the_pace(self) -> None:
        out = paced_orders(obs(), [["SELL", "WHEAT", 500]], pace=24.0)
        self.assertEqual(out[0][0], "SELL")
        self.assertLess(out[0][2], 500)

    def test_non_sell_orders_pass_through(self) -> None:
        orders = [["HIRE"], ["BUY_LAND"], ["BUY_SEED", "WHEAT", 5]]
        self.assertEqual(paced_orders(obs(), list(orders)), orders)

    def test_fertilizer_is_never_held(self) -> None:
        # The town buys no fertilizer, so its price never recovers.
        out = paced_orders(obs(), [["SELL", "FERTILIZER", 40]], pace=24.0)
        self.assertEqual(out[0][2], 40)

    def test_livestock_orders_are_untouched(self) -> None:
        out = paced_orders(obs(), [["SELL", "COW", 1]], pace=24.0)
        self.assertEqual(out[0], ["SELL", "COW", 1])

    def test_guards_release_everything(self) -> None:
        out = paced_orders(obs(money=5), [["SELL", "WHEAT", 500]], pace=24.0)
        self.assertEqual(out[0][2], 500)


if __name__ == "__main__":
    unittest.main()
