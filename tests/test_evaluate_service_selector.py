import unittest

from research.evaluation.evaluate_service_selector import evaluate


class EvaluateServiceSelectorTests(unittest.TestCase):
    def test_compares_learned_with_both_fixed_arms(self) -> None:
        records = [
            {
                "features": {"player": 0.0},
                "label": 1,
                "outcomes": {
                    "0": {
                        "result": "loss",
                        "utility": -1001.0,
                        "terminal_margin": -1000.0,
                    },
                    "1": {
                        "result": "win",
                        "utility": 1001.0,
                        "terminal_margin": 1000.0,
                    },
                },
                "opponent": "control.py",
            }
        ]

        report = evaluate({"arm": 1}, records)

        self.assertEqual(report["learned"]["wins"], 1)
        self.assertEqual(report["baseline"]["losses"], 1)
        self.assertEqual(report["paired"]["wins"], 1)


if __name__ == "__main__":
    unittest.main()
