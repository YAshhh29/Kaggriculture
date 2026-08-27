import unittest

from analyze_wheat_trades import analyze_wheat_trades


def record(*, day, hour, price, action=None):
    return {
        "action": action,
        "observation": {
            "day": day,
            "hour": hour,
            "market": {
                "prices": {"WHEAT": price},
                "inventory": {"WHEAT": 10_000},
            },
        },
    }


class AnalyzeWheatTradesTests(unittest.TestCase):
    def test_aligns_action_with_previous_observation_quote(self) -> None:
        replay = {
            "steps": [
                [record(day=2, hour=3, price=20)],
                [
                    record(
                        day=2,
                        hour=4,
                        price=22,
                        action={
                            "market": [["BUY_PRODUCT", "WHEAT", 4]]
                        },
                    )
                ],
                [
                    record(
                        day=2,
                        hour=5,
                        price=24,
                        action={"market": [["SELL", "WHEAT", 2]]},
                    )
                ],
            ]
        }

        report = analyze_wheat_trades(replay, 0)

        self.assertEqual(report["buy"]["weighted_mean_quote"], 20.0)
        self.assertEqual(report["sell"]["weighted_mean_quote"], 22.0)
        self.assertEqual(report["daily_units"][0]["bought"], 4)
        self.assertEqual(report["daily_units"][0]["sold"], 2)


if __name__ == "__main__":
    unittest.main()
