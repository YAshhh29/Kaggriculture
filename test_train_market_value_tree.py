import unittest

from research.training.train_market_value_tree import (
    _strategy_summary,
    fit_tree,
    predict,
)


class MarketValueTreeTests(unittest.TestCase):
    def test_summarizes_regret_by_seed(self) -> None:
        rows = [
            {"seed": 30, "model_regret": 2},
            {"seed": 30, "model_regret": 3},
            {"seed": 31, "model_regret": 1},
        ]

        summary = _strategy_summary(rows, "model")

        self.assertEqual(summary["regret_by_seed"], {"30": 5.0, "31": 1.0})
        self.assertEqual(summary["worst_seed_regret"], 5.0)

    def test_fits_a_simple_price_split(self) -> None:
        rows = [
            self._row(30, -5),
            self._row(31, -3),
            self._row(36, 4),
            self._row(37, 6),
        ]

        tree = fit_tree(rows, max_depth=1, min_leaf=2)

        self.assertEqual(tree["feature"], "wheat_market_price")
        self.assertLess(predict(tree, self._features(31)), 0)
        self.assertGreater(predict(tree, self._features(36)), 0)

    @staticmethod
    def _row(price: int, delta: int) -> dict:
        return {
            "features": MarketValueTreeTests._features(price),
            "outcomes": {"sell_minus_hold_terminal_coins": delta},
        }

    @staticmethod
    def _features(price: int) -> dict:
        return {
            "day": 1,
            "hour": 0,
            "money": 3_000,
            "wheat_seeds": 0,
            "shed_wheat": 24,
            "carried_wheat": 0,
            "planted_wheat": 6,
            "wheat_market_price": price,
            "wheat_market_inventory": 1_000,
        }


if __name__ == "__main__":
    unittest.main()