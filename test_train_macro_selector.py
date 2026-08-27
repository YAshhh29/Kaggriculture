import unittest

from train_macro_selector import evaluate_tree, train_tree


def _record(value: float, compact: float, expanded: float) -> dict:
    return {
        "features": {"opponent_nonwheat": value, "player": 0.0},
        "outcomes": {
            "0": {
                "utility": compact,
                "result": "win" if compact > 0 else "loss",
            },
            "1": {
                "utility": expanded,
                "result": "win" if expanded > 0 else "loss",
            },
        },
        "label": 0 if compact > expanded else 1,
    }


class TrainMacroSelectorTests(unittest.TestCase):
    def test_learns_a_utility_improving_split(self) -> None:
        records = [
            _record(0.0, 1000, -1000),
            _record(0.2, 900, -900),
            _record(2.0, -800, 800),
            _record(3.0, -1000, 1000),
        ]

        model, score = train_tree(records, max_depth=1, min_leaf=2)
        evaluation = evaluate_tree(model, records)

        self.assertEqual(model["feature"], "opponent_nonwheat")
        self.assertEqual(evaluation["wins"], 4)
        self.assertEqual(evaluation["label_accuracy"], 1.0)
        self.assertEqual(score, 4_003_700)


if __name__ == "__main__":
    unittest.main()
