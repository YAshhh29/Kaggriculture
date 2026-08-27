import unittest

from research.evaluation.evaluate_future_labor import promotion


def result(wins: int, margin: float, errors: int = 0) -> dict:
    games = 4
    return {
        "summary": {
            "games": games,
            "wins": wins,
            "losses": games - wins - errors,
            "errors": errors,
            "mean_margin": margin,
        }
    }


def report(
    control: tuple[dict, dict],
    candidate: tuple[dict, dict],
) -> dict:
    return {
        "variants": {
            "submitted_control": {
                "alpha": control[0],
                "beta": control[1],
            },
            "future_labor": {
                "alpha": candidate[0],
                "beta": candidate[1],
            },
        }
    }


class EvaluateFutureLaborTests(unittest.TestCase):
    def test_promotes_more_wins_without_opponent_regression(self) -> None:
        verdict = promotion(
            report(
                (result(2, 0), result(2, 0)),
                (result(3, 10), result(2, 5)),
            )
        )

        self.assertEqual(verdict["decision"], "PROMOTE")
        self.assertTrue(all(verdict["checks"].values()))

    def test_rejects_one_opponent_regression_despite_more_wins(self) -> None:
        verdict = promotion(
            report(
                (result(2, 0), result(2, 0)),
                (result(4, 20), result(1, 20)),
            )
        )

        self.assertEqual(verdict["decision"], "REJECT")
        self.assertFalse(
            verdict["checks"]["no_opponent_win_regression"]
        )


if __name__ == "__main__":
    unittest.main()