import unittest

from research.training.train_market_ridge import (
    _solve_linear_system,
    evaluate_leave_one_seed_out,
    fit_ridge,
    predict,
)


class MarketRidgeTests(unittest.TestCase):
    def test_decision_threshold_reduces_sell_predictions(self) -> None:
        rows = [
            {
                **self._row(30, -5),
                "seed": 30,
                "intervention": {"baseline_choice": "HOLD"},
                "outcomes": {
                    "sell_minus_hold_terminal_coins": -5,
                    "hold": {"terminal_money": 100},
                    "sell": {"terminal_money": 95},
                },
                "features": {
                    **self._features(30),
                    "decision_observation_step": 1,
                },
            },
            {
                **self._row(37, 6),
                "seed": 31,
                "intervention": {"baseline_choice": "SELL"},
                "outcomes": {
                    "sell_minus_hold_terminal_coins": 6,
                    "hold": {"terminal_money": 100},
                    "sell": {"terminal_money": 106},
                },
                "features": {
                    **self._features(37),
                    "decision_observation_step": 1,
                },
            },
        ]

        low = evaluate_leave_one_seed_out(rows, alpha=1.0, decision_threshold=0)
        high = evaluate_leave_one_seed_out(rows, alpha=1.0, decision_threshold=100)

        self.assertGreater(
            sum(p["model_choice"] == "SELL" for p in low["predictions"]),
            sum(p["model_choice"] == "SELL" for p in high["predictions"]),
        )

    def test_solves_a_linear_system_with_pivoting(self) -> None:
        solution = _solve_linear_system(
            [[0.0, 2.0], [1.0, 1.0]],
            [4.0, 3.0],
        )

        self.assertAlmostEqual(solution[0], 1.0)
        self.assertAlmostEqual(solution[1], 2.0)

    def test_fits_price_direction(self) -> None:
        rows = [
            self._row(30, -5),
            self._row(31, -3),
            self._row(36, 4),
            self._row(37, 6),
        ]

        model = fit_ridge(rows, alpha=1.0)

        self.assertLess(predict(model, self._features(31)), 0)
        self.assertGreater(predict(model, self._features(36)), 0)

    @staticmethod
    def _row(price: int, delta: int) -> dict:
        return {
            "features": MarketRidgeTests._features(price),
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