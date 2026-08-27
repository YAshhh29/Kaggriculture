import unittest
from unittest.mock import patch

from research.evaluation.evaluate_market_models import evaluate_grid


class EvaluateMarketModelsTests(unittest.TestCase):
    @patch("research.evaluation.evaluate_market_models.RIDGE_ALPHAS", (1.0,))
    @patch(
        "research.evaluation.evaluate_market_models.TREE_CONFIGURATIONS",
        [(1, 2)],
    )
    @patch("research.evaluation.evaluate_market_models.evaluate_ridge")
    @patch("research.evaluation.evaluate_market_models.evaluate_tree")
    def test_selects_only_model_beating_total_and_worst_seed_regret(
        self,
        tree_evaluator,
        ridge_evaluator,
    ) -> None:
        tree_evaluator.return_value = self._result(8, 4, 10, 5)
        ridge_evaluator.return_value = self._result(
            7,
            3,
            10,
            5,
            choices=(2, 0),
        )

        report = evaluate_grid([{"seed": 30}])

        self.assertEqual(report["qualifying_configurations"], 1)
        self.assertEqual(
            report["selected_configuration"]["family"],
            "tree",
        )

    @staticmethod
    def _result(
        model_total: int,
        model_worst: int,
        v9_total: int,
        v9_worst: int,
        choices: tuple[int, int] = (1, 1),
    ) -> dict:
        return {
            "model": {
                "total_one_step_regret": model_total,
                "worst_seed_regret": model_worst,
            },
            "v9_behavior": {
                "total_one_step_regret": v9_total,
                "worst_seed_regret": v9_worst,
            },
            "predictions": [
                {"model_choice": "HOLD"} for _ in range(choices[0])
            ]
            + [
                {"model_choice": "SELL"} for _ in range(choices[1])
            ],
        }


if __name__ == "__main__":
    unittest.main()